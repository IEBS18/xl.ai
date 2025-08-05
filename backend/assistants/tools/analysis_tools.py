"""
Analysis Tools Configuration

Provides configurable analysis tool definitions for OpenAI Assistants.
All tool functions and schemas are loaded from configuration, not hardcoded.
"""

import os
import json
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

class AnalysisTools:
    """
    Configurable analysis tools for OpenAI Assistants.
    
    This class provides tool configurations and schemas that can be
    loaded from environment variables or configuration files.
    """
    
    @staticmethod
    def get_config(tools_list: Optional[List[str]] = None, **kwargs) -> List[Dict[str, Any]]:
        """
        Get analysis tools configuration.
        
        Args:
            tools_list: List of specific tools to include. If None, loads from environment.
            **kwargs: Additional configuration parameters
            
        Returns:
            List of tool configurations for OpenAI Assistants API
        """
        
        if tools_list is None:
            tools_list = AnalysisTools._get_enabled_tools()
        
        tool_configs = []
        
        for tool_name in tools_list:
            tool_config = AnalysisTools._get_tool_config(tool_name)
            if tool_config:
                tool_configs.append(tool_config)
        
        return tool_configs
    
    @staticmethod
    def _get_enabled_tools() -> List[str]:
        """
        Get list of enabled analysis tools from environment.
        
        Returns:
            List of enabled tool names
        """
        
        enabled_tools_env = os.getenv('ANALYSIS_TOOLS_ENABLED')
        
        if enabled_tools_env:
            try:
                return json.loads(enabled_tools_env)
            except json.JSONDecodeError:
                # Fallback to comma-separated string
                return [tool.strip() for tool in enabled_tools_env.split(',')]
        
        # Default tools (can be empty if none configured)
        default_tools = os.getenv('ANALYSIS_TOOLS_DEFAULT', '').split(',')
        return [tool.strip() for tool in default_tools if tool.strip()]
    
    @staticmethod
    def _get_tool_config(tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific analysis tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool configuration dictionary or None if not found
        """
        
        # Load tool configuration from environment variable
        config_var = f"ANALYSIS_TOOL_{tool_name.upper()}_CONFIG"
        tool_config_env = os.getenv(config_var)
        
        if tool_config_env:
            try:
                return json.loads(tool_config_env)
            except json.JSONDecodeError:
                print(f"Invalid JSON in {config_var}")
                return None
        
        # Try to load from a configuration file
        config_file = AnalysisTools._get_tool_config_file(tool_name)
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                print(f"Could not load config file for tool: {tool_name}")
                return None
        
        return None
    
    @staticmethod
    def _get_tool_config_file(tool_name: str) -> Optional[str]:
        """
        Get configuration file path for a tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Path to configuration file or None
        """
        
        # Check for tool-specific config file path
        config_file_var = f"ANALYSIS_TOOL_{tool_name.upper()}_CONFIG_FILE"
        config_file = os.getenv(config_file_var)
        
        if config_file:
            return config_file
        
        # Check for general config directory
        config_dir = os.getenv('ANALYSIS_TOOLS_CONFIG_DIR', './config/tools')
        if os.path.exists(config_dir):
            config_file_path = os.path.join(config_dir, f"{tool_name}.json")
            if os.path.exists(config_file_path):
                return config_file_path
        
        return None
    
    @staticmethod
    def get_available_tools() -> List[str]:
        """
        Get list of all available analysis tools.
        
        Returns:
            List of available tool names
        """
        
        available_tools = []
        
        # Check environment variables for tool configs
        for key, value in os.environ.items():
            if key.startswith('ANALYSIS_TOOL_') and key.endswith('_CONFIG'):
                # Extract tool name from environment variable
                tool_name = key.replace('ANALYSIS_TOOL_', '').replace('_CONFIG', '').lower()
                available_tools.append(tool_name)
        
        # Check config directory for tool files
        config_dir = os.getenv('ANALYSIS_TOOLS_CONFIG_DIR', './config/tools')
        if os.path.exists(config_dir):
            for filename in os.listdir(config_dir):
                if filename.endswith('.json'):
                    tool_name = filename.replace('.json', '')
                    if tool_name not in available_tools:
                        available_tools.append(tool_name)
        
        return available_tools
    
    @staticmethod
    def validate_tool_config(tool_config: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate a tool configuration.
        
        Args:
            tool_config: Tool configuration dictionary
            
        Returns:
            Tuple of (is_valid, message)
        """
        
        required_fields = ['type', 'function']
        
        for field in required_fields:
            if field not in tool_config:
                return False, f"Missing required field: {field}"
        
        # Validate function schema
        function_config = tool_config.get('function', {})
        function_required_fields = ['name', 'description']
        
        for field in function_required_fields:
            if field not in function_config:
                return False, f"Missing required function field: {field}"
        
        # Validate parameters schema if present
        parameters = function_config.get('parameters')
        if parameters and not isinstance(parameters, dict):
            return False, "Parameters must be a dictionary"
        
        return True, "Tool configuration is valid"
    
    @staticmethod
    def get_tool_schema_template() -> Dict[str, Any]:
        """
        Get a template for creating new tool schemas.
        
        Returns:
            Template dictionary for tool configuration
        """
        
        return {
            "type": "function",
            "function": {
                "name": "tool_name_here",
                "description": "Description of what this tool does",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "parameter_name": {
                            "type": "string",
                            "description": "Description of this parameter"
                        }
                    },
                    "required": ["parameter_name"]
                }
            }
        }
    
    @staticmethod
    def create_tool_config_file(tool_name: str, tool_config: Dict[str, Any], config_dir: Optional[str] = None) -> str:
        """
        Create a configuration file for a tool.
        
        Args:
            tool_name: Name of the tool
            tool_config: Tool configuration dictionary
            config_dir: Directory to save config file (optional)
            
        Returns:
            Path to created config file
        """
        
        if config_dir is None:
            config_dir = os.getenv('ANALYSIS_TOOLS_CONFIG_DIR', './config/tools')
        
        # Create directory if it doesn't exist
        os.makedirs(config_dir, exist_ok=True)
        
        config_file_path = os.path.join(config_dir, f"{tool_name}.json")
        
        with open(config_file_path, 'w') as f:
            json.dump(tool_config, f, indent=2)
        
        return config_file_path
    
    @staticmethod
    def load_tools_from_directory(directory: str) -> List[Dict[str, Any]]:
        """
        Load all tool configurations from a directory.
        
        Args:
            directory: Path to directory containing tool config files
            
        Returns:
            List of tool configurations
        """
        
        tool_configs = []
        
        if not os.path.exists(directory):
            return tool_configs
        
        for filename in os.listdir(directory):
            if filename.endswith('.json'):
                file_path = os.path.join(directory, filename)
                try:
                    with open(file_path, 'r') as f:
                        tool_config = json.load(f)
                        
                    # Validate the configuration
                    is_valid, message = AnalysisTools.validate_tool_config(tool_config)
                    if is_valid:
                        tool_configs.append(tool_config)
                    else:
                        print(f"Invalid tool config in {filename}: {message}")
                        
                except (json.JSONDecodeError, IOError) as e:
                    print(f"Could not load tool config from {filename}: {e}")
        
        return tool_configs