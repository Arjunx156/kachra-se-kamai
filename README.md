# Kachra se Kamai · कचरा से कमाई · "earn from your waste"

Snap a photo of your dustbin. AI tells you what's in it, what it's worth, and what's headed to Delhi's landfill. Your recyclables are bundled with your neighbours' and picked up by a local waste picker at a fair, transparent price. Branded plastic packaging earns extra rewards from brands' take-back (EPR) obligations, which are simulated in this demo. A 3D model of a landfill mountain, next to Qutub Minar for scale, shrinks as the city diverts waste.

Built for **Environmental Hacks** (event 02 of the Bharat Builds Tour, WeMakeDevs × AWS), **Waste and Energy** track, October 2026.

## The problem

- **Delhi generates 11,852 tonnes of waste a day and processes only 7,611.** The rest goes to dumpsites such as Bhalswa and Ghazipur. ([CPCB affidavit to the NGT, reported 1 Jan 2026](https://madhyamamonline.com/amp/india/delhi-processes-only-64-of-daily-waste-rest-dumped-at-bhalswa-ghazipur-landfills-cpcb-tells-ngt-1482173))
- **Ghazipur landfill was reported at 65 m tall in 2018**, only a few metres short of **Qutub Minar's 72.5 m**. ([Business Today, 3 Sep 2018](https://www.businesstoday.in/latest/economy-politics/story/east-delhi-ghazipur-garbage-dump-now-almost-as-tall-as-qutub-minar-110974-2018-09-03); [UNESCO](https://whc.unesco.org/en/list/233))
- Households can't see their own contribution, have no incentive to segregate, and selling recyclables means haggling with the kabadiwala over guessed weights.
- Informal waste pickers do much of the city's recycling, but they work without routes or guaranteed prices and remain invisible in the system.
- Under India's Extended Producer Responsibility (EPR) rules for plastic packaging, brands must meet take-back targets, but traceable post-consumer collection data from households is hard to get.

## What it does

| User | What they get |
|---|---|
| Household | Money for recyclables at transparent rates, EPR brand rewards, doorstep pickup with no haggling, and a segregation score with an AI tip after every scan |
| Waste picker | Pre-bundled pickups on a map in route order, a guaranteed 40% share, and an earnings record |
| Recycler | A rate board (₹/kg) that drives all pricing, and pre-sorted incoming supply |
| RWA / city | Live counters, a society leaderboard, and the landfill mountain |
| Brand (simulated) | Photo-backed collection of their packaging for EPR. **Simulated; there is no real brand integration.** |

### The three AI-assisted workflows

1. **Bin Vision:** Amazon Bedrock Converse API with **Amazon Nova Lite** (image + text). It returns the items, materials, estimated kg, readable brands, a segregation score and a one-line tip. The output is validated with pydantic, retried once if it isn't valid JSON, clamped, and rejected with a friendly message if the photo isn't of waste.
2. **Pricing:** deterministic Python, with no AI involved. ₹ = Σ kg × rate over recyclables. Households get 60% pro rata and pickers 40%, and the split sums exactly to the paisa. EPR reward is ₹0.50 per branded plastic packet, capped at ₹10 per scan.
3. **Kamai Coach:** a **Strands Agents** agent on Bedrock with four tools over the household's own data. It writes a 3-action weekly plan that cites the household's real numbers, and the UI shows which tools it called.

## Architecture

See [docs/architecture.md](docs/architecture.md) for the diagram and the flows. In short:

**React + Vite SPA (AWS Amplify Hosting) → API Gateway HTTP API → 8 Python 3.12 Lambda functions (AWS SAM) → DynamoDB (6 tables), S3 (photos), Amazon Bedrock (Nova Lite), Strands Agents.**

### Where AWS fits

| Service / tool | Why |
|---|---|
| **AWS SAM** (open source) | The whole backend is one `template.yaml`: API, functions, tables, bucket, IAM, layer |
| **Strands Agents** (AWS open source) | The coach agent and its tool-calling loop |
| Amazon Bedrock · Amazon Nova Lite | Bin photo analysis (Converse API, image input) and the coach's model |
| AWS Lambda (arm64) | One function per API resource, with least-privilege policies |
| Amazon API Gateway (HTTP API) | REST endpoints with CORS |
| Amazon DynamoDB | Users, societies, scans, bundles, rates, and atomic stats counters |
| Amazon S3 | Private photo storage via presigned PUT, 30-day lifecycle |
| AWS Amplify Hosting | Frontend hosting and CI from this GitHub repo |

## What's real and what's simulated

- **Real:** the AI analysis of your actual photo, the pricing and payout maths, the bundling, routing and transactions, the stats, and the coach's tool calls over real stored data. Cited facts are linked above.
- **Demo values (labelled "Demo" in the UI):** the ₹/kg rate board (not market data; the recycler role can edit it), the 60/40 split, the ₹0.50 EPR reward, the 1.5 kg bundle threshold, and the mountain's target kg.
- **Simulated:** the brand/EPR partner, payments (no money moves), and identity (a demo role switcher instead of sign-in).
- **AI estimates (labelled "AI estimate"):** item weights and the ₹ value at scan time. The final value is set at collection.
- **Illustrative:** the mountain starts at Ghazipur's reported height and shrinks as kg are diverted on this platform. It does not measure the real landfill.
- **Demo data:** all people and society names are fictional. Neighbourhood names are real Delhi areas with approximate coordinates.

## Run it yourself

### Prerequisites
AWS account with Bedrock model access for **Amazon Nova Lite** in `us-east-1`. Enable it under *Bedrock console → Model access*, and confirm the inference profile ID `us.amazon.nova-lite-v1:0`. You also need AWS CLI v2, AWS SAM CLI, Python 3.12, and Node 20+.

### Backend
```bash
cd backend
sam build
sam deploy --guided            # first time: stack kachra-se-kamai, us-east-1, set AdminKey (>= 12 chars)
# later: sam deploy --parameter-overrides AdminKey=<your key>
API_URL=<ApiUrl output>
curl "$API_URL/health"
curl -X POST "$API_URL/admin/seed" -H "x-admin-key: <AdminKey>"   # demo societies, users, rates, 40 scans
```

### Frontend
```bash
cd frontend
cp .env.example .env.local     # set VITE_API_URL=<ApiUrl>
npm ci
npm run dev
```
**To host it on Amplify:** open the Amplify console → *Host web app* → GitHub → this repo, with app root `frontend/`. The build spec is in `amplify.yml`. Add the environment variable `VITE_API_URL`, then add the SPA rewrite: source `</^[^.]+$|\.(?!(css|gif|ico|jpg|js|png|txt|svg|woff|woff2|ttf|map|json)$)([^.]+$)/>`, target `/index.html`, type `200 (Rewrite)`.

### Local preview (no AWS account needed)
Runs the real Lambda handlers against mocked DynamoDB/S3 (moto), seeded with demo data. Bedrock isn't available locally, so scans return a sample AI reply (labelled in the tip) and the coach shows a notice.
```bash
cd backend && .venv/Scripts/pip install "moto[server]" && .venv/Scripts/python local/server.py   # API on :8787
cd frontend && echo VITE_API_URL=http://127.0.0.1:8787 > .env.local && npm run dev             # http://127.0.0.1:5173
```

### Tests
```bash
cd backend && python -m venv .venv && .venv/Scripts/pip install -r requirements.txt   # (bin/ on macOS/Linux)
.venv/Scripts/python -m pytest --cov=src      # 62 tests: pricing, vision parsing, bundling, full API flow on moto
cd ../frontend && npm test
```

### Cost and clean-up
Everything is serverless and on-demand. Set an AWS Budgets alert at $5. After judging, run `sam delete` and delete the Amplify app.

## AI tools used
- **Claude Code** (Anthropic): code generation for the backend, frontend, tests and docs.
- **Claude** (Anthropic): ideation and planning of the spec.

## Credits and licences
- This project: [MIT](LICENSE).
- Map tiles and data © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors (ODbL), via Leaflet (BSD-2-Clause) and react-leaflet (Hippocratic-2.1).
- three.js (MIT), @react-three/fiber and @react-three/drei (MIT), React (MIT), React Router (MIT), Tailwind CSS (MIT), Vite (MIT).
- Strands Agents (Apache-2.0), boto3 (Apache-2.0), pydantic (MIT), moto (Apache-2.0), pytest (MIT).
- Fonts: Baloo 2 and Mukta via Google Fonts (SIL Open Font License 1.1).
- The 3D landfill and tower are procedural geometry written for this project. No third-party 3D models are used.
- Facts are cited inline above.
