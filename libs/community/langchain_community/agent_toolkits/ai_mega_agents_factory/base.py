"""Base classes for AI Mega Agents Factory."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

from langchain_core.callbacks import BaseCallbackManager
from langchain_core.language_models import BaseLanguageModel
from langchain_core.tools import BaseTool


class AgentCategory(str, Enum):
    """Categories of mega agents."""
    
    DATA_PROCESSING = "data_processing"
    AI_ML = "ai_ml"
    BUSINESS_INTELLIGENCE = "business_intelligence"
    COMMUNICATION = "communication"
    INTEGRATION = "integration"
    SECURITY = "security"
    WORKFLOW = "workflow"
    SPECIALIST = "specialist"


class MonetizationTier(str, Enum):
    """Monetization tiers for agents."""
    
    FREE = "free"
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class MegaAgentManifest(BaseModel):
    """YAML-serializable agent manifest."""
    
    name: str = Field(description="Agent name")
    version: str = Field(description="Agent version")
    category: AgentCategory = Field(description="Agent category")
    description: str = Field(description="Agent description")
    author: str = Field(description="Agent author")
    license: str = Field(default="Enterprise", description="License type")
    tags: List[str] = Field(default_factory=list, description="Agent tags")
    
    # Technical specifications
    min_langchain_version: str = Field(default="0.1.0", description="Minimum LangChain version")
    supported_llm_types: List[str] = Field(default_factory=list, description="Supported LLM types")
    required_tools: List[str] = Field(default_factory=list, description="Required tools")
    
    # API specifications
    api_enabled: bool = Field(default=True, description="Whether API is enabled")
    api_version: str = Field(default="v1", description="API version")
    
    # Monetization
    monetization_tier: MonetizationTier = Field(default=MonetizationTier.BASIC)
    pricing_model: str = Field(default="usage_based", description="Pricing model")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class MegaAgentConfig(BaseModel):
    """Configuration for mega agents."""
    
    agent_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    manifest: MegaAgentManifest
    
    # Runtime configuration
    max_iterations: int = Field(default=10, description="Maximum iterations")
    timeout: int = Field(default=300, description="Timeout in seconds")
    verbose: bool = Field(default=False, description="Verbose logging")
    
    # Security configuration
    api_key_required: bool = Field(default=True, description="Require API key")
    rate_limit: int = Field(default=100, description="Rate limit per minute")
    
    # Performance configuration
    cache_enabled: bool = Field(default=True, description="Enable caching")
    batch_size: int = Field(default=10, description="Batch processing size")


class BaseMegaAgent(ABC):
    """Base class for all mega agents."""
    
    def __init__(
        self,
        config: MegaAgentConfig,
        llm: Optional[BaseLanguageModel] = None,
        callback_manager: Optional[BaseCallbackManager] = None,
        **kwargs: Any,
    ):
        """Initialize the mega agent.
        
        Args:
            config: Agent configuration
            llm: Language model to use
            callback_manager: Callback manager for monitoring
            **kwargs: Additional configuration
        """
        self.config = config
        self.llm = llm
        self.callback_manager = callback_manager
        self._tools: List[BaseTool] = []
        self._initialized = False
        
    @property
    def agent_id(self) -> str:
        """Get agent ID."""
        return self.config.agent_id
        
    @property
    def manifest(self) -> MegaAgentManifest:
        """Get agent manifest."""
        return self.config.manifest
        
    @property
    def name(self) -> str:
        """Get agent name."""
        return self.manifest.name
        
    @property
    def category(self) -> AgentCategory:
        """Get agent category."""
        return self.manifest.category
        
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the agent."""
        pass
        
    @abstractmethod
    def get_tools(self) -> List[BaseTool]:
        """Get the tools for this agent."""
        pass
        
    @abstractmethod
    async def execute(
        self,
        input_data: Dict[str, Any],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Execute the agent with input data.
        
        Args:
            input_data: Input data for execution
            **kwargs: Additional execution parameters
            
        Returns:
            Execution results
        """
        pass
        
    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics."""
        pass
        
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data.
        
        Args:
            input_data: Input data to validate
            
        Returns:
            True if valid, False otherwise
        """
        return True
        
    def to_manifest_yaml(self) -> str:
        """Export manifest as YAML string."""
        import yaml
        return yaml.dump(self.manifest.dict(), default_flow_style=False)
        
    def save_manifest(self, file_path: str) -> None:
        """Save manifest to YAML file.
        
        Args:
            file_path: Path to save the manifest
        """
        with open(file_path, 'w') as f:
            f.write(self.to_manifest_yaml())