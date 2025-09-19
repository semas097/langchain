"""ETL Agent API endpoint implementation."""

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from langchain_community.agent_toolkits.ai_mega_agents_factory.agents.data_processing.etl import ETLAgent
from langchain_community.agent_toolkits.ai_mega_agents_factory.base import MegaAgentConfig, MegaAgentManifest, AgentCategory, MonetizationTier

app = FastAPI(
    title="ETL Agent API",
    description="Enterprise ETL agent microservice",
    version="1.0.0",
)

# Initialize ETL agent
manifest = MegaAgentManifest(
    name="ETL Agent",
    version="1.0.0",
    category=AgentCategory.DATA_PROCESSING,
    description="Enterprise ETL agent for data extraction, transformation, and loading",
    author="AI Mega Agents Factory",
    tags=["etl", "data", "processing", "pipeline"],
    monetization_tier=MonetizationTier.BASIC,
)
config = MegaAgentConfig(manifest=manifest)
etl_agent = ETLAgent(config=config)
etl_agent.initialize()


class ExtractRequest(BaseModel):
    """Extract operation request."""
    source_type: str
    source_path: str
    delimiter: Optional[str] = ","


class TransformRequest(BaseModel):
    """Transform operation request."""
    data: Dict[str, Any]
    transformations: List[Dict[str, Any]]


class LoadRequest(BaseModel):
    """Load operation request."""
    data: Dict[str, Any]
    target_type: str
    target_path: str


class ETLPipelineRequest(BaseModel):
    """Complete ETL pipeline request."""
    source: Dict[str, Any]
    transformations: Optional[List[Dict[str, Any]]] = []
    target: Dict[str, Any]


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "agent": "ETL Agent",
        "version": "1.0.0",
        "metrics": etl_agent.get_metrics(),
    }


@app.get("/info")
async def get_agent_info():
    """Get agent information."""
    return {
        "manifest": etl_agent.manifest.dict(),
        "tools": [tool.name for tool in etl_agent.get_tools()],
        "metrics": etl_agent.get_metrics(),
    }


@app.post("/extract")
async def extract_data(request: ExtractRequest):
    """Extract data from source."""
    try:
        from langchain_community.agent_toolkits.ai_mega_agents_factory.agents.data_processing.etl import extract_from_csv, extract_from_json
        
        if request.source_type == "csv":
            result = extract_from_csv.invoke({
                "file_path": request.source_path,
                "delimiter": request.delimiter
            })
        elif request.source_type == "json":
            result = extract_from_json.invoke({
                "file_path": request.source_path
            })
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported source type: {request.source_type}")
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/transform")
async def transform_data_endpoint(request: TransformRequest):
    """Apply transformations to data."""
    try:
        from langchain_community.agent_toolkits.ai_mega_agents_factory.agents.data_processing.etl import transform_data
        
        result = transform_data.invoke({
            "data": request.data,
            "transformations": request.transformations
        })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/load")
async def load_data(request: LoadRequest):
    """Load data to target."""
    try:
        from langchain_community.agent_toolkits.ai_mega_agents_factory.agents.data_processing.etl import load_to_csv
        
        if request.target_type == "csv":
            result = load_to_csv.invoke({
                "data": request.data,
                "output_path": request.target_path
            })
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported target type: {request.target_type}")
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/pipeline")
async def execute_pipeline(request: ETLPipelineRequest):
    """Execute complete ETL pipeline."""
    try:
        result = await etl_agent.execute({
            "source": request.source,
            "transformations": request.transformations,
            "target": request.target,
        })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/validate")
async def validate_data_quality(data: Dict[str, Any]):
    """Validate data quality."""
    try:
        from langchain_community.agent_toolkits.ai_mega_agents_factory.agents.data_processing.etl import validate_data_quality
        
        result = validate_data_quality.invoke({"data": data})
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)