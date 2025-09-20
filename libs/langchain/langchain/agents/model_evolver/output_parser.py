"""Output parser for Model Evolver Agent."""

import re
from typing import Union

from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.exceptions import OutputParserException

from langchain.agents.agent import AgentOutputParser


class ModelEvolverOutputParser(AgentOutputParser):
    """Output parser for the Model Evolver Agent."""

    def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:
        """Parse the LLM output for the Model Evolver Agent.
        
        Expected format:
        Thought: [reasoning about the task]
        Action: [action to take]
        Action Input: [input for the action]
        
        Or:
        
        Thought: [final reasoning]
        Final Answer: [final result]
        """
        # Check if agent should finish
        if "Final Answer:" in llm_output:
            return AgentFinish(
                return_values={"output": llm_output.split("Final Answer:")[-1].strip()},
                log=llm_output,
            )
        
        # Parse action
        regex = r"Action\s*\d*\s*:(.*?)\nAction\s*\d*\s*Input\s*\d*\s*:[\s]*(.*)"
        match = re.search(regex, llm_output, re.DOTALL)
        if not match:
            raise OutputParserException(f"Could not parse LLM output: `{llm_output}`")
        
        action = match.group(1).strip()
        action_input = match.group(2)
        
        return AgentAction(tool=action, tool_input=action_input.strip(" ").strip('"'), log=llm_output)