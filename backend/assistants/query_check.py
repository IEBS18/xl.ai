from openai import AzureOpenAI
from enum import Enum
from typing import Optional, Dict, Any
import json
import re
import os
from dotenv import load_dotenv

load_dotenv()

class QueryCategory(Enum):
    DATA_ANALYSIS = "data analysis"
    SIMPLE_CALCULATION = "simple calculation"
    CONVERSATIONAL = "conversational"
    REPORT = "report"
    DATA_ANALYSIS_AND_REPORT = "data analysis and report both"

class OpenAIQueryCategorizer:
    """
    An OpenAI assistant class that categorizes user queries into predefined categories.
    """
    
    def __init__(self):
        """
        Initialize the query categorizer using Azure OpenAI from environment variables.
        
        Required environment variables:
        - AZUREAPI: Azure OpenAI API key
        - AZUREVERSION: Azure OpenAI API version
        - AZUREENDPOINT: Azure OpenAI endpoint
        - AZUREMODEL: Azure OpenAI model name
        """
        self.openai_client = AzureOpenAI(
            api_key=os.getenv('AZUREAPI'),
            api_version=os.getenv('AZUREVERSION'),
            azure_endpoint=os.getenv('AZUREENDPOINT'),
            # azure_model=os.getenv('AZURE_OPENAI_MODEL')
        )
        self.MODEL =os.getenv('AZUREMODEL') 
        
        # Define category descriptions for better classification
        self.category_descriptions = {
            QueryCategory.DATA_ANALYSIS: {
                "description": "Queries that involve analyzing, processing, or exploring data. Includes statistical analysis, data visualization, pattern recognition, data cleaning, or extracting insights from datasets.",
                "keywords": ["analyze", "data", "statistics", "visualization", "trends", "patterns", "dataset", "csv", "excel", "database", "insights", "correlation", "distribution", "forecast", "predict", "model"]
            },
            QueryCategory.SIMPLE_CALCULATION: {
                "description": "Basic mathematical operations, conversions, or straightforward numerical computations that don't require complex data analysis.",
                "keywords": ["calculate", "compute", "math", "add", "subtract", "multiply", "divide", "percentage", "convert", "formula", "equation", "sum", "average", "total", "count", "highest", "lowest", "maximum", "minimum"]
            },
            QueryCategory.CONVERSATIONAL: {
                "description": "General conversation, questions seeking information, explanations, discussions, or casual interactions that don't involve calculations or data analysis.",
                "keywords": ["what", "how", "why", "explain", "tell me", "discuss", "opinion", "advice", "help", "information", "define", "describe", "hi", "hello", "thanks", "bye"]
            },
            QueryCategory.REPORT: {
                "description": "Requests to create, generate, or format reports, summaries, documentation, or structured presentations of information without requiring new data analysis.",
                "keywords": ["report", "summary", "document", "presentation", "generate report", "create report", "write up", "executive summary", "findings", "compile", "format"]
            },
            QueryCategory.DATA_ANALYSIS_AND_REPORT: {
                "description": "Queries that combine both data analysis and report generation - analyzing data AND presenting findings in a structured report format. This requires both analytical work and comprehensive reporting.",
                "keywords": ["analyze and report", "data report", "analysis report", "findings report", "data summary", "analytical report", "comprehensive analysis", "detailed report", "business analysis", "strategic analysis"]
            }
        }
    
    def _create_classification_prompt(self, user_query: str) -> str:
        """
        Create a structured prompt for query classification.
        
        Args:
            user_query (str): The user's input query
            
        Returns:
            str: Formatted prompt for classification
        """
        categories_info = ""
        for i, (category, info) in enumerate(self.category_descriptions.items(), 1):
            categories_info += f"{i}. {category.value}: {info['description']}\n"
        
        prompt = f"""
You are a query classification assistant. Analyze the following user query and classify it into ONE of these categories:

{categories_info}

Classification Guidelines:
- If the query involves both analyzing data AND creating a report, choose "data analysis and report both"
- If the query only involves data analysis without report generation, choose "data analysis"
- If the query only involves creating reports without data analysis, choose "report"
- Simple math operations without data analysis should be "simple calculation"
- General questions, conversations, or information requests should be "conversational"

CLASSIFICATION RULES WITH CLEAR DISTINCTIONS:

🔢 **"simple calculation"** - Use when:
   - Direct mathematical operations: calculate, compute, find
   - Basic aggregations: total, sum, average, mean, count, maximum, minimum, highest, lowest
   - Single numerical answers: "What is...", "How many...", "Calculate the..."
   - NO complex analysis, just straightforward math
   - Examples: "Calculate average price", "What's the total revenue?", "Count customers"

📊 **"data analysis"** - Use when:
   - Understanding patterns, trends, relationships, factors
   - Exploratory analysis: analyze, explore, investigate, understand, examine
   - Advanced analytics: forecasting, modeling, statistical analysis, correlations
   - Requests for visualizations AS PART OF ANALYSIS (charts, graphs, plots)
   - Insights and interpretations: why, how, factors affecting, drivers, impact
   - Examples: "Analyze sales trends", "Forecast revenue", "Show sales trends with charts", "Create visualizations to understand patterns"

📋 **"report"** - Use when:
   - ONLY formatting/presenting existing analysis into a business document
   - Explicit requests for: "report", "executive summary", "business document", "presentation"
   - Creating formatted business deliverables from completed analysis
   - No new analysis required, just formatting existing insights

🔄 **"data analysis and report both"** - Use when:
   - Query EXPLICITLY asks for BOTH comprehensive analysis AND a formatted business report/document
   - Must contain BOTH analytical work AND explicit report/document creation requests
   - Examples: "Analyze sales data AND generate a comprehensive business report", "Perform analysis AND create executive summary document"
   - NOT just analysis with visualizations - must explicitly request separate report document

💬 **"conversational"** - Use when:
   - Greetings, general questions, capability inquiries
   - No calculations or analysis needed

CRITICAL DISTINCTION - Simple Calculation vs Data Analysis:
❌ WRONG: "Calculate average price" → data analysis
✅ CORRECT: "Calculate average price" → simple calculation

❌ WRONG: "Analyze pricing factors" → simple calculation  
✅ CORRECT: "Analyze pricing factors" → data analysis

KEY RULE: If the query asks for a specific NUMBER or VALUE through basic math → simple calculation
If the query asks to UNDERSTAND, EXPLORE, or find PATTERNS → data analysis

User Query: "{user_query}"

Respond with ONLY the category name (exactly as listed above), followed by a brief explanation in this format:
Category: [category name]
Reason: [brief explanation]
"""
        return prompt
    
    def categorize_query(self, user_query: str) -> Dict[str, Any]:
        """
        Categorize a user query into one of the predefined categories.
        
        Args:
            user_query (str): The user's input query
            
        Returns:
            Dict containing the category, confidence, and reasoning
        """
        try:
            # Create the classification prompt
            prompt = self._create_classification_prompt(user_query)
            
            # Call OpenAI API
            response = self.openai_client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": "You are a precise query classification assistant. Always follow the exact output format requested."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.1  # Low temperature for consistent classification
            )
            
            # Parse the response
            response_text = response.choices[0].message.content.strip()
            print(response_text)
            return self._parse_classification_response(response_text, user_query)
            
        except Exception as e:
            return {
                "category": None,
                "category_enum": None,
                "confidence": 0.0,
                "reasoning": f"Error occurred during classification: {str(e)}",
                "original_query": user_query,
                "success": False
            }
    
    def _parse_classification_response(self, response_text: str, original_query: str) -> Dict[str, Any]:
        """
        Parse the OpenAI response to extract category and reasoning.
        
        Args:
            response_text (str): Response from OpenAI
            original_query (str): Original user query
            
        Returns:
            Dict containing parsed classification results
        """
        try:
            # Extract category and reason using regex
            category_match = re.search(r'Category:\s*(.+)', response_text, re.IGNORECASE)
            reason_match = re.search(r'Reason:\s*(.+)', response_text, re.IGNORECASE)
            
            if category_match:
                category_text = category_match.group(1).strip().lower()
                
                # Find matching category enum
                category_enum = None
                for cat in QueryCategory:
                    if cat.value.lower() == category_text:
                        category_enum = cat
                        break
                
                reasoning = reason_match.group(1).strip() if reason_match else "No reasoning provided"
                
                return {
                    "category": category_text,
                    "category_enum": category_enum,
                    "confidence": 0.9 if category_enum else 0.3,
                    "reasoning": reasoning,
                    "original_query": original_query,
                    "success": True
                }
            else:
                return {
                    "category": None,
                    "category_enum": None,
                    "confidence": 0.0,
                    "reasoning": "Could not parse classification response",
                    "original_query": original_query,
                    "success": False,
                    "raw_response": response_text
                }
                
        except Exception as e:
            return {
                "category": None,
                "category_enum": None,
                "confidence": 0.0,
                "reasoning": f"Error parsing response: {str(e)}",
                "original_query": original_query,
                "success": False,
                "raw_response": response_text
            }
    
    def batch_categorize(self, queries: list) -> list:
        """
        Categorize multiple queries at once.
        
        Args:
            queries (list): List of user queries
            
        Returns:
            list: List of categorization results
        """
        results = []
        for query in queries:
            result = self.categorize_query(query)
            results.append(result)
        return results
    
    def get_category_statistics(self, queries: list) -> Dict[str, Any]:
        """
        Get statistics about query categories from a batch of queries.
        
        Args:
            queries (list): List of user queries
            
        Returns:
            Dict containing category statistics
        """
        results = self.batch_categorize(queries)
        
        category_counts = {}
        successful_classifications = 0
        
        for result in results:
            if result['success'] and result['category']:
                category = result['category']
                category_counts[category] = category_counts.get(category, 0) + 1
                successful_classifications += 1
        
        total_queries = len(queries)
        
        return {
            "total_queries": total_queries,
            "successful_classifications": successful_classifications,
            "success_rate": successful_classifications / total_queries if total_queries > 0 else 0,
            "category_distribution": category_counts,
            "category_percentages": {
                cat: (count / successful_classifications * 100) 
                for cat, count in category_counts.items()
            } if successful_classifications > 0 else {}
        }

def main():
    """
    Main interactive function for query categorization.
    """
    print("=" * 60)
    print("🤖 OpenAI Query Categorizer")
    print("=" * 60)
    print("\nAvailable Categories:")
    print("1. Data Analysis")
    print("2. Simple Calculation") 
    print("3. Conversational")
    print("4. Report")
    print("5. Data Analysis and Report Both")
    print("\n" + "-" * 60)
    
    try:
        # Initialize the categorizer
        categorizer = OpenAIQueryCategorizer()
        print("✅ Azure OpenAI client initialized successfully!")
        
        while True:
            print("\n" + "=" * 60)
            print("Options:")
            print("1. Categorize a single query")
            print("2. Test with example queries")
            print("3. Batch categorize multiple queries")
            print("4. Exit")
            print("-" * 60)
            
            choice = input("Enter your choice (1-4): ").strip()
            
            if choice == '1':
                single_query_mode(categorizer)
            elif choice == '2':
                example_queries_mode(categorizer)
            elif choice == '3':
                batch_queries_mode(categorizer)
            elif choice == '4':
                print("\n👋 Thank you for using the Query Categorizer!")
                break
            else:
                print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")
                
    except Exception as e:
        print(f"❌ Error initializing categorizer: {str(e)}")
        print("Please check your Azure OpenAI configuration in .env file")

def single_query_mode(categorizer):
    """Handle single query categorization."""
    print("\n" + "=" * 60)
    print("📝 Single Query Mode")
    print("=" * 60)
    
    while True:
        query = input("\nEnter your query (or 'back' to return to main menu): ").strip()
        
        if query.lower() == 'back':
            break
        
        if not query:
            print("❌ Please enter a valid query.")
            continue
            
        print("\n🔄 Categorizing query...")
        result = categorizer.categorize_query(query)
        
        print("\n" + "=" * 50)
        print("📊 CATEGORIZATION RESULT")
        print("=" * 50)
        
        if result['success']:
            print(f"🎯 Category: {result['category'].upper()}")
            print(f"📈 Confidence: {result['confidence']:.1%}")
            print(f"💭 Reasoning: {result['reasoning']}")
            print(f"📝 Original Query: {result['original_query']}")
        else:
            print(f"❌ Categorization failed: {result['reasoning']}")
            if 'raw_response' in result:
                print(f"🔍 Raw response: {result['raw_response']}")

def example_queries_mode(categorizer):
    """Test with predefined example queries."""
    print("\n" + "=" * 60)
    print("🧪 Example Queries Mode")
    print("=" * 60)
    
    example_queries = [
        "What's 15% of 250?",
        "Analyze the sales data in this CSV file and find trends",
        "How are you doing today?",
        "Create a monthly performance report",
        "Analyze customer data and generate a comprehensive report with insights",
        "Analyze the attached In-Market Forecasting dataset and prepare a detailed report",
        "Calculate the compound interest for $10,000 at 5% for 3 years",
        "Parse this dataset and create an executive summary of findings"
    ]
    
    print(f"\n🔄 Testing {len(example_queries)} example queries...")
    results = categorizer.batch_categorize(example_queries)
    
    print("\n" + "=" * 80)
    print("📊 EXAMPLE QUERIES RESULTS")
    print("=" * 80)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Query: {result['original_query']}")
        if result['success']:
            print(f"   ✅ Category: {result['category']}")
            print(f"   📈 Confidence: {result['confidence']:.1%}")
            print(f"   💭 Reasoning: {result['reasoning']}")
        else:
            print(f"   ❌ Failed: {result['reasoning']}")
    
    # Show statistics
    stats = categorizer.get_category_statistics(example_queries)
    print("\n" + "=" * 50)
    print("📈 STATISTICS")
    print("=" * 50)
    print(f"Total Queries: {stats['total_queries']}")
    print(f"Success Rate: {stats['success_rate']:.1%}")
    print("\nCategory Distribution:")
    for category, percentage in stats['category_percentages'].items():
        print(f"  • {category}: {percentage:.1f}%")

def batch_queries_mode(categorizer):
    """Handle batch query categorization."""
    print("\n" + "=" * 60)
    print("📦 Batch Queries Mode")
    print("=" * 60)
    print("Enter multiple queries (one per line). Type 'DONE' when finished.")
    
    queries = []
    while True:
        query = input(f"Query {len(queries) + 1}: ").strip()
        if query.upper() == 'DONE':
            break
        if query:
            queries.append(query)
    
    if not queries:
        print("❌ No queries provided.")
        return
    
    print(f"\n🔄 Processing {len(queries)} queries...")
    results = categorizer.batch_categorize(queries)
    
    print("\n" + "=" * 80)
    print("📊 BATCH CATEGORIZATION RESULTS")
    print("=" * 80)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Query: {result['original_query']}")
        if result['success']:
            print(f"   ✅ Category: {result['category']}")
            print(f"   📈 Confidence: {result['confidence']:.1%}")
            print(f"   💭 Reasoning: {result['reasoning']}")
        else:
            print(f"   ❌ Failed: {result['reasoning']}")
    
    # Show statistics
    stats = categorizer.get_category_statistics(queries)
    print("\n" + "=" * 50)
    print("📈 BATCH STATISTICS")
    print("=" * 50)
    print(f"Total Queries: {stats['total_queries']}")
    print(f"Success Rate: {stats['success_rate']:.1%}")
    print("\nCategory Distribution:")
    for category, percentage in stats['category_percentages'].items():
        print(f"  • {category}: {percentage:.1f}%")

# Example usage and testing
if __name__ == "__main__":
    main()