import os
import pandas as pd
import numpy as np
import json
from collections import Counter
import re
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()


def detect_header_row_pattern(file_path, sheet_name=0, max_rows_to_check=20):
    """
    Detect header row based on data patterns
    """
    # Read first N rows without treating any as header
    df = pd.read_excel(file_path, sheet_name=sheet_name, header=None, nrows=max_rows_to_check)
    
    scores = []
    
    for row_idx in range(len(df)):
        score = 0
        row_data = df.iloc[row_idx].astype(str)
        
        # Check for typical header characteristics
        non_null_count = row_data.notna().sum()
        if non_null_count == 0:
            scores.append(0)
            continue
            
        # 1. Text vs numeric ratio (headers usually have more text)
        text_count = sum(1 for val in row_data if val and not str(val).replace('.', '').replace('-', '').isdigit())
        text_ratio = text_count / non_null_count if non_null_count > 0 else 0
        score += text_ratio * 30
        
        # 2. Unique values (headers should have mostly unique values)
        unique_ratio = len(set(row_data.dropna())) / non_null_count if non_null_count > 0 else 0
        score += unique_ratio * 25
        
        # 3. Check for header-like words
        header_keywords = ['name', 'id', 'date', 'amount', 'total', 'code', 'type', 'status', 
                          'email', 'phone', 'address', 'description', 'category', 'price']
        keyword_matches = sum(1 for val in row_data if any(keyword in str(val).lower() for keyword in header_keywords))
        score += (keyword_matches / non_null_count) * 20 if non_null_count > 0 else 0
        
        # 4. Length consistency (headers often have similar lengths)
        lengths = [len(str(val)) for val in row_data if val and str(val) != 'nan']
        if lengths:
            length_std = np.std(lengths)
            score += max(0, 15 - length_std)  # Lower std deviation = higher score
        
        # 5. No purely numeric row (headers shouldn't be all numbers)
        all_numeric = all(str(val).replace('.', '').replace('-', '').isdigit() for val in row_data if val and str(val) != 'nan')
        if not all_numeric and non_null_count > 0:
            score += 10
            
        scores.append(score)
    
    # Find the row with highest score
    best_row = np.argmax(scores) if scores else 0
    return best_row, scores[best_row] if scores else 0

def detect_header_with_azure_openai_env(file_path, sheet_name=0, max_rows=15):
    """
    Use Azure OpenAI with environment variables
    """
    try:
        client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_BASE_URL"),
            api_key=os.getenv("AZURE_API"),
            api_version=os.getenv("AZURE_API_VERSION")
        )
        
        deployment_name = os.getenv("AZURE_OPENAI_MODEL")
        
        # Read first few rows
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=None, nrows=max_rows)
        
        # Convert to string representation for OpenAI
        rows_text = ""
        for idx, row in df.iterrows():
            row_values = [str(val) if pd.notna(val) else "EMPTY" for val in row]
            rows_text += f"Row {idx}: {' | '.join(row_values)}\n"
        
        prompt = f"""
        Analyze the following Excel data rows and identify which row contains the column headers.
        
        Data:
        {rows_text}
        
        Look for:
        - Row with descriptive column names
        - Row that looks like field labels rather than data values
        - Row with text that describes what each column contains
        
        Respond with only a JSON object in this format:
        {{
            "header_row": <row_number>,
            "confidence": <0.0-1.0>,
            "reasoning": "<brief explanation>"
        }}
        """
        
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=200
        )
        
        result = json.loads(response.choices[0].message.content)
        return result["header_row"], result["confidence"], result["reasoning"]
        
    except Exception as e:
        print(f"Azure OpenAI API error: {e}")
        return None, 0, "API call failed"

def validate_header_detection(df, suspected_header_row):
    """
    Validate if the detected header row makes sense
    """
    if suspected_header_row >= len(df):
        return False, "Row index out of bounds"
    
    header_values = df.iloc[suspected_header_row].astype(str)
    
    # Check for reasonable header characteristics
    non_empty = header_values[header_values != 'nan'].count()
    if non_empty < len(df.columns) * 0.3:  # At least 30% should be filled
        return False, "Too many empty header cells"
    
    # Check if subsequent rows look like data
    if suspected_header_row + 1 < len(df):
        next_row = df.iloc[suspected_header_row + 1].astype(str)
        # Simple heuristic: next row should have some data
        next_non_empty = next_row[next_row != 'nan'].count()
        if next_non_empty == 0:
            return False, "Next row appears to be empty"
    
    return True, "Header validation passed"

def smart_header_detection(file_path, sheet_name=0, use_azure_ai=True):
    """
    Combine pattern-based and Azure AI-based detection for best results
    """
    print(f"Analyzing file: {file_path}")
    print(f"Sheet: {sheet_name}")
    
    # Method 1: Pattern-based detection
    print("\n🔍 Running pattern-based detection...")
    pattern_row, pattern_score = detect_header_row_pattern(file_path, sheet_name)
    
    result = {
        'pattern_detection': {
            'row': int(pattern_row),
            'score': float(pattern_score)
        }
    }
    
    print(f"   Pattern detection suggests row {pattern_row} (score: {pattern_score:.2f})")
    
    # Method 2: Azure OpenAI detection
    if use_azure_ai and all([
        os.getenv("AZURE_OPENAI_ENDPOINT"),
        os.getenv("AZURE_OPENAI_API_KEY")
    ]):
        print("\n🤖 Running Azure OpenAI detection...")
        ai_row, ai_confidence, ai_reasoning = detect_header_with_azure_openai_env(file_path, sheet_name)
        
        if ai_row is not None:
            result['ai_detection'] = {
                'row': int(ai_row),
                'confidence': float(ai_confidence),
                'reasoning': ai_reasoning
            }
            print(f"   AI detection suggests row {ai_row} (confidence: {ai_confidence:.2f})")
            print(f"   Reasoning: {ai_reasoning}")
            
            # Combine results (weighted approach)
            if ai_confidence > 0.8:
                final_row = ai_row
                method_used = "Azure AI (high confidence)"
            elif ai_confidence > 0.6 and abs(pattern_row - ai_row) <= 1:
                final_row = ai_row
                method_used = "Combined (AI + pattern agreement)"
            elif pattern_score > 60:
                final_row = pattern_row
                method_used = "Pattern-based (high score)"
            else:
                final_row = ai_row if ai_confidence > 0.5 else pattern_row
                method_used = "Best available option"
        else:
            final_row = pattern_row
            method_used = "Pattern-based (AI failed)"
            print("   AI detection failed, using pattern-based result")
    else:
        final_row = pattern_row
        method_used = "Pattern-based only"
        if use_azure_ai:
            print("\n⚠️  Azure OpenAI credentials not found, using pattern-based detection only")
        else:
            print("\n📊 Using pattern-based detection only")
    
    result['final_header_row'] = int(final_row)
    result['method_used'] = method_used
    
    # Validate the result
    temp_df = pd.read_excel(file_path, sheet_name=sheet_name, header=None, nrows=20)
    is_valid, validation_msg = validate_header_detection(temp_df, final_row)
    result['validation'] = {
        'is_valid': is_valid,
        'message': validation_msg
    }
    
    print(f"\n✅ Final decision: Row {final_row} ({method_used})")
    print(f"   Validation: {validation_msg}")
    
    return result

def load_excel_with_smart_header(file_path, sheet_name=0, use_azure_ai=True):
    """
    Load Excel file with automatically detected header row
    """
    detection_result = smart_header_detection(file_path, sheet_name, use_azure_ai)
    header_row = detection_result['final_header_row']
    
    # Load the Excel file with the detected header row
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=header_row)
        print(f"\n📈 Successfully loaded DataFrame with shape: {df.shape}")
        print(f"   Columns: {list(df.columns)}")
        
        return df, detection_result
    except Exception as e:
        print(f"\n❌ Error loading Excel file: {e}")
        return None, detection_result

def setup_azure_credentials():
    """
    Interactive setup for Azure OpenAI credentials
    """
    print("🔧 Azure OpenAI Setup")
    print("=" * 50)
    
    if not os.getenv("AZURE_OPENAI_ENDPOINT"):
        endpoint = input("Enter your Azure OpenAI endpoint: ")
        os.environ["AZURE_OPENAI_ENDPOINT"] = endpoint
    
    if not os.getenv("AZURE_OPENAI_API_KEY"):
        api_key = input("Enter your Azure OpenAI API key: ")
        os.environ["AZURE_OPENAI_API_KEY"] = api_key
    
    if not os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"):
        deployment = input("Enter your deployment name (default: gpt-35-turbo): ") or "gpt-35-turbo"
        os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"] = deployment
    
    print("✅ Credentials configured!")

def main():
    """
    Main function to demonstrate Excel header detection
    """
    print("🎯 Excel Header Detection Tool")
    print("=" * 50)
    
    # Get file path from user
    file_path = input("Enter path to your Excel file: ").strip().strip('"')
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return
    
    # Get sheet name/index
    sheet_input = input("Enter sheet name or index (default: 0): ").strip()
    sheet_name = int(sheet_input) if sheet_input.isdigit() else (sheet_input if sheet_input else 0)
    
    # Ask about Azure OpenAI usage
    use_ai = input("Use Azure OpenAI for enhanced detection? (y/n, default: y): ").strip().lower()
    use_azure_ai = use_ai != 'n'
    
    if use_azure_ai and not all([os.getenv("AZURE_BASE_URL"), os.getenv("AZURE_API")]):
        setup_choice = input("Azure OpenAI credentials not found. Set them up now? (y/n): ").strip().lower()
        if setup_choice == 'y':
            setup_azure_credentials()
        else:
            use_azure_ai = False
    
    # Perform detection and load data
    try:
        df, detection_info = load_excel_with_smart_header(file_path, sheet_name, use_azure_ai)
        
        if df is not None:
            print("\n" + "=" * 50)
            print("📊 DETECTION SUMMARY")
            print("=" * 50)
            print(json.dumps(detection_info, indent=2))
            
            print("\n" + "=" * 50)
            print("📋 DATA PREVIEW")
            print("=" * 50)
            print(df.head())
            
            # Ask if user wants to save the result
            save_choice = input("\nSave the processed data to a new file? (y/n): ").strip().lower()
            if save_choice == 'y':
                output_path = input("Enter output file path (e.g., output.xlsx): ").strip()
                try:
                    df.to_excel(output_path, index=False)
                    print(f"✅ Data saved to: {output_path}")
                except Exception as e:
                    print(f"❌ Error saving file: {e}")
        
    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    main()