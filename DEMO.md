# Backend & Frontend Demo

## Quick Start

### 1. Install Backend Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Backend API

```bash
python src/api/app.py
```

The Flask API will start on `http://localhost:5000`

Endpoints:
- `POST /api/incidents/analyze` - Analyze an incident
- `POST /api/incidents/<incident_id>/approve` - Approve recommendation
- `POST /api/incidents/<incident_id>/reject` - Reject recommendation
- `GET /api/audit-log` - Retrieve audit log
- `GET /api/health` - Health check

### 3. Open Frontend

Open `frontend/index.html` in your browser (or run a simple HTTP server):

```bash
# Python 3
python -m http.server 8000

# Then visit: http://localhost:8000/frontend/index.html
```

## Demo Features

### Incident 1: Singapore Port Congestion
- **Shipment ID**: PO-789456
- **Product**: Microchip A3 (5,000 units)
- **Issue**: 48-hour delay in Singapore port
- **SLA Penalty**: $60,000 (48 hrs × $1,250/hr)
- **Expected**: Internal transfer recommendation (Option 2) - 87% confidence
- **Savings**: $13,000 vs. alternate supplier

### Incident 2: Shanghai On-Time
- **Shipment ID**: PO-654321
- **Product**: Capacitor XL (10,000 units)
- **Issue**: No delay
- **SLA Penalty**: $0
- **Expected**: Use for testing alternate scenarios

## In-Memory Data

All data is simulated for demo purposes:

### Tools Implemented
1. `get_shipment_status` - Fetch shipment data
2. `find_alt_suppliers` - Find alternative suppliers
3. `calc_sla_penalty` - Calculate SLA penalties
4. `get_internal_stock` - Check internal inventory
5. `query_vector_store` - Query similar past incidents (mock)

### Safety Gates in Action
- ✅ **Tool-Call Budget**: Limited to 5 calls per incident
- ✅ **Schema Validation**: Structured recommendations only
- ✅ **Confidence Threshold**: Human review if <75% confidence
- ✅ **Propose-Only (v1)**: Human must approve before execution
- ✅ **Audit Logging**: Every decision is logged

## Frontend Demo Flow

1. **Select Incident** → Choose from 2 demo incidents
2. **Analyze** → LLM analyzes with 4 tool calls (budget: 5/5)
3. **View Recommendation** → Shows option, confidence, reasoning
4. **Review Data** → See shipment status, penalties, alternatives
5. **Human Decision** → Approve or Reject
6. **Audit Trail** → View all decisions in audit log

## API Response Example

```json
{
  "status": "success",
  "incident_id": "INC-2026-05-31-001",
  "recommendation": {
    "recommended_option": "Option 2",
    "confidence_score": 0.87,
    "reasoning": "Internal stock transfer available for 5000 units. Faster delivery (3-4 hours vs 48+ hour delay) and cost-effective at $50/unit. Eliminates SLA penalty risk.",
    "cost_delta": -13000,
    "risk_level": "low"
  },
  "routing": {
    "route": "dashboard",
    "reason": "Confidence score 0.87 meets threshold",
    "priority": "normal"
  },
  "tools_called": ["get_shipment_status", "calc_sla_penalty", "get_internal_stock", "find_alt_suppliers"],
  "budget_info": {
    "calls_used": 4,
    "max_calls": 5,
    "calls_remaining": 1
  },
  "audit_log_id": 1
}
```

## Troubleshooting

**Frontend can't connect to backend?**
- Ensure Flask is running on port 5000
- Check CORS is enabled (should be automatic)
- Open browser DevTools (F12) → Network tab to see request

**Port 5000 already in use?**
```bash
# Change port in src/api/app.py
app.run(debug=True, port=5001)  # Use 5001 instead
```

**Need to reset data?**
- Restart the Flask backend
- In-memory data resets on restart

## Next Steps (Production)

1. Replace in-memory data with real S/4HANA integration
2. Implement real LLM (OpenAI/Claude) instead of simulation
3. Add vector embeddings (Pinecone/Weaviate)
4. Implement S/4HANA execution (PO updates, transfers)
5. Add WebSocket for real-time updates
6. Add React frontend for better UX
7. Implement comprehensive audit logging to database
