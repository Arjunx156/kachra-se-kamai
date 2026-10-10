# Kachra se Kamai — Full Build Spec

> **For Claude Code:** This file is the single source of truth for this project. Read it fully before writing any code. Build strictly in the milestone order in §13. After each milestone, run the tests, make sure the app still works end to end, and commit. Do not skip ahead to stretch goals until every core milestone works. If something in this spec is impossible or clearly wrong (e.g. an AWS API has changed), stop, explain the problem in one paragraph, propose the smallest fix, and continue only after confirming. Never invent statistics, prices, or facts. Anything that is a demo value must be labelled as one in the code and in the UI.

---

## 1. Context: the hackathon (hard constraints)

- **Event:** Environmental Hacks, event 02 of the Bharat Builds Tour (WeMakeDevs × AWS). Runs online Oct 8–11, 2026.
- **Track:** Waste and Energy.
- **Team:** solo (Arjun).
- **Deadline:** Sunday, Oct 11, 2026. The exact cutoff time is published on https://www.wemakedevs.org/aws/env/schedule. Check it and treat it as absolute; the form closes at the deadline.
- **Rules that affect how we build:**
  1. **New work only.** The project must be started after the hackathon opened. Make the first git commit today and commit often. The judges check that repo history matches the event dates.
  2. **Must use AWS, and the demo video must show it.** At least one AWS open-source tool or deployment on AWS. We do both: AWS SAM CLI and Strands Agents (open source) plus deployed AWS services.
  3. **Submission = 3 things:** a public GitHub repo, a demo video of 3 minutes or less on YouTube (public or unlisted), and a short writeup (problem, build, where AWS fits).
  4. **List AI coding tools used** in the writeup (Claude Code, Claude).
  5. **Anything not written by us needs a credit and a compatible licence.**
  6. **No live demo.** If it isn't in the video, it doesn't count. Features that exist only in the writeup don't count.
- **Judging criteria:** (1) Idea and impact, (2) Built on AWS, (3) Design and usability, (4) Execution: *one feature that works beats five that almost do*, (5) Demo video.

**Implication:** Working core > breadth. Every milestone must leave the app in a demoable state.

---

## 2. The idea in one line

**Kachra se Kamai ("earn from your waste")**: snap a photo of your dustbin, and AI tells you what's in it, what it's worth, and what's headed to Delhi's landfill mountain. Your recyclables are then bundled with your neighbours' and picked up by a local waste picker at a fair, transparent price. Branded plastic packaging earns you extra rewards funded by brands' legal take-back (EPR) obligations. A live 3D model of Delhi's landfill mountain shrinks as the city diverts waste.

### Problem statement (for README and writeup)

- Delhi produces on the order of 11,000 tonnes of municipal solid waste a day, and much of it ends up at landfill sites such as Ghazipur, Bhalswa and Okhla. Ghazipur has been reported at around 65 m, approaching the height of Qutub Minar (~73 m). **Verify these figures from a reliable source (e.g. news reports, CPCB/MCD documents) and cite them in the README before using them in the video. If you can't verify a number, don't use it.**
- Households can't see their contribution, there's no incentive to segregate, and selling recyclables means haggling with the kabadiwala over guessed weights.
- Informal waste pickers do most of India's recycling but are unpaid for that service, work without routes or guaranteed prices, and are invisible in the system.
- Brands must meet plastic packaging take-back targets under India's Extended Producer Responsibility (EPR) rules (Plastic Waste Management Rules, CPCB's centralised EPR portal), but verified, traceable post-consumer collection data from households is hard to obtain.

### Why each user benefits (this must be obvious in the UI)

| User | What they get |
|---|---|
| Household | Money for recyclables at transparent rates, EPR brand rewards, doorstep pickup with no haggling, and a clear daily score and tips |
| Waste picker | Pre-bundled pickups, a planned route, a guaranteed fair price, and a visible earnings record |
| Recycler / aggregator | Steady, pre-sorted supply at the rates they set |
| RWA / city view | Verified waste data, society leaderboard, and the live landfill mountain |
| Brand (simulated) | Verified, photo-backed collection of their packaging for EPR. **Simulated in this demo; no real brand integration.** |

---

## 3. Scope

### Core (must ship, must appear in the video)
1. Household: photograph the bin → AI analysis → itemised result (materials, estimated kg, ₹ value, landfill vs recyclable vs compostable, segregation score, brand packets detected) → saved to history and wallet.
2. Pricing engine: deterministic ₹ calculation from the recycler rate board. **The LLM never computes money.**
3. Bundling: pending recyclables from households in the same society are grouped into pickup bundles.
4. Picker app: list and map of open bundles in route order → accept → mark collected → payouts split and credited.
5. Recycler: rate board (₹/kg per material) that drives all pricing.
6. City view: live counters (kg scanned, kg diverted, ₹ paid out), society leaderboard, and the 3D landfill mountain that shrinks as kg are diverted.
7. AI coach: Strands Agents agent that writes each household a weekly plan using tools over their real scan data.
8. Deployed on AWS: SAM backend, Amplify-hosted frontend. Seed script for realistic demo data.

### Stretch (only after core is fully working and committed)
- S1. Step Functions pipeline for scan processing (async, visible in the AWS console for the video).
- S2. Cognito sign-in with role groups (replacing the demo role switcher).
- S3. Amazon Polly Hindi voice for the picker ("Agla stop: Green Park Society, 6 kilo").
- S4. Amazon Location Service route calculation instead of nearest-neighbour ordering.
- S5. EventBridge scheduled bundling every 15 minutes, plus SNS notification to pickers.
- S6. Hindi/English UI toggle across all screens.

### Explicitly out of scope
Real payments, real brand integrations, real MCD integration, native mobile apps, hardware.

---

## 4. Tech stack (decided; do not change without asking)

| Layer | Choice |
|---|---|
| Frontend | React 18 + Vite + TypeScript + Tailwind CSS + React Router |
| 3D mountain | three.js via `@react-three/fiber` + `@react-three/drei` |
| Map | Leaflet + `react-leaflet` with OpenStreetMap tiles (attribution required) |
| Backend | Python 3.12 AWS Lambda functions, defined in **AWS SAM** (`template.yaml`) |
| API | API Gateway **HTTP API** with CORS |
| Database | DynamoDB (on-demand billing) |
| Image storage | S3, uploads via presigned PUT URLs |
| Vision AI | Amazon Bedrock **Converse API**, model **Amazon Nova Lite** (supports image input). Use the US cross-region inference profile `us.amazon.nova-lite-v1:0`. Confirm the exact ID in the Bedrock console and make it a SAM parameter. |
| Agent | **Strands Agents SDK** (AWS open source, `strands-agents` on PyPI) with `BedrockModel`. Check the current Strands docs for exact import paths before writing code. |
| Validation | `pydantic` v2 |
| Tests | `pytest` (backend), Bedrock mocked |
| Hosting | AWS Amplify Hosting for the frontend |
| Region | `us-east-1` for everything |

---

## 5. Repository structure

```
kachra-se-kamai/
├── README.md                  # problem, solution, architecture, setup, AWS services, AI tools used, credits
├── PROJECT_SPEC.md            # this file
├── LICENSE                    # MIT
├── docs/
│   ├── architecture.md        # Mermaid diagram of the architecture
│   ├── writeup.md             # submission writeup draft
│   └── demo-script.md         # 3-minute video script
├── backend/
│   ├── template.yaml
│   ├── samconfig.toml
│   ├── requirements.txt       # pydantic, strands-agents (boto3 is in the Lambda runtime but pin it for local tests)
│   ├── src/
│   │   ├── handlers/
│   │   │   ├── uploads.py     # POST /uploads
│   │   │   ├── scans.py       # POST /scans, GET /scans, GET /scans/{scanId}
│   │   │   ├── users.py       # GET /me, POST /users
│   │   │   ├── bundles.py     # POST /bundles/build, GET /bundles, POST /bundles/{id}/accept, POST /bundles/{id}/collect
│   │   │   ├── rates.py       # GET /rates, PUT /rates/{material}
│   │   │   ├── stats.py       # GET /stats/city, GET /leaderboard
│   │   │   ├── coach.py       # POST /coach
│   │   │   └── admin.py       # POST /admin/seed, POST /admin/reset
│   │   └── lib/
│   │       ├── materials.py   # material enum + categories
│   │       ├── models.py      # pydantic models
│   │       ├── vision.py      # Bedrock bin analysis
│   │       ├── pricing.py     # deterministic pricing + payout split
│   │       ├── bundling.py    # grouping + route ordering
│   │       ├── stats.py       # atomic counter updates
│   │       ├── db.py          # DynamoDB helpers (float <-> Decimal)
│   │       ├── http.py        # response helpers, CORS, error format
│   │       └── config.py      # env vars + DEMO constants
│   └── tests/
│       ├── test_pricing.py
│       ├── test_bundling.py
│       ├── test_vision_parsing.py
│       └── fixtures/          # sample model outputs (JSON). Bin photos taken by Arjun himself, never downloaded images.
└── frontend/
    ├── index.html
    ├── vite.config.ts
    ├── tailwind.config.js
    ├── .env.example           # VITE_API_URL=
    └── src/
        ├── main.tsx
        ├── App.tsx            # router + role switcher
        ├── api.ts             # typed API client
        ├── types.ts
        ├── i18n.ts            # EN/HI strings (stretch S6)
        ├── lib/compressImage.ts
        ├── components/        # MaterialChip, KgSplitBar, WalletCard, ScoreRing, Mountain3D, BundleCard, DemoBadge
        └── pages/
            ├── Landing.tsx
            ├── household/{Home,Snap,Result,History,Coach}.tsx
            ├── picker/{Bundles,BundleDetail,Earnings}.tsx
            ├── recycler/{RateBoard,Incoming}.tsx
            └── city/CityView.tsx
```

---

## 6. Materials and categories (`lib/materials.py`)

| Code | Display (EN / HI) | Category | Notes |
|---|---|---|---|
| `PET_BOTTLE` | PET bottles / प्लास्टिक बोतल | recyclable | water and cold-drink bottles |
| `HARD_PLASTIC` | Hard plastic / सख्त प्लास्टिक | recyclable | tubs, containers, caps |
| `MILK_POUCH` | Milk pouches / दूध की थैली | recyclable | LDPE |
| `MULTILAYER_PACKET` | Chips / snack packets / चिप्स के पैकेट | recyclable (EPR) | hard to recycle; collected for EPR co-processing |
| `PAPER` | Paper / newspaper / कागज़ | recyclable | |
| `CARDBOARD` | Cardboard / गत्ता | recyclable | |
| `METAL` | Metal cans / धातु | recyclable | |
| `GLASS` | Glass / कांच | recyclable | |
| `E_WASTE` | E-waste / ई-कचरा | recyclable | batteries, cables, small electronics; flag for safe handling |
| `WET_ORGANIC` | Wet / kitchen waste / गीला कचरा | compostable | |
| `SANITARY` | Sanitary waste / सैनिटरी कचरा | landfill | |
| `OTHER_LANDFILL` | Other / अन्य | landfill | |

---

## 7. Data model (DynamoDB, all on-demand)

Use string ISO timestamps (`createdAt`). Convert floats to `Decimal` on write and back on read (`lib/db.py`). Round kg to 2 decimals and ₹ to 2 decimals.

### 7.1 `Users`
- PK `userId` (string, e.g. `u_ab12`)
- `name`, `role` (`household` | `picker` | `recycler` | `city`), `societyId` (households), `lat`, `lng` (pickers' base), `language` (`en`|`hi`), `createdAt`

### 7.2 `Societies`
- PK `societyId`
- `name`, `ward`, `lat`, `lng`
- Seed with 5–6 real Delhi neighbourhood names and approximate public coordinates (e.g. Mayur Vihar Ph-1, Laxmi Nagar, Rohini Sec-9, Dwarka Sec-10, Lajpat Nagar, Patparganj). Use fictional society names inside them ("Shanti Apartments, Mayur Vihar Ph-1").

### 7.3 `Scans`
- PK `userId`, SK `scanId` (`s_<timestamp>_<rand>`)
- `societyId`, `imageKey`, `createdAt`
- `items`: list of `{ name, material, count, estWeightKg, brand | null }`
- `totals`: `{ recyclableKg, compostableKg, landfillKg }`
- `estValueRs` (household share at current rates), `eprPackets` (count of branded packets), `eprRs`
- `segregationScore` (0–100), `tip` (one sentence from AI)
- `status`: `pending` → `bundled` → `collected`
- `bundleId` (when bundled)
- **GSI `status-index`**: PK `status`, SK `createdAt`
- **GSI `society-index`**: PK `societyId`, SK `createdAt`

### 7.4 `Bundles`
- PK `bundleId`
- `societyId`, `scanRefs` (list of `{userId, scanId}`), `materials` (map material → kg), `totalKg`, `valueRs`, `status` (`open` | `accepted` | `collected`), `pickerId`, `createdAt`, `collectedAt`
- **GSI `status-index`**: PK `status`, SK `createdAt`

### 7.5 `Rates`
- PK `material`
- `rsPerKg`, `updatedBy`, `updatedAt`
- Seed with **demo rates** (§9), clearly labelled.

### 7.6 `Stats` (atomic counters with `UpdateItem ADD`)
- PK `scope`: `city#delhi`, `society#<id>`, `user#<id>`, `picker#<id>`
- Counters: `scannedKg`, `recyclableKg`, `compostableKg`, `landfillKg`, `divertedKg`, `householdPayoutRs`, `pickerPayoutRs`, `eprRs`, `scanCount`, `pickupCount`

---

## 8. API (HTTP API; JSON in/out)

All responses: `{ "ok": true, "data": ... }` or `{ "ok": false, "error": { "code": "...", "message": "..." } }`. CORS allow all origins (hackathon). For the MVP, identity is passed as `userId` in the body or query (demo role switcher). Lambda timeout is 29 s on all API functions.

| Method | Path | Body / query | Does |
|---|---|---|---|
| POST | `/users` | `{name, role, societyId?, lat?, lng?}` | create user |
| GET | `/me?userId=` | | user + `Stats user#id` (wallet: householdPayoutRs, eprRs, divertedKg) |
| POST | `/uploads` | `{userId, contentType}` | returns `{uploadUrl, imageKey}` presigned PUT, 5 min expiry, `image/jpeg` or `image/png` only, key `scans/<userId>/<uuid>.jpg` |
| POST | `/scans` | `{userId, imageKey}` | runs vision (§10.1) → pricing → saves scan → updates stats → returns full scan |
| GET | `/scans?userId=` | | user's scans, newest first |
| GET | `/scans/{scanId}?userId=` | | one scan |
| GET | `/rates` | | rate board |
| PUT | `/rates/{material}` | `{rsPerKg, userId}` | recycler updates a rate (validate 0–500) |
| POST | `/bundles/build` | | run bundling (§10.3) over all `pending` scans |
| GET | `/bundles?status=open&pickerId=` | | open bundles ordered by route from picker's base |
| POST | `/bundles/{id}/accept` | `{pickerId}` | open → accepted (conditional write; fail if already taken) |
| POST | `/bundles/{id}/collect` | `{pickerId}` | accepted → collected; compute payouts (§9); mark scans `collected`; update all stats |
| GET | `/stats/city` | | city counters + mountain params (§11.4) |
| GET | `/leaderboard` | | societies ranked by `divertedKg`, with kg and ₹ |
| POST | `/coach` | `{userId, language}` | Strands agent weekly plan (§10.4) |
| POST | `/admin/seed` | | create demo societies, users, rates, and ~40 historical scans with realistic mixes (no Bedrock calls); mark them `demo: true` |
| POST | `/admin/reset` | | wipe demo data |

Protect `/admin/*` with a simple shared header `x-admin-key` from a SAM parameter (hackathon-level only).

---

## 9. Pricing, payouts, EPR (`lib/pricing.py`): deterministic, fully unit-tested

**Demo rates (₹/kg). These are DEMO VALUES, not market data.** Put them in `config.py` with a comment, seed them into `Rates`, and show a small "Demo rates" badge on the rate board and result screens. Arjun may replace them with rates he verifies.

| Material | Demo ₹/kg |
|---|---|
| PET_BOTTLE | 15 |
| HARD_PLASTIC | 10 |
| MILK_POUCH | 8 |
| MULTILAYER_PACKET | 2 |
| PAPER | 10 |
| CARDBOARD | 8 |
| METAL | 25 |
| GLASS | 2 |
| E_WASTE | 20 |

Rules:
- `bundleValueRs = Σ (kg_material × rsPerKg_material)` over recyclable materials only.
- Split (demo constants): **picker 40%**, **households 60%**. Each household's share is proportional to its recyclable kg in the bundle.
- Scan-time `estValueRs` = the household's 60% share of its own recyclables at current rates (an estimate; final value is set at collection).
- **EPR reward (simulated brand-funded):** ₹0.50 per detected branded plastic packet (`MULTILAYER_PACKET`, `MILK_POUCH`, `PET_BOTTLE` with a non-null `brand`), capped at ₹10 per scan. Credited at collection. Label in UI: "Brand rewards (simulated EPR partner)".
- Compostable kg are **not** paid or diverted in the MVP. Show them as "could become compost".
- Round all ₹ to 2 decimals. Payout split must sum exactly to `bundleValueRs` (put any rounding remainder on the picker share).

---

## 10. AI workflows

### 10.1 Bin Vision (`lib/vision.py`): Bedrock Converse, Nova Lite, image + text

- Read image bytes from S3 (max 5 MB). Call `bedrock-runtime.converse` with one user message containing the image block (`format` `jpeg`/`png`) and the prompt below. `temperature 0.1`, `maxTokens 2000`.
- Extract the text, take the substring from the first `{` to the last `}`, `json.loads`, validate with pydantic. On failure, retry once with the extra line "Your previous reply was not valid JSON. Reply with JSON only." On a second failure return error `AI_PARSE_FAILED`.
- Post-processing (in code, not AI): clamp each `estWeightKg` to 0.005–10; drop unknown materials into `OTHER_LANDFILL`; compute `totals` from categories; compute pricing (§9).
- If `isWasteImage` is false → return error `NOT_A_BIN` with a friendly message.

**Prompt (use verbatim, keep in `vision.py`):**

```
You are a waste-audit assistant for households in Delhi, India.
Look at the photo of a household dustbin or pile of discarded items.

Identify each distinct item or group of similar items you can see. For each, estimate:
- material: one of PET_BOTTLE, HARD_PLASTIC, MILK_POUCH, MULTILAYER_PACKET, PAPER, CARDBOARD, METAL, GLASS, E_WASTE, WET_ORGANIC, SANITARY, OTHER_LANDFILL
- count: number of items (integer; 1 for loose material like food scraps)
- estWeightKg: your best estimate of total weight in kilograms for that group
- brand: the brand name if clearly readable on packaging (e.g. "Amul", "Lay's"), otherwise null. Never guess a brand you cannot read.

Also assess:
- isWasteImage: true if the photo shows waste/discarded items, false otherwise
- segregationScore: 0-100. 100 = dry and wet waste fully separated; 0 = everything mixed and contaminated
- tip: one short, practical sentence (max 20 words) on what this household could do better, specific to what you see

Rules:
- Only list items you can actually see. Do not invent items.
- Be conservative with weights. Typical: empty PET bottle 0.02-0.04 kg, chips packet 0.005-0.01 kg, milk pouch 0.005 kg, newspaper sheet 0.02 kg, cardboard box 0.1-0.4 kg.
- Respond with JSON only, no other text, matching exactly:
{"isWasteImage": bool, "segregationScore": int, "tip": string,
 "items": [{"name": string, "material": string, "count": int, "estWeightKg": number, "brand": string|null}]}
```

- UI must label weights and values as **"AI estimate"**.

### 10.2 Pricing: code only (§9)

### 10.3 Bundling + route (`lib/bundling.py`): deterministic
- Query `Scans` `status-index` for `pending`. Group by `societyId`.
- A society group becomes a bundle when total recyclable kg ≥ `MIN_BUNDLE_KG` (demo: 1.5 kg) **or** it contains scans older than 12 h.
- Write the bundle; set those scans to `bundled` with `bundleId` (use a DynamoDB transaction per bundle, max 100 items; chunk if larger).
- Route order for `GET /bundles`: nearest-neighbour from the picker's base `lat/lng` over open bundles' society coordinates (haversine). Return `routeOrder`, `distanceKmFromPrev`, and total route km.
- Stretch S4 replaces this with Amazon Location Service.

### 10.4 Coach agent (`handlers/coach.py`): **Strands Agents** on Bedrock
- `BedrockModel` with model id from env (Nova Lite, or Nova Pro if available), region `us-east-1`.
- Tools (Python functions decorated as Strands tools, each querying DynamoDB for the given user):
  - `get_material_totals(user_id, days=7)` → kg per material and category
  - `get_scan_history(user_id, limit=10)` → recent scans (date, totals, score)
  - `get_rates()` → current rate board
  - `get_society_rank(user_id)` → society position on the leaderboard
- System prompt:
```
You are "Kamai Coach", a friendly, practical waste coach for Delhi households.
Use your tools to look at this household's real data before answering. Never invent numbers; only use figures returned by tools.
Write a weekly plan with exactly 3 actions. For each action give: what to do, why (citing their own data), and the expected impact in kg diverted and ₹ earned per week, computed from tool data and current rates.
Keep it under 150 words. Respond in {language: English or simple Hinglish}.
```
- Return the text plus the list of tools called (show "Checked: your last 7 days, rates, society rank" in the UI, which makes the agent's work visible in the video).
- If the user has fewer than 2 scans, return a fixed onboarding message without calling the model.

### 10.5 Stretch S1: Step Functions scan pipeline
`POST /scans` starts an execution and returns `scanId` with status `processing`. The state machine runs `Analyze (Bedrock)` → `Validate` → `Price` → `Persist` → `UpdateStats`, with a `Catch` → `MarkFailed`. The frontend polls `GET /scans/{scanId}` every 1.5 s. Show the state machine graph in the video.

---

## 11. Frontend specification

### 11.1 Global
- Mobile-first (design at 390 px width), works on desktop.
- Top bar: logo text "Kachra se Kamai", role switcher (Household / Picker / Recycler / City). The role switcher selects a seeded demo user per role and stores the choice in `localStorage` (wrapped in try/catch).
- Visual style: warm and grounded, not corporate. Palette: deep green `#1F5F3F` (primary), marigold `#F2A900` (money/rewards), slate `#334155` (text), off-white `#FAF7F0` (background), clay red `#C2410C` (landfill). Big numbers, rounded cards, generous spacing.
- Every AI-estimated number carries a small "AI estimate" tag. Every demo-valued number carries a "Demo" tag (`DemoBadge`).
- Loading and error states on every API call. Errors are friendly text plus a retry button.

### 11.2 Household
- **Home:** WalletCard (₹ earned, ₹ brand rewards, kg diverted, kg sent to landfill this week), ScoreRing (average segregation score), a mini version of the mountain, a big "📸 Snap my bin" button, and the latest result.
- **Snap:** `<input type="file" accept="image/*" capture="environment">`. Compress client-side to max 1280 px on the long edge, JPEG quality 0.8 (`lib/compressImage.ts`, canvas). Flow: `POST /uploads` → PUT to S3 → `POST /scans` → navigate to Result. Show a progress state with steps: "Uploading → AI is looking at your bin → Calculating your kamai".
- **Result:** the photo; an item list with MaterialChips and kg; KgSplitBar (green recyclable / brown compostable / red landfill); "You could earn ₹X" (AI estimate); brand packets found ("3 Amul pouches → ₹1.50 brand reward"); segregation score with the AI tip; "Added to tonight's pickup from <society>".
- **History:** list of scans with date, score, kg split, status (pending / in pickup / collected ✓ with ₹ credited).
- **Coach:** "Get my weekly plan" button → agent response, "Checked: …" tool trace, and a language toggle (EN / Hinglish).

### 11.3 Picker (keep it simple: big buttons, large text, minimal reading)
- **Bundles:** a map (Leaflet) with numbered markers in route order plus a list of BundleCards (society, kg by material, ₹ value, picker's 40% share shown prominently, distance). "Accept" button.
- **BundleDetail:** households count, materials, "Mark collected" (confirmation modal). On success: "₹X added to your earnings".
- **Earnings:** today's total, all-time total, pickups count.
- A "Refresh bundles" button calls `POST /bundles/build` then reloads.

### 11.4 City view (the hero screen for the video)
- **Mountain3D:** a stylised landfill mound (procedural cone/terrain with noise, earthy colours, a few gulls optional) next to a simple Qutub Minar–like tower silhouette made from basic shapes for scale. Generic geometry only; no copied 3D models without a compatible licence and credit.
  - Height = `H0 × max(0.5, 1 − divertedKg / TARGET_KG)`, with `TARGET_KG` a demo constant (e.g. 500 kg) so the shrink is visible during the demo. Animate smoothly when the value changes (lerp).
  - **Label clearly: "Illustrative: the mountain shrinks as Delhi diverts waste on this platform."** Do not claim real-time physical measurement.
- Live counters (poll `/stats/city` every 5 s): kg scanned, kg diverted, ₹ paid to households, ₹ paid to pickers, brand rewards.
- Society leaderboard table.
- An "If 1% of Delhi households did this…" projection card. **Only compute it from cited inputs that Arjun has verified** (households count, per-household kg). Otherwise omit the card.

### 11.5 Recycler
- **RateBoard:** editable ₹/kg per material with save → `PUT /rates/{material}`, and a "Demo rates" badge.
- **Incoming:** collected bundles with material kg totals.

---

## 12. AWS infrastructure (`backend/template.yaml`)

- `Transform: AWS::Serverless-2016-10-31`
- Parameters: `ModelId` (default `us.amazon.nova-lite-v1:0`), `AdminKey` (NoEcho), `CoachModelId` (default same as `ModelId`).
- Globals: Runtime `python3.12`, Timeout 29, MemorySize 512, Architectures `arm64`, env vars for all table names, bucket name, model ids, `MIN_BUNDLE_KG`, `TARGET_KG`.
- Resources:
  - `HttpApi` (`AWS::Serverless::HttpApi`) with `CorsConfiguration` (all origins, GET/POST/PUT/OPTIONS, headers `*`).
  - `PhotoBucket`: S3, block all public access, CORS rule allowing PUT from any origin (hackathon), lifecycle rule deleting `scans/` after 30 days.
  - Six DynamoDB tables (§7) with the GSIs, `PAY_PER_REQUEST`.
  - One Lambda function per handler file, each with the minimum policies it needs: `DynamoDBCrudPolicy` on the relevant tables, `S3ReadPolicy`/`S3CrudPolicy` on the bucket, and an inline statement allowing `bedrock:InvokeModel` and `bedrock:InvokeModelWithResponseStream` on `*` (needed for inference profiles) for the vision and coach functions.
  - The coach function packages `strands-agents` (via `requirements.txt` and `sam build`). If it exceeds Lambda size limits, use a Lambda layer or container image and say so.
- Outputs: `ApiUrl`, `PhotoBucketName`.
- `samconfig.toml`: stack name `kachra-se-kamai`, region `us-east-1`, `capabilities CAPABILITY_IAM`, `resolve_s3 = true`.

### Deploy commands
```
cd backend
sam build
sam deploy --guided        # first time; then: sam deploy
curl -X POST "$API_URL/admin/seed" -H "x-admin-key: <AdminKey>"
```

### Frontend hosting
- `frontend/.env.production` with `VITE_API_URL=<ApiUrl>`.
- Connect the GitHub repo in the AWS Amplify console (Host web app → GitHub → `frontend/` as app root, build `npm ci && npm run build`, output `dist`). Add the `VITE_API_URL` environment variable in Amplify.
- Add an SPA rewrite rule: `</^[^.]+$|\.(?!(css|gif|ico|jpg|js|png|txt|svg|woff|woff2|ttf|map|json)$)([^.]+$)/>` → `/index.html` (200).

### Cost safety
- Set an AWS Budgets alert at $5.
- Stay on the free tier. Bedrock Nova Lite costs fractions of a cent per scan.
- After judging: `sam delete` and delete the Amplify app.

---

## 13. Milestones (build in this order; commit after each)

Times are targets for Sat Oct 10 → Sun Oct 11. If a milestone runs over by more than 50%, cut scope inside it rather than skipping tests.

| # | Milestone | Done when | Target |
|---|---|---|---|
| M0 | Repo init: README stub, LICENSE, .gitignore, folder structure, first commit, push to public GitHub | repo visible on GitHub | 10:30 |
| M1 | Backend skeleton: SAM template with HttpApi, tables, bucket, a `/health` function; deployed | `curl $API_URL/health` returns ok | 12:00 |
| M2 | Bin Vision end to end: `/uploads`, `/scans` with Bedrock, pricing, stats; unit tests for parsing and pricing | upload a real bin photo via curl/script → sensible JSON saved in DynamoDB | 14:30 |
| M3 | Bundles + picker + rates + payouts + seed: all bundle endpoints, `/rates`, `/me`, `/stats/city`, `/leaderboard`, `/admin/seed`; tests for bundling and payout split | seed → build bundles → accept → collect → stats and wallets update correctly | 17:30 |
| M4 | Frontend core: Landing, role switcher, Household (Home/Snap/Result/History), Picker (Bundles/Detail/Earnings), Recycler RateBoard; deployed on Amplify | full flow works on a phone browser against the deployed API | 22:00 |
| M5 | City view: Mountain3D, counters, leaderboard | collecting a bundle visibly shrinks the mountain within 5 s | 00:30 |
| M6 | Coach agent (Strands): endpoint + Coach screen with tool trace | plan cites the user's real numbers | Sun 10:00 |
| M7 | Polish + docs: empty states, error states, Demo/AI badges, README, `docs/architecture.md` (Mermaid), `docs/writeup.md`, `docs/demo-script.md` | a fresh reader can understand and run it | Sun 12:00 |
| M8 | Video + submit (Arjun): record, upload to YouTube (unlisted), check the link in a signed-out browser, submit the form | submitted ≥ 2 h before deadline | Sun, early afternoon |

Stretch goals S1–S6 only after M7, in this order: S1 (Step Functions, strong for the video), S6 (Hindi), S3 (Polly), S5, S2, S4.

---

## 14. Testing checklist

### Automated (`pytest backend/tests`)
- Pricing: single material, mixed materials, zero recyclables, rounding, payout split sums exactly to bundle value, EPR cap at ₹10.
- Vision parsing: valid JSON, JSON wrapped in prose, invalid JSON → retry path, unknown material → `OTHER_LANDFILL`, weight clamping, `isWasteImage=false` → `NOT_A_BIN`.
- Bundling: threshold logic, age-based bundling, grouping by society, nearest-neighbour order on known coordinates.

### Manual (before recording)
- [ ] Real bin photo (mixed) → sensible items, score, tip
- [ ] Well-segregated dry waste photo → higher score
- [ ] Non-waste photo (e.g. a laptop on a desk) → friendly NOT_A_BIN message
- [ ] Brand packet clearly visible → brand detected, EPR reward shown
- [ ] Build bundles → picker sees route on map → accept → collect → household wallet, picker earnings, city counters, leaderboard and mountain all update
- [ ] Rate change by recycler changes the next scan's estimate
- [ ] Coach plan references the user's real numbers
- [ ] Works on phone (camera capture) and desktop
- [ ] No console errors; no secrets in the repo

---

## 15. Demo video plan (≤ 3:00, `docs/demo-script.md`)

| Time | Shot |
|---|---|
| 0:00–0:20 | Hook: Ghazipur landfill (use only footage/images with a licence that allows it, or your own phone footage, or a simple animated graphic) + the verified height comparison with Qutub Minar. "Every Delhi home adds to this daily. Nobody sees their share." |
| 0:20–0:35 | One line: "Kachra se Kamai: your waste pays you, and the mountain shrinks." |
| 0:35–1:20 | Household: snap a real bin → AI result → ₹ estimate, brand rewards, score and tip. |
| 1:20–1:55 | Picker: route on map → accept → collect → payout split. |
| 1:55–2:15 | City view: mountain shrinks live, leaderboard updates. |
| 2:15–2:35 | Coach agent: weekly plan citing real data, with the tool trace visible. |
| 2:35–2:55 | AWS architecture diagram + quick console shots (Bedrock, Lambda, DynamoDB, SAM/CloudFormation stack, Step Functions if S1 is done). Name Strands Agents and SAM as the AWS open-source tools. |
| 2:55–3:00 | Close: impact line + repo URL. |

Keep the final export under 3:00 (aim 2:50).

---

## 16. Writeup outline (`docs/writeup.md`)
1. Problem (with cited figures)
2. Solution and who benefits (the table from §2)
3. How it works (the three AI workflows; pricing is deterministic)
4. Where AWS fits (each service and why; SAM + Strands as open source)
5. What's real vs simulated (demo rates, simulated EPR partner, illustrative mountain, AI weight estimates)
6. What's next (real recycler partners, brand EPR integration, MCD pilot, picker onboarding)
7. AI tools used: Claude Code (code generation), Claude (ideation and planning)
8. Credits and licences for all third-party assets and libraries

---

## 17. Non-negotiables (re-read before each commit)
- The LLM never computes money; code does.
- No fabricated statistics. Every real-world figure in the UI, README or video is verified and cited, or removed.
- Demo values and AI estimates are labelled as such.
- No secrets committed (`.env`, keys). `.gitignore` covers `.env*`, `.aws-sam/`, `node_modules/`, `dist/`.
- Commit after every milestone with a clear message. History must show work during Oct 8–11, 2026.
- The app must remain deployable and demoable at every commit.
