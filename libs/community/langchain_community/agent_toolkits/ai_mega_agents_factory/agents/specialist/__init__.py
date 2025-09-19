"""Specialist agents."""

from langchain_community.agent_toolkits.ai_mega_agents_factory.agents.specialist.financial_trading import FinancialTradingAgent
from langchain_community.agent_toolkits.ai_mega_agents_factory.agents.specialist.healthcare_data import HealthcareDataAgent
from langchain_community.agent_toolkits.ai_mega_agents_factory.agents.specialist.legal_document import LegalDocumentAgent
from langchain_community.agent_toolkits.ai_mega_agents_factory.agents.specialist.marketing_campaign import MarketingCampaignAgent
from langchain_community.agent_toolkits.ai_mega_agents_factory.agents.specialist.supply_chain import SupplyChainAgent
from langchain_community.agent_toolkits.ai_mega_agents_factory.agents.specialist.hr_analytics import HRAnalyticsAgent
from langchain_community.agent_toolkits.ai_mega_agents_factory.agents.specialist.iot_device import IoTDeviceAgent
from langchain_community.agent_toolkits.ai_mega_agents_factory.agents.specialist.social_media import SocialMediaAgent
from langchain_community.agent_toolkits.ai_mega_agents_factory.agents.specialist.content_generation import ContentGenerationAgent
from langchain_community.agent_toolkits.ai_mega_agents_factory.agents.specialist.code_analysis import CodeAnalysisAgent
from langchain_community.agent_toolkits.ai_mega_agents_factory.agents.specialist.customer_support import CustomerSupportAgent

__all__ = [
    "FinancialTradingAgent",
    "HealthcareDataAgent",
    "LegalDocumentAgent",
    "MarketingCampaignAgent",
    "SupplyChainAgent", 
    "HRAnalyticsAgent",
    "IoTDeviceAgent",
    "SocialMediaAgent",
    "ContentGenerationAgent",
    "CodeAnalysisAgent",
    "CustomerSupportAgent",
]