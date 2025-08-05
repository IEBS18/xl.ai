# utils/dataframe_utils.py - NEW utility functions for DataFrame and code handling

import pandas as pd
import logging
from datetime import datetime
from typing import Dict, Any, Union

def standardize_dataframe_response(dataframes: Dict[str, Any]) -> Dict[str, Any]:
    """
    NEW: Standardize DataFrame response format for consistent frontend handling.
    
    This function ensures all DataFrames are returned in a consistent format
    regardless of which handler generated them.
    
    Args:
        dataframes: Dictionary of DataFrames in various formats
        
    Returns:
        Dictionary with standardized DataFrame format
    """
    standardized = {}
    
    try:
        for df_name, df_value in dataframes.items():
            if isinstance(df_value, pd.DataFrame):
                # Direct DataFrame object
                standardized[df_name] = {
                    'data': df_value,  # Keep actual DataFrame for backend
                    'type': 'dataframe',
                    'name': df_name,
                    'shape': df_value.shape,
                    'columns': list(df_value.columns),
                    'dtypes': df_value.dtypes.to_dict(),
                    'preview_html': generate_dataframe_preview_html(df_value),
                    'json_data': df_value.head(100).to_dict('records'),
                    'summary': {
                        'rows': len(df_value),
                        'columns': len(df_value.columns),
                        'memory_usage_mb': df_value.memory_usage(deep=True).sum() / (1024 * 1024),
                        'null_counts': df_value.isnull().sum().to_dict(),
                        'numeric_columns': list(df_value.select_dtypes(include=['number']).columns),
                        'categorical_columns': list(df_value.select_dtypes(include=['object']).columns)
                    },
                    'metadata': {
                        'created_at': datetime.now().isoformat(),
                        'source': 'enhanced_analyzer',
                        'processed': True
                    }
                }
                
            elif isinstance(df_value, dict) and df_value.get('type') == 'dataframe':
                # Already structured format - just validate and enhance
                actual_df = df_value.get('data')
                if isinstance(actual_df, pd.DataFrame):
                    standardized[df_name] = {
                        **df_value,  # Keep existing structure
                        'summary': df_value.get('summary', generate_dataframe_summary(actual_df)),
                        'metadata': {
                            'created_at': datetime.now().isoformat(),
                            'source': 'enhanced_analyzer',
                            'processed': True,
                            **df_value.get('metadata', {})
                        }
                    }
                else:
                    # Invalid structure, create placeholder
                    standardized[df_name] = create_placeholder_dataframe_info(df_name, df_value)
                    
            else:
                # Unknown format, create placeholder
                standardized[df_name] = create_placeholder_dataframe_info(df_name, df_value)
                
    except Exception as e:
        logging.error(f"Error standardizing DataFrame response: {e}")
        # Return empty dict if standardization fails
        return {}
    
    return standardized


def standardize_code_response(generated_code: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    NEW: Standardize generated code response format for consistent frontend handling.
    
    Args:
        generated_code: Generated code in various formats
        
    Returns:
        Dictionary with standardized code format
    """
    try:
        if isinstance(generated_code, dict):
            # Already structured
            code_string = generated_code.get('code', '')
            return {
                'code': code_string,
                'type': 'code',
                'language': generated_code.get('language', 'python'),
                'lines': generated_code.get('lines', len(code_string.split('\n'))),
                'preview': code_string[:500] + '...' if len(code_string) > 500 else code_string,
                'summary': generate_code_summary(code_string),
                'metadata': {
                    'created_at': datetime.now().isoformat(),
                    'source': 'enhanced_analyzer',
                    'processed': True,
                    **generated_code.get('metadata', {})
                }
            }
        elif isinstance(generated_code, str):
            # Raw string
            return {
                'code': generated_code,
                'type': 'code',
                'language': 'python',
                'lines': len(generated_code.split('\n')),
                'preview': generated_code[:500] + '...' if len(generated_code) > 500 else generated_code,
                'summary': generate_code_summary(generated_code),
                'metadata': {
                    'created_at': datetime.now().isoformat(),
                    'source': 'enhanced_analyzer',
                    'processed': True
                }
            }
        else:
            # Empty or invalid
            return {
                'code': '',
                'type': 'code',
                'language': 'python',
                'lines': 0,
                'preview': '',
                'summary': generate_code_summary(''),
                'metadata': {
                    'created_at': datetime.now().isoformat(),
                    'source': 'enhanced_analyzer',
                    'processed': True
                }
            }
            
    except Exception as e:
        logging.error(f"Error standardizing code response: {e}")
        return {
            'code': '',
            'type': 'code',
            'language': 'python',
            'lines': 0,
            'preview': '',
            'summary': {'error': str(e)},
            'metadata': {'error': True}
        }


def generate_dataframe_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate comprehensive summary for a DataFrame"""
    try:
        return {
            'rows': len(df),
            'columns': len(df.columns),
            'memory_usage_mb': df.memory_usage(deep=True).sum() / (1024 * 1024),
            'null_counts': df.isnull().sum().to_dict(),
            'numeric_columns': list(df.select_dtypes(include=['number']).columns),
            'categorical_columns': list(df.select_dtypes(include=['object']).columns),
            'datetime_columns': list(df.select_dtypes(include=['datetime64']).columns),
            'total_null_values': df.isnull().sum().sum(),
            'duplicate_rows': df.duplicated().sum(),
            'column_types': df.dtypes.value_counts().to_dict()
        }
    except Exception as e:
        logging.error(f"Error generating DataFrame summary: {e}")
        return {'error': str(e)}


def generate_code_summary(code_string: str) -> Dict[str, Any]:
    """Generate comprehensive summary for generated code"""
    try:
        if not code_string:
            return {
                'total_lines': 0,
                'non_empty_lines': 0,
                'imports': 0,
                'functions': 0,
                'classes': 0,
                'comments': 0,
                'size_bytes': 0
            }
        
        lines = code_string.split('\n')
        
        return {
            'total_lines': len(lines),
            'non_empty_lines': len([line for line in lines if line.strip()]),
            'imports': len([line for line in lines if line.strip().startswith(('import ', 'from '))]),
            'functions': len([line for line in lines if line.strip().startswith('def ')]),
            'classes': len([line for line in lines if line.strip().startswith('class ')]),
            'comments': len([line for line in lines if line.strip().startswith('#')]),
            'size_bytes': len(code_string.encode('utf-8')),
            'complexity_score': calculate_code_complexity(code_string),
            'contains_loops': any(keyword in code_string for keyword in ['for ', 'while ']),
            'contains_conditions': any(keyword in code_string for keyword in ['if ', 'elif ', 'else:']),
            'contains_dataframe_ops': 'df.' in code_string or 'DataFrame' in code_string,
            'contains_plotting': any(keyword in code_string for keyword in ['plt.', 'plot(', 'matplotlib']),
            'libraries_used': extract_libraries_from_code(code_string)
        }
    except Exception as e:
        logging.error(f"Error generating code summary: {e}")
        return {'error': str(e)}


def calculate_code_complexity(code_string: str) -> int:
    """Calculate basic complexity score for code"""
    try:
        complexity = 0
        
        # Count decision points
        decision_keywords = ['if ', 'elif ', 'while ', 'for ', 'try:', 'except', 'with ']
        for keyword in decision_keywords:
            complexity += code_string.count(keyword)
        
        # Count function definitions
        complexity += code_string.count('def ')
        
        # Count class definitions  
        complexity += code_string.count('class ')
        
        return complexity
    except:
        return 0


def extract_libraries_from_code(code_string: str) -> list:
    """Extract library names from import statements"""
    try:
        libraries = []
        lines = code_string.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('import '):
                # Handle "import pandas as pd"
                parts = line[7:].split(' as ')
                lib_name = parts[0].split('.')[0].strip()
                libraries.append(lib_name)
            elif line.startswith('from '):
                # Handle "from pandas import DataFrame"
                parts = line.split(' import ')
                if len(parts) > 1:
                    lib_name = parts[0][5:].split('.')[0].strip()
                    libraries.append(lib_name)
        
        return list(set(libraries))  # Remove duplicates
    except:
        return []


def generate_dataframe_preview_html(df: pd.DataFrame, max_rows: int = 10) -> str:
    """Generate HTML preview for DataFrame"""
    try:
        # Use existing table generation utility if available
        try:
            from utils.utils import generate_tailwind_table
            return generate_tailwind_table(df.head(max_rows))
        except ImportError:
            # Fallback to simple HTML table
            return generate_simple_html_table(df.head(max_rows))
    except Exception as e:
        logging.error(f"Error generating DataFrame preview: {e}")
        return f"<p>DataFrame with {df.shape[0]} rows and {df.shape[1]} columns</p>"


def generate_simple_html_table(df: pd.DataFrame) -> str:
    """Generate simple HTML table as fallback"""
    try:
        return df.to_html(
            classes="table table-striped table-hover",
            table_id="dataframe-preview",
            index=False,
            max_rows=50,
            escape=False
        )
    except Exception as e:
        logging.error(f"Error generating simple HTML table: {e}")
        return f"<p>Error generating table: {str(e)}</p>"


def create_placeholder_dataframe_info(df_name: str, df_value: Any) -> Dict[str, Any]:
    """Create placeholder DataFrame info for invalid or unknown formats"""
    return {
        'data': pd.DataFrame({'Info': [f'Invalid DataFrame format for {df_name}']}),
        'type': 'placeholder',
        'name': df_name,
        'shape': (1, 1),
        'columns': ['Info'],
        'dtypes': {'Info': 'object'},
        'preview_html': f"<p>Invalid DataFrame format for {df_name}</p>",
        'json_data': [{'Info': f'Invalid DataFrame format for {df_name}'}],
        'summary': {
            'rows': 1,
            'columns': 1,
            'error': True,
            'original_type': str(type(df_value))
        },
        'metadata': {
            'created_at': datetime.now().isoformat(),
            'source': 'error_handler',
            'processed': False,
            'error': True
        }
    }


def validate_dataframe_format(df_data: Any) -> bool:
    """Validate if data is in proper DataFrame format"""
    try:
        if isinstance(df_data, pd.DataFrame):
            return True
        elif isinstance(df_data, dict) and df_data.get('type') == 'dataframe':
            return isinstance(df_data.get('data'), pd.DataFrame)
        else:
            return False
    except:
        return False


def validate_code_format(code_data: Any) -> bool:
    """Validate if data is in proper code format"""
    try:
        if isinstance(code_data, str):
            return True
        elif isinstance(code_data, dict) and code_data.get('type') == 'code':
            return isinstance(code_data.get('code'), str)
        else:
            return False
    except:
        return False


def extract_dataframe_from_result(result: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
    """Extract actual DataFrame objects from result for backend processing"""
    extracted = {}
    
    try:
        dataframes = result.get('dataframes', {})
        for df_name, df_info in dataframes.items():
            if isinstance(df_info, pd.DataFrame):
                extracted[df_name] = df_info
            elif isinstance(df_info, dict) and df_info.get('type') == 'dataframe':
                actual_df = df_info.get('data')
                if isinstance(actual_df, pd.DataFrame):
                    extracted[df_name] = actual_df
    except Exception as e:
        logging.error(f"Error extracting DataFrames from result: {e}")
    
    return extracted


def extract_code_from_result(result: Dict[str, Any]) -> str:
    """Extract actual code string from result for backend processing"""
    try:
        generated_code = result.get('generated_code', '')
        if isinstance(generated_code, dict):
            return generated_code.get('code', '')
        elif isinstance(generated_code, str):
            return generated_code
        else:
            return str(generated_code) if generated_code else ''
    except Exception as e:
        logging.error(f"Error extracting code from result: {e}")
        return ''


def merge_dataframe_results(*results: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple analysis results while preserving DataFrame integrity"""
    merged = {
        'dataframes': {},
        'generated_code': '',
        'success': True,
        'type': 'merged_analysis',
        'timestamp': datetime.now().isoformat()
    }
    
    try:
        all_code_parts = []
        
        for result in results:
            if not result:
                continue
                
            # Merge DataFrames
            result_dfs = result.get('dataframes', {})
            for df_name, df_info in result_dfs.items():
                # Avoid name conflicts
                unique_name = df_name
                counter = 1
                while unique_name in merged['dataframes']:
                    unique_name = f"{df_name}_{counter}"
                    counter += 1
                merged['dataframes'][unique_name] = df_info
            
            # Merge code
            code = extract_code_from_result(result)
            if code:
                all_code_parts.append(f"# Analysis {len(all_code_parts) + 1}\n{code}")
            
            # Update success status
            if not result.get('success', True):
                merged['success'] = False
        
        # Combine all code
        merged['generated_code'] = standardize_code_response('\n\n'.join(all_code_parts))
        
        # Standardize merged DataFrames
        merged['dataframes'] = standardize_dataframe_response(merged['dataframes'])
        
        return merged
        
    except Exception as e:
        logging.error(f"Error merging DataFrame results: {e}")
        return {
            'dataframes': {},
            'generated_code': standardize_code_response(''),
            'success': False,
            'error': str(e),
            'type': 'merge_error',
            'timestamp': datetime.now().isoformat()
        }