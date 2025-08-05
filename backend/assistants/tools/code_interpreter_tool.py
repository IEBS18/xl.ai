"""
Code Interpreter Tool Configuration

Provides configurable wrapper for OpenAI's Code Interpreter tool.
No hardcoded functions - all configurations are loaded from environment or parameters.
"""

import os
import json
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

class CodeInterpreterTool:
    """
    Configurable wrapper for OpenAI Code Interpreter tool.
    
    This class provides configuration for the Code Interpreter tool
    without hardcoding any specific analysis functions.
    """
    
    @staticmethod
    def get_config(analysis_type: str = "general", **kwargs) -> Dict[str, Any]:
        """
        Get Code Interpreter tool configuration.
        
        Args:
            analysis_type: Type of analysis (general, forecasting, reporting, etc.)
            **kwargs: Additional configuration parameters
            
        Returns:
            Tool configuration dictionary for OpenAI Assistants API
        """
        
        # Base Code Interpreter configuration
        base_config = {
            "type": "code_interpreter"
        }
        
        # Load additional configurations from environment if available
        code_interpreter_config = os.getenv('CODE_INTERPRETER_CONFIG')
        if code_interpreter_config:
            try:
                additional_config = json.loads(code_interpreter_config)
                base_config.update(additional_config)
            except json.JSONDecodeError:
                pass  # Use base config if JSON is invalid
        
        # Apply analysis-type specific configurations
        type_specific_config = CodeInterpreterTool._get_type_specific_config(analysis_type)
        base_config.update(type_specific_config)
        
        # Apply any additional kwargs
        base_config.update(kwargs)
        
        return base_config
    
    @staticmethod
    def _get_type_specific_config(analysis_type: str) -> Dict[str, Any]:
        """
        Get configuration specific to analysis type.
        
        Args:
            analysis_type: Type of analysis
            
        Returns:
            Type-specific configuration
        """
        
        # Load type-specific configs from environment variables
        config_var = f"CODE_INTERPRETER_{analysis_type.upper()}_CONFIG"
        type_config = os.getenv(config_var)
        
        if type_config:
            try:
                return json.loads(type_config)
            except json.JSONDecodeError:
                pass
        
        # Default empty config if no specific configuration found
        return {}
    
    @staticmethod
    def get_supported_file_types() -> List[str]:
        """
        Get list of supported file types for Code Interpreter.
        
        Returns:
            List of supported file extensions
        """
        
        # Load from environment or use defaults
        supported_types_env = os.getenv('CODE_INTERPRETER_SUPPORTED_TYPES')
        
        if supported_types_env:
            try:
                return json.loads(supported_types_env)
            except json.JSONDecodeError:
                pass
        
        # Default supported types
        return [
            '.csv', '.xlsx', '.xls', '.json', '.txt',
            '.py', '.ipynb', '.md', '.tsv'
        ]
    
    @staticmethod
    def get_execution_limits() -> Dict[str, Any]:
        """
        Get execution limits for Code Interpreter.
        
        Returns:
            Dictionary with execution limits
        """
        
        limits = {
            'max_execution_time': int(os.getenv('CODE_INTERPRETER_MAX_TIME', '300')),  # 5 minutes
            'max_file_size': int(os.getenv('CODE_INTERPRETER_MAX_FILE_SIZE', '104857600')),  # 100MB
            'max_output_size': int(os.getenv('CODE_INTERPRETER_MAX_OUTPUT', '10485760')),  # 10MB
        }
        
        return limits
    
    @staticmethod
    def validate_file_for_code_interpreter(file_path: str) -> tuple[bool, str]:
        """
        Validate if a file can be used with Code Interpreter.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            Tuple of (is_valid, message)
        """
        
        if not os.path.exists(file_path):
            return False, "File does not exist"
        
        # Check file extension
        _, ext = os.path.splitext(file_path.lower())
        supported_types = CodeInterpreterTool.get_supported_file_types()
        
        if ext not in supported_types:
            return False, f"File type {ext} not supported. Supported types: {supported_types}"
        
        # Check file size
        file_size = os.path.getsize(file_path)
        limits = CodeInterpreterTool.get_execution_limits()
        max_size = limits.get('max_file_size', 104857600)
        
        if file_size > max_size:
            return False, f"File size {file_size} exceeds maximum {max_size} bytes"
        
        return True, "File is valid for Code Interpreter"
    
    @staticmethod
    def get_tool_instructions(analysis_type: str = "general") -> str:
        """
        Get instructions for the Code Interpreter tool.
        
        Args:
            analysis_type: Type of analysis
            
        Returns:
            Instructions string for the assistant
        """
        
        # Load instructions from environment variable
        instructions_var = f"CODE_INTERPRETER_{analysis_type.upper()}_INSTRUCTIONS"
        custom_instructions = os.getenv(instructions_var)
        
        if custom_instructions:
            return custom_instructions
        
        # Load general instructions
        general_instructions = os.getenv('CODE_INTERPRETER_GENERAL_INSTRUCTIONS')
        if general_instructions:
            return general_instructions
        
        # Return empty string - let the assistant manager handle default instructions
        return ""