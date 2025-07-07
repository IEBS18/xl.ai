import sys
import io
import contextlib
import traceback
import subprocess
from typing import Dict, Any, Optional, List
import json
import re
import importlib.metadata
import importlib.util

class PythonCodeExecutor:
    def __init__(self):
        self.allowed_packages = {
            'numpy', 'pandas', 'scikit-learn', 'matplotlib', 
            'seaborn', 'plotly', 'scipy', 'statsmodels', 'xgboost',
            'lightgbm', 'catboost', 'tensorflow', 'torch', 'keras'
        }
        self.restricted_modules = {
            'os', 'subprocess', 'sys', 'eval', 'exec', 'open', 'file',
            '__import__', 'compile', 'globals', 'locals', 'vars'
        }
    
    def check_code_safety(self, code: str) -> tuple[bool, str]:
        """Basic safety checks for the generated code"""
        dangerous_patterns = [
            r'\b(os\.|subprocess\.|sys\.)',
            r'\b(eval|exec|compile|__import__)\s*\(',
            r'\bopen\s*\(',
            r'\bfile\s*\(',
            r'globals\s*\(\)|locals\s*\(\)',
            r'__.*__',  # dunder methods
            r'import\s+os|import\s+subprocess|import\s+sys'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                return False, f"Potentially dangerous code detected: {pattern}"
        
        return True, "Code appears safe"
    
    def install_missing_packages(self, code: str) -> List[str]:
        """Extract and install missing packages from import statements"""
        import_patterns = [
            r'import\s+(\w+)',
            r'from\s+(\w+)',
            r'import\s+(\w+)\s+as\s+\w+',
            r'from\s+(\w+)\s+import'
        ]
        
        required_packages = set()
        for pattern in import_patterns:
            matches = re.findall(pattern, code)
            for match in matches:
                if match in self.allowed_packages:
                    required_packages.add(match)
        
        installed_packages = []
        for package in required_packages:
            try:
                importlib.metadata.distribution(package)
            except importlib.metadata.PackageNotFoundError:
                try:
                    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                    installed_packages.append(package)
                except subprocess.CalledProcessError:
                    print(f"Warning: Could not install {package}")
        
        return installed_packages
    
    def execute_code(self, code: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the generated Python code safely
        
        Args:
            code: Python code string to execute
            data: Optional data dictionary to pass to the code
            
        Returns:
            Dictionary containing execution results
        """
        # Safety check
        is_safe, safety_msg = self.check_code_safety(code)
        if not is_safe:
            return {
                'success': False,
                'error': f"Code safety check failed: {safety_msg}",
                'output': None,
                'plots': None
            }
        
        # Install missing packages
        try:
            installed = self.install_missing_packages(code)
            if installed:
                print(f"Installed packages: {', '.join(installed)}")
        except Exception as e:
            print(f"Package installation warning: {e}")
        
        # Capture stdout and stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        # Prepare execution environment with proper builtins
        exec_globals = {
            '__builtins__': {
                # Essential built-ins
                'print': print,
                'len': len,
                'range': range,
                'enumerate': enumerate,
                'zip': zip,
                'map': map,
                'filter': filter,
                'sum': sum,
                'min': min,
                'max': max,
                'abs': abs,
                'round': round,
                'sorted': sorted,
                'reversed': reversed,
                'any': any,
                'all': all,
                
                # Data types
                'int': int,
                'float': float,
                'str': str,
                'bool': bool,
                'list': list,
                'dict': dict,
                'set': set,
                'tuple': tuple,
                'frozenset': frozenset,
                'complex': complex,
                'bytes': bytes,
                'bytearray': bytearray,
                
                # Type checking
                'type': type,
                'isinstance': isinstance,
                'issubclass': issubclass,
                'hasattr': hasattr,
                'getattr': getattr,
                'setattr': setattr,
                'delattr': delattr,
                'dir': dir,
                'id': id,
                
                # Import functionality
                '__import__': __import__,
                
                # Other essentials
                'slice': slice,
                'property': property,
                'staticmethod': staticmethod,
                'classmethod': classmethod,
                'super': super,
                'iter': iter,
                'next': next,
                'callable': callable,
                'divmod': divmod,
                'pow': pow,
                'repr': repr,
                'ascii': ascii,
                'ord': ord,
                'chr': chr,
                'bin': bin,
                'oct': oct,
                'hex': hex,
                'hash': hash,
                'object': object,
                'Exception': Exception,
                'ValueError': ValueError,
                'TypeError': TypeError,
                'AttributeError': AttributeError,
                'IndexError': IndexError,
                'KeyError': KeyError,
                'ImportError': ImportError,
                'ModuleNotFoundError': ModuleNotFoundError,
                'RuntimeError': RuntimeError,
                'StopIteration': StopIteration,
                'NotImplementedError': NotImplementedError,
                'ZeroDivisionError': ZeroDivisionError,
                'OverflowError': OverflowError,
                'MemoryError': MemoryError,
                'SystemError': SystemError,
                'Warning': Warning,
                'UserWarning': UserWarning,
                'DeprecationWarning': DeprecationWarning,
                'FutureWarning': FutureWarning,
                'RuntimeWarning': RuntimeWarning,
                'SyntaxWarning': SyntaxWarning,
            }
        }
        
        # Add data to execution environment if provided
        if data:
            exec_globals.update(data)
        
        exec_locals = {}
        
        try:
            # Redirect stdout/stderr to capture output
            with contextlib.redirect_stdout(stdout_capture), \
                 contextlib.redirect_stderr(stderr_capture):
                
                # Execute the code
                exec(code, exec_globals, exec_locals)
            
            # Capture any variables that might contain results
            results = {}
            for var_name, var_value in exec_locals.items():
                if not var_name.startswith('_'):
                    try:
                        # Try to serialize the value
                        json.dumps(var_value, default=str)
                        results[var_name] = var_value
                    except:
                        # If not serializable, convert to string
                        results[var_name] = str(var_value)
            
            # Get printed output
            output = stdout_capture.getvalue()
            
            # Check for matplotlib plots
            plots = self._extract_plots()
            
            return {
                'success': True,
                'output': output,
                'variables': results,
                'plots': plots,
                'error': None
            }
            
        except Exception as e:
            error_output = stderr_capture.getvalue()
            return {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc(),
                'stderr': error_output,
                'output': stdout_capture.getvalue(),
                'variables': None,
                'plots': None
            }
    
    def _extract_plots(self) -> List[str]:
        """Extract matplotlib plots if any were created"""
        plots = []
        try:
            import matplotlib.pyplot as plt
            import base64
            import io
            
            # Get all figure numbers
            fig_nums = plt.get_fignums()
            
            for fig_num in fig_nums:
                fig = plt.figure(fig_num)
                
                # Save plot to bytes
                img_buffer = io.BytesIO()
                fig.savefig(img_buffer, format='png', bbox_inches='tight', dpi=300)
                img_buffer.seek(0)
                
                # Convert to base64
                img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
                plots.append(img_base64)
                
                plt.close(fig)
                
        except ImportError:
            pass
        except Exception as e:
            print(f"Plot extraction error: {e}")
            
        return plots


# Example usage function
def execute_ai_generated_code(openai_code: str, input_data: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Main function to execute AI-generated Python code
    
    Args:
        openai_code: The Python code generated by OpenAI
        input_data: Optional data to pass to the code (e.g., datasets)
        
    Returns:
        Execution results dictionary
    """
    executor = PythonCodeExecutor()
    return executor.execute_code(openai_code, input_data)


# Example usage
if __name__ == "__main__":
    # Example AI-generated code for linear regression
    sample_ai_code = """
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import matplotlib.pyplot as plt

# Generate sample data
np.random.seed(42)
X = np.random.randn(100, 1)
y = 2 * X.flatten() + 1 + np.random.randn(100) * 0.1

# Create DataFrame
df = pd.DataFrame({'X': X.flatten(), 'y': y})

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Create and train model
model = LinearRegression()
model.fit(X_train, y_train)

# Make predictions
y_pred = model.predict(X_test)

# Calculate metrics
mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"Mean Squared Error: {mse:.4f}")
print(f"R² Score: {r2:.4f}")
print(f"Model Coefficients: {model.coef_[0]:.4f}")
print(f"Model Intercept: {model.intercept_:.4f}")

# Create plot
plt.figure(figsize=(10, 6))
plt.scatter(X_test, y_test, alpha=0.5, label='Actual')
plt.scatter(X_test, y_pred, alpha=0.5, label='Predicted')
plt.xlabel('X')
plt.ylabel('y')
plt.title('Linear Regression Results')
plt.legend()
plt.grid(True, alpha=0.3)

# Store results
results = {
    'mse': mse,
    'r2_score': r2,
    'coefficients': model.coef_.tolist(),
    'intercept': model.intercept_,
    'predictions': y_pred.tolist()
}
"""
    
    # Execute the code
    result = execute_ai_generated_code(sample_ai_code)
    
    if result['success']:
        print("Code executed successfully!")
        print(f"Output: {result['output']}")
        print(f"Variables: {result['variables']}")
        if result['plots']:
            print(f"Generated {len(result['plots'])} plots")
    else:
        print("Code execution failed!")
        print(f"Error: {result['error']}")