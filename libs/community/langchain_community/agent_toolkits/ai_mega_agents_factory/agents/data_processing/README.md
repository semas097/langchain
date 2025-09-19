# ETL Agent 🏭

Enterprise-grade Extract, Transform, Load (ETL) agent for automated data processing pipelines.

## Overview

The ETL Agent is a powerful microservice that handles complex data processing workflows with enterprise-grade reliability, monitoring, and scalability. Built on LangChain architecture, it provides a complete ETL solution for modern data pipelines.

## Features

### Core Capabilities
- **Multi-format Support**: CSV, JSON, XML, Parquet
- **Advanced Transformations**: Data cleaning, type conversion, filtering, aggregation
- **Quality Validation**: Automated data quality scoring and validation
- **Batch Processing**: Efficient handling of large datasets
- **Real-time Monitoring**: Performance metrics and execution tracking

### Enterprise Features
- **Scalable Architecture**: Billion-scale processing capability
- **Security**: Enterprise-grade authentication and authorization
- **Monitoring**: Comprehensive metrics and logging
- **SLA Compliance**: 99.9% availability guarantee
- **Multi-tenant**: Isolated execution environments

## Quick Start

### Installation

```bash
pip install langchain-community[ai-mega-agents]
```

### Basic Usage

```python
from langchain_community.agent_toolkits.ai_mega_agents_factory import MegaAgentFactory
from langchain_community.agent_toolkits.ai_mega_agents_factory.factory import AgentType

# Create ETL agent
factory = MegaAgentFactory()
etl_agent = factory.create_agent(AgentType.ETL_AGENT)
etl_agent.initialize()

# Execute ETL pipeline
result = await etl_agent.execute({
    "source": {
        "type": "csv",
        "path": "/data/input.csv",
        "delimiter": ","
    },
    "transformations": [
        {
            "operation": "filter_rows",
            "column": "status",
            "condition": "equals",
            "value": "active"
        },
        {
            "operation": "convert_type",
            "column": "amount",
            "target_type": "numeric"
        }
    ],
    "target": {
        "type": "csv",
        "path": "/data/output.csv"
    }
})

print(f"Processed {result['records_processed']['loaded']} records")
print(f"Data quality score: {result['data_quality_score']}")
```

## API Integration

### Standalone API Server

```python
from langchain_community.agent_toolkits.ai_mega_agents_factory.agents.data_processing.etl_api import app
import uvicorn

# Run ETL Agent API server
uvicorn.run(app, host="0.0.0.0", port=8001)
```

### API Endpoints

#### Health Check
```http
GET /health
```

#### Execute Pipeline
```http
POST /pipeline
Content-Type: application/json

{
    "source": {
        "type": "csv",
        "path": "/data/input.csv"
    },
    "transformations": [
        {
            "operation": "rename_column",
            "old_name": "old_col",
            "new_name": "new_col"
        }
    ],
    "target": {
        "type": "csv",
        "path": "/data/output.csv"
    }
}
```

#### Individual Operations
```http
POST /extract
POST /transform
POST /load
POST /validate
```

## Configuration

### YAML Manifest

The ETL Agent uses a YAML manifest for configuration:

```yaml
name: ETL Agent
version: 1.0.0
category: data_processing
description: Enterprise ETL agent for data processing
monetization_tier: basic
pricing_model: usage_based

# Performance limits
max_file_size: 100MB
max_processing_time: 300s
data_quality_threshold: 0.95

# Supported formats
supported_formats:
  input: [csv, json, xml, parquet]
  output: [csv, json, parquet, sql]
```

## Transformations

### Supported Operations

1. **Column Operations**
   - Rename columns
   - Add/remove columns
   - Reorder columns

2. **Data Type Conversions**
   - String to numeric
   - Date/time parsing
   - Boolean conversion

3. **Filtering**
   - Row filtering by conditions
   - Column selection
   - Duplicate removal

4. **Aggregation**
   - Group by operations
   - Statistical functions
   - Custom calculations

### Example Transformations

```python
transformations = [
    {
        "operation": "rename_column",
        "old_name": "customer_id",
        "new_name": "id"
    },
    {
        "operation": "filter_rows",
        "column": "status",
        "condition": "equals",
        "value": "active"
    },
    {
        "operation": "convert_type",
        "column": "created_date",
        "target_type": "datetime"
    },
    {
        "operation": "add_column",
        "column_name": "processed_at",
        "column_value": "2025-01-01T00:00:00Z"
    }
]
```

## Monitoring & Metrics

### Performance Metrics

```python
metrics = etl_agent.get_metrics()
print(f"Records extracted: {metrics['records_extracted']}")
print(f"Records transformed: {metrics['records_transformed']}")
print(f"Records loaded: {metrics['records_loaded']}")
print(f"Execution time: {metrics['execution_time']}")
print(f"Throughput: {metrics['throughput_per_second']} rec/sec")
print(f"Data quality score: {metrics['data_quality_score']}")
```

### Quality Validation

```python
quality_result = await etl_agent._validate_quality(data)
print(f"Quality score: {quality_result['quality_score']}")
print(f"Null cells: {quality_result['null_cells']}")
print(f"Duplicate rows: {quality_result['duplicate_rows']}")
```

## Monetization & Subscription

### Pricing Tiers

| Tier | Monthly Fee | Executions/Month | Max File Size | Features |
|------|-------------|------------------|---------------|----------|
| Free | $0 | 10 | 1MB | Basic transformations |
| Basic | $29.99 | 1,000 | 10MB | Advanced transformations |
| Professional | $99.99 | 10,000 | 100MB | All features + API |
| Enterprise | $499.99 | Unlimited | Unlimited | Custom + SLA |

### Usage-Based Pricing

- $0.01 per execution (Basic)
- $0.005 per execution (Professional)  
- $0.001 per execution (Enterprise)
- $0.001 per MB over tier limit
- $0.0001 per second over 1 minute compute time

### Subscription Management

```python
from langchain_community.agent_toolkits.ai_mega_agents_factory.agents.data_processing.etl_monetization import ETLMonetizationManager

monetization = ETLMonetizationManager()

# Create subscription
subscription = monetization.create_subscription(
    user_id="user123",
    tier=MonetizationTier.PROFESSIONAL
)

# Validate usage
validation = monetization.validate_etl_usage(
    user_id="user123",
    file_size_mb=50.0,
    features_required=["quality_metrics"]
)

# Process payment
billing = monetization.process_etl_payment(
    user_id="user123",
    pipeline_executions=1,
    compute_time=120.0,
    file_size_mb=50.0
)
```

## Production Deployment

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8001

CMD ["uvicorn", "etl_api:app", "--host", "0.0.0.0", "--port", "8001"]
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: etl-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: etl-agent
  template:
    metadata:
      labels:
        app: etl-agent
    spec:
      containers:
      - name: etl-agent
        image: ai-mega-agents/etl-agent:latest
        ports:
        - containerPort: 8001
        env:
        - name: API_KEY
          valueFrom:
            secretKeyRef:
              name: etl-secrets
              key: api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
```

### Load Balancer Configuration

```yaml
apiVersion: v1
kind: Service
metadata:
  name: etl-agent-service
spec:
  selector:
    app: etl-agent
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8001
  type: LoadBalancer
```

## Security

### Authentication

```python
# API with authentication
from langchain_community.agent_toolkits.ai_mega_agents_factory.api import MegaAgentAPIServer

server = MegaAgentAPIServer(api_key="your-secret-api-key")
```

### Rate Limiting

- Free: 10 requests/minute
- Basic: 100 requests/minute
- Professional: 1,000 requests/minute
- Enterprise: Unlimited

### Data Security

- TLS 1.3 encryption in transit
- AES-256 encryption at rest
- SOC 2 Type II compliance
- GDPR compliance
- HIPAA compliance (Enterprise)

## Troubleshooting

### Common Issues

1. **File Size Limit Exceeded**
   ```
   Error: File size 15MB exceeds limit of 10MB
   Solution: Upgrade to Professional tier or split file
   ```

2. **Feature Not Available**
   ```
   Error: Features not available: ['quality_metrics']
   Solution: Upgrade subscription tier
   ```

3. **Rate Limit Exceeded**
   ```
   Error: Rate limit exceeded
   Solution: Wait or upgrade subscription tier
   ```

### Debug Mode

```python
# Enable verbose logging
config.verbose = True
etl_agent = ETLAgent(config=config)

# Check agent status
print(etl_agent.get_metrics())
```

## Support

### Documentation
- [API Reference](./etl_api.py)
- [Transformation Guide](./transformations.md)
- [Performance Tuning](./performance.md)

### Support Channels
- **Community**: GitHub Issues (Free tier)
- **Email**: support@ai-mega-agents.com (Basic/Professional)
- **Dedicated**: Slack channel (Enterprise)

### SLA
- **Professional**: 99.5% uptime
- **Enterprise**: 99.9% uptime with 4-hour response time

## Examples

See the [examples directory](./examples/) for complete use cases:

- [Customer Data ETL](./examples/customer_data_etl.py)
- [Financial Data Processing](./examples/financial_etl.py)
- [Real-time Stream Processing](./examples/streaming_etl.py)
- [Multi-source Data Integration](./examples/multi_source_etl.py)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

Enterprise License - See [LICENSE](../LICENSE) for details.

---

**ETL Agent** - Part of the AI Mega Agents Factory  
© 2025 AI Mega Agents Factory. All rights reserved.