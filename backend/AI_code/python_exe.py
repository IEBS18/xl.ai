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
        # Modules we’ll always make available under these aliases
        import pandas as _pd
        from sklearn.impute import SimpleImputer as _SI
        from sklearn.preprocessing import MinMaxScaler as _MMS
        import numpy as _np

        self._injected = {
            "pd": _pd,
            "SimpleImputer": _SI,
            "MinMaxScaler": _MMS,
            "np": _np,
        }

        self.allowed_packages = {
            'numpy', 'pandas', 'scikit-learn', 'matplotlib', 
            'seaborn', 'plotly', 'scipy', 'statsmodels', 'xgboost',
            'lightgbm', 'catboost', 'tensorflow', 'torch', 'keras'
        }
        self.dangerous_patterns = [
            r'\b(os\.|subprocess\.|sys\.)',
            r'\b(eval|exec|compile|__import__)\s*\(',
            r'\bopen\s*\(',
            r'\bfile\s*\(',
            r'globals\s*\(\)|locals\s*\(\)',
            r'__.*__',
            r'import\s+os|import\s+subprocess|import\s+sys'
        ]

    def check_code_safety(self, code: str) -> tuple[bool, str]:
        for pat in self.dangerous_patterns:
            if re.search(pat, code, re.IGNORECASE):
                return False, f"Blocked by safety pattern: {pat}"
        return True, "OK"

    def install_missing_packages(self, code: str) -> List[str]:
        import_patterns = [r'import\s+(\w+)', r'from\s+(\w+)\s+import']
        required = set()
        for pat in import_patterns:
            for m in re.findall(pat, code):
                if m in self.allowed_packages:
                    required.add(m)
        installed = []
        for pkg in required:
            try:
                importlib.metadata.distribution(pkg)
            except importlib.metadata.PackageNotFoundError:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', pkg])
                installed.append(pkg)
        return installed

    def execute_code(self, code: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        safe, msg = self.check_code_safety(code)
        if not safe:
            return {"success": False, "error": msg}

        # Optionally install imports
        try:
            self.install_missing_packages(code)
        except:
            pass

        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()

        # Build a fresh globals dict each run
        exec_globals = {
            "__builtins__": {
                **{name: __builtins__[name] for name in (
                    'print','len','range','sum','min','max','abs','round',
                    'int','float','str','bool','list','dict','tuple','set',
                    'type','isinstance','enumerate','zip','map','filter',
                    'iter','next','Exception','ValueError'
                )},
                "__import__": __import__,
            }
        }
        # Inject our data-science modules
        exec_globals.update(self._injected)

        # Inject any user data (df, etc.)
        if data:
            exec_globals.update(data)

        exec_locals = {}
        try:
            with contextlib.redirect_stdout(stdout_buf), contextlib.redirect_stderr(stderr_buf):
                exec(code, exec_globals, exec_locals)
            # Capture variables
            results = {}
            for k,v in exec_locals.items():
                if not k.startswith("_"):
                    try:
                        json.dumps(v, default=str)
                        results[k] = v
                    except:
                        results[k] = str(v)
            return {
                "success": True,
                "output": stdout_buf.getvalue(),
                "variables": results,
                "plots": [],  # or your plot extraction logic
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "output": stdout_buf.getvalue(),
                "stderr": stderr_buf.getvalue(),
                "traceback": traceback.format_exc(),
                "variables": None,
                "plots": None,
                "error": str(e)
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