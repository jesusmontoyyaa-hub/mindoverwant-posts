# @mindoverwant posting strategy

The weekly autopilot reads this file first, follows the CURRENT CADENCE, and updates the LOG and, when a decision point is reached, the cadence itself.

## CURRENT CADENCE
Mode: TEST_2_PER_DAY (started 2026-10-23, at the owner's request)
- Every day 10:00 AM America/Denver: quote-card POST
- Every day 6:00 PM America/Denver: REEL (no voiceover)
- REEL FORMAT (owner, 2026-10-30): exactly 7.1 seconds, quote typed out with a typewriter effect (reel.py does both), and a TRENDING Instagram audio attached in Metricool via instagramData.audioConfiguration {"audioId":"<song title artist>","audioVolume":100,"videoVolume":0}. Each run, web-search this week's trending Instagram Reels audio and pick tracks that fit motivational/discipline content; vary tracks across the week. If Metricool rejects a track (ambiguous match, or not available to this account), retry with the numeric id it lists or the next track; never leave a Reel scheduled without audio unless every option fails, and say so.

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
- 2026-10-29 (weekly run, test week 1 Oct 23-29): 6 Reels published through Oct 28 = 311 views / 282 reach (avg ~47 reach; 122, 36, 14, 110, 19, 10). 5 quote cards = 3 reach total (avg 0.6), 0 shares/saves. Reels interactions: 1 like + 1 save total. Followers: 1 (+0 net this week per Metricool). Account reach by day: 109 Oct 22, 34 Oct 23, 97 Oct 25 (Sun Reel), single digits otherwise. First frame-1-hook Reel (Tue) had best avg watch time (3.9s) but only 10 views. Best Reels: direct "you/tonight" callouts and "quiet work" theme. Cards are far below 1/3 of Reel reach - on track to be cut on the Nov 5 decision run. Not a decision run; kept 2-per-day for week 2 (Oct 30-Nov 5), 10 AM / 6 PM confirmed as peak hours by Metricool best-time. Content leans into direct-address hooks and "send this to" share prompts.
- 2026-10-30: Owner asked for typewriter text, 7.1 s Reels and trending Instagram audio. reel.py updated; Oct 30 - Nov 5 Reels re-rendered (7.1 s, typewriter) and swapped into Metricool at the same times. Trending audio could NOT be attached: Metricool returned 403 'Instagram audio catalog not available' (account must be an Instagram Business account linked to a Facebook Page). Reels still carry the built-in original music. Each run: try audioConfiguration once; if it 403s, schedule without it and remind the owner.
- 2026-10-29: Owner asked for an extra Reel to preview the new 7.1 s typewriter format; posted ~8:00 PM.
