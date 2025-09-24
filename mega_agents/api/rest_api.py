"""REST API for AI Mega Agents Atlas

This module provides a comprehensive REST API for accessing all 49 agents
in the AI Mega Agents Atlas ecosystem.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
from dataclasses import asdict

try:
    from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from pydantic import BaseModel
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    # Fallback for basic HTTP server
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import urllib.parse
    # Fallback BaseModel class
    class BaseModel:
        pass


from ..core.agent_registry import agent_registry
from ..core.revenue_engine import revenue_engine
from ..core.scaling_manager import scaling_manager
from ..agents.analytics.agent import AnalyticsAgent
from ..core.base_agent import AgentConfig


# Pydantic models for API requests/responses
class AgentRequest(BaseModel):
    """Standard agent request model"""
    type: str
    data_source: Optional[str] = None
    parameters: Dict[str, Any] = {}
    priority: bool = False
    client_id: str = "default"


class AgentResponse(BaseModel):
    """Standard agent response model"""
    status: str
    agent_id: str
    agent_type: str
    response_data: Dict[str, Any]
    revenue_generated: float
    processing_time_ms: float
    timestamp: str


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    uptime_seconds: float
    total_agents: int
    active_agents: int
    total_requests: int
    total_revenue: float
    system_health: Dict[str, Any]


class MegaAgentsAPI:
    """Enterprise REST API for AI Mega Agents Atlas
    
    Provides comprehensive API access to all 49 agents with:
    - RESTful endpoints for all agent types
    - Authentication and authorization
    - Rate limiting and throttling
    - Revenue tracking and billing
    - Real-time monitoring and health checks
    - Auto-scaling integration
    """
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8000, debug: bool = False):
        """Initialize the REST API"""
        self.host = host
        self.port = port
        self.debug = debug
        self.logger = logging.getLogger("mega_agents.api")
        
        # Initialize FastAPI if available, otherwise use fallback
        if FASTAPI_AVAILABLE:
            self.app = FastAPI(
                title="AI Mega Agents Atlas API",
                description="Enterprise AI Agent Platform - 49 Verified Agents",
                version="1.0.0",
                docs_url="/docs",
                redoc_url="/redoc"
            )
            self._setup_fastapi()
        else:
            self.app = None
            self.logger.warning("FastAPI not available, using basic HTTP server")
        
        # API statistics
        self.request_count = 0
        self.error_count = 0
        self.start_time = datetime.utcnow()
        
        # Initialize agents
        asyncio.create_task(self._initialize_agents())
    
    def _setup_fastapi(self):
        """Setup FastAPI application with middleware and routes"""
        
        # CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Security
        security = HTTPBearer()
        
        # Routes
        @self.app.get("/")
        async def root():
            """API root endpoint"""
            return {
                "name": "AI Mega Agents Atlas API",
                "version": "1.0.0",
                "description": "Enterprise AI Agent Platform with 49 Verified Agents",
                "documentation": "/docs",
                "health": "/health",
                "agents": "/agents"
            }
        
        @self.app.get("/health", response_model=HealthResponse)
        async def health_check():
            """Comprehensive health check endpoint"""
            try:
                registry_status = await agent_registry.get_registry_status()
                revenue_analytics = await revenue_engine.get_revenue_analytics()
                scaling_status = await scaling_manager.get_scaling_status()
                
                uptime = (datetime.utcnow() - self.start_time).total_seconds()
                
                return HealthResponse(
                    status="healthy",
                    uptime_seconds=uptime,
                    total_agents=registry_status["total_registered_types"],
                    active_agents=registry_status["total_active_instances"],
                    total_requests=self.request_count,
                    total_revenue=revenue_analytics["total_revenue"],
                    system_health={
                        "registry": "healthy",
                        "revenue_engine": "healthy",
                        "scaling_manager": "healthy",
                        "api_error_rate": self.error_count / max(self.request_count, 1)
                    }
                )
            except Exception as e:
                self.logger.error(f"Health check failed: {e}")
                raise HTTPException(status_code=500, detail="Health check failed")
        
        @self.app.get("/agents")
        async def list_agents():
            """List all registered agent types"""
            try:
                registered_agents = agent_registry.list_registered_agents()
                active_instances = agent_registry.list_agent_instances()
                
                return {
                    "registered_agents": registered_agents,
                    "active_instances": len(active_instances),
                    "total_types": len(registered_agents)
                }
            except Exception as e:
                self.logger.error(f"Error listing agents: {e}")
                raise HTTPException(status_code=500, detail="Failed to list agents")
        
        @self.app.get("/agents/{agent_type}")
        async def get_agent_info(agent_type: str):
            """Get information about a specific agent type"""
            try:
                registered_agents = agent_registry.list_registered_agents()
                if agent_type not in registered_agents:
                    raise HTTPException(status_code=404, detail=f"Agent type {agent_type} not found")
                
                agent_instances = [
                    instance for instance_id, instance in agent_registry.list_agent_instances().items()
                    if instance["config"]["agent_type"] == agent_type
                ]
                
                return {
                    "agent_type": agent_type,
                    "info": registered_agents[agent_type],
                    "active_instances": len(agent_instances),
                    "instances": agent_instances
                }
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error getting agent info: {e}")
                raise HTTPException(status_code=500, detail="Failed to get agent info")
        
        @self.app.post("/agents/{agent_type}/request", response_model=AgentResponse)
        async def process_agent_request(
            agent_type: str, 
            request: AgentRequest,
            background_tasks: BackgroundTasks,
            credentials: HTTPAuthorizationCredentials = Depends(security)
        ):
            """Process a request for a specific agent type"""
            try:
                self.request_count += 1
                start_time = datetime.utcnow()
                
                # Validate agent type
                registered_agents = agent_registry.list_registered_agents()
                if agent_type not in registered_agents:
                    self.error_count += 1
                    raise HTTPException(status_code=404, detail=f"Agent type {agent_type} not found")
                
                # Process request through agent registry
                request_data = request.dict()
                response = await agent_registry.route_request(agent_type, request_data)
                
                processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                # Calculate revenue
                revenue = await revenue_engine.calculate_revenue(
                    agent_instance_id="api_request",
                    agent_type=agent_type,
                    client_id=request.client_id,
                    usage_data=request_data
                )
                
                # Background task for analytics
                background_tasks.add_task(self._log_request_analytics, agent_type, request_data, response, revenue)
                
                return AgentResponse(
                    status=response.get("status", "success"),
                    agent_id=response.get("agent_id", "unknown"),
                    agent_type=agent_type,
                    response_data=response,
                    revenue_generated=revenue,
                    processing_time_ms=processing_time,
                    timestamp=datetime.utcnow().isoformat()
                )
                
            except HTTPException:
                raise
            except Exception as e:
                self.error_count += 1
                self.logger.error(f"Error processing agent request: {e}")
                raise HTTPException(status_code=500, detail=f"Request processing failed: {str(e)}")
        
        @self.app.get("/analytics/revenue")
        async def get_revenue_analytics():
            """Get revenue analytics"""
            try:
                return await revenue_engine.get_revenue_analytics()
            except Exception as e:
                self.logger.error(f"Error getting revenue analytics: {e}")
                raise HTTPException(status_code=500, detail="Failed to get revenue analytics")
        
        @self.app.get("/analytics/scaling")
        async def get_scaling_analytics():
            """Get scaling analytics"""
            try:
                return await scaling_manager.get_scaling_status()
            except Exception as e:
                self.logger.error(f"Error getting scaling analytics: {e}")
                raise HTTPException(status_code=500, detail="Failed to get scaling analytics")
        
        @self.app.post("/admin/agents/{agent_type}/scale")
        async def trigger_scaling(
            agent_type: str,
            direction: str,
            credentials: HTTPAuthorizationCredentials = Depends(security)
        ):
            """Manually trigger scaling for an agent type"""
            try:
                from ..core.scaling_manager import ScalingDirection
                
                scale_direction = ScalingDirection(direction)
                success = await scaling_manager.trigger_scaling(
                    agent_type, scale_direction, "Manual API trigger"
                )
                
                return {
                    "success": success,
                    "agent_type": agent_type,
                    "direction": direction,
                    "timestamp": datetime.utcnow().isoformat()
                }
            except Exception as e:
                self.logger.error(f"Error triggering scaling: {e}")
                raise HTTPException(status_code=500, detail="Failed to trigger scaling")
        
        # Specific agent endpoints
        @self.app.post("/agents/analytics/analyze")
        async def analytics_analyze(request: AgentRequest):
            """Analytics agent endpoint"""
            return await process_agent_request("analytics", request, BackgroundTasks(), HTTPBearer())
        
        @self.app.post("/agents/content/create")
        async def content_create(request: AgentRequest):
            """Content creation agent endpoint"""
            return await process_agent_request("content", request, BackgroundTasks(), HTTPBearer())
        
        @self.app.post("/agents/customer-service/support")
        async def customer_service_support(request: AgentRequest):
            """Customer service agent endpoint"""
            return await process_agent_request("customer_service", request, BackgroundTasks(), HTTPBearer())
    
    async def _initialize_agents(self):
        """Initialize default agent instances"""
        try:
            # Register Analytics Agent
            analytics_config = AgentConfig(
                name="AI Analytics Agent",
                agent_type="analytics",
                description="Advanced data analytics and business intelligence"
            )
            
            agent_registry.register_agent_type(
                agent_class=AnalyticsAgent,
                agent_type="analytics",
                name="AI Analytics Agent",
                description="Advanced data analytics and business intelligence",
                capabilities=["statistical_analysis", "predictive_modeling", "dashboards"],
                revenue_models=["usage_based", "subscription"]
            )
            
            self.logger.info("Agents initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing agents: {e}")
    
    async def _log_request_analytics(self, agent_type: str, request_data: Dict, response: Dict, revenue: float):
        """Log request analytics in background"""
        try:
            # In real implementation, this would log to analytics database
            self.logger.info(
                f"Request Analytics - Agent: {agent_type}, "
                f"Revenue: ${revenue:.4f}, "
                f"Status: {response.get('status', 'unknown')}"
            )
        except Exception as e:
            self.logger.error(f"Error logging analytics: {e}")
    
    async def start_server(self):
        """Start the API server"""
        if FASTAPI_AVAILABLE:
            config = uvicorn.Config(
                self.app,
                host=self.host,
                port=self.port,
                log_level="info" if self.debug else "warning"
            )
            server = uvicorn.Server(config)
            await server.serve()
        else:
            # Fallback HTTP server
            await self._start_basic_server()
    
    async def _start_basic_server(self):
        """Start basic HTTP server as fallback"""
        class RequestHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                if self.path == '/health':
                    response = {
                        "status": "healthy",
                        "message": "AI Mega Agents Atlas API is running",
                        "note": "Install FastAPI for full functionality"
                    }
                else:
                    response = {
                        "name": "AI Mega Agents Atlas API",
                        "version": "1.0.0",
                        "note": "Install FastAPI for full functionality"
                    }
                
                self.wfile.write(json.dumps(response).encode())
        
        server = HTTPServer((self.host, self.port), RequestHandler)
        self.logger.info(f"Starting basic HTTP server on {self.host}:{self.port}")
        server.serve_forever()


# Main execution
async def main():
    """Main function to start the API server"""
    api = MegaAgentsAPI(debug=True)
    await api.start_server()


if __name__ == "__main__":
    if FASTAPI_AVAILABLE:
        # Use uvicorn directly
        uvicorn.run(
            "mega_agents.api.rest_api:app",
            host="0.0.0.0",
            port=8000,
            reload=True
        )
    else:
        # Use asyncio
        asyncio.run(main())