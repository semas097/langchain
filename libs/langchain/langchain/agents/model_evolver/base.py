"""Model Evolver Agent implementation."""

from __future__ import annotations

from typing import Any, List, Optional, Sequence, Type, Union

from langchain_core._api import deprecated
from langchain_core.callbacks import CallbackManagerForChainRun
from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import BasePromptTemplate
from langchain_core.tools import BaseTool
from pydantic import Field

from langchain._api.deprecation import AGENT_DEPRECATION_WARNING
from langchain.agents.agent import Agent, AgentOutputParser
from langchain.agents.agent_types import AgentType
from langchain.agents.model_evolver.output_parser import ModelEvolverOutputParser
from langchain.agents.model_evolver.prompt import MODEL_EVOLVER_PROMPT
from langchain.agents.utils import validate_tools_single_input


@deprecated(
    "0.1.0",
    message=AGENT_DEPRECATION_WARNING,
    removal="1.0",
)
class ModelEvolverAgent(Agent):
    """Agent for model evolution and optimization tasks.
    
    This agent provides capabilities for model analysis, comparison,
    and basic evolution strategies in a safe, educational context.
    """

    output_parser: AgentOutputParser = Field(default_factory=ModelEvolverOutputParser)

    @classmethod
    def _get_default_output_parser(cls, **kwargs: Any) -> AgentOutputParser:
        return ModelEvolverOutputParser()

    @property
    def _agent_type(self) -> str:
        """Return Identifier of agent type."""
        return "model-evolver"

    @classmethod
    def create_prompt(cls, tools: Sequence[BaseTool]) -> BasePromptTemplate:
        """Return default prompt."""
        tool_strings = "\n".join([f"{tool.name}: {tool.description}" for tool in tools])
        template = MODEL_EVOLVER_PROMPT.format(tools=tool_strings)
        return MODEL_EVOLVER_PROMPT

    @classmethod
    def from_llm_and_tools(
        cls,
        llm: BaseLanguageModel,
        tools: Sequence[BaseTool],
        callback_manager: Optional[Any] = None,
        output_parser: Optional[AgentOutputParser] = None,
        **kwargs: Any,
    ) -> ModelEvolverAgent:
        """Construct an agent from an LLM and tools."""
        cls._validate_tools(tools)
        prompt = cls.create_prompt(tools)
        llm_chain = cls._get_llm_chain(
            llm=llm,
            prompt=prompt,
            callback_manager=callback_manager,
        )
        tool_names = [tool.name for tool in tools]
        _output_parser = output_parser or cls._get_default_output_parser()
        return cls(
            llm_chain=llm_chain,
            allowed_tools=tool_names,
            output_parser=_output_parser,
            **kwargs,
        )

    @classmethod
    def _validate_tools(cls, tools: Sequence[BaseTool]) -> None:
        """Validate that appropriate tools are passed in."""
        validate_tools_single_input(cls.__name__, tools)


def create_model_evolver_agent(
    llm: BaseLanguageModel,
    tools: Sequence[BaseTool],
    **kwargs: Any,
) -> ModelEvolverAgent:
    """Create a model evolver agent.
    
    Args:
        llm: Language model to use for the agent.
        tools: Tools to use for model evolution tasks.
        **kwargs: Additional arguments to pass to the agent.
        
    Returns:
        A ModelEvolverAgent instance.
    """
    return ModelEvolverAgent.from_llm_and_tools(
        llm=llm,
        tools=tools,
        **kwargs,
    )