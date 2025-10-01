from typing import Annotated, Callable, List, Tuple, Optional, Dict, Any
from dataclasses import dataclass, field
import random
import re
from abc import ABC, abstractmethod

from openai import OpenAI
import json


# Handoff constants for agent switching
HANDOFF_TEMPLATE = "Transferred to: {agent_name}. Adopt persona immediately."
HANDOFF_PATTERN = r"Transferred to: (.*?)(?:\.|$)"


@dataclass
class BaseAgent(ABC):
    """
    Base agent class for creating AI agents with tool calling and handoff capabilities.
    
    This class provides a foundation for building agents that can:
    - Use custom tools/functions
    - Switch control to other agents (handoffs)
    - Work with different LLM providers (OpenAI, Anthropic, Ollama, etc.)
    
    Attributes:
        name: The name of the agent
        model: The LLM model name (e.g., "gpt-4o-mini", "gpt-4", etc.)
        api_key: API key for the LLM provider
        base_url: Base URL for the API (for custom endpoints like Ollama)
        instructions: System prompt that defines the agent's behavior
        functions: List of callable functions that the agent can use as tools
        verbose: Whether to print agent responses (default: True)
    """
    
    name: str = "BaseAgent"
    model: str = "gpt-4o-mini"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    instructions: str = "You are a helpful AI agent."
    functions: List[Callable] = field(default_factory=list)
    verbose: bool = True
    
    def __post_init__(self):
        """Initialize the agent after dataclass initialization."""
        # Initialize OpenAI client
        client_kwargs = {}
        if self.api_key:
            client_kwargs['api_key'] = self.api_key
        if self.base_url:
            client_kwargs['base_url'] = self.base_url
        
        self.client = OpenAI(**client_kwargs)
        
        # Convert functions to OpenAI tool format
        self.tools = self._create_tools() if self.functions else None
    
    def _create_tools(self) -> List[Dict[str, Any]]:
        """Convert Python functions to OpenAI tool format."""
        tools = []
        for func in self.functions:
            tool = {
                "type": "function",
                "function": {
                    "name": func.__name__,
                    "description": func.__doc__ or f"Function {func.__name__}",
                    "parameters": self._get_function_schema(func)
                }
            }
            tools.append(tool)
        return tools
    
    def _get_function_schema(self, func: Callable) -> Dict[str, Any]:
        """Extract JSON schema from function annotations."""
        import inspect
        sig = inspect.signature(func)
        
        properties = {}
        required = []
        
        for param_name, param in sig.parameters.items():
            if param.annotation != inspect.Parameter.empty:
                # Check if it's an Annotated type
                if hasattr(param.annotation, '__metadata__'):
                    param_type = param.annotation.__origin__
                    description = param.annotation.__metadata__[0] if param.annotation.__metadata__ else ""
                else:
                    param_type = param.annotation
                    description = ""
                
                # Map Python types to JSON schema types
                type_mapping = {
                    str: "string",
                    int: "integer",
                    float: "number",
                    bool: "boolean",
                    list: "array",
                    dict: "object"
                }
                
                json_type = type_mapping.get(param_type, "string")
                
                properties[param_name] = {
                    "type": json_type,
                    "description": description
                }
                
                if param.default == inspect.Parameter.empty:
                    required.append(param_name)
        
        return {
            "type": "object",
            "properties": properties,
            "required": required
        }
    
    def _invoke_function(self, function_name: str, arguments: str) -> str:
        """Invoke a function by name with JSON arguments."""
        try:
            # Find the function
            func = next((f for f in self.functions if f.__name__ == function_name), None)
            if not func:
                return f"Error: Function {function_name} not found"
            
            # Parse arguments
            args = json.loads(arguments)
            
            # Call function
            result = func(**args)
            return str(result)
        except Exception as e:
            return f"Error executing {function_name}: {str(e)}"
    
    def run(self, messages: List[Dict[str, str]]) -> Tuple[str, List[Dict[str, str]]]:
        """
        Run the agent with the given conversation history.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
            
        Returns:
            Tuple of (next_agent_name, new_messages)
            - next_agent_name: Name of the agent to run next (for handoffs)
            - new_messages: List of new message dicts generated (including tool results)
        """
        # Add system message
        full_messages = [{"role": "system", "content": self.instructions}] + messages
        
        # Generate response from the LLM
        response_kwargs = {"model": self.model, "messages": full_messages}
        if self.tools:
            response_kwargs["tools"] = self.tools
        
        response = self.client.chat.completions.create(**response_kwargs)
        
        assistant_message = response.choices[0].message
        new_messages = []
        
        # Add assistant message
        message_dict = {"role": "assistant", "content": assistant_message.content or ""}
        
        # Print agent response if verbose
        if assistant_message.content and self.verbose:
            print(f"\n{self.name}: {assistant_message.content}")
        
        # Handle tool calls
        if assistant_message.tool_calls:
            message_dict["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in assistant_message.tool_calls
            ]
            new_messages.append(message_dict)
            
            # Execute tool calls
            next_agent_name = self.name
            for tool_call in assistant_message.tool_calls:
                function_name = tool_call.function.name
                arguments = tool_call.function.arguments
                
                result = self._invoke_function(function_name, arguments)
                
                # Add tool result message
                tool_message = {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                }
                new_messages.append(tool_message)
                
                # Check for handoff
                match = re.search(HANDOFF_PATTERN, result)
                if match:
                    next_agent_name = match.group(1)
            
            return next_agent_name, new_messages
        else:
            new_messages.append(message_dict)
            return self.name, new_messages
    
    @abstractmethod
    def get_handoff_functions(self) -> List[Callable]:
        """
        Define handoff functions for this agent.
        
        This method should be implemented by subclasses to define
        which other agents this agent can transfer control to.
        
        Returns:
            List of handoff functions
        """
        pass
    
    def add_tool(self, func: Callable) -> None:
        """
        Add a new tool/function to the agent dynamically.
        
        Args:
            func: The function to add as a tool
        """
        if func not in self.functions:
            self.functions.append(func)
            # Recreate tools and tool invoker
            self.__post_init__()
    
    def remove_tool(self, func_name: str) -> None:
        """
        Remove a tool/function from the agent by name.
        
        Args:
            func_name: The name of the function to remove
        """
        self.functions = [f for f in self.functions if f.__name__ != func_name]
        # Recreate tools and tool invoker
        self.__post_init__()
    
    def update_instructions(self, new_instructions: str) -> None:
        """
        Update the agent's system instructions.
        
        Args:
            new_instructions: The new instruction text
        """
        self.instructions = new_instructions
        self._system_message = ChatMessage.from_system(self.instructions)
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get the agent's configuration.
        
        Returns:
            Dictionary containing agent configuration
        """
        return {
            "name": self.name,
            "model": self.model,
            "instructions": self.instructions,
            "num_tools": len(self.functions) if self.functions else 0,
            "tool_names": [f.__name__ for f in self.functions] if self.functions else []
        }


def create_handoff_function(target_agent_name: str, description: str = None) -> Callable:
    """
    Factory function to create a handoff function for agent switching.
    
    Args:
        target_agent_name: Name of the agent to transfer control to
        description: Optional description for when to use this handoff
        
    Returns:
        A handoff function that can be added to an agent's tools
    """
    default_desc = f"Transfer control to {target_agent_name}"
    func_description = description or default_desc
    
    def handoff_func() -> str:
        return HANDOFF_TEMPLATE.format(agent_name=target_agent_name)
    
    handoff_func.__doc__ = func_description
    handoff_func.__name__ = f"transfer_to_{target_agent_name.lower().replace(' ', '_')}"
    
    return handoff_func


# Example usage and helper functions

def run_agent_loop(
    agents: Dict[str, BaseAgent], 
    starting_agent_name: str = None,
    max_iterations: int = 100
) -> List[Dict[str, str]]:
    """
    Run a multi-agent conversation loop.
    
    Args:
        agents: Dictionary mapping agent names to agent instances
        starting_agent_name: Name of the first agent to run (optional)
        max_iterations: Maximum number of iterations to prevent infinite loops
        
    Returns:
        Complete conversation history as list of message dicts
    """
    if not agents:
        raise ValueError("No agents provided")
    
    current_agent_name = starting_agent_name or list(agents.keys())[0]
    messages = []
    iterations = 0
    
    print("Type 'quit' or 'exit' to end the conversation")
    print("-" * 50)
    
    while iterations < max_iterations:
        agent = agents.get(current_agent_name)
        if not agent:
            print(f"Error: Agent '{current_agent_name}' not found")
            break
        
        # Get user input if last message was from assistant or conversation is empty
        if not messages or messages[-1]["role"] == "assistant":
            user_input = input("\nUser: ").strip()
            
            if user_input.lower() in ["quit", "exit"]:
                print("\nEnding conversation. Goodbye!")
                break
            
            if not user_input:
                continue
                
            messages.append({"role": "user", "content": user_input})
        
        # Run the agent
        current_agent_name, new_messages = agent.run(messages)
        messages.extend(new_messages)
        
        iterations += 1
    
    if iterations >= max_iterations:
        print(f"\nReached maximum iterations ({max_iterations}). Ending conversation.")
    
    return messages