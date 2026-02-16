# d3p Market Intelligence Pipeline

A 15-minute demo of the **d3p protocol** — autonomous AI agents discovering, evaluating, and paying for services from other agents via Lightning Network.

## What it does

Executes a 4-service Market Intelligence pipeline:

```
btc-price → vibe-check → hallucination-detector → schema-validator
```

Each step composes its input from the previous step's output. The pipeline:

1. **Discovers** available services via d3p-discovery
2. **Checks** schema compatibility between pipeline steps
3. **Quotes** dynamic pricing for each service
4. **Executes** 4 services sequentially with output→input composition
5. **Composes** a final intelligence report
6. **Verifies** the output against a JSON schema

Total cost: ~30 sats ($0.02). Human involvement: 0.

## Quick start

```bash
git clone https://github.com/awkie1/d3p-demo.git
cd d3p-demo
pip install -r requirements.txt
python3 demo.py
```

## Usage

```bash
# Default: mock payments, real services
python3 demo.py

# Explicit mock payments
python3 demo.py --mock-payments

# Live L402 Lightning payments (requires funded wallet)
python3 demo.py --live

# Point at a different d3p node
python3 demo.py --base-url https://your-node.com/api/services
```

## What you'll see

```
╭─ d3p Market Intelligence Pipeline ──────────────────────────────╮
│ Protocol: d3p (digital3 agent protocol)                         │
│ Payment:  L402 Lightning (mock)                                 │
│ Target:   https://labs.digital3.ai/api/services                 │
╰─────────────────────────────────────────────────────────────────╯

  PHASE 1  Service Discovery
  ✓ Discovered 10 services (142ms)

  PHASE 2  Schema Compatibility Check
  PHASE 3  Dynamic Price Quotes
  PHASE 4  Pipeline Execution

  [1/4] Bitcoin Price Oracle (btc-price)
       ✓ $68,512 USD (24h: -0.8%)  142ms

  [2/4] Vibe Oracle (vibe-check)
       ✓ mid vibes. touch grass maybe? (score: 5/10)  89ms

  [3/4] Hallucination Detector (check-hallucination)
       ✓ risk: low (confidence: 80%)  112ms

  [4/4] Schema Validator (validate-schema)
       ✓ schema valid  45ms

  PHASE 5  Composed Intelligence Report

  Total cost: ~30 sats ($0.02).  Human involvement: 0.
```

## How it works

### Protocol stack

- **d3p-discovery**: Query `POST /api/discover/query` to find services by capability, price, reputation
- **Service manifests**: Each service publishes a JSON-LD descriptor with input/output schemas
- **L402 Lightning**: Services gate behind HTTP 402. Pay a Lightning invoice, get a macaroon+preimage token
- **Schema composition**: Pipeline engine maps output fields from one service to input fields of the next

### Payment flow (L402)

```
Agent → POST /btc-price           → 402 Payment Required
Agent → POST /l402/invoice         → bolt11 Lightning invoice (5 sats)
Agent → pays invoice via Lightning → gets preimage
Agent → POST /btc-price
        Authorization: L402 <macaroon>:<preimage>
                                   → 200 OK + data
```

### Pipeline composition

```
btc-price output: {price: 68512, change_24h: -0.8, currency: "USD"}
     ↓ compose_vibe_input()
vibe-check input: {text: "Bitcoin is at $68,512..."}
     ↓
vibe-check output: {analysis: "mid vibes", vibe_score: 5.0}
     ↓ compose_hallucination_input()
check-hallucination input: {text: "Market analysis: Bitcoin at $68,512..."}
     ↓
check-hallucination output: {risk_level: "low", confidence_score: 80}
     ↓ compose_schema_input()
validate-schema input: {data: <full report>, schema: <expected shape>}
```

## Protocol

- **Spec**: [github.com/digital3-ai/d3p-protocol](https://github.com/digital3-ai/d3p-protocol)
- **Live services**: [labs.digital3.ai](https://labs.digital3.ai)
- **Docs**: [digital3.ai/docs](https://digital3.ai/docs)

## License

MIT
