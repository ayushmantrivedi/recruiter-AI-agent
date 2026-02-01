# Recruiter AI Platform

A production-grade multi-agent intelligence platform for recruiters, built with FastAPI, PostgreSQL, and Redis. This system uses a Concept → Action → Judgment cognitive architecture to understand recruiter intent, orchestrate API actions intelligently, and produce ranked, explainable hiring leads.

## 🧠 Architecture Overview

The system implements three specialized AI agents:

### 1. Concept Reasoner (LCM + MLM)
- **Purpose**: Convert vague recruiter intent into explicit concept constraints
- **Technology**: HuggingFace Transformers (BERT) + OpenAI GPT reasoning
- **Output**: Concept vectors (hiring_pressure, role_scarcity, outsourcing_likelihood) and structured constraints

### 2. Action Orchestrator (LAM Core)
- **Purpose**: Core brain managing tool registry, execution policy, and feedback learning
- **Features**: Tool selection, execution loop, confidence tracking, exit conditions
- **Tools**: Arbeitnow Jobs, GitHub Jobs, News APIs, Company Metadata APIs

### 3. Signal Judge (Verifier)
- **Purpose**: Score companies, rank leads, explain "why now"
- **Method**: Evidence-first reasoning from API data
- **Output**: Ranked leads with confidence scores and explanations

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.10+ (for local development)
- OpenAI API key (optional, fallback to rule-based reasoning)
- HuggingFace token (optional)

### Production Deployment

1. **Clone and configure:**
```bash
git clone <repository>
cd recruiter-ai-backend
cp env.example .env
# Edit .env with your configuration
```

2. **Launch with Docker:**
```bash
docker-compose up -d
```

3. **Check health:**
```bash
curl http://localhost:8000/api/recruiter/health
```

#### Local Demo Mode (Fastest)

1. Run **`./run_local.ps1`** (Windows) or **`./run_local.sh`** (Mac/Linux).
2. Open your browser to: **[http://localhost:8000/ui](http://localhost:8000/ui)**

This is the standard interface that requires zero setup. Just enter a name and start searching.

### Modern React Interface (Optional)

If you want to use the new dashboard and metrics:
1. Keep the server running above.
2. In a new terminal:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
3. Open: **http://localhost:3000**

3. **Run tests:**
```bash
pytest
```

## 📡 API Usage

### Process a Recruiter Query

```bash
curl -X POST "http://localhost:8000/api/recruiter/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Find senior backend engineers in Bangalore",
    "recruiter_id": "recruiter_123"
  }'
```

**Response:**
```json
{
  "query_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "original_query": "Find senior backend engineers in Bangalore",
  "concept_vector": {
    "hiring_pressure": 0.7,
    "role_scarcity": 0.8,
    "outsourcing_likelihood": 0.3
  },
  "constraints": {
    "role": "backend engineer",
    "region": "india",
    "min_job_posts": 6,
    "window_days": 63,
    "exclude_enterprise": false
  },
  "leads": [
    {
      "company": "TechCorp India",
      "score": 85,
      "confidence": 0.82,
      "reasons": [
        "12 backend positions posted in 30 days",
        "Recent engineering office opening",
        "Mid-stage growth company"
      ],
      "evidence_count": 8
    }
  ],
  "orchestration_summary": {
    "confidence": 0.89,
    "total_steps": 4,
    "total_cost": 0.0,
    "evidence_count": 24
  }
}
```

### Get Query Status

```bash
curl "http://localhost:8000/api/recruiter/query/550e8400-e29b-41d4-a716-446655440000"
```

### Get Recruiter Statistics

```bash
curl "http://localhost:8000/api/recruiter/stats/recruiter_123"
```

## 🛠 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | development | Application environment |
| `DB_HOST` | localhost | PostgreSQL host |
| `REDIS_HOST` | localhost | Redis host |
| `OPENAI_API_KEY` | - | OpenAI API key for reasoning |
| `MAX_STEPS` | 10 | Maximum orchestration steps |
| `CONFIDENCE_THRESHOLD` | 0.85 | Minimum confidence to stop |
| `ARBEITNOW_RATE_LIMIT` | 100 | API rate limit per hour |

### Tool Registry

The system includes these free-first tools:

- **Arbeitnow Jobs**: Recent job postings (free, no key)
- **GitHub Jobs**: Developer positions (free)
- **Mediastack News**: Company news and signals (free tier)
- **Company Metadata**: Enhanced company information (paid upgrade)

## 🧪 Testing

### Unit Tests
```bash
pytest tests/unit/
```

### Integration Tests
```bash
pytest tests/integration/
```

### End-to-End Tests
```bash
pytest tests/e2e/
```

### Test Coverage
```bash
pytest --cov=app --cov-report=html
```

## 📊 Observability

### Metrics
- **Prometheus**: `/metrics` endpoint
- **Health Check**: `/api/recruiter/health`
- **Structured Logging**: JSON format with correlation IDs

### Monitoring
```bash
# Start monitoring stack
docker-compose --profile monitoring up -d

# Access Grafana at http://localhost:3000
```

## 🗂 Project Structure

```
├── app/                    # FastAPI application
├── frontend/               # React + Vite UI
├── tests/                  # Test suite
├── render.yaml             # Render Blueprint
├── run_local.ps1           # Windows Demo script
├── run_local.sh            # Linux/macOS Demo script
├── requirements.txt        # Python dependencies
├── runtime.txt             # Python version
└── README.md
```

## 🔒 Security

- **API Authentication**: JWT-based auth (recruiter routes)
- **Input Validation**: Pydantic models with strict validation
- **Rate Limiting**: Redis-based request throttling
- **HTTPS**: SSL/TLS in production
- **Secrets Management**: Environment-based configuration

## 💰 Business Model

### Billing Tiers
- **Free**: Basic queries, limited results
- **Professional**: $29/month, advanced features, more results
- **Enterprise**: Custom pricing, unlimited usage, priority support

### Cost Optimization
- Free-first API strategy
- Intelligent caching and rate limiting
- Usage-based billing with cost controls

## 🚦 Production Checklist

- [ ] Environment variables configured
- [ ] SSL certificates installed
- [ ] Database migrations run
- [ ] Redis persistence enabled
- [ ] Monitoring alerts configured
- [ ] Backup strategy implemented
- [ ] Load balancer configured
- [ ] Rate limiting tuned
- [ ] API keys secured

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: See `/docs` endpoint for OpenAPI spec
- **Issues**: GitHub Issues for bug reports
- **Discussions**: GitHub Discussions for questions
- **Email**: support@recruiter-ai.com

---

**Built with ❤️ for recruiters who want to find the perfect candidates faster.**
