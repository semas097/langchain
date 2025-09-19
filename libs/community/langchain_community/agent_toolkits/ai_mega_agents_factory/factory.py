"""Factory for creating and managing mega agents."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Type, Union

from langchain_core.callbacks import BaseCallbackManager
from langchain_core.language_models import BaseLanguageModel

from langchain_community.agent_toolkits.ai_mega_agents_factory.base import (
    AgentCategory,
    BaseMegaAgent,
    MegaAgentConfig,
    MegaAgentManifest,
)


class AgentType(str, Enum):
    """Types of mega agents available."""
    
    # Data Processing Agents (5)
    ETL_AGENT = "etl_agent"
    DATA_VALIDATION_AGENT = "data_validation_agent"
    DATA_TRANSFORMATION_AGENT = "data_transformation_agent"
    DATA_MIGRATION_AGENT = "data_migration_agent"
    DATA_CLEANUP_AGENT = "data_cleanup_agent"
    
    # AI/ML Agents (8)
    MODEL_TRAINING_AGENT = "model_training_agent"
    PREDICTION_AGENT = "prediction_agent"
    CLASSIFICATION_AGENT = "classification_agent"
    CLUSTERING_AGENT = "clustering_agent"
    RECOMMENDATION_AGENT = "recommendation_agent"
    NLP_PROCESSING_AGENT = "nlp_processing_agent"
    COMPUTER_VISION_AGENT = "computer_vision_agent"
    TIME_SERIES_ANALYSIS_AGENT = "time_series_analysis_agent"
    
    # Business Intelligence Agents (6)
    ANALYTICS_AGENT = "analytics_agent"
    REPORTING_AGENT = "reporting_agent"
    DASHBOARD_AGENT = "dashboard_agent"
    KPI_MONITORING_AGENT = "kpi_monitoring_agent"
    FORECASTING_AGENT = "forecasting_agent"
    BENCHMARKING_AGENT = "benchmarking_agent"
    
    # Communication Agents (4)
    EMAIL_AGENT = "email_agent"
    SLACK_AGENT = "slack_agent"
    TEAMS_AGENT = "teams_agent"
    SMS_AGENT = "sms_agent"
    
    # Integration Agents (6)
    API_GATEWAY_AGENT = "api_gateway_agent"
    DATABASE_CONNECTOR_AGENT = "database_connector_agent"
    CLOUD_SERVICES_AGENT = "cloud_services_agent"
    FILE_SYSTEM_AGENT = "file_system_agent"
    WEB_SCRAPING_AGENT = "web_scraping_agent"
    MESSAGE_QUEUE_AGENT = "message_queue_agent"
    
    # Security Agents (4)
    AUTHENTICATION_AGENT = "authentication_agent"
    AUTHORIZATION_AGENT = "authorization_agent"
    ENCRYPTION_AGENT = "encryption_agent"
    AUDIT_AGENT = "audit_agent"
    
    # Workflow Agents (5)
    TASK_ORCHESTRATION_AGENT = "task_orchestration_agent"
    PROCESS_AUTOMATION_AGENT = "process_automation_agent"
    SCHEDULING_AGENT = "scheduling_agent"
    MONITORING_AGENT = "monitoring_agent"
    ERROR_HANDLING_AGENT = "error_handling_agent"
    
    # Specialist Agents (11)
    FINANCIAL_TRADING_AGENT = "financial_trading_agent"
    HEALTHCARE_DATA_AGENT = "healthcare_data_agent"
    LEGAL_DOCUMENT_AGENT = "legal_document_agent"
    MARKETING_CAMPAIGN_AGENT = "marketing_campaign_agent"
    SUPPLY_CHAIN_AGENT = "supply_chain_agent"
    HR_ANALYTICS_AGENT = "hr_analytics_agent"
    IOT_DEVICE_AGENT = "iot_device_agent"
    SOCIAL_MEDIA_AGENT = "social_media_agent"
    CONTENT_GENERATION_AGENT = "content_generation_agent"
    CODE_ANALYSIS_AGENT = "code_analysis_agent"
    CUSTOMER_SUPPORT_AGENT = "customer_support_agent"


class MegaAgentFactory:
    """Factory for creating and managing mega agents."""
    
    def __init__(self):
        """Initialize the factory."""
        self._agent_registry: Dict[AgentType, Type[BaseMegaAgent]] = {}
        self._category_mapping: Dict[AgentType, AgentCategory] = {}
        self._initialize_registry()
        
    def _initialize_registry(self) -> None:
        """Initialize the agent registry with mappings."""
        # Register implemented agents
        from langchain_community.agent_toolkits.ai_mega_agents_factory.agents.data_processing.etl import ETLAgent
        
        self.register_agent(AgentType.ETL_AGENT, ETLAgent)
        
        # Data Processing Agents
        data_processing_agents = [
            AgentType.ETL_AGENT,
            AgentType.DATA_VALIDATION_AGENT,
            AgentType.DATA_TRANSFORMATION_AGENT,
            AgentType.DATA_MIGRATION_AGENT,
            AgentType.DATA_CLEANUP_AGENT,
        ]
        
        # AI/ML Agents
        ai_ml_agents = [
            AgentType.MODEL_TRAINING_AGENT,
            AgentType.PREDICTION_AGENT,
            AgentType.CLASSIFICATION_AGENT,
            AgentType.CLUSTERING_AGENT,
            AgentType.RECOMMENDATION_AGENT,
            AgentType.NLP_PROCESSING_AGENT,
            AgentType.COMPUTER_VISION_AGENT,
            AgentType.TIME_SERIES_ANALYSIS_AGENT,
        ]
        
        # Business Intelligence Agents
        bi_agents = [
            AgentType.ANALYTICS_AGENT,
            AgentType.REPORTING_AGENT,
            AgentType.DASHBOARD_AGENT,
            AgentType.KPI_MONITORING_AGENT,
            AgentType.FORECASTING_AGENT,
            AgentType.BENCHMARKING_AGENT,
        ]
        
        # Communication Agents
        communication_agents = [
            AgentType.EMAIL_AGENT,
            AgentType.SLACK_AGENT,
            AgentType.TEAMS_AGENT,
            AgentType.SMS_AGENT,
        ]
        
        # Integration Agents
        integration_agents = [
            AgentType.API_GATEWAY_AGENT,
            AgentType.DATABASE_CONNECTOR_AGENT,
            AgentType.CLOUD_SERVICES_AGENT,
            AgentType.FILE_SYSTEM_AGENT,
            AgentType.WEB_SCRAPING_AGENT,
            AgentType.MESSAGE_QUEUE_AGENT,
        ]
        
        # Security Agents
        security_agents = [
            AgentType.AUTHENTICATION_AGENT,
            AgentType.AUTHORIZATION_AGENT,
            AgentType.ENCRYPTION_AGENT,
            AgentType.AUDIT_AGENT,
        ]
        
        # Workflow Agents
        workflow_agents = [
            AgentType.TASK_ORCHESTRATION_AGENT,
            AgentType.PROCESS_AUTOMATION_AGENT,
            AgentType.SCHEDULING_AGENT,
            AgentType.MONITORING_AGENT,
            AgentType.ERROR_HANDLING_AGENT,
        ]
        
        # Specialist Agents
        specialist_agents = [
            AgentType.FINANCIAL_TRADING_AGENT,
            AgentType.HEALTHCARE_DATA_AGENT,
            AgentType.LEGAL_DOCUMENT_AGENT,
            AgentType.MARKETING_CAMPAIGN_AGENT,
            AgentType.SUPPLY_CHAIN_AGENT,
            AgentType.HR_ANALYTICS_AGENT,
            AgentType.IOT_DEVICE_AGENT,
            AgentType.SOCIAL_MEDIA_AGENT,
            AgentType.CONTENT_GENERATION_AGENT,
            AgentType.CODE_ANALYSIS_AGENT,
            AgentType.CUSTOMER_SUPPORT_AGENT,
        ]
        
        # Map agents to categories
        for agent_type in data_processing_agents:
            self._category_mapping[agent_type] = AgentCategory.DATA_PROCESSING
            
        for agent_type in ai_ml_agents:
            self._category_mapping[agent_type] = AgentCategory.AI_ML
            
        for agent_type in bi_agents:
            self._category_mapping[agent_type] = AgentCategory.BUSINESS_INTELLIGENCE
            
        for agent_type in communication_agents:
            self._category_mapping[agent_type] = AgentCategory.COMMUNICATION
            
        for agent_type in integration_agents:
            self._category_mapping[agent_type] = AgentCategory.INTEGRATION
            
        for agent_type in security_agents:
            self._category_mapping[agent_type] = AgentCategory.SECURITY
            
        for agent_type in workflow_agents:
            self._category_mapping[agent_type] = AgentCategory.WORKFLOW
            
        for agent_type in specialist_agents:
            self._category_mapping[agent_type] = AgentCategory.SPECIALIST
    
    def register_agent(
        self,
        agent_type: AgentType,
        agent_class: Type[BaseMegaAgent],
    ) -> None:
        """Register an agent class with the factory.
        
        Args:
            agent_type: Type of agent
            agent_class: Agent class to register
        """
        self._agent_registry[agent_type] = agent_class
    
    def create_agent(
        self,
        agent_type: AgentType,
        config: Optional[MegaAgentConfig] = None,
        llm: Optional[BaseLanguageModel] = None,
        callback_manager: Optional[BaseCallbackManager] = None,
        **kwargs: Any,
    ) -> BaseMegaAgent:
        """Create an agent instance.
        
        Args:
            agent_type: Type of agent to create
            config: Agent configuration
            llm: Language model to use
            callback_manager: Callback manager
            **kwargs: Additional configuration
            
        Returns:
            Agent instance
            
        Raises:
            ValueError: If agent type is not registered
        """
        if agent_type not in self._agent_registry:
            raise ValueError(f"Agent type {agent_type} is not registered")
            
        agent_class = self._agent_registry[agent_type]
        
        # Create default config if not provided
        if config is None:
            manifest = MegaAgentManifest(
                name=agent_type.value.replace("_", " ").title(),
                version="1.0.0",
                category=self._category_mapping[agent_type],
                description=f"Enterprise {agent_type.value.replace('_', ' ')} agent",
                author="AI Mega Agents Factory",
            )
            config = MegaAgentConfig(manifest=manifest)
        
        return agent_class(
            config=config,
            llm=llm,
            callback_manager=callback_manager,
            **kwargs,
        )
    
    def list_agents(self, category: Optional[AgentCategory] = None) -> List[AgentType]:
        """List available agent types.
        
        Args:
            category: Optional category filter
            
        Returns:
            List of agent types
        """
        if category is None:
            return list(self._category_mapping.keys())
        
        return [
            agent_type
            for agent_type, agent_category in self._category_mapping.items()
            if agent_category == category
        ]
    
    def get_agent_category(self, agent_type: AgentType) -> AgentCategory:
        """Get the category for an agent type.
        
        Args:
            agent_type: Agent type
            
        Returns:
            Agent category
        """
        return self._category_mapping[agent_type]
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics.
        
        Returns:
            Registry statistics
        """
        stats = {
            "total_agents": len(self._category_mapping),
            "registered_agents": len(self._agent_registry),
            "categories": {},
        }
        
        for category in AgentCategory:
            count = sum(
                1 for agent_category in self._category_mapping.values()
                if agent_category == category
            )
            stats["categories"][category.value] = count
            
        return stats


# Global factory instance
mega_agent_factory = MegaAgentFactory()