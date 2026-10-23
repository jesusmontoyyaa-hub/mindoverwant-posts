# @mindoverwant posting strategy

The weekly autopilot reads this file first, follows the CURRENT CADENCE, and updates the LOG and, when a decision point is reached, the cadence itself.

## CURRENT CADENCE
Mode: TEST_2_PER_DAY (started week of 2026-10-30)
- Every day 10:00 AM America/Denver: quote-card POST
- Every day 6:00 PM America/Denver: REEL (music only, no voiceover)

## FALLBACK CADENCE (use if the test fails)
Mode: DAILY_MIX
- Fri 10:00 AM Reel, Sat 10:00 AM card, Sun 6:00 PM Reel, Mon 10:00 AM card, Tue 6:00 PM card, Wed 6:00 PM Reel, Thu 10:00 AM card

## THE TEST
- Baseline: week of 2026-10-23 to 2026-10-29, one post per day (3 Reels, 4 cards).
- Test: two weeks of 2-per-day, 2026-10-30 to 2026-11-12.
- Decision run: the Thursday run on 2026-11-12 (or the first run after it with a full 2 weeks of data).
- Decision rule:
  - KEEP 2-per-day if average reach per Reel in the test weeks is at least 70% of the baseline average AND followers gained per week is higher than in the baseline week.
  - Otherwise switch to the FALLBACK CADENCE (or, if Reels clearly beat cards on reach and shares, a Reel-heavy variant: daily Reel at 6 PM + quote cards Mon/Wed/Fri 10 AM).
  - If analytics are missing or too thin to judge, extend the test one more week and say so.
- Record the decision and the numbers behind it in the LOG, update CURRENT CADENCE, and tell the owner in the weekly message.

## LOG
- 2026-10-22: Page launched. First Reel published 9:04 PM and reported doing well by the owner. Baseline week scheduled at 1 post/day. Owner delegated the cadence decision; chose a 2-week 2-per-day test with the rule above.
