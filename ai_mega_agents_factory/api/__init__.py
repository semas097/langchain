"""
AI Mega Agents Factory - API Layer

FastAPI-based REST API for managing and interacting with AI agents.
Provides endpoints for agent creation, execution, monitoring, and billing.
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
import time
from datetime import datetime

from ai_mega_agents_factory import (
    AgentConfig, AgentTier, AgentResult, agent_registry, 
    monetization_service, BaseAgentFactory
)


app = FastAPI(
    title="AI Mega Agents Factory API",
    description="Comprehensive API for managing 49 specialized AI agents",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class CreateAgentRequest(BaseModel):
    agent_type: str
    name: str
    description: str
    tier: AgentTier = AgentTier.FREE
    config: Dict[str, Any] = {}


class ExecuteTaskRequest(BaseModel):
    task: Dict[str, Any]
    async_execution: bool = False


class AgentStatusResponse(BaseModel):
    agent_id: str
    name: str
    status: str
    metrics: Dict[str, Any]
    version: str
    tier: str


class UsageResponse(BaseModel):
    agent_id: str
    usage: Dict[str, int]
    total_cost: float
    tier: str


# Health Check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}


# Agent Management Endpoints
@app.post("/agents", response_model=AgentStatusResponse)
async def create_agent(request: CreateAgentRequest):
    """Create a new agent instance"""
    try:
        config = AgentConfig(
            name=request.name,
            description=request.description,
            tier=request.tier,
            **request.config
        )
        
        agent = await agent_registry.create_agent(request.agent_type, config)
        if not agent:
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to create agent of type: {request.agent_type}"
            )
        
        status = agent.get_status()
        return AgentStatusResponse(**status)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents", response_model=List[AgentStatusResponse])
async def list_agents():
    """List all active agents"""
    try:
        agents = agent_registry.list_agents()
        return [AgentStatusResponse(**agent) for agent in agents]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents/types")
async def list_agent_types():
    """List all available agent types"""
    try:
        types = agent_registry.list_agent_types()
        return {"agent_types": types}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents/{agent_id}", response_model=AgentStatusResponse)
async def get_agent(agent_id: str):
    """Get specific agent status"""
    try:
        agent = agent_registry.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        status = agent.get_status()
        return AgentStatusResponse(**status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str):
    """Stop and remove an agent"""
    try:
        success = await agent_registry.stop_agent(agent_id)
        if not success:
            raise HTTPException(status_code=404, detail="Agent not found or failed to stop")
        
        return {"message": "Agent stopped successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Task Execution Endpoints
@app.post("/agents/{agent_id}/execute")
async def execute_task(
    agent_id: str, 
    request: ExecuteTaskRequest,
    background_tasks: BackgroundTasks
):
    """Execute a task on a specific agent"""
    try:
        agent = agent_registry.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        if request.async_execution:
            # Execute in background
            background_tasks.add_task(_execute_task_background, agent, request.task)
            return {"message": "Task queued for execution", "async": True}
        else:
            # Execute synchronously
            start_time = time.time()
            result = await agent.execute(request.task)
            execution_time = time.time() - start_time
            
            # Track usage for billing
            monetization_service.track_usage(agent_id, "task_execution")
            
            # Update metrics
            agent.metrics.total_requests += 1
            if result.success:
                agent.metrics.successful_requests += 1
            else:
                agent.metrics.failed_requests += 1
            
            agent.metrics.average_response_time = (
                (agent.metrics.average_response_time * (agent.metrics.total_requests - 1) + execution_time) 
                / agent.metrics.total_requests
            )
            agent.metrics.last_activity = datetime.utcnow()
            
            return result.dict()
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _execute_task_background(agent: BaseAgentFactory, task: Dict[str, Any]):
    """Background task execution"""
    try:
        result = await agent.execute(task)
        # Here you could store the result or send to a webhook
        monetization_service.track_usage(agent.config.agent_id, "task_execution")
    except Exception as e:
        # Log error
        pass


# Monitoring and Analytics Endpoints
@app.get("/agents/{agent_id}/metrics")
async def get_agent_metrics(agent_id: str):
    """Get detailed metrics for an agent"""
    try:
        agent = agent_registry.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        return {
            "agent_id": agent_id,
            "metrics": agent.metrics.dict(),
            "config": agent.config.dict(),
            "status": agent.status.value
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/overview")
async def get_analytics_overview():
    """Get system-wide analytics"""
    try:
        agents = agent_registry.list_agents()
        total_agents = len(agents)
        running_agents = len([a for a in agents if a["status"] == "running"])
        
        total_requests = sum(a["metrics"]["total_requests"] for a in agents)
        total_success = sum(a["metrics"]["successful_requests"] for a in agents)
        
        return {
            "total_agents": total_agents,
            "running_agents": running_agents,
            "total_requests": total_requests,
            "total_successful_requests": total_success,
            "overall_success_rate": (total_success / total_requests * 100) if total_requests > 0 else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Billing and Monetization Endpoints
@app.get("/agents/{agent_id}/usage", response_model=UsageResponse)
async def get_agent_usage(agent_id: str):
    """Get usage and billing information for an agent"""
    try:
        agent = agent_registry.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        usage = monetization_service.get_usage(agent_id)
        total_cost = monetization_service.calculate_cost(agent_id, agent.config.tier)
        
        return UsageResponse(
            agent_id=agent_id,
            usage=usage,
            total_cost=total_cost,
            tier=agent.config.tier.value
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/billing/summary")
async def get_billing_summary():
    """Get billing summary for all agents"""
    try:
        agents = agent_registry.list_agents()
        billing_data = []
        
        for agent_data in agents:
            agent_id = agent_data["agent_id"]
            agent = agent_registry.get_agent(agent_id)
            
            if agent:
                usage = monetization_service.get_usage(agent_id)
                cost = monetization_service.calculate_cost(agent_id, agent.config.tier)
                
                billing_data.append({
                    "agent_id": agent_id,
                    "agent_name": agent.config.name,
                    "tier": agent.config.tier.value,
                    "usage": usage,
                    "cost": cost
                })
        
        total_cost = sum(item["cost"] for item in billing_data)
        
        return {
            "total_cost": total_cost,
            "agent_billing": billing_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Error Handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Resource not found"}
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)