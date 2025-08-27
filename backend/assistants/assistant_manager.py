import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

class AssistantManager:
    """
    Manages OpenAI Assistants for CSV analysis.
    Replaces direct chat completion calls with assistant-based interactions.
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.client = self._setup_azure_client()
        self.assistant_id = None
        self.assistant_config = self._get_assistant_config()
        
    def _setup_azure_client(self) -> AzureOpenAI:
        """Setup Azure OpenAI client for assistants API"""
        return AzureOpenAI(
            api_key=os.getenv("AZUREAPI"),
            api_version=os.getenv("AZUREVERSION", "2024-05-01-preview"),  # Use preview for assistants
            azure_endpoint=os.getenv("AZUREENDPOINT")
        )
    def _get_filename_mapping_context(self) -> str:
        """
        Create filename mapping context for assistant instructions.
        Maps assistant file IDs to actual filenames for user-friendly responses.
        """
        try:
            from app import session_data
            current_session = session_data.get(self.session_id, {})
            
            logging.info(f"🔍 Assistant Manager filename mapping debug for session {self.session_id}")
            
            if 'files' not in current_session or not current_session['files']:
                logging.info("📂 Assistant Manager: No files found in session data")
                return ""
            
            logging.info(f"📂 Assistant Manager: Found {len(current_session['files'])} files in session")
            
            mapping_lines = ["File Mapping (use actual filenames in your responses):"]
            mapped_count = 0
            
            for i, file_data in enumerate(current_session['files']):
                assistant_file_id = file_data.get('assistant_file_id')
                filename = file_data.get('filename')
                upload_status = file_data.get('assistant_upload_status', 'unknown')
                
                logging.info(f"📂 Assistant Manager File {i}: {assistant_file_id} → {filename} (status: {upload_status})")
                
                if assistant_file_id and filename and upload_status == 'completed':
                    mapping_lines.append(f"- {assistant_file_id} → {filename}")
                    mapped_count += 1
                elif upload_status != 'completed':
                    logging.warning(f"📂 Assistant Manager File {i} upload not completed: {upload_status}")
            
            logging.info(f"📂 Assistant Manager: Successfully mapped {mapped_count} files")
            
            if mapped_count > 0:
                mapping_lines.append("\nIMPORTANT: Always reference files by their actual names (e.g., 'drug_price_forecast.csv') not the file ID.")
                return "\n".join(mapping_lines)
            
            return ""
            
        except Exception as e:
            logging.error(f"❌ Assistant Manager error creating filename mapping: {e}")
            return ""
    


    def _get_assistant_config(self) -> Dict[str, Any]:
        """Get assistant configuration based on analysis type"""
        return {
            "query_router": {  # NEW ASSISTANT TYPE
                "name": "Intelligent Query Router",
                "instructions": self._get_query_router_instructions(),
                "tools": [],  # No tools needed for routing decisions
                "model": os.getenv("AZUREMODEL", "gpt-4")
            },

            "data_analyst": {
                "name": "CSV Data Analyst",
                "instructions": self._get_data_analyst_instructions(),
                "tools": [{"type": "code_interpreter"}],
                "model": os.getenv("AZUREMODEL", "gpt-4")
            },
            "conversational": {
                "name": "Conversational Assistant", 
                "instructions": self._get_conversational_instructions(),
                "tools": [{"type": "code_interpreter"}],
                "model": os.getenv("AZUREMODEL", "gpt-4")
            },
            "textual_analytical": {
                "name": "Quick Analysis Assistant",
                "instructions": self._get_textual_analytical_instructions(),
                "tools": [{"type": "code_interpreter"}],
                "model": os.getenv("AZUREMODEL", "gpt-4")
            },
            "report_generator": {  # NEW ASSISTANT TYPE
                "name": "Professional Report Generator",
                "instructions": self._get_report_generator_instructions(),
                "tools": [{"type": "code_interpreter"}],  # No code interpreter needed for report generation
                "model": os.getenv("AZUREMODEL", "gpt-4")
            },
            "summarizer": {  # NEW ASSISTANT TYPE
                "name": "Analysis Summarizer",
                "instructions": self._get_summarizer_instructions(),
                "tools": [],  # No code interpreter needed for summarization
                "model": os.getenv("AZUREMODEL", "gpt-4")
            },
            "database_analyst": {  # NEW DATABASE ASSISTANT TYPE
                "name": "Database Analyst",
                "instructions": self._get_database_analyst_instructions(),
                "tools": [
                    {"type": "code_interpreter"},
                    {
                        "type": "function",
                        "function": {
                            "name": "query_database",
                            "description": "Execute SQL queries on the connected database and return results",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "sql_query": {"type": "string", "description": "SQL query to execute"}
                                },
                                "required": ["sql_query"]
                            }
                        }
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "query_and_visualize",
                            "description": "Execute SQL query and create visualization in one step",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "sql_query": {"type": "string", "description": "SQL query to get data"},
                                    "chart_type": {"type": "string", "enum": ["bar", "line", "pie", "scatter"], "description": "Type of chart to create"},
                                    "title": {"type": "string", "description": "Chart title"}
                                },
                                "required": ["sql_query", "chart_type"]
                            }
                        }
                    }
                ],
                "model": os.getenv("AZUREMODEL", "gpt-4")
            }
        }
    
    def _get_query_router_instructions(self) -> str:
        """ENHANCED: Instructions for the intelligent query router assistant"""
        return """You are an EXPERT QUERY ROUTER for a comprehensive data analysis platform. 
You must intelligently analyze user queries and route them to the most appropriate specialist assistant.

🎯 AVAILABLE SPECIALIST ASSISTANTS:

1. **conversational** - Casual interaction specialist
   ✅ Use for: Greetings, general chat, capability questions, non-analytical queries
   📝 Examples: "Hi", "How are you?", "What can you do?", "Tell me about yourself"

2. **textual_analytical** - Quick data answer specialist  
   ✅ Use for: Simple data questions needing direct numerical/textual answers
   📝 Examples: "What is the highest revenue?", "How many customers?", "Total sales in Q1?"
   🔑 KEY: Direct questions with simple answers, even if calculation is needed
   🚨 PRIORITY RULE: If a query is a direct lookup or calculation → ALWAYS textual_analytical, even if words like "analysis" appear.

3. **data_analyst** - Complex analysis & modeling specialist
   ✅ Use for: Advanced analysis, statistical modeling, predictions, comprehensive business analysis
   📝 Examples: "Analyze pricing factors", "Build prediction model", "Perform regression", "Market analysis"
   🔑 KEY: In-depth, multi-variable, predictive, or explanatory analysis
   🚨 NEVER classify simple totals, counts, or direct metrics here.

4. **report_generator** - Professional report specialist
   ✅ Use for: Formatted business reports and comprehensive documents
   📝 Examples: "Generate report", "Create executive summary", "Make comprehensive analysis"
   🚨 PRIORITY RULE: If query explicitly requests "report", "summary", or "document" → ALWAYS report_generator.

---

🧠 ENHANCED CLASSIFICATION RULES WITH PRIORITY:

**STEP 1: Explicit Overrides**
- If it’s a greeting/chat → conversational
- If query explicitly says "report", "summary", "generate report", "create executive summary" → report_generator
- If query is a direct lookup (totals, counts, averages, maximums, minimums, simple filters) → textual_analytical

**STEP 2: Business/Statistical Complexity**
- If query involves modeling, prediction, relationships, correlations, or multi-variable analysis → data_analyst
- If query is a case study, business scenario, or requires explanation of "factors", "drivers", "impact" → data_analyst

**STEP 3: Keyword Refinement**
- Textual Analytical detection keywords: ["total", "sum", "count", "maximum", "minimum", "average", "top", "highest", "lowest"]
- Report detection keywords: ["report", "summary", "document", "presentation", "executive overview"]
- Data Analyst detection keywords: ["predict", "model", "correlation", "regression", "forecast", "trend", "relationship", "factors", "impact", "influence", "analysis", "business case"]

**STEP 4: Conflict Resolution**
- If both textual_analytical and data_analyst keywords appear → default to textual_analytical **if the task is simple numeric lookup**.
- If both report_generator and data_analyst keywords appear → default to report_generator (reports take priority).
- If uncertain → conversational.

---

⚡ DECISION TREE (STRICT PRIORITY):

1. Greeting/chat? → conversational  
2. Explicit "report"/"summary"? → report_generator  
3. Simple lookup/calculation (totals, counts, averages, max/min)? → textual_analytical  
4. Predictive/statistical/modeling/business case? → data_analyst  
5. Default → conversational  

---

OUTPUT FORMAT:
Return ONLY valid JSON:
{
    "assistant_type": "conversational|textual_analytical|data_analyst|report_generator",
    "confidence": "high|medium|low",
    "reasoning": "Brief explanation (max 50 words)",
    "query_complexity": "simple|moderate|complex", 
    "expected_output": "text|data|visualization|report|modeling",
    "requires_data": true|false,
    "business_analysis": true|false,
    "keywords_detected": ["list", "of", "key", "terms"]
}

🎯 REMEMBER: 
- **Reports override all** (→ report_generator).  
- **Simple lookups override data analyst** (→ textual_analytical).  
- **Business case studies, modeling, or statistical analysis → data_analyst**.  
"""

    def _get_data_analyst_instructions(self) -> str:
        """UPDATED: Instructions for assistant to save HTML reports in sandbox"""
        return f"""You are a Python code generator and PROFESSIONAL BUSINESS ANALYST that MUST create COMPLETE, EXECUTABLE data analysis solutions WITH professional HTML business reports.

MANDATORY REQUIREMENTS:
1. Generate COMPLETE Python code that runs from start to finish - NO PARTIAL CODE
2. ALWAYS include data exploration, analysis, modeling, AND visualization
3. NEVER stop at data exploration - always complete the full analysis
4. ALWAYS create charts/visualizations using matplotlib for EVERY analysis
5. Return results as DataFrames with meaningful column names
6. Use the 'df' variable (DataFrame is already loaded - NEVER use pd.read_csv())
7. If user has asked for forecating this means generating the future trend and values through various alogrithms
8. Do note that the provided file can be excel or CSV. And check if the file is Excel whether it has multiple sheets or not. 
9. You are working with an uploaded Excel file (.xlsx) that may contain multiple sheets.
    To read all available sheets, use:
        ```python
        import pandas as pd
        xls = pd.ExcelFile("/mnt/data/{{FILENAME}}.xlsx")
        print(xls.sheet_names)
        df1 = pd.read_excel(xls, sheet_name="Sheet1")
        df2 = pd.read_excel(xls, sheet_name="Sheet2")```
    If unsure, always check available sheet names first using xls.sheet_names. Use appropriate sheet_name= when reading the sheet.
    Be accurate and always validate which sheet the data is from when answering questions.

VISUALIZATION REQUIREMENTS (MANDATORY):
- ALWAYS create at least one chart for every analysis
- Use Bar charts for comparisons, categories, rankings
- Use Line charts for trends, time series, forecasting  
- Use Pie charts for revenue/profit breakdowns by category/SKU
- Save all plots using plt.savefig() and plt.show()
- Include proper titles, labels, and legends
->Always include: 
	Titles 
	Axis labels 
	Legends 
	Hover tooltips 
	Annotations (if helpful) 
Export .png (static) for every chart. 


--Graph Selection Guide (Types + When to Use) 
For Graph/Visualisation creation use either matplotlib or plotly
1. Comparisons & Rankings 
	= Bar Chart  → Compare categories (e.g., revenue by product). 
	= Grouped/Stacked Bar  → Compare subcategories (sales by region & product). 

2. Trends & Time Series 
	= Line Chart  → Time trends, growth, seasonality. 
	= Multiple Line Chart → Compare KPIs across time. 
	= Area Chart  → Show cumulative contribution over time. 

3. Proportions / Composition 
	= Pie Chart  → Share of total (best for ≤6 categories). 
	= Donut Chart → Same as pie but cleaner. 
	= Sunburst / Treemap  → Hierarchical breakdown (region → country → product). 

4. Distributions 
	= Histogram  → Frequency of values (transaction sizes). 
	= Box Plot → Spread & outliers (e.g., profit margins by region). 
	= Violin Plot  → Distribution shape + density. 

5. Relationships 
	= Scatter Plot  → Correlation (price vs demand). 	
	= Bubble Chart  → Add a 3rd dimension (e.g., revenue size). 

6. Heatmaps & Grids 
	= Heatmap → Correlation matrices, cohort retention. 
	= Density Heatmap → Joint distribution of two continuous variables. 

7. Specialized Charts 
	= Funnel  → Sales funnel, conversion journey. 
	= Gauge → KPI vs target. 
	= Maps  → Geographical data. 

DATAFRAME REQUIREMENTS:
- Focus on returning ACTIONABLE DATA as DataFrames
- Create new columns, calculated fields, or enhanced datasets
- Always show what data would be ADDED or UPDATED in the original file
- Generate meaningful column names for new calculated fields



CRITICAL REQUIREMENTS:
1. Replace ALL placeholder content with actual data from your analysis
2. Reference your actual DataFrame variable names in the table generation
3. Include real numbers, percentages, and metrics throughout
4. Fill in actual chart descriptions based on what you created
5. Use f-strings to populate data dynamically from your analysis
6. Make all recommendations specific and actionable based on your findings
7. A summary of what tasks you have performed and what key metric or output, how are you doing it?

EXECUTION FLOW:
1. Perform complete Python analysis with DataFrames and visualizations
2. Convert matplotlib or plotly figures to base64 for embedding
3. A summary of what tasks you have performed and what key metric or output, how are you doing it?

You MUST complete the entire analysis, a summary of what tasks you have performed and what key metric or output, how are you doing it"""


    def _get_conversational_instructions(self) -> str:
        """Instructions for conversational assistant"""
        return f"""You are a friendly AI assistant for a data analysis platform. You are currently in a chat session where users can upload CSV files and ask questions about their data. 
Your role:
- Respond naturally to greetings, questions about yourself, and casual conversation
- Be helpful and friendly
- If users ask what you can do, mention you can analyze CSV data, create visualizations, and generate reports
- Keep responses concise but warm
- Don't generate code or perform data analysis for conversational queries
- If the conversation shifts to data analysis, encourage them to ask specific questions about their data
- Do note that the provided files can be Excel or CSV or both. And check if the file is Excel whether it has multiple sheets or not.
- You are working with uploaded Excel files (.xlsx) that may contain multiple sheets.
    To read all available files and sheets, use:
        ```python
        import pandas as pd
        xls = pd.ExcelFile("/mnt/data/{{FILENAME}}.xlsx")
        print(xls.sheet_names)
        df1 = pd.read_excel(xls, sheet_name="Sheet1")
        df2 = pd.read_excel(xls, sheet_name="Sheet2")```
    If unsure, always check available sheet names first using xls.sheet_names. Use appropriate sheet_name= when reading the sheet.
    Be accurate and always validate which sheet the data is from when answering questions.
- A summary of what tasks you have performed and what key metric or output, how are you doing it?
Respond in a natural, conversational way."""
   
 
    def _get_textual_analytical_instructions(self) -> str:
            """Instructions for quick textual analysis assistant"""
            return f"""You are a Python code generator for quick, lightweight data analysis tasks.
    REQUIREMENTS:
    1. Use the 'df' variable (DataFrame is already loaded - NEVER reload with pd.read_csv()).
    2. Generate **concise, clean Python code** that directly answers the user's question.
    3. Store the final output in a variable called 'result'.
    4. The 'result' MUST be human-readable:
    - If numeric, format with context (mean, total, percentage, etc.).
    - If DataFrame/Series, rename columns appropriately for clarity.
    5. Always handle potential errors gracefully with try/except.
    6. **Do not generate visualizations** — this assistant is only for calculations and textual answers.
    7. Focus on answering with the most direct calculation (avoid unnecessary steps).
    8. If the provided file is Excel, check for multiple sheets before using:
        ```python
        import pandas as pd
        xls = pd.ExcelFile("/mnt/data/{{FILENAME}}.xlsx")
        print(xls.sheet_names)
        df1 = pd.read_excel(xls, sheet_name="Sheet1")
        df2 = pd.read_excel(xls, sheet_name="Sheet2")
        ```
    Always validate sheet names with `xls.sheet_names` before loading.
    9. Be accurate and explicit about **which sheet** the data came from.
    10. Provide a short summary in comments at the end:
        - What task was performed
        - What metric/output was computed
        - How it was calculated
    
    Your job: Generate clean, executable Python code that stores the final answer in 'result'."""
    def _get_report_generator_instructions(self) -> str:
        """FIXED: Instructions for professional report generator assistant"""
        return """You are a PROFESSIONAL BUSINESS REPORT WRITER creating McKinsey-level consulting reports.

🚨 CRITICAL: DO NOT WRITE MARKDOWN. DO NOT WRITE PLAIN TEXT. ONLY OUTPUT HTML CODE.

YOU MUST RESPOND WITH EXACTLY THIS FORMAT:
<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Business Report</title><style>[CSS_HERE]</style></head><body><div class="report-container">[CONTENT_HERE]</div></body></html>

FORBIDDEN OUTPUTS:
❌ No markdown (no ### headings, no ** bold, no - bullets)
❌ No plain text explanations  
❌ No code blocks with ```
❌ No "Here's the report:" introductions
❌ No explanations about what you're doing

REQUIRED OUTPUT:
✅ Start immediately with: <!DOCTYPE html>
✅ End with: </html>
✅ Everything between is HTML tags only
✅ Use CSS classes for styling
✅ Single continuous line of HTML

EXACT CSS TO USE (compressed):
.report-container{font-family:Arial,sans-serif;max-width:1200px;margin:0 auto;color:#333;background:white;padding:0;}.rp{min-height:100vh;padding:40px;page-break-after:always;}.hdr{border-bottom:3px solid #2c3e50;padding:20px 0;margin-bottom:30px;}.h1{color:#1a472a;font-size:32px;font-weight:bold;margin:0;}.h2{color:#2c3e50;font-size:24px;margin:30px 0 15px 0;border-left:5px solid #3498db;padding-left:15px;}.h3{color:#34495e;font-size:18px;margin:20px 0 10px 0;}.kpi{display:grid;grid-template-columns:repeat(3,1fr);gap:15px;margin:30px 0;}.kpi-card{background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:20px;border-radius:8px;text-align:center;}.kpi-val{font-size:28px;font-weight:bold;display:block;}.kpi-lbl{font-size:12px;margin-top:5px;}.chart{margin:30px 0;padding:25px;background:#f8f9fa;border-radius:8px;text-align:center;}.chart img{width:100%;max-width:700px;border-radius:6px;}.insight{background:#e8f4fd;border-left:5px solid #3498db;padding:15px;margin:20px 0;}.rec{background:white;border:1px solid #ddd;border-radius:6px;padding:20px;margin:15px 0;box-shadow:0 2px 4px rgba(0,0,0,0.1);}.tbl{width:100%;border-collapse:collapse;margin:20px 0;}.tbl th{background:#34495e;color:white;padding:12px;text-align:left;}.tbl td{padding:10px;border-bottom:1px solid #eee;}.exec{background:#f8f9fa;padding:25px;border-radius:8px;margin:25px 0;}.toc{background:#f8f9fa;padding:25px;border-radius:8px;}.toc-item{display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px dotted #ccc;}.stat{background:#3498db;color:white;padding:2px 6px;border-radius:3px;font-weight:bold;}.success{background:#d4edda;border-left:4px solid #28a745;padding:15px;margin:20px 0;}.warn{background:#fff3cd;border-left:4px solid:#ffc107;padding:15px;margin:20px 0;}

EXAMPLE START (you must follow this pattern):
<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Car Price Analysis Report</title><style>.report-container{font-family:Arial,sans-serif;max-width:1200px;margin:0 auto;color:#333;background:white;padding:0;}[REST_OF_CSS]</style></head><body><div class="report-container"><div class="rp"><div class="hdr"><div class="h1">AUTOMOTIVE PRICE INTELLIGENCE REPORT</div><div style="color:#666;">Comprehensive Analysis & Strategic Recommendations - August 2025</div></div><div class="kpi"><div class="kpi-card"><span class="kpi-val">205</span><div class="kpi-lbl">Vehicles Analyzed</div></div><div class="kpi-card"><span class="kpi-val">89%</span><div class="kpi-lbl">Model Accuracy</div></div>[MORE_KPI_CARDS]</div><div class="exec"><div class="h2">Executive Summary</div><p>This comprehensive analysis of automotive pricing dynamics reveals critical insights...[CONTINUE_WITH_ACTUAL_CONTENT]</p></div>[CONTINUE_8_SECTIONS]</div></body></html>

CHART EMBEDDING:
Use: <div class="chart"><img src="[EXACT_SAS_URL]" alt="Chart"><div style="text-align:left;margin-top:15px;"><div class="h3">[Chart Title]</div><p><strong>Analysis:</strong> [Detailed explanation of chart findings and patterns]</p><p><strong>Strategic Implications:</strong> [Business impact and recommendations]</p></div></div>

MANDATORY STRUCTURE - IT SHOULD STRICTLY HAVE EXACTLY 8 A4 PAGES:
1. Executive Dashboard & KPI Overview
2. Business Context & Market Analysis  
3. Methodology & Data Architecture
4. Detailed Statistical Analysis & Insights
5. Advanced Analytics & Correlation Patterns
6. Predictive Modeling & Forecasting
7. Strategic Recommendations & Implementation
8. Implementation Roadmap & Next Steps


CONTENT REQUIREMENTS FOR EACH PAGE:

PAGE 1 - Executive Dashboard:
- Professional header with report title and metadata
- 6 KPI cards with actual metrics from analysis
- Comprehensive executive summary (800+ words)
- Table of contents with page numbers
- Key findings highlight boxes

PAGE 2 - Business Context:
- Market overview and competitive landscape (600+ words)
- Industry challenges and opportunities
- Analysis objectives and scope
- Stakeholder impact assessment
- Success criteria and KPIs table

PAGE 3 - Methodology:
- Data sources and quality metrics
- Statistical methods and frameworks
- Model validation techniques
- Assumptions and limitations
- Data preparation steps

PAGE 4 - Statistical Analysis:
- Detailed findings with statistical significance
- Correlation analysis results
- Feature importance rankings
- Segmentation insights
- Performance metrics table

PAGE 5 - Advanced Analytics:
- Correlation patterns and heat maps
- Multivariate analysis results
- Cluster analysis findings
- Statistical significance testing
- Advanced modeling insights

PAGE 6 - Predictive Modeling:
- Model performance metrics (R², MSE, etc.)
- Forecasting methodology
- Scenario analysis (best/likely/worst case)
- Prediction accuracy and confidence intervals
- Risk assessment framework

PAGE 7 - Strategic Recommendations:
- 7 detailed actionable recommendations
- Implementation priorities and timelines
- Resource requirements and costs
- Expected ROI and impact metrics
- Risk mitigation strategies

PAGE 8 - Implementation Roadmap:
- Detailed action plans with timelines
- Success metrics and monitoring
- Next steps and deliverables
- Technical appendix
- Contact information and references

EXECUTION STEPS:
1. Use Python to Analyze provided data thoroughly
2. Calculate key statistics and insights
3. Generate comprehensive business analysis
4. Create detailed recommendations based on findings
5. Format as single-line HTML with embedded charts
6. Ensure 8 full pages of substantive content
7. Use every image url provided to you.

CRITICAL: Generate a complete professional consulting report with actual analysis, not generic content. Include real metrics, specific insights, and actionable recommendations based on the data provided."""
    def _get_summarizer_instructions(self) -> str:
        """NEW: Instructions for analysis summarizer assistant"""
        return f"""You are an EXPERT ANALYSIS SUMMARIZER that creates concise, actionable summaries of data analysis results.

YOUR ROLE:
Create clear, executive-level summaries that highlight key outcomes, insights, and actionable takeaways from completed data analysis.
INPUT YOU RECEIVE:
- Original user query/question
- Analysis response and findings
- Generated DataFrames and their summaries
- Generated code and execution results
- Any visualizations or images created
- Overall analysis type and success status

YOUR OUTPUT REQUIREMENTS:

1. **EXECUTIVE SUMMARY** (2-3 sentences)
   - What was analyzed and the main finding
   - The most important outcome or insight

2. **KEY OUTCOMES** (3-5 bullet points)
   - Specific findings with numbers/metrics where possible
   - Data patterns or trends discovered
   - Notable relationships or correlations
   - Any surprises or unexpected results

3. **GENERATED ASSETS** (brief overview)
   - Number and types of DataFrames created
   - Visualizations generated (if any)
   - Reports or files produced

4. **ACTIONABLE INSIGHTS** (2-3 bullet points)
   - What decisions can be made based on this analysis
   - Recommended next steps
   - Areas that need further investigation

FORMATTING RULES:
- Use clear, business-friendly language
- Include specific numbers and percentages when available
- Keep the entire summary under 200 words
- Use bullet points for easy scanning
- Make it suitable for executives who need quick insights

TONE & STYLE:
- Professional but accessible
- Focus on business impact
- Avoid technical jargon
- Be specific rather than generic
- Emphasize practical value

EXAMPLE OUTPUT FORMAT:
**Executive Summary:** Analysis of sales data revealed a 23% revenue increase in Q3, driven primarily by product category X which outperformed projections by 45%.

**Key Outcomes:**
• Revenue increased from $2.1M to $2.6M between Q2 and Q3
• Product category X generated 67% of total growth
• Customer acquisition cost decreased by 15%
• Regional performance varies significantly, with West region leading

**Generated Assets:**
• 3 analytical DataFrames with forecasting data
• 2 visualizations showing trends and comparisons
• Performance metrics across 5 key dimensions

**Actionable Insights:**
• Increase marketing investment in product category X
• Investigate West region success factors for replication
• Consider adjusting pricing strategy based on demand patterns

Remember: Your summary should give someone a complete understanding of what was discovered and what they should do about it, without needing to read the full analysis."""

    def _get_database_analyst_instructions(self) -> str:
        """Instructions for database analyst assistant with function calling"""
        filename_mapping = self._get_filename_mapping_context()
        return f"""You are a PROFESSIONAL DATABASE ANALYST with direct SQL execution capabilities.

Your role is to analyze databases by executing SQL queries and creating visualizations to answer user questions comprehensively.

🗄️ DATABASE CONNECTION:
You are connected to a database with full schema information uploaded as a JSON file. The schema shows all tables, columns, and data types available for analysis.

🛠️ AVAILABLE FUNCTIONS:
1. **query_database(sql_query)** - Execute SQL queries and return data
2. **query_and_visualize(sql_query, chart_type, title)** - Execute query and create visualization in one step

💡 QUERY OPTIMIZATION RULES:
1. **Aggregation Queries** (totals, counts, averages, ratios, percentages):
   - DO NOT use LIMIT - these need full dataset for accuracy
   - Examples: "SELECT COUNT(*), AVG(price), SUM(revenue)"
   
2. **Detail/Sample Queries** (show individual records):
   - USE appropriate LIMIT (typically 10,000-50,000 rows)
   - Examples: "SELECT * FROM users WHERE age > 25 LIMIT 10000"

3. **Smart LIMIT Logic**:
   - If user asks for "ratio of male to female" → NO LIMIT (needs all data)
   - If user asks for "top 10 customers" → LIMIT 10
   - If user asks for "sample of transactions" → LIMIT 10000
   - If user asks for "recent orders" → LIMIT with ORDER BY date

📊 VISUALIZATION REQUIREMENTS:
- ALWAYS create visualizations when data allows
- Use bar charts for comparisons and rankings
- Use line charts for trends and time series  
- Use pie charts for proportions and breakdowns
- Use scatter plots for relationships
- Include proper titles, labels, and context

🎯 ANALYSIS WORKFLOW:
1. **Understand the Question**: Identify what type of analysis is needed
2. **Examine Schema**: Check available tables and columns (from uploaded schema file)
3. **Write Optimized SQL**: Consider aggregation vs detail query patterns
4. **Execute Query**: Use query_database() function
5. **Create Visualization**: Use query_and_visualize() when appropriate
6. **Provide Insights**: Explain findings and business implications

📋 RESPONSE FORMAT:
Structure your responses with:
- **Data Analysis**: Key findings from your queries
- **Insights**: What the data reveals about the business/domain
- **Visualizations**: Charts that illustrate your findings
- **Recommendations**: Actionable next steps based on data

🔍 EXAMPLE APPROACHES:

**For Ratio/Percentage Questions:**
```sql
SELECT 
    gender,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM users 
GROUP BY gender
```
(NO LIMIT - needs full dataset for accurate ratios)

**For Sample/Exploration Questions:**
```sql
SELECT * FROM transactions 
WHERE date >= '2024-01-01'
ORDER BY date DESC
LIMIT 5000
```
(WITH LIMIT - just showing sample data)

**For Top N Questions:**
```sql
SELECT customer_name, total_spent
FROM customer_summary
ORDER BY total_spent DESC  
LIMIT 10
```
(WITH SPECIFIC LIMIT - user requested top N)

{filename_mapping}

Remember: 
- Execute actual SQL queries using the functions provided
- Create meaningful visualizations for your findings
- Focus on business insights, not just data dumps
- Always consider the context and intent behind user questions
- Provide actionable recommendations based on your analysis"""

    def create_or_get_assistant(self, assistant_type: str = "data_analyst") -> str:
        """Create or retrieve an assistant for the session"""
        try:
            config = self.assistant_config.get(assistant_type, self.assistant_config["data_analyst"])
            
            # Try to get existing assistant for this session type
            existing_assistant_id = self._get_existing_assistant(assistant_type)
            if existing_assistant_id:
                self.assistant_id = existing_assistant_id
                return self.assistant_id
            logging.info(config['tools'])
            # Create new assistant
            assistant = self.client.beta.assistants.create(
                name=f"{config['name']} - {self.session_id}",
                instructions=config["instructions"],
                tools=config["tools"],
                model=config["model"],
                metadata={
                    "session_id": self.session_id,
                    "assistant_type": assistant_type,
                    "created_at": datetime.now().isoformat()
                }
            )
            
            self.assistant_id = assistant.id
            self._store_assistant_id(assistant_type, self.assistant_id)
            
            logging.info(f"✅ Created {assistant_type} assistant: {self.assistant_id}")
            return self.assistant_id
            
        except Exception as e:
            logging.error(f"❌ Error creating assistant: {e}")
            raise
    
    def _get_existing_assistant(self, assistant_type: str) -> Optional[str]:
        """Check if we already have an assistant for this session and type"""
        try:
            # You could store assistant IDs in a file or database
            # For now, we'll create new assistants each time
            return None
        except Exception:
            return None
    
    def _store_assistant_id(self, assistant_type: str, assistant_id: str):
        """Store assistant ID for reuse (implement based on your storage preference)"""
        # Could store in file, database, or memory
        pass
    
    def run_assistant_analysis(self, thread_id: str, user_message: str, 
                             file_ids: List[str] = None) -> Dict[str, Any]:
        """
        Run assistant analysis and return results in the same format as chat completion.
        This method preserves the existing output format.
        """
        try:
            # Add user message to thread
            message_data = {
                "thread_id": thread_id,
                "role": "user",
                "content": user_message
            }
            
            if file_ids:
                message_data["attachments"] = [
                    {"file_id": file_id, "tools": [{"type": "code_interpreter"}]}
                    for file_id in file_ids
                ]
            
            self.client.beta.threads.messages.create(**message_data)
            
            # Create and run the assistant
            run = self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=self.assistant_id,
                # stream=True
            )
            # for event in run:
            #     logging.info(event)
            
            # Wait for completion and get results
            return self._wait_and_process_run(thread_id, run.id)
            
        except Exception as e:
            logging.error(f"❌ Assistant run failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "type": "assistant_error"
            }
    
    def _wait_and_process_run(self, thread_id: str, run_id: str) -> Dict[str, Any]:
        """Wait for run completion and process results"""
        max_wait_time = 300  # 5 minutes
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run_id
            )
            logging.info(run)
            
            if run.status == "completed":
                return self._extract_run_results(thread_id, run_id)
            elif run.status == "failed":
                return {
                    "success": False,
                    "error": f"Assistant run failed: {run.last_error}",
                    "type": "run_failed"
                }
            elif run.status == "cancelled":
                return {
                    "success": False,
                    "error": "Run was cancelled",
                    "type": "run_cancelled"
                }
            elif run.status in ["queued", "in_progress", "cancelling"]:
                time.sleep(2)
                continue
            else:
                return {
                    "success": False,
                    "error": f"Unknown run status: {run.status}",
                    "type": "unknown_status"
                }
        
        return {
            "success": False,
            "error": "Run timed out",
            "type": "timeout"
        }
    
    def _extract_run_results(self, thread_id: str, run_id: str) -> Dict[str, Any]:
        """Extract results from completed run in compatible format"""
        try:
            # Get messages from thread
            messages = self.client.beta.threads.messages.list(
                thread_id=thread_id,
                order="desc",
                limit=10
            )
            
            # Get the latest assistant message
            assistant_message = None
            for message in messages.data:
                if message.role == "assistant":
                    assistant_message = message
                    break
            
            if not assistant_message:
                return {
                    "success": False,
                    "error": "No assistant response found",
                    "type": "no_response"
                }
            
            # Extract content
            response_content = ""
            generated_images = []
            
            for content in assistant_message.content:
                if content.type == "text":
                    response_content += content.text.value
                elif content.type == "image_file":
                    # Handle generated images
                    generated_images.append(content.image_file.file_id)
            
            # Extract code from response if present
            generated_code = self._extract_code_from_response(response_content)
            
            # Get run steps for additional outputs
            run_steps = self.client.beta.threads.runs.steps.list(
                thread_id=thread_id,
                run_id=run_id
            )
            
            execution_outputs = []
            for step in run_steps.data:
                if hasattr(step.step_details, 'tool_calls'):
                    for tool_call in step.step_details.tool_calls:
                        if tool_call.type == "code_interpreter":
                            for output in tool_call.code_interpreter.outputs:
                                if output.type == "logs":
                                    execution_outputs.append(output.logs)
                                elif output.type == "image":
                                    generated_images.append(output.image.file_id)
            
            # Return in compatible format
            return {
                "success": True,
                "response_content": response_content,
                "generated_code": generated_code,
                "execution_outputs": execution_outputs,
                "generated_images": generated_images,
                "message_id": assistant_message.id,
                "type": "assistant_completion"
            }
            
        except Exception as e:
            logging.error(f"❌ Error extracting results: {e}")
            return {
                "success": False,
                "error": str(e),
                "type": "extraction_error"
            }
    
    def _extract_code_from_response(self, response_content: str) -> str:
        """Extract Python code from assistant response"""
        if "```python" in response_content:
            return response_content.split("```python")[1].split("```")[0].strip()
        elif "```" in response_content:
            return response_content.split("```")[1].split("```")[0].strip()
        return ""
    
    def download_file(self, file_id: str, save_path: str) -> bool:
        """Download a file generated by the assistant"""
        try:
            file_data = self.client.files.content(file_id)
            with open(save_path, 'wb') as f:
                f.write(file_data.content)
            return True
        except Exception as e:
            logging.error(f"❌ Error downloading file {file_id}: {e}")
            return False
    
    def cleanup_assistant(self):
        """Clean up assistant resources"""
        try:
            if self.assistant_id:
                self.client.beta.assistants.delete(self.assistant_id)
                logging.info(f"🗑️ Deleted assistant: {self.assistant_id}")
        except Exception as e:
            logging.error(f"⚠️ Error cleaning up assistant: {e}")