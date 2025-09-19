# AI Mega Agents Factory Docker Configuration

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ai_mega_agents_factory/ ./ai_mega_agents_factory/
COPY scripts/ ./scripts/

# Create non-root user
RUN useradd --create-home --shell /bin/bash agent
RUN chown -R agent:agent /app
USER agent

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "ai_mega_agents_factory.api:app", "--host", "0.0.0.0", "--port", "8000"]