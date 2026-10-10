# Kachra se Kamai: submission writeup (draft)

## 1. Problem
Delhi generates **11,852 tonnes of waste a day and processes only 7,611**. The rest goes to dumpsites like Ghazipur and Bhalswa ([CPCB affidavit to the NGT, reported Jan 2026](https://madhyamamonline.com/amp/india/delhi-processes-only-64-of-daily-waste-rest-dumped-at-bhalswa-ghazipur-landfills-cpcb-tells-ngt-1482173)). Ghazipur was reported at **65 m in 2018**, close to Qutub Minar's **72.5 m** ([Business Today](https://www.businesstoday.in/latest/economy-politics/story/east-delhi-ghazipur-garbage-dump-now-almost-as-tall-as-qutub-minar-110974-2018-09-03), [UNESCO](https://whc.unesco.org/en/list/233)). Households can't see their share and have no reason to segregate. Waste pickers do much of the recycling without routes or fair prices. Brands need traceable post-consumer collection to meet their plastic EPR targets.

## 2. Solution and who benefits
Snap your dustbin, and AI itemises it: materials, estimated kg, ₹ value, what's going to landfill, a segregation score and one practical tip. Recyclables from the same society are bundled into one pickup for a local waste picker, priced from a recycler's posted rate board. Households get 60% and the picker a guaranteed 40%, with no haggling. Branded plastic packets earn an extra (simulated) EPR reward. A city view shows live counters, a society leaderboard, and a 3D landfill mountain next to Qutub Minar that shrinks as kg are diverted.

| User | Gets |
|---|---|
| Household | Transparent money for recyclables, brand rewards, doorstep pickup, a score and tips |
| Waste picker | Pre-bundled pickups, a route map, a guaranteed share, an earnings record |
| Recycler | Pre-sorted supply at the rates they set |
| RWA / city | Verified data, leaderboard, live mountain |
| Brand (simulated) | Photo-backed EPR collection data |

## 3. How it works
1. **Bin Vision:** Amazon Bedrock Converse with Amazon Nova Lite reads the photo and returns strict JSON. The code validates it, retries once on bad JSON, clamps weights, and rejects photos that aren't waste.
2. **Pricing is deterministic code, never the LLM.** It is unit-tested for mixed materials, rounding, the exact 60/40 split and the EPR cap.
3. **Kamai Coach:** a Strands Agents agent with four tools over the household's own DynamoDB data writes a 3-action weekly plan citing their real numbers. The UI shows which tools it checked.

Bundling groups scans by society once they reach 1.5 kg (or once any scan is 12 h old), in DynamoDB transactions. Pickups are ordered by nearest neighbour. Accept and collect use conditional writes, so a bundle can't be taken or paid twice.

## 4. Where AWS fits
- **AWS SAM** (open source): the whole backend in one template, covering the HTTP API, 8 Lambda functions, 6 DynamoDB tables, the S3 bucket, IAM and the Strands layer.
- **Strands Agents** (AWS open source): the coach agent.
- **Amazon Bedrock (Nova Lite):** image understanding and the coach's reasoning.
- **Lambda (arm64), API Gateway HTTP API, DynamoDB (atomic counters, GSIs, transactions), S3 (presigned uploads, lifecycle).**
- **AWS Amplify Hosting:** the React frontend, deployed from GitHub.

## 5. What's real and what's simulated
- Real: AI analysis of your photo, all pricing and payout maths, bundling, routing, stats, and the coach's tool use.
- Demo values (labelled in the UI): the ₹/kg rates, the 60/40 split, the ₹0.50 EPR reward, the bundle threshold, and the mountain's target.
- Simulated: the brand/EPR partner, payments, and sign-in (a role switcher is used instead).
- AI estimates (labelled in the UI): weights and the scan-time ₹ value.
- The mountain is **illustrative**. It is not a measurement of the real landfill.

## 6. What's next
Real recycler partners and live rates, a brand EPR integration through CPCB's centralised portal, a pilot with an RWA and MCD ward, picker onboarding with Hindi voice guidance, and Cognito sign-in.

## 7. AI tools used
Claude Code (code generation for the backend, frontend, tests and docs) and Claude (ideation and planning).

## 8. Credits and licences
MIT licence. OpenStreetMap data (ODbL) via Leaflet / react-leaflet. three.js, React Three Fiber/drei, React, Tailwind and Vite (MIT). Strands Agents and boto3 (Apache-2.0). Fonts Baloo 2 and Mukta (OFL). All 3D geometry is procedural and original. The full list is in the README.
