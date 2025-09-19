"""Communication agents."""

from langchain_community.agent_toolkits.ai_mega_agents_factory.agents.communication.email import EmailAgent
from langchain_community.agent_toolkits.ai_mega_agents_factory.agents.communication.slack import SlackAgent
from langchain_community.agent_toolkits.ai_mega_agents_factory.agents.communication.teams import TeamsAgent
from langchain_community.agent_toolkits.ai_mega_agents_factory.agents.communication.sms import SMSAgent

__all__ = [
    "EmailAgent",
    "SlackAgent",
    "TeamsAgent", 
    "SMSAgent",
]