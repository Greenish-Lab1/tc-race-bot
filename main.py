"""tc-race-bot: a mean-reversion bot for cbBTC (CBBTC/USDC) on make.fun's
bars-replay/v1, Python 3.13, standard library only.

Strategy (one asset, long only, full-size in/out, no leverage):
  - Keep the 130-bar simple moving average of 1-minute closes.
  - BUY the whole cash balance when the latest close is more than 1.1%
    below that average (a dip) — but never into a steep downtrend: the
    buy is skipped while the 240-bar return is below -1% (falling-knife
    guard; with fewer than 240 bars of history the guard passes).
  - SELL the whole position when the latest close is more than 1.1%
    above that average (the reversion).
  - One open position at most; at most one order per reply.
  - Every order caps its fill at 200 bps from the latest close
    (max_slippage_bps): a 1-minute bar on this pool has never moved
    more than ~64 bps in the dev window, so 200 bps admits every
    normal fill and still refuses a wild one.

Why this shape: on the frozen 24 h dev window the price ranged
(about $63.1k-$65.2k) with one 2% rally and a slow fade, and fast
trend systems bled ~26 bps per round trip in fees, slippage and
impact on whipsaws. Buying 1% dips against the 2-hour average and
selling 1.1% rips harvested the range's biggest swing instead:
dev net PnL +$20.73 on $1,000 (2 trades, max drawdown 0.65%) — one
round trip bought the dip at $63,689 and sold near the rally top
at $65,062. The same rule at nearby settings (average 130-140
bars, band 1.0-1.1%) also clears the dev gate (+$11.20 to
+$21.96), so the result is a plateau of the rule, not one tuned
point. Every signal is taken at full size (100% of equity: no
leverage exists in this replay, so full size is the maximum
aggression); the 240-bar downtrend guard is the drawdown control,
keeping the race-window drawdown far inside the 25% bar — the
bot's worst case is one position bought early in a decline, and
it buys nothing further while the downtrend lasts.

Deterministic: integer arithmetic only, no clock, no environment,
no randomness, no files, no network. The only state is the list
of closes seen so far.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"

# Strategy parameters (in basis points / bars).
AVG_BARS = 130          # bars in the moving average
BAND_BPS = 110          # buy below avg*(1-band), sell above avg*(1+band)
TREND_BARS = 240        # bars for the downtrend guard
TREND_MIN_BPS = -100    # skip a buy while the TREND_BARS return is below this
MAX_SLIPPAGE_BPS = 200  # cap on a fill's move from the latest close

_closes = []  # closes seen so far, newest last (ints, price_scale 5)


def _sma_sum(n):
    return sum(_closes[-n:])


def on_batch(state, batch):
    # Only a batch that actually carries a CBBTC bar advances the strategy.
    bar = None
    for b in batch["bars"]:
        if b["symbol"] == SYMBOL:
            bar = b
            break
    if bar is None or state.warming_up:
        return []
    close = int(bar["c"])
    _closes.append(close)

    if len(_closes) < AVG_BARS:
        return []
    avg_sum = _sma_sum(AVG_BARS)  # sum of the last AVG_BARS closes
    # close < avg * (1 - BAND_BPS/10000)  <=>  close * AVG_BARS * 10000 < avg_sum * (10000 - BAND_BPS)
    below = close * AVG_BARS * 10000 < avg_sum * (10000 - BAND_BPS)
    # close > avg * (1 + BAND_BPS/10000)  <=>  close * AVG_BARS * 10000 > avg_sum * (10000 + BAND_BPS)
    above = close * AVG_BARS * 10000 > avg_sum * (10000 + BAND_BPS)

    holding = state.positions.get(SYMBOL)
    qty = holding.qty if holding is not None else 0

    if qty == 0 and below:
        # Downtrend guard: skip the dip-buy while the TREND_BARS return
        # is below TREND_MIN_BPS. With less history than that, pass.
        if len(_closes) > TREND_BARS:
            old = _closes[-TREND_BARS - 1]  # the close TREND_BARS bars back
            # (close/old - 1) * 10000 >= TREND_MIN_BPS
            #   <=> close * 10000 >= old * (10000 + TREND_MIN_BPS)
            if close * 10000 < old * (10000 + TREND_MIN_BPS):
                return []
        if state.cash > 0:
            return [{
                "side": "buy",
                "symbol": SYMBOL,
                "notional_quote_units": state.cash,
                "max_slippage_bps": MAX_SLIPPAGE_BPS,
            }]
        return []

    if qty > 0 and above:
        return [{
            "side": "sell",
            "symbol": SYMBOL,
            "qty": qty,
            "max_slippage_bps": MAX_SLIPPAGE_BPS,
        }]

    return []


makefun_bars.run(on_batch)
