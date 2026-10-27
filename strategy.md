# @mindoverwant posting strategy

The weekly autopilot reads this file first, follows the CURRENT CADENCE, and updates the LOG and, when a decision point is reached, the cadence itself.

## CURRENT CADENCE
Mode: TEST_2_PER_DAY (started 2026-10-23, at the owner's request)
- Every day 10:00 AM America/Denver: quote-card POST
- Every day 6:00 PM America/Denver: REEL (music only, no voiceover)

## FALLBACK CADENCE (use if the test fails)
Mode: DAILY_MIX
- Fri 10:00 AM Reel, Sat 10:00 AM card, Sun 6:00 PM Reel, Mon 10:00 AM card, Tue 6:00 PM card, Wed 6:00 PM Reel, Thu 10:00 AM card

## THE TEST
- The owner started 2-per-day immediately, so there is no 1-per-day baseline week. The test checks for saturation instead.
- Test: two weeks of 2-per-day, 2026-10-23 to 2026-11-05 (week 1 = Oct 23-29, week 2 = Oct 30-Nov 5).
- Decision run: the Thursday run on 2026-11-05 (or the first run after it with a full 2 weeks of data).
- Decision rule:
  - KEEP 2-per-day if average reach per Reel in week 2 is at least 70% of week 1 AND followers gained in week 2 is at least what week 1 gained (or still clearly growing).
  - Also compare cards vs Reels: if quote cards average under a third of Reel reach and get few shares/saves, keep the daily Reel but cut cards to Mon/Wed/Fri.
  - Otherwise switch to the FALLBACK CADENCE (or, if Reels clearly beat cards on reach and shares, a Reel-heavy variant: daily Reel at 6 PM + quote cards Mon/Wed/Fri 10 AM).
  - If analytics are missing or too thin to judge, extend the test one more week and say so.
- Record the decision and the numbers behind it in the LOG, update CURRENT CADENCE, and tell the owner in the weekly message.

## LOG
- 2026-10-22: Page launched. First Reel published 9:04 PM and reported doing well by the owner. Baseline week scheduled at 1 post/day. Owner delegated the cadence decision; chose a 2-week 2-per-day test with the rule above.
- 2026-10-23: Owner requested an extra Reel today; posted 1:15 PM (on top of the 10 AM card), so the baseline week has 4 Reels and 4 cards.
- 2026-10-23: Owner said to start 2-per-day immediately. Filled Sat Oct 24 - Thu Oct 29 so every day has a 10 AM card and a 6 PM Reel (Tue card moved from 6 PM to 10 AM). Test window moved to Oct 23 - Nov 5.
- 2026-10-27 (mid-week check): 5 Reels so far = 301 views total (122, 36, 14, 110, 19). Avg watch time only 1.6-3.6s on 14.6s Reels, so most viewers swiped during the old 2.2s fade-in hook. 5 quote cards reached ~0-1 people each (feed posts barely reach non-followers on a ~1-follower page). Saturday 8 PM Reel (Metricool shifted it) was worst at 14 views; Thu 9 PM and Sun 6 PM best. Fix shipped: reel.py now shows the hook on frame 1 and Reels run ~10s; Oct 27-29 Reels re-rendered. Next: judge whether watch time rises; if cards stay near zero by Nov 5, cut them per the decision rule.
