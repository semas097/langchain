"""API server for mega agents."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Depends, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from langchain_community.agent_toolkits.ai_mega_agents_factory.base import (
    BaseMegaAgent,
    AgentCategory,
)
from langchain_community.agent_toolkits.ai_mega_agents_factory.factory import (
    AgentType,
    MegaAgentFactory,
    mega_agent_factory,
)


class AgentExecutionRequest(BaseModel):
    """Request model for agent execution."""
    
    input_data: Dict[str, Any]
    config: Optional[Dict[str, Any]] = None


class AgentExecutionResponse(BaseModel):
    """Response model for agent execution."""
    
    agent_id: str
    agent_type: str
    execution_time: float
    result: Dict[str, Any]
    metrics: Dict[str, Any]


class AgentListResponse(BaseModel):
    """Response model for listing agents."""
    
    agents: List[Dict[str, Any]]
    total: int
    category_filter: Optional[str] = None


class AgentInfoResponse(BaseModel):
    """Response model for agent information."""
    
    agent_type: str
    category: str
    manifest: Dict[str, Any]
    is_registered: bool


class HealthResponse(BaseModel):
    """Response model for health check."""
    
    status: str
    version: str
    uptime: float
    factory_stats: Dict[str, Any]


security = HTTPBearer(auto_error=False)


class MegaAgentAPIServer:
    """API server for mega agents."""
    
    def __init__(
        self,
        factory: Optional[MegaAgentFactory] = None,
        api_key: Optional[str] = None,
        enable_cors: bool = True,
        cors_origins: Optional[List[str]] = None,
    ):
        """Initialize the API server.
        
        Args:
            factory: Agent factory instance
            api_key: Optional API key for authentication
            enable_cors: Whether to enable CORS
            cors_origins: CORS allowed origins
        """
        self.factory = factory or mega_agent_factory
        self.api_key = api_key
        self.start_time = time.time()
        
        # Create FastAPI app
        self.app = FastAPI(
            title="AI Mega Agents Factory API",
            description="Enterprise-grade AI agent microservices API",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc",
        )
        
        # Configure CORS
        if enable_cors:
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=cors_origins or ["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
        
        # Agent instances cache
        self._agent_cache: Dict[str, BaseMegaAgent] = {}
        
        # Setup routes
        self._setup_routes()
    
    def _verify_api_key(
        self,
        credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
    ) -> bool:
        """Verify API key if configured.
        
        Args:
            credentials: HTTP authorization credentials
            
        Returns:
            True if valid or no API key required
            
        Raises:
            HTTPException: If API key is invalid
        """
        if self.api_key is None:
            return True
            
        if credentials is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key required",
            )
            
        if credentials.credentials != self.api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
            )
            
        return True
    
    def _setup_routes(self) -> None:
        """Setup API routes."""
        
        @self.app.get("/health", response_model=HealthResponse)
        async def health_check():
            """Health check endpoint."""
            return HealthResponse(
                status="healthy",
                version="1.0.0",
                uptime=time.time() - self.start_time,
                factory_stats=self.factory.get_registry_stats(),
            )
        
        @self.app.get("/agents", response_model=AgentListResponse)
        async def list_agents(
            category: Optional[str] = None,
            _: bool = Depends(self._verify_api_key),
        ):
            """List available agents."""
            try:
                category_filter = None
                if category:
                    category_filter = AgentCategory(category)
                
                agent_types = self.factory.list_agents(category_filter)
                
                agents = []
                for agent_type in agent_types:
                    agent_category = self.factory.get_agent_category(agent_type)
                    agents.append({
                        "type": agent_type.value,
                        "category": agent_category.value,
                        "name": agent_type.value.replace("_", " ").title(),
                        "is_registered": agent_type in self.factory._agent_registry,
                    })
                
                return AgentListResponse(
                    agents=agents,
                    total=len(agents),
                    category_filter=category,
                )
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e),
                )
        
        @self.app.get("/agents/{agent_type}", response_model=AgentInfoResponse)
        async def get_agent_info(
            agent_type: str,
            _: bool = Depends(self._verify_api_key),
        ):
            """Get information about a specific agent."""
            try:
                agent_type_enum = AgentType(agent_type)
                category = self.factory.get_agent_category(agent_type_enum)
                
                # Create a temporary agent to get manifest
                agent = self.factory.create_agent(agent_type_enum)
                
                return AgentInfoResponse(
                    agent_type=agent_type,
                    category=category.value,
                    manifest=agent.manifest.dict(),
                    is_registered=agent_type_enum in self.factory._agent_registry,
                )
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid agent type: {agent_type}",
                )
        
        @self.app.post("/agents/{agent_type}/execute", response_model=AgentExecutionResponse)
        async def execute_agent(
            agent_type: str,
            request: AgentExecutionRequest,
            _: bool = Depends(self._verify_api_key),
        ):
            """Execute an agent."""
            try:
                agent_type_enum = AgentType(agent_type)
                
                # Get or create agent instance
                if agent_type not in self._agent_cache:
                    self._agent_cache[agent_type] = self.factory.create_agent(agent_type_enum)
                
                agent = self._agent_cache[agent_type]
                
                # Execute agent
                start_time = time.time()
                result = await agent.execute(request.input_data)
                execution_time = time.time() - start_time
                
                return AgentExecutionResponse(
                    agent_id=agent.agent_id,
                    agent_type=agent_type,
                    execution_time=execution_time,
                    result=result,
                    metrics=agent.get_metrics(),
                )
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid agent type: {agent_type}",
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Agent execution failed: {str(e)}",
                )
        
        @self.app.get("/categories")
        async def list_categories(
            _: bool = Depends(self._verify_api_key),
        ):
            """List agent categories."""
            return [category.value for category in AgentCategory]
    
    def run(
        self,
        host: str = "0.0.0.0",
        port: int = 8000,
        **kwargs: Any,
    ) -> None:
        """Run the API server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
            **kwargs: Additional uvicorn arguments
        """
        uvicorn.run(self.app, host=host, port=port, **kwargs)


def create_agent_endpoint(
    agent_type: AgentType,
    factory: Optional[MegaAgentFactory] = None,
) -> FastAPI:
    """Create a standalone API endpoint for a specific agent.
    
    Args:
        agent_type: Type of agent
        factory: Agent factory instance
        
    Returns:
        FastAPI application for the agent
    """
    factory = factory or mega_agent_factory
    
    app = FastAPI(
        title=f"{agent_type.value.replace('_', ' ').title()} Agent API",
        description=f"Standalone API for {agent_type.value} agent",
        version="1.0.0",
    )
    
    # Create agent instance
    agent = factory.create_agent(agent_type)
    
    @app.get("/health")
    async def health():
        """Health check."""
        return {"status": "healthy", "agent_type": agent_type.value}
    
    @app.get("/info")
    async def info():
        """Get agent information."""
        return {
            "agent_type": agent_type.value,
            "manifest": agent.manifest.dict(),
            "metrics": agent.get_metrics(),
        }
    
    @app.post("/execute")
    async def execute(request: AgentExecutionRequest):
        """Execute the agent."""
        try:
            start_time = time.time()
            result = await agent.execute(request.input_data)
            execution_time = time.time() - start_time
            
            return {
                "agent_id": agent.agent_id,
                "execution_time": execution_time,
                "result": result,
                "metrics": agent.get_metrics(),
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )
    
    return app