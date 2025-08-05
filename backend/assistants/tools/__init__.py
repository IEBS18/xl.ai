"""
OpenAI Assistants Tools Module

This module provides tool configurations and wrappers for OpenAI Assistants API.
All tools are configurable and avoid hardcoded implementations.
"""

from .code_interpreter_tool import CodeInterpreterTool
from .analysis_tools import AnalysisTools

__all__ = [
    'CodeInterpreterTool',
    'AnalysisTools'
]

# Tool registry for dynamic loading
AVAILABLE_TOOLS = {
    'code_interpreter': CodeInterpreterTool,
    'analysis_tools': AnalysisTools
}

def get_tool_config(tool_name: str, **kwargs):
    """
    Get tool configuration dynamically.
    
    Args:
        tool_name: Name of the tool to configure
        **kwargs: Additional configuration parameters
        
    Returns:
        Tool configuration dictionary
    """
    if tool_name in AVAILABLE_TOOLS:
        tool_class = AVAILABLE_TOOLS[tool_name]
        return tool_class.get_config(**kwargs)
    else:
        raise ValueError(f"Unknown tool: {tool_name}")

def get_available_tools():
    """Get list of available tool names."""
    return list(AVAILABLE_TOOLS.keys())