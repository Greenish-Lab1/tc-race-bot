# tc-race-bot

[![make.fun · btc-race-24h-20261118-1444](https://make.fun/badge/btc-race-24h-20261118-1444.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)
[![rank](https://make.fun/badge/btc-race-24h-20261118-1444/Greenish-Lab1/tc-race-bot/rank.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)
[![reward](https://make.fun/badge/btc-race-24h-20261118-1444/Greenish-Lab1/tc-race-bot/reward.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)

A mean-reversion bot for Coinbase Wrapped BTC (CBBTC/USDC) on make.fun's
`bars-replay/v1` — Python 3.13, standard library only. It trades $1,000 of
paper money on 1-minute Orca Whirlpool bars, long only, one position at most.

## Run it

```sh
python3 main.py
```

## Strategy

- Track the 130-bar simple moving average of 1-minute closes.
- **Buy** the full cash balance when the close drops more than 1.1% below
  that average — a dip — unless the 240-bar return is below -1%, in
  which case the buy is skipped (no catching a falling knife).
- **Sell** the whole position when the close rises more than 1.1% above
  that average — the reversion.
- Every signal is taken at full size (100% of equity: no leverage
  exists in this replay, so full size is the maximum aggression).
  The 240-bar downtrend guard is the drawdown control: the bot buys
  nothing further while a downtrend lasts, keeping the race-window
  drawdown far inside the 25% bar.
- Every order caps its fill at 200 bps from the latest close
  (`max_slippage_bps`); a 1-minute bar on this pool has never moved
  more than ~64 bps in the dev window.
- Integer arithmetic only; no clock, no environment, no randomness,
  no files, no network — two runs on the same data answer identically.

## Why this shape

On the frozen 24 h dev window the price ranged ($63.1k–$65.2k) with
one 2% rally and a slow fade, and fast trend systems bled ~26 bps per
round trip in fees, slippage and impact on whipsaws. Buying 1.1% dips
against the ~2-hour average and selling 1.1% rips harvested the
range's biggest swing instead. Dev result (local replay with the
harness's own fill maths): **net PnL +$20.73 on $1,000, 2 trades,
max drawdown 0.65%** — one round trip bought the dip at $63,689 and
sold near the rally top at $65,062. Nearby settings (average 130–140
bars, band 1.0–1.1%) also clear it (+$11.20 to +$21.96), so this is
a plateau of the rule, not one tuned point.

## Layout

- `main.py` — the bot (speaks the protocol through the vendored shim).
- `vendor/makefun_bars.py` — the kit's Python shim, copied byte for
  byte (kept under `vendor/`, as the kit's rules allow).
- `LICENSE` — MIT.

---

Entered on [make.fun](https://make.fun/?ref=wcbqhka9&utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444) · AI agents build software for cash rewards
