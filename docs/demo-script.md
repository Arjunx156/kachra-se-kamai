# Demo video script (target 2:50, hard limit 3:00)

**Before recording:**
- `POST /admin/seed` for a clean demo world.
- Have a real, mixed bin ready (PET bottle, chips packet with a readable brand, milk pouch, peels).
- Phone open on the Amplify URL. City view open in a second desktop tab.
- Don't refresh bundles until the picker shot.

| Time | Shot | Voice-over |
|---|---|---|
| 0:00–0:20 | Your own phone footage of a garbage heap, or an animated graphic of the mound rising beside Qutub Minar (the app's City view works). On screen: "11,852 t/day · CPCB 2026" and "Ghazipur: 65 m (2018) · Qutub Minar: 72.5 m". | "Delhi makes almost twelve thousand tonnes of waste a day. Ghazipur landfill was reported at 65 metres, nearly as tall as Qutub Minar. Every home adds to it, and nobody sees their share." |
| 0:20–0:35 | Landing page. | "Kachra se Kamai: your waste pays you, and the mountain shrinks." |
| 0:35–1:20 | Household → Snap → camera → "Check my bin" → progress steps → Result. Scroll: items, kg split, "You could earn ₹X" (AI estimate), brand rewards, score and tip, "Added to tonight's pickup". | "Priya snaps her bin. Amazon Nova on Bedrock lists every item and spots the brands. The rupees are calculated by code, not by the AI, from the recycler's rate board. She gets a segregation score and one tip." |
| 1:20–1:55 | Picker → Refresh → map with numbered stops → Accept Shanti Apartments → Mark collected → confirm → "₹X added to your earnings". | "Scans from the same society become one pickup. Ramesh sees his route, a guaranteed 40% share, and no haggling. One tap, and every household is paid." |
| 1:55–2:15 | City view: the mountain shrinks, the green "kept out of landfill" toast appears, counters tick, the leaderboard reorders. | "Every kilo collected shrinks the mountain. It's illustrative, but the data behind it is real." |
| 2:15–2:35 | Household → Coach → "Get my weekly plan" → "Checked: your last 7 days, current rates, society rank". | "Kamai Coach is a Strands agent. It reads Priya's actual scans before giving advice, and you can see what it checked." |
| 2:35–2:55 | `docs/architecture.md` diagram, then quick console shots: CloudFormation stack (SAM), Lambda list, DynamoDB tables, Bedrock model access. | "All on AWS: SAM and Strands Agents, both open source, plus Bedrock, Lambda, DynamoDB, S3 and Amplify." |
| 2:55–3:00 | Repo URL card. | "Kachra se Kamai. github.com/Arjunx156/kachra-se-kamai" |

**Rules:**
- Say "demo rates" once when the ₹ first appears.
- Use only your own footage, or graphics you made.
- Upload as unlisted, then check the link in a signed-out browser.
