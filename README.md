# magicpin AI Challenge — Vera Merchant Engagement Engine

**Participant**: Abhinandan Aggarwal  
**Role / Persona**: Senior AI Engineer & Competition Strategist  

**Submission Version**: `1.0.0`  
**Evaluation Standard**: 5-Dimension Grounded Rubric (Specificity, Category Fit, Merchant Fit, Trigger Relevance, Engagement Compulsion)

---

## 1. System Architecture

The solution is a **Stateful, Context-Grounded Merchant Engagement Engine** built with FastAPI, designed specifically to outperform existing production Vera on the key operational vulnerabilities: **auto-reply loops**, **intent-handoff stalls**, **unanchored hallucinations**, and **generic promotional copy**.

```
                           ┌──────────────────────────┐
                           │   magicpin Judge / API   │
                           └─────────────┬────────────┘
                                         │
                   ┌─────────────────────┴─────────────────────┐
                   ▼                                           ▼
      [POST /v1/context / tick]                       [POST /v1/reply]
                   │                                           │
                   ▼                                           ▼
      ┌─────────────────────────┐                 ┌─────────────────────────┐
      │   Stateful Store        │                 │  Intent Classification  │
      │  - 4 Context Layers     │                 │  - Auto-reply detector  │
      │  - Version Tracking     │                 │  - Hostile opt-out      │
      │  - Suppression Cache    │                 │  - Execution intent     │
      └────────────┬────────────┘                 │  - Off-topic redirect   │
                   │                              └────────────┬────────────┘
                   ▼                                           │
      ┌─────────────────────────┐                              ▼
      │ Trigger Prioritization  │                 ┌─────────────────────────┐
      │ & Relevance Filter      │                 │  Multi-Turn Progression │
      └────────────┬────────────┘                 │  & Action Engine        │
                   │                              └────────────┬────────────┘
                   ▼                                           │
      ┌────────────────────────────────────────────────────────┴────────────┐
      │                        Master Composer                              │
      │   ┌─────────────────────────────────────────────────────────────┐   │
      │   │ Deterministic Domain Intelligence Layer (Zero Hallucination)│   │
      │   ├─────────────────────────────────────────────────────────────┤   │
      │   │ Optional LLM Augmentation & Evidence Pack Integration       │   │
      │   ├─────────────────────────────────────────────────────────────┤   │
      │   │ Post-Generation Hallucination Guard (URL & Taboo Filter)    │   │
      │   └─────────────────────────────────────────────────────────────┘   │
      └──────────────────────────────────┬──────────────────────────────────┘
                                         ▼
                               Action Output / Response
```

---

## 2. Key Capabilities & Innovations

### A. 4-Context Grounding Framework
* **CategoryContext**: Dynamic ingestion of tone, taboos, canonical service+price offer catalog, city peer CTR benchmarks, research digests, and seasonal signals.
* **MerchantContext**: Grounded in real performance deltas, active vs expired offers, verified badges, owner first names, and customer aggregates.
* **TriggerContext**: Explicit "Why Now" anchor linking external events (regulations, matches, digests) and internal events (dips, spikes, recalls).
* **CustomerContext**: Automatic delegation from `send_as="vera"` to `send_as="merchant_on_behalf"`, personalizing open slot suggestions and chronic medicine refills.

### B. Auto-Reply Hell Protection
* Detects WhatsApp Business canned messages (English, Hindi, and Hinglish) and identical message repetitions.
* Escalates with structured exponential backoff (`wait_seconds: 14400` -> `86400`) and cleanly closes conversations (`action: "end"`) after repeated automated replies, burning zero turns.

### C. Zero-Stall Intent-Handoff
* When a merchant signals execution commitment (*"Ok let's do it"*, *"proceed"*, *"haan kar do"*, *"send the abstract"*), the engine **never asks qualifying questions**.
* Transitions immediately into Action mode, delivering structured drafts, confirming slot reservations, and scheduling posts with 1-click `CONFIRM` CTAs.

### D. Category-Native Voice & Taboo Enforcement
* **Dentists**: Peer-clinical collegial tone, citing trials (JIDA, DCI). Strict taboos enforced: no *"guaranteed"*, *"cure"*, *"miracle"*.
* **Salons**: Warm, approachable expert; service+price over flat discounts (*"Haircut @ ₹99"*).
* **Restaurants**: Operator-to-operator vocabulary (*"covers"*, *"footfall"*, *"AOV"*); contrarian data-backed IPL Saturday delivery framing.
* **Gyms**: Disciplined coach tone; normalizes post-resolution seasonal acquisition lulls and prioritizes member retention.
* **Pharmacies**: Trustworthy, precise, molecule-level accuracy, senior citizen respect (*"Namaste"*).

### E. Zero-Hallucination & URL Safety Guard
* Strips all URLs from outbound message bodies to comply with Meta WhatsApp template policies and avoid judge penalties.
* Validates numbers, prices, and dates directly against context facts.

---

## 3. Endpoints Implemented

| Endpoint | Method | Purpose | SLA |
|---|---|---|---|
| `/v1/healthz` | GET | Liveness probe with uptime and loaded context counts per scope | < 5ms |
| `/v1/metadata` | GET | Bot identity, version, team, and approach metadata | < 5ms |
| `/v1/context` | POST | Atomic context ingestion with strict version replacement & idempotency (409 on stale) | < 10ms |
| `/v1/tick` | POST | Proactive trigger evaluation, suppression check, and action composition | < 15ms |
| `/v1/reply` | POST | Inbound conversation response routing (send, wait, end) | < 15ms |
| `/v1/teardown` | POST | In-memory state reset for test harnesses | < 5ms |

---

## 4. Local Execution & Testing

### Quick Start
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run test suites
python3 tests/run_tests.py
python3 tests/run_adversarial_tests.py

# 3. Start the FastAPI server
python3 bot.py
```

### Running the Evaluation Harness & Simulator
```bash
# In another terminal:
export BOT_URL=http://localhost:8080

# Run local evaluator scorecard
python3 scripts/local_eval.py

# Generate 30 canonical submission lines
python3 scripts/generate_submission.py

# Run judge simulator (if LLM key configured)
python3 judge_simulator.py
```

---

## 5. Environment Variables

| Variable | Default | Description |
|---|---|---|
| `HOST` | `0.0.0.0` | Bind host |
| `PORT` | `8080` | Bind port |
| `TEAM_NAME` | `Abhinandan Aggarwal` | Team identity |
| `VERSION` | `1.0.0` | Bot semantic version |
| `LLM_PROVIDER` | `""` | Optional LLM provider (`openai`, `anthropic`, `gemini`, `deepseek`, `groq`, `ollama`) |
| `LLM_API_KEY` | `""` | Optional API key (engine operates 100% deterministically when blank) |
| `LLM_MODEL` | `gpt-4o-mini` | Optional LLM model identifier |

---

## 6. Submission Deliverables Summary

1. `bot.py`: Primary FastAPI application & standalone `compose()` entrypoint.
2. `submission.jsonl`: 30 canonical (merchant, trigger) test evaluations across all 5 categories.
3. `app/`: Production-grade modular backend (context store, trigger engine, composer, intent router, validators).
4. `tests/`: Full regression and adversarial test suites covering scenarios A through T.
