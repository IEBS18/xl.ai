# assistants/structured_report_generator.py

import json
import logging
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

@dataclass
class ReportSection:
    """Defines a single report section"""
    section_id: str
    title: str
    description: str
    requirements: List[str]
    data_sources: List[str]
    expected_length: str  # "short", "medium", "long"
    priority: int  # 1-10, higher = more important
    dependencies: List[str]  # sections that must be completed first
    content_type: str  # "analysis", "visualization", "summary", "recommendation"
    
class StructuredReportGenerator:
    """
    Advanced HTML report generator that creates detailed sections iteratively
    """
    
    def __init__(self, assistant_manager, thread_manager, session_id: str):
        self.assistant_manager = assistant_manager
        self.thread_manager = thread_manager
        self.session_id = session_id
        self.thread_id = thread_manager.create_or_get_thread(session_id)
        
        # Track generated sections and data
        self.generated_sections = {}
        self.section_metadata = {}
        self.report_context = {}
        
    def generate_comprehensive_report(self, user_query: str, analysis_result: Dict[str, Any], 
                                    image_sas_urls: List[str]) -> Dict[str, Any]:
        """
        Main method to generate comprehensive structured HTML report
        
        Flow:
        1. Generate JSON report structure/outline
        2. Process each section individually with assistant
        3. Combine all sections into final HTML report
        4. Apply HTML formatting and styling
        """
        try:
            print("🏗️ Starting structured HTML report generation process...")
            
            # STEP 1: Generate report structure (JSON outline)
            report_structure = self._generate_report_structure(user_query, analysis_result, image_sas_urls)
            
            if not report_structure.get("success"):
                return self._fallback_html_report_generation(user_query, analysis_result, image_sas_urls)
            
            # STEP 2: Generate each section individually
            section_results = self._generate_sections_iteratively(
                report_structure["sections"], 
                user_query, 
                analysis_result, 
                image_sas_urls
            )
            
            # STEP 3: Combine sections into final HTML report
            final_html_report = self._combine_sections_into_html_report(
                report_structure, 
                section_results, 
                user_query,
                image_sas_urls
            )
            
            # STEP 4: Apply professional HTML styling and validation
            formatted_html_report = self._format_final_html_report(final_html_report, image_sas_urls)
            
            return {
                "success": True,
                "html_report": formatted_html_report["content"],  # HTML content for frontend
                "embedded_images": image_sas_urls,
                "report_type": "structured_iterative_html_report",
                "sections_generated": len(section_results),
                "report_structure": report_structure,
                "section_metadata": self.section_metadata,
                "generation_method": "iterative_assistant_html_sections"
            }
            
        except Exception as e:
            print(f"❌ Error in structured HTML report generation: {e}")
            logging.exception("Structured HTML report generation failed")
            return self._fallback_html_report_generation(user_query, analysis_result, image_sas_urls)
    
    def _generate_report_structure(self, user_query: str, analysis_result: Dict[str, Any], 
                                 image_sas_urls: List[str]) -> Dict[str, Any]:
        """
        STEP 1: Generate JSON structure defining all report sections
        """
        try:
            print("📋 Generating report structure (JSON outline)...")
            
            # Create structure generation assistant
            assistant_id = self.assistant_manager.create_or_get_assistant("report_generator")
            
            # Prepare context for structure generation
            structure_context = self._prepare_structure_context(user_query, analysis_result, image_sas_urls)
            
            structure_prompt = f"""
Generate a detailed JSON structure for a comprehensive business report. This structure will define each section that will be generated individually.

ANALYSIS CONTEXT:
{structure_context}

REQUIREMENTS:
1. Generate a JSON structure with 8-12 detailed sections
2. Each section should have specific requirements and data sources
3. Include section dependencies (some sections need others completed first)
4. Specify expected content length and priority
5. Include both analytical and strategic sections
6. Account for {len(image_sas_urls)} visualizations available

OUTPUT ONLY VALID JSON in this exact format:
{{
  "report_title": "Professional Business Analysis Report",
  "report_subtitle": "Comprehensive Data Analysis and Strategic Insights",
  "executive_summary": "Brief overview of what this report contains",
  "sections": [
    {{
      "section_id": "executive_summary",
      "title": "Executive Summary",
      "description": "High-level overview of key findings and business impact",
      "requirements": [
        "Summarize top 3-5 key findings",
        "Include quantified business impact",
        "Provide clear recommendations preview"
      ],
      "data_sources": ["analysis_result", "key_metrics"],
      "expected_length": "medium",
      "priority": 10,
      "dependencies": [],
      "content_type": "summary"
    }},
    {{
      "section_id": "business_context",
      "title": "Business Context and Objectives",
      "description": "Background information and analysis objectives",
      "requirements": [
        "Explain business problem being solved",
        "Define success criteria",
        "Describe dataset and scope"
      ],
      "data_sources": ["user_query", "dataset_info"],
      "expected_length": "medium",
      "priority": 8,
      "dependencies": [],
      "content_type": "analysis"
    }},
    {{
      "section_id": "methodology",
      "title": "Analytical Methodology",
      "description": "Approach and methods used in analysis",
      "requirements": [
        "Describe analytical approach",
        "Explain data processing steps",
        "Document assumptions and limitations"
      ],
      "data_sources": ["generated_code", "analysis_result"],
      "expected_length": "medium",
      "priority": 6,
      "dependencies": [],
      "content_type": "analysis"
    }},
    {{
      "section_id": "data_overview",
      "title": "Data Overview and Quality Assessment", 
      "description": "Dataset characteristics and data quality analysis",
      "requirements": [
        "Dataset size and structure",
        "Data quality assessment",
        "Key variables and distributions"
      ],
      "data_sources": ["dataframes", "dataset_info"],
      "expected_length": "long",
      "priority": 7,
      "dependencies": [],
      "content_type": "analysis"
    }},
    {{
      "section_id": "key_findings",
      "title": "Key Findings and Insights",
      "description": "Primary analytical findings with supporting evidence",
      "requirements": [
        "Present top 5-7 key findings",
        "Include statistical evidence",
        "Reference supporting visualizations"
      ],
      "data_sources": ["analysis_result", "dataframes", "visualizations"],
      "expected_length": "long",
      "priority": 9,
      "dependencies": ["data_overview"],
      "content_type": "analysis"
    }},
    {{
      "section_id": "detailed_analysis",
      "title": "Detailed Statistical Analysis",
      "description": "In-depth analysis with charts and data tables",
      "requirements": [
        "Reference each visualization with analysis",
        "Include generated DataFrames insights",
        "Provide statistical interpretations"
      ],
      "data_sources": ["visualizations", "dataframes", "analysis_result"],
      "expected_length": "long",
      "priority": 8,
      "dependencies": ["key_findings"],
      "content_type": "visualization"
    }},
    {{
      "section_id": "business_implications",
      "title": "Business Implications and Impact",
      "description": "Strategic implications of findings for business",
      "requirements": [
        "Translate findings to business impact",
        "Quantify potential value",
        "Identify risks and opportunities"
      ],
      "data_sources": ["key_findings", "analysis_result"],
      "expected_length": "long",
      "priority": 9,
      "dependencies": ["key_findings", "detailed_analysis"],
      "content_type": "analysis"
    }},
    {{
      "section_id": "strategic_recommendations",
      "title": "Strategic Recommendations",
      "description": "Actionable recommendations based on analysis",
      "requirements": [
        "Provide 5-8 specific recommendations",
        "Include implementation priorities",
        "Estimate resource requirements"
      ],
      "data_sources": ["business_implications", "key_findings"],
      "expected_length": "long",
      "priority": 10,
      "dependencies": ["business_implications"],
      "content_type": "recommendation"
    }},
    {{
      "section_id": "implementation_roadmap",
      "title": "Implementation Roadmap",
      "description": "Step-by-step implementation plan",
      "requirements": [
        "Timeline for implementation",
        "Resource allocation",
        "Success metrics and KPIs"
      ],
      "data_sources": ["strategic_recommendations"],
      "expected_length": "medium",
      "priority": 7,
      "dependencies": ["strategic_recommendations"],
      "content_type": "recommendation"
    }},
    {{
      "section_id": "risk_assessment",
      "title": "Risk Assessment and Mitigation",
      "description": "Identified risks and mitigation strategies",
      "requirements": [
        "Identify key risks",
        "Assess probability and impact",
        "Provide mitigation strategies"
      ],
      "data_sources": ["analysis_result", "business_implications"],
      "expected_length": "medium",
      "priority": 6,
      "dependencies": ["business_implications"],
      "content_type": "analysis"
    }},
    {{
      "section_id": "appendices",
      "title": "Technical Appendices",
      "description": "Technical details and supporting documentation",
      "requirements": [
        "Include generated code",
        "Data dictionaries",
        "Additional charts and tables"
      ],
      "data_sources": ["generated_code", "dataframes", "visualizations"],
      "expected_length": "medium",
      "priority": 4,
      "dependencies": ["detailed_analysis"],
      "content_type": "analysis"
    }}
  ],
  "total_sections": 11,
  "estimated_pages": 15
}}

Generate the JSON structure now:
"""
            
            # Get structure from assistant
            result = self.assistant_manager.run_assistant_analysis(
                self.thread_id,
                structure_prompt
            )
            
            if result.get("success"):
                response_content = result.get("response_content", "")
                
                # Extract JSON from response
                json_structure = self._extract_json_from_response(response_content)
                
                if json_structure:
                    print(f"✅ Generated report structure with {len(json_structure.get('sections', []))} sections")
                    return {
                        "success": True,
                        "structure": json_structure,
                        "sections": json_structure.get("sections", []),
                        "metadata": {
                            "total_sections": len(json_structure.get("sections", [])),
                            "generation_method": "assistant_json",
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                else:
                    print("⚠️ Failed to extract JSON, using fallback structure")
                    return self._get_fallback_structure(user_query, analysis_result, image_sas_urls)
            else:
                print("⚠️ Assistant failed to generate structure")
                return self._get_fallback_structure(user_query, analysis_result, image_sas_urls)
                
        except Exception as e:
            print(f"❌ Error generating report structure: {e}")
            return self._get_fallback_structure(user_query, analysis_result, image_sas_urls)
    
    def _extract_json_from_response(self, response_content: str) -> Optional[Dict[str, Any]]:
        """Extract and validate JSON structure from assistant response"""
        try:
            # Look for JSON in the response
            if "{" in response_content and "}" in response_content:
                # Find the start and end of JSON
                start_idx = response_content.find("{")
                # Find the matching closing brace
                brace_count = 0
                end_idx = -1
                
                for i in range(start_idx, len(response_content)):
                    if response_content[i] == "{":
                        brace_count += 1
                    elif response_content[i] == "}":
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx = i + 1
                            break
                
                if end_idx != -1:
                    json_str = response_content[start_idx:end_idx]
                    structure = json.loads(json_str)
                    
                    # Validate structure
                    if "sections" in structure and len(structure["sections"]) > 0:
                        # Validate each section has required fields
                        required_fields = ["section_id", "title", "description", "requirements"]
                        for section in structure["sections"]:
                            if all(field in section for field in required_fields):
                                continue
                            else:
                                print(f"⚠️ Section missing required fields: {section.get('section_id', 'unknown')}")
                                return None
                        
                        return structure
            
            return None
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            return None
        except Exception as e:
            print(f"❌ Error extracting JSON: {e}")
            return None
    
    def _prepare_structure_context(self, user_query: str, analysis_result: Dict[str, Any], 
                                 image_sas_urls: List[str]) -> str:
        """Prepare context for structure generation"""
        try:
            dataframes = analysis_result.get('dataframes', {})
            
            context = f"""
USER QUERY: {user_query}

ANALYSIS RESULTS:
- Type: {analysis_result.get('type', 'unknown')}
- Success: {analysis_result.get('success', False)}
- Response Length: {len(str(analysis_result.get('response', '')))} characters
- Generated Code: {'Yes' if analysis_result.get('generated_code') else 'No'}

AVAILABLE DATA:
- Generated DataFrames: {len(dataframes)}
- Available Visualizations: {len(image_sas_urls)}
- Data Sources: analysis results, generated code, DataFrames, visualizations

DATAFRAME DETAILS:
"""
            
            for df_name, df_info in dataframes.items():
                if isinstance(df_info, dict) and df_info.get('type') == 'dataframe':
                    shape = df_info.get('shape', (0, 0))
                    context += f"- {df_name}: {shape[0]} rows × {shape[1]} columns\n"
                elif hasattr(df_info, 'shape'):
                    context += f"- {df_name}: {df_info.shape[0]} rows × {df_info.shape[1]} columns\n"
            
            if len(image_sas_urls) > 0:
                context += f"\nVISUALIZATIONS:\n"
                for i, url in enumerate(image_sas_urls, 1):
                    context += f"- Chart {i}: Available for embedding\n"
            
            return context
            
        except Exception as e:
            print(f"⚠️ Error preparing structure context: {e}")
            return f"User Query: {user_query}\nAnalysis completed with {len(dataframes)} DataFrames and {len(image_sas_urls)} visualizations."
    
    def _generate_sections_iteratively(self, sections: List[Dict[str, Any]], user_query: str,
                                     analysis_result: Dict[str, Any], image_sas_urls: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        STEP 2: Generate each section individually using assistant
        """
        print(f"📝 Generating {len(sections)} sections iteratively...")
        
        section_results = {}
        
        # Sort sections by dependencies and priority
        sorted_sections = self._sort_sections_by_dependencies(sections)
        
        for i, section in enumerate(sorted_sections, 1):
            try:
                section_id = section.get("section_id", f"section_{i}")
                print(f"📄 Generating section {i}/{len(sections)}: {section.get('title', section_id)}")
                
                # Generate individual section
                section_result = self._generate_individual_section(
                    section, user_query, analysis_result, image_sas_urls, section_results
                )
                
                if section_result.get("success"):
                    section_results[section_id] = section_result
                    
                    # Store metadata
                    self.section_metadata[section_id] = {
                        "generation_time": datetime.now().isoformat(),
                        "content_length": len(section_result.get("content", "")),
                        "priority": section.get("priority", 5),
                        "dependencies_met": self._check_dependencies_met(section, section_results)
                    }
                    
                    print(f"✅ Section '{section.get('title')}' generated successfully")
                else:
                    print(f"⚠️ Failed to generate section '{section.get('title')}', using fallback")
                    section_results[section_id] = self._generate_fallback_section(section, analysis_result)
                
            except Exception as e:
                print(f"❌ Error generating section {section_id}: {e}")
                section_results[section_id] = self._generate_fallback_section(section, analysis_result)
        
        print(f"✅ Generated {len(section_results)} sections successfully")
        return section_results
    
    def _sort_sections_by_dependencies(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort sections by dependencies and priority"""
        try:
            # Simple topological sort based on dependencies
            sorted_sections = []
            remaining_sections = sections.copy()
            completed_sections = set()
            
            max_iterations = len(sections) * 2  # Prevent infinite loops
            iterations = 0
            
            while remaining_sections and iterations < max_iterations:
                progress_made = False
                
                for section in remaining_sections[:]:  # Copy to modify during iteration
                    dependencies = section.get("dependencies", [])
                    
                    # Check if all dependencies are completed
                    if all(dep in completed_sections for dep in dependencies):
                        sorted_sections.append(section)
                        remaining_sections.remove(section)
                        completed_sections.add(section.get("section_id", ""))
                        progress_made = True
                
                if not progress_made:
                    # Add remaining sections by priority to break circular dependencies
                    remaining_sections.sort(key=lambda x: x.get("priority", 5), reverse=True)
                    for section in remaining_sections:
                        sorted_sections.append(section)
                        completed_sections.add(section.get("section_id", ""))
                    break
                
                iterations += 1
            
            return sorted_sections
            
        except Exception as e:
            print(f"⚠️ Error sorting sections: {e}")
            return sections  # Return original order as fallback
    
    def _generate_individual_section(self, section: Dict[str, Any], user_query: str,
                                   analysis_result: Dict[str, Any], image_sas_urls: List[str],
                                   completed_sections: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Generate content for a single section using assistant"""
        try:
            section_id = section.get("section_id", "unknown")
            section_title = section.get("title", "Unknown Section")
            
            # Prepare section-specific context
            section_context = self._prepare_section_context(
                section, user_query, analysis_result, image_sas_urls, completed_sections
            )
            
            # Create section generation prompt
            section_prompt = self._create_section_prompt(section, section_context, image_sas_urls)
            
            # Use assistant to generate section content
            result = self.assistant_manager.run_assistant_analysis(
                self.thread_id,
                section_prompt
            )
            
            if result.get("success"):
                content = result.get("response_content", "")
                
                # Post-process section content
                processed_content = self._post_process_section_content(
                    content, section, image_sas_urls
                )
                
                return {
                    "success": True,
                    "content": processed_content,
                    "section_id": section_id,
                    "title": section_title,
                    "content_type": section.get("content_type", "analysis"),
                    "length": len(processed_content),
                    "generation_method": "assistant",
                    "raw_content": content
                }
            else:
                return {"success": False, "error": result.get("error", "Unknown error")}
                
        except Exception as e:
            print(f"❌ Error generating individual section: {e}")
            return {"success": False, "error": str(e)}
    
    def _prepare_section_context(self, section: Dict[str, Any], user_query: str,
                               analysis_result: Dict[str, Any], image_sas_urls: List[str],
                               completed_sections: Dict[str, Dict[str, Any]]) -> str:
        """Prepare context specific to the section being generated"""
        try:
            context = f"""
SECTION TO GENERATE: {section.get('title', 'Unknown')}
SECTION DESCRIPTION: {section.get('description', 'No description')}

ORIGINAL USER QUERY: {user_query}

SECTION REQUIREMENTS:
"""
            for req in section.get("requirements", []):
                context += f"- {req}\n"
            
            context += f"\nDATA SOURCES FOR THIS SECTION:\n"
            for source in section.get("data_sources", []):
                context += f"- {source}\n"
            
            # Add completed sections context if there are dependencies
            dependencies = section.get("dependencies", [])
            if dependencies:
                context += f"\nCOMPLETED DEPENDENCIES:\n"
                for dep_id in dependencies:
                    if dep_id in completed_sections:
                        dep_content = completed_sections[dep_id].get("content", "")[:200]
                        context += f"- {dep_id}: {dep_content}...\n"
            
            # Add relevant data based on data sources
            data_sources = section.get("data_sources", [])
            
            if "analysis_result" in data_sources:
                context += f"\nANALYSIS RESULT:\n{str(analysis_result.get('response', ''))[:500]}...\n"
            
            if "dataframes" in data_sources:
                dataframes = analysis_result.get('dataframes', {})
                context += f"\nGENERATED DATAFRAMES ({len(dataframes)}):\n"
                for df_name, df_info in dataframes.items():
                    if isinstance(df_info, dict) and df_info.get('type') == 'dataframe':
                        shape = df_info.get('shape', (0, 0))
                        context += f"- {df_name}: {shape[0]} rows × {shape[1]} columns\n"
            
            if "visualizations" in data_sources and image_sas_urls:
                context += f"\nAVAILABLE VISUALIZATIONS ({len(image_sas_urls)}):\n"
                for i, url in enumerate(image_sas_urls, 1):
                    context += f"- Chart {i}: {url}\n"
            
            if "generated_code" in data_sources:
                generated_code = analysis_result.get('generated_code', '')
                if isinstance(generated_code, dict):
                    code_content = generated_code.get('code', '')
                else:
                    code_content = generated_code
                
                if code_content:
                    context += f"\nGENERATED CODE:\n```python\n{code_content[:500]}...\n```\n"
            
            return context
            
        except Exception as e:
            print(f"⚠️ Error preparing section context: {e}")
            return f"Section: {section.get('title', 'Unknown')}\nUser Query: {user_query}"
    
    def _create_section_prompt(self, section: Dict[str, Any], context: str, image_sas_urls: List[str]) -> str:
        """Create specialized prompt for generating HTML section content"""
        
        expected_length = section.get("expected_length", "medium")
        content_type = section.get("content_type", "analysis")
        
        # Length guidelines
        length_guidelines = {
            "short": "2-3 comprehensive paragraphs (300-500 words)",
            "medium": "4-6 detailed paragraphs (600-1000 words)", 
            "long": "7-12 comprehensive paragraphs (1200-2000 words)"
        }
        
        # Content type specific instructions
        type_instructions = {
            "analysis": "Focus on data insights, statistical findings, and analytical depth",
            "summary": "Provide concise overview with key highlights and main takeaways",
            "recommendation": "Include specific, actionable recommendations with implementation details",
            "visualization": "Reference charts and visual elements, explain what they show and their significance"
        }
        
        prompt = f"""
You are generating ONE SPECIFIC SECTION of a comprehensive business report in HTML format.

{context}

SECTION GENERATION REQUIREMENTS:
1. Write ONLY the content for this specific section in HTML format
2. Expected length: {length_guidelines.get(expected_length, 'Medium length')}
3. Content focus: {type_instructions.get(content_type, 'Analytical focus')}
4. Professional business writing style
5. Include specific data points and quantified insights where possible
6. Generate properly formatted HTML with professional styling

SECTION TITLE: {section.get('title', 'Unknown Section')}

SPECIFIC REQUIREMENTS FOR THIS SECTION:
"""
        
        for req in section.get("requirements", []):
            prompt += f"• {req}\n"
        
        if "visualizations" in section.get("data_sources", []) and image_sas_urls:
            prompt += f"""
CHART EMBEDDING INSTRUCTIONS:
When referencing visualizations, use this HTML format:
<div class="chart-container">
    <img src="{image_sas_urls[0] if image_sas_urls else '[URL]'}" alt="Analysis Chart" class="chart-image">
    <p class="chart-description">The analysis shows significant trends indicating...</p>
</div>

Available charts: {len(image_sas_urls)} visualizations
"""
        
        prompt += f"""
HTML OUTPUT REQUIREMENTS:
- Generate clean, semantic HTML5 markup
- Include section heading: <h2 class="section-title">{section.get('title', 'Section Title')}</h2>
- Use proper HTML tags: <p>, <ul>, <li>, <strong>, <em>, <div>, etc.
- Add CSS classes for styling: "insight-box", "metric-highlight", "recommendation-item"
- Generate detailed, substantive content that meets the specified length
- Reference specific data points and findings from the context
- Include proper HTML structure but NO <html>, <head>, or <body> tags
- Do NOT include CSS styles - only HTML markup with classes

EXAMPLE HTML STRUCTURE:
<div class="section-container">
    <h2 class="section-title">Section Title</h2>
    <div class="section-content">
        <p class="section-intro">Introduction paragraph...</p>
        <div class="insight-box">
            <h3>Key Insight</h3>
            <p>Detailed analysis...</p>
        </div>
        <ul class="findings-list">
            <li class="finding-item">First finding with <strong class="metric-highlight">42%</strong> improvement</li>
        </ul>
    </div>
</div>

Generate the HTML section content now:
"""
        
        return prompt
    
    def _post_process_section_content(self, content: str, section: Dict[str, Any], 
                                    image_sas_urls: List[str]) -> str:
        """Post-process generated section content"""
        try:
            processed_content = content
            
            # Ensure section has proper HTML structure
            section_title = section.get('title', 'Section')
            
            # If content doesn't start with proper div structure, wrap it
            if not processed_content.strip().startswith('<div class="section-container">'):
                if not processed_content.startswith(f'<h2 class="section-title">{section_title}</h2>'):
                    processed_content = f'<h2 class="section-title">{section_title}</h2>\n<div class="section-content">\n{processed_content}\n</div>'
                
                processed_content = f'<div class="section-container">\n{processed_content}\n</div>'
            
            # Ensure proper image URL formatting
            for i, url in enumerate(image_sas_urls, 1):
                # Look for chart references and ensure they have proper URLs
                chart_patterns = [f"Chart {i}", f"Figure {i}", f"Visualization {i}"]
                for pattern in chart_patterns:
                    if pattern in processed_content and f'src="{url}"' not in processed_content:
                        # Replace text reference with proper image HTML
                        chart_html = f'''<div class="chart-container">
    <img src="{url}" alt="Analysis Chart {i}" class="chart-image">
    <p class="chart-description">{pattern}: Generated from data analysis</p>
</div>'''
                        processed_content = processed_content.replace(pattern, chart_html)
            
            return processed_content
            
        except Exception as e:
            print(f"⚠️ Error post-processing section: {e}")
            return content
    
    def _check_dependencies_met(self, section: Dict[str, Any], completed_sections: Dict[str, Dict[str, Any]]) -> bool:
        """Check if all dependencies for a section are met"""
        dependencies = section.get("dependencies", [])
        return all(dep in completed_sections for dep in dependencies)
    
    def _clean_html_content(self, html_content: str) -> str:
        """Clean HTML content by removing escaped characters and fixing formatting"""
        import re
        
        # Remove literal \n characters
        cleaned = html_content.replace('\\n', '')
        
        # Remove escaped quotes
        cleaned = cleaned.replace('\\"', '"')
        
        # Remove other common escape characters
        cleaned = cleaned.replace('\\t', '')
        cleaned = cleaned.replace('\\r', '')
        
        # Fix multiple spaces
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Fix spacing around HTML tags
        cleaned = re.sub(r'>\s+<', '><', cleaned)
        
        return cleaned
    
    def _combine_sections_into_html_report(self, report_structure: Dict[str, Any], 
                                         section_results: Dict[str, Dict[str, Any]], 
                                         user_query: str, image_sas_urls: List[str]) -> Dict[str, Any]:
        """
        STEP 3: Combine all generated sections into final HTML report
        """
        try:
            print("📋 Combining sections into final HTML report...")
            
            # Get report metadata from structure
            structure = report_structure.get("structure", {})
            report_title = structure.get("report_title", "Comprehensive Business Analysis Report")
            report_subtitle = structure.get("report_subtitle", "Data Analysis and Strategic Insights")
            
            # Professional HTML template with embedded CSS
            html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report_title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
            background: #f8f9fa;
        }}
        .report-container {{
            background: white;
            padding: 3rem;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #2c3e50;
            padding-bottom: 2rem;
            margin-bottom: 3rem;
        }}
        .header h1 {{
            color: #1a472a;
            font-size: 2.5rem;
            margin: 0;
            font-weight: 700;
        }}
        .header h2 {{
            color: #666;
            font-size: 1.3rem;
            margin: 0.5rem 0 0 0;
            font-weight: 400;
        }}
        .metadata {{
            background: #f8f9fa;
            padding: 1.5rem;
            border-radius: 8px;
            margin: 2rem 0;
            border-left: 4px solid #3498db;
        }}
        .metadata strong {{
            color: #2c3e50;
        }}
        .toc {{
            background: #f8f9fa;
            padding: 2rem;
            border-radius: 8px;
            margin: 2rem 0;
        }}
        .toc h3 {{
            color: #2c3e50;
            margin-top: 0;
            border-bottom: 2px solid #3498db;
            padding-bottom: 0.5rem;
        }}
        .toc-list {{
            list-style: none;
            padding: 0;
        }}
        .toc-item {{
            display: flex;
            justify-content: space-between;
            padding: 0.5rem 0;
            border-bottom: 1px dotted #ccc;
        }}
        .toc-item:last-child {{
            border-bottom: none;
        }}
        .section-container {{
            margin: 3rem 0;
            page-break-inside: avoid;
        }}
        .section-title {{
            color: #2c3e50;
            font-size: 1.8rem;
            margin: 2rem 0 1rem 0;
            border-left: 5px solid #3498db;
            padding-left: 1rem;
            page-break-after: avoid;
        }}
        .section-content {{
            margin-left: 1rem;
        }}
        .insight-box {{
            background: #e8f4fd;
            border-left: 5px solid #3498db;
            padding: 1.5rem;
            margin: 1.5rem 0;
            border-radius: 0 8px 8px 0;
        }}
        .insight-box h3 {{
            color: #2c3e50;
            margin-top: 0;
        }}
        .metric-highlight {{
            background: #3498db;
            color: white;
            padding: 2px 6px;
            border-radius: 3px;
            font-weight: bold;
        }}
        .recommendation-item {{
            background: #f8f9fa;
            border: 1px solid #ddd;
            border-radius: 6px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .recommendation-item h4 {{
            color: #2c3e50;
            margin-top: 0;
        }}
        .findings-list {{
            list-style: none;
            padding: 0;
        }}
        .finding-item {{
            background: #f8f9fa;
            padding: 1rem;
            margin: 0.5rem 0;
            border-left: 4px solid #27ae60;
            border-radius: 0 4px 4px 0;
        }}
        .chart-container {{
            margin: 2rem 0;
            text-align: center;
            background: #f8f9fa;
            padding: 1.5rem;
            border-radius: 8px;
        }}
        .chart-image {{
            max-width: 100%;
            height: auto;
            border-radius: 6px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .chart-description {{
            margin-top: 1rem;
            font-style: italic;
            color: #666;
        }}
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin: 2rem 0;
        }}
        .kpi-card {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 1.5rem;
            border-radius: 8px;
            text-align: center;
        }}
        .kpi-value {{
            font-size: 2rem;
            font-weight: bold;
            display: block;
        }}
        .kpi-label {{
            font-size: 0.9rem;
            margin-top: 0.5rem;
        }}
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1.5rem 0;
            background: white;
        }}
        .data-table th {{
            background: #34495e;
            color: white;
            padding: 1rem;
            text-align: left;
        }}
        .data-table td {{
            padding: 0.8rem;
            border-bottom: 1px solid #eee;
        }}
        .data-table tr:nth-child(even) {{
            background: #f8f9fa;
        }}
        .footer {{
            margin-top: 4rem;
            padding-top: 2rem;
            border-top: 2px solid #ecf0f1;
            text-align: center;
            color: #7f8c8d;
            font-size: 0.9rem;
        }}
        @media print {{
            body {{ background: white; }}
            .report-container {{ box-shadow: none; }}
            .section-container {{ page-break-inside: avoid; }}
        }}
    </style>
</head>
<body>
    <div class="report-container">
        <div class="header">
            <h1>{report_title}</h1>
            <h2>{report_subtitle}</h2>
        </div>
        
        <div class="metadata">
            <p><strong>Generated:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            <p><strong>Analysis Query:</strong> {user_query}</p>
            <p><strong>Report Sections:</strong> {len(section_results)}</p>
            <p><strong>Visualizations:</strong> {len(image_sas_urls)}</p>
        </div>"""
            
            # Add table of contents
            html_content += """
        <div class="toc">
            <h3>Table of Contents</h3>
            <ul class="toc-list">"""
            
            for i, section in enumerate(report_structure.get("sections", []), 1):
                section_id = section.get("section_id", f"section_{i}")
                if section_id in section_results:
                    html_content += f"""
                <li class="toc-item">
                    <span>{i}. {section.get('title', 'Unknown Section')}</span>
                    <span>Page {i}</span>
                </li>"""
            
            html_content += """
            </ul>
        </div>
        
        <div style="border-top: 2px solid #ecf0f1; margin: 2rem 0;"></div>"""
            
            # Add each section in order
            for i, section in enumerate(report_structure.get("sections", []), 1):
                section_id = section.get("section_id", f"section_{i}")
                
                if section_id in section_results:
                    section_content = section_results[section_id].get("content", "")
                    
                    # Clean up the section content (ensure proper HTML)
                    section_content = self._convert_section_to_html(section_content, section, image_sas_urls)
                    
                    html_content += f"""
        {section_content}"""
                else:
                    # Add placeholder for missing sections
                    html_content += f"""
        <div class="section-container">
            <h2 class="section-title">{section.get('title', 'Missing Section')}</h2>
            <div class="section-content">
                <p><em>This section could not be generated due to processing limitations.</em></p>
            </div>
        </div>"""
            
            # Add footer with generation details
            html_content += f"""
        
        <div class="footer">
            <h3>Report Generation Details</h3>
            <p><strong>Generation Method:</strong> Structured Iterative Assistant Sections</p>
            <p><strong>Sections Successfully Generated:</strong> {len([s for s in section_results.values() if s.get('success')])}</p>
            <p><strong>Total Content Length:</strong> {len(html_content):,} characters</p>
            <p><strong>Generation Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><em>This report was generated using advanced AI-powered analysis with structured section-by-section generation for maximum detail and accuracy.</em></p>
        </div>
        
    </div>
</body>
</html>"""
            html_content = self._clean_html_content(html_content)
            
            return {
                "success": True,
                "content": html_content,
                "sections_included": len(section_results),
                "total_length": len(html_content),
                "structure_used": structure,
                "generation_metadata": {
                    "method": "iterative_html_sections",
                    "timestamp": datetime.now().isoformat(),
                    "sections_generated": len(section_results),
                    "successful_sections": len([s for s in section_results.values() if s.get("success")])
                }
            }
            
        except Exception as e:
            print(f"❌ Error combining HTML sections: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": "<html><body><h1>Error generating HTML report</h1></body></html>",
                "sections_included": 0
            }
    
    def _convert_section_to_html(self, section_content: str, section: Dict[str, Any], image_sas_urls: List[str]) -> str:
        """Convert section content to proper HTML format"""
        try:
            # If content is already properly structured HTML, return as is
            if "<div class=\"section-container\">" in section_content:
                return section_content
            
            # If content is HTML but not properly wrapped, clean it up
            if "<h2" in section_content or "<div" in section_content:
                section_title = section.get('title', 'Section')
                if not section_content.startswith('<div class="section-container">'):
                    if not section_content.startswith(f'<h2 class="section-title">{section_title}</h2>'):
                        section_content = f'<h2 class="section-title">{section_title}</h2>\n<div class="section-content">\n{section_content}\n</div>'
                    section_content = f'<div class="section-container">\n{section_content}\n</div>'
                return section_content
            
            # If content is markdown or plain text, convert to HTML
            html_section = f'''<div class="section-container">
    <h2 class="section-title">{section.get('title', 'Section')}</h2>
    <div class="section-content">'''
            
            # Split content into paragraphs
            paragraphs = section_content.split('\n\n')
            
            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue
                
                # Handle different content types
                if para.startswith('•') or para.startswith('-') or para.startswith('*'):
                    # Convert to list
                    items = [item.strip().lstrip('•-* ') for item in para.split('\n') if item.strip()]
                    html_section += '\n        <ul class="findings-list">'
                    for item in items:
                        # Highlight metrics
                        item = self._highlight_metrics(item)
                        html_section += f'\n            <li class="finding-item">{item}</li>'
                    html_section += '\n        </ul>'
                    
                elif 'Chart:' in para or 'Image:' in para:
                    # Handle chart references
                    parts = para.split('Chart:')
                    if len(parts) > 1:
                        chart_url = parts[1].strip().split()[0]
                        description = parts[0].strip() if parts[0].strip() else "Analysis visualization"
                        html_section += f'''
        <div class="chart-container">
            <img src="{chart_url}" alt="Analysis Chart" class="chart-image">
            <p class="chart-description">{description}</p>
        </div>'''
                    else:
                        html_section += f'\n        <p>{self._highlight_metrics(para)}</p>'
                        
                elif any(keyword in para.lower() for keyword in ['recommendation', 'suggest', 'should', 'implement']):
                    # Style as recommendation
                    html_section += f'\n        <div class="recommendation-item"><p>{self._highlight_metrics(para)}</p></div>'
                    
                elif any(keyword in para.lower() for keyword in ['key finding', 'insight', 'important', 'significant']):
                    # Style as insight box
                    html_section += f'\n        <div class="insight-box"><p>{self._highlight_metrics(para)}</p></div>'
                    
                else:
                    # Regular paragraph
                    html_section += f'\n        <p>{self._highlight_metrics(para)}</p>'
            
            html_section += '\n    </div>\n</div>'
            return html_section
            
        except Exception as e:
            print(f"⚠️ Error converting section to HTML: {e}")
            return f'''<div class="section-container">
    <h2 class="section-title">{section.get('title', 'Section')}</h2>
    <div class="section-content"><p>{section_content}</p></div>
</div>'''
    
    def _highlight_metrics(self, text: str) -> str:
        """Highlight numbers and metrics in text"""
        # Highlight percentages, currency, and large numbers
        text = re.sub(r'\b(\d+(?:,\d{3})*(?:\.\d+)?%)\b', r'<span class="metric-highlight">\1</span>', text)
        text = re.sub(r'\b(\$\d+(?:,\d{3})*(?:\.\d+)?[KMB]?)\b', r'<span class="metric-highlight">\1</span>', text)
        text = re.sub(r'\b(\d+(?:,\d{3})+)\b', r'<span class="metric-highlight">\1</span>', text)
        return text
    
    def _format_final_html_report(self, final_report: Dict[str, Any], image_sas_urls: List[str]) -> Dict[str, Any]:
        """
        STEP 4: Apply final HTML formatting and enhancements to the report
        """
        try:
            print("🎨 Applying final HTML formatting to report...")
            
            content = final_report.get("content", "")
            
            # Ensure all image URLs are properly embedded in HTML
            formatted_content = self._ensure_html_image_urls_embedded(content, image_sas_urls)
            
            # Apply additional HTML enhancements
            formatted_content = self._apply_html_enhancements(formatted_content)
            
            # Validate HTML report structure
            validation_result = self._validate_html_report_structure(formatted_content)
            
            return {
                "content": formatted_content,
                "formatting_applied": True,
                "image_urls_embedded": len(image_sas_urls),
                "validation_passed": validation_result.get("valid", False),
                "validation_details": validation_result,
                "final_length": len(formatted_content),
                "formatting_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"⚠️ Error in final HTML formatting: {e}")
            return {
                "content": final_report.get("content", ""),
                "formatting_applied": False,
                "error": str(e)
            }
    
    def _ensure_html_image_urls_embedded(self, content: str, image_sas_urls: List[str]) -> str:
        """Ensure all image URLs are properly embedded in HTML content"""
        try:
            formatted_content = content
            
            # Track which URLs have been embedded
            embedded_urls = set()
            
            for i, url in enumerate(image_sas_urls, 1):
                if url in formatted_content:
                    embedded_urls.add(url)
                else:
                    # Look for placeholder chart containers and add missing images
                    chart_patterns = [
                        f"Chart {i}",
                        f"Figure {i}",
                        f"Visualization {i}",
                        f"Image {i}"
                    ]
                    
                    for pattern in chart_patterns:
                        if pattern in formatted_content and url not in formatted_content:
                            # Find location to insert chart
                            pattern_location = formatted_content.find(pattern)
                            if pattern_location != -1:
                                # Insert chart HTML after the pattern
                                chart_html = f'''
            <div class="chart-container">
                <img src="{url}" alt="Analysis Chart {i}" class="chart-image">
                <p class="chart-description">Chart {i}: Generated from data analysis</p>
            </div>'''
                                # Insert after the current paragraph
                                insertion_point = formatted_content.find('</p>', pattern_location)
                                if insertion_point != -1:
                                    formatted_content = (formatted_content[:insertion_point + 4] + 
                                                       chart_html + 
                                                       formatted_content[insertion_point + 4:])
                                    embedded_urls.add(url)
                                    break
            
            # If some URLs weren't embedded, add them in a dedicated visualizations section
            missing_urls = [url for url in image_sas_urls if url not in embedded_urls]
            
            if missing_urls:
                # Find a good insertion point (before footer)
                footer_start = formatted_content.find('<div class="footer">')
                if footer_start != -1:
                    visualizations_html = '''
        <div class="section-container">
            <h2 class="section-title">Additional Visualizations</h2>
            <div class="section-content">'''
                    
                    for i, url in enumerate(missing_urls, 1):
                        visualizations_html += f'''
                <div class="chart-container">
                    <img src="{url}" alt="Additional Chart {i}" class="chart-image">
                    <p class="chart-description">Additional visualization {i} generated during analysis</p>
                </div>'''
                    
                    visualizations_html += '''
            </div>
        </div>'''
                    
                    # Insert before footer
                    formatted_content = (formatted_content[:footer_start] + 
                                       visualizations_html + 
                                       formatted_content[footer_start:])
            
            return formatted_content
            
        except Exception as e:
            print(f"⚠️ Error embedding HTML image URLs: {e}")
            return content
    
    def _apply_html_enhancements(self, content: str) -> str:
        """Apply additional HTML enhancements and optimizations"""
        try:
            enhanced_content = content
            
            # Ensure proper spacing and structure
            
            # Add responsive meta viewport if missing
            if '<meta name="viewport"' not in enhanced_content:
                enhanced_content = enhanced_content.replace(
                    '<meta charset="UTF-8">',
                    '<meta charset="UTF-8">  <meta name="viewport" content="width=device-width, initial-scale=1.0">'
                )
            
            # Enhance accessibility with alt texts and ARIA labels
            enhanced_content = re.sub(
                r'<img([^>]*?)alt=""([^>]*?)>',
                r'<img\1alt="Data analysis chart"\2>',
                enhanced_content
            )
            
            # Add print-friendly styles if not present
            if '@media print' not in enhanced_content:
                print_styles = '''
        @media print {
            body { background: white !important; }
            .report-container { box-shadow: none !important; }
            .section-container { page-break-inside: avoid; }
            .chart-container { page-break-inside: avoid; }
        }'''
                
                enhanced_content = enhanced_content.replace('</style>', print_styles + '\n    </style>')
            
            # Optimize for performance - add loading="lazy" to images below the fold
            chart_images = re.findall(r'<img[^>]*class="chart-image"[^>]*>', enhanced_content)
            for i, img_tag in enumerate(chart_images):
                if i > 2:  # Images after the first 3
                    if 'loading=' not in img_tag:
                        new_img_tag = img_tag.replace('<img', '<img loading="lazy"')
                        enhanced_content = enhanced_content.replace(img_tag, new_img_tag)
            
            return enhanced_content
            
        except Exception as e:
            print(f"⚠️ Error applying HTML enhancements: {e}")
            return content
    
    def _validate_html_report_structure(self, content: str) -> Dict[str, Any]:
        """Validate the HTML structure and completeness of the generated report"""
        try:
            validation = {
                "valid": True,
                "issues": [],
                "sections_found": 0,
                "has_doctype": False,
                "has_title": False,
                "has_css": False,
                "has_responsive_design": False,
                "images_embedded": 0,
                "estimated_file_size_kb": 0
            }
            
            # Check for proper HTML5 doctype
            if content.startswith('<!DOCTYPE html>'):
                validation["has_doctype"] = True
            else:
                validation["issues"].append("Missing HTML5 doctype")
            
            # Check for title tag
            if '<title>' in content and '</title>' in content:
                validation["has_title"] = True
            else:
                validation["issues"].append("Missing HTML title tag")
            
            # Check for embedded CSS
            if '<style>' in content and '</style>' in content:
                validation["has_css"] = True
            else:
                validation["issues"].append("Missing embedded CSS styles")
            
            # Check for responsive design
            if 'viewport' in content and 'device-width' in content:
                validation["has_responsive_design"] = True
            else:
                validation["issues"].append("Missing responsive design meta tag")
            
            # Count sections
            section_count = len(re.findall(r'class="section-title"', content))
            validation["sections_found"] = section_count
            
            if section_count < 5:
                validation["issues"].append(f"Low section count: {section_count}")
            
            # Count embedded images
            image_count = len(re.findall(r'<img[^>]*src="http', content))
            validation["images_embedded"] = image_count
            
            # Estimate file size
            validation["estimated_file_size_kb"] = round(len(content.encode('utf-8')) / 1024, 2)
            
            # Check minimum content length for comprehensive report
            if len(content) < 15000:  # Less than ~15KB
                validation["issues"].append("Report may be too short for comprehensive analysis")
            
            # Check for proper HTML structure
            required_elements = ['<html', '<head>', '<body>', '</html>']
            for element in required_elements:
                if element not in content:
                    validation["issues"].append(f"Missing required HTML element: {element}")
            
            # Overall validation
            validation["valid"] = len(validation["issues"]) == 0
            validation["quality_score"] = max(0, 100 - (len(validation["issues"]) * 10))
            
            return validation
            
        except Exception as e:
            print(f"⚠️ Error validating HTML report: {e}")
            return {"valid": False, "error": str(e)}
    
    def _get_fallback_structure(self, user_query: str, analysis_result: Dict[str, Any], 
                              image_sas_urls: List[str]) -> Dict[str, Any]:
        """Provide fallback structure when JSON generation fails"""
        
        fallback_sections = [
            {
                "section_id": "executive_summary",
                "title": "Executive Summary",
                "description": "High-level overview of key findings",
                "requirements": ["Summarize top findings", "Include business impact"],
                "data_sources": ["analysis_result"],
                "expected_length": "medium",
                "priority": 10,
                "dependencies": [],
                "content_type": "summary"
            },
            {
                "section_id": "business_context",
                "title": "Business Context and Analysis Scope",
                "description": "Background and objectives",
                "requirements": ["Explain business problem", "Define scope"],
                "data_sources": ["user_query"],
                "expected_length": "medium",
                "priority": 8,
                "dependencies": [],
                "content_type": "analysis"
            },
            {
                "section_id": "key_findings",
                "title": "Key Findings and Insights",
                "description": "Primary analytical findings",
                "requirements": ["Present key findings", "Include supporting data"],
                "data_sources": ["analysis_result", "dataframes"],
                "expected_length": "long",
                "priority": 9,
                "dependencies": [],
                "content_type": "analysis"
            },
            {
                "section_id": "detailed_analysis",
                "title": "Detailed Analysis and Visualizations",
                "description": "In-depth analysis with charts",
                "requirements": ["Reference visualizations", "Explain insights"],
                "data_sources": ["visualizations", "dataframes"],
                "expected_length": "long",
                "priority": 8,
                "dependencies": ["key_findings"],
                "content_type": "visualization"
            },
            {
                "section_id": "recommendations",
                "title": "Strategic Recommendations",
                "description": "Actionable business recommendations",
                "requirements": ["Provide specific recommendations", "Include priorities"],
                "data_sources": ["key_findings"],
                "expected_length": "long",
                "priority": 9,
                "dependencies": ["key_findings"],
                "content_type": "recommendation"
            },
            {
                "section_id": "implementation",
                "title": "Implementation Plan",
                "description": "Implementation roadmap and next steps",
                "requirements": ["Timeline", "Resource requirements"],
                "data_sources": ["recommendations"],
                "expected_length": "medium",
                "priority": 7,
                "dependencies": ["recommendations"],
                "content_type": "recommendation"
            }
        ]
        
        return {
            "success": True,
            "structure": {
                "report_title": "Comprehensive Business Analysis Report",
                "report_subtitle": "Data Analysis and Strategic Insights",
                "sections": fallback_sections,
                "total_sections": len(fallback_sections)
            },
            "sections": fallback_sections,
            "metadata": {
                "total_sections": len(fallback_sections),
                "generation_method": "fallback_structure",
                "timestamp": datetime.now().isoformat()
            }
        }
    
    def _generate_fallback_section(self, section: Dict[str, Any], analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback content when section generation fails"""
        
        section_id = section.get("section_id", "unknown")
        section_title = section.get("title", "Unknown Section")
        
        fallback_content = f'''<div class="section-container">
    <h2 class="section-title">{section_title}</h2>
    <div class="section-content">
        <p>This section analyzes the {section.get('description', 'data analysis results')}.</p>
        
        <div class="insight-box">
            <h3>Key Points</h3>
            <p>Based on the analysis performed, the following insights have been identified:</p>
            <ul class="findings-list">
                <li class="finding-item">The analysis has been completed successfully</li>
                <li class="finding-item">Key data patterns have been identified in the dataset</li>
                <li class="finding-item">Statistical relationships have been examined</li>
                <li class="finding-item">Business implications have been considered</li>
            </ul>
        </div>
        
        <p>{section.get('description', 'This section provides important insights for business decision-making.')}</p>
        
        <p><em>Note: This section was generated using fallback content due to processing limitations.</em></p>
    </div>
</div>'''
        
        return {
            "success": True,
            "content": fallback_content,
            "section_id": section_id,
            "title": section_title,
            "generation_method": "fallback",
            "length": len(fallback_content)
        }
    
    def _fallback_html_report_generation(self, user_query: str, analysis_result: Dict[str, Any], 
                                       image_sas_urls: List[str]) -> Dict[str, Any]:
        """Complete fallback HTML report generation when structured approach fails"""
        
        print("🔄 Using fallback HTML report generation...")
        
        # Generate comprehensive fallback HTML report
        fallback_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Comprehensive Business Analysis Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
            background: #f8f9fa;
        }}
        .report-container {{
            background: white;
            padding: 3rem;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #2c3e50;
            padding-bottom: 2rem;
            margin-bottom: 3rem;
        }}
        .header h1 {{
            color: #1a472a;
            font-size: 2.5rem;
            margin: 0;
            font-weight: 700;
        }}
        .section-title {{
            color: #2c3e50;
            font-size: 1.8rem;
            margin: 2rem 0 1rem 0;
            border-left: 5px solid #3498db;
            padding-left: 1rem;
        }}
        .chart-container {{
            margin: 2rem 0;
            text-align: center;
            background: #f8f9fa;
            padding: 1.5rem;
            border-radius: 8px;
        }}
        .chart-image {{
            max-width: 100%;
            height: auto;
            border-radius: 6px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .insight-box {{
            background: #e8f4fd;
            border-left: 5px solid #3498db;
            padding: 1.5rem;
            margin: 1.5rem 0;
            border-radius: 0 8px 8px 0;
        }}
        .metric-highlight {{
            background: #3498db;
            color: white;
            padding: 2px 6px;
            border-radius: 3px;
            font-weight: bold;
        }}
        .recommendation-item {{
            background: #f8f9fa;
            border: 1px solid #ddd;
            border-radius: 6px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
    </style>
</head>
<body>
    <div class="report-container">
        <div class="header">
            <h1>Comprehensive Business Analysis Report</h1>
            <p><strong>Generated:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            <p><strong>Analysis Query:</strong> {user_query}</p>
        </div>
        
        <h2 class="section-title">Executive Summary</h2>
        <p>This report presents a comprehensive analysis of the provided dataset in response to the query: "{user_query}"</p>
        <div class="insight-box">
            <p>The analysis has identified key patterns and insights that can inform business decision-making and strategic planning.</p>
        </div>
        
        <h2 class="section-title">Key Findings</h2>
        <p>Based on the data analysis performed, several important findings have emerged:</p>
        <ul>
            <li>The dataset contains valuable information for business insights</li>
            <li>Statistical patterns have been identified and analyzed</li>
            <li>Visualizations have been generated to support the findings</li>
            <li>Actionable recommendations have been developed</li>
        </ul>
        
        <h2 class="section-title">Analysis Results</h2>
        <div class="insight-box">
            <h3>Primary Analysis</h3>
            <p>{analysis_result.get('response', 'The analysis has been completed successfully with comprehensive insights generated.')[:1000]}...</p>
        </div>
        
        <h2 class="section-title">Generated Visualizations</h2>
        <p>The analysis produced <span class="metric-highlight">{len(image_sas_urls)}</span> visualization(s) to support the findings:</p>"""
        
        for i, url in enumerate(image_sas_urls, 1):
            fallback_html += f"""
        <div class="chart-container">
            <img src="{url}" alt="Analysis Chart {i}" class="chart-image">
            <p><strong>Chart {i}:</strong> Generated visualization from data analysis</p>
        </div>"""
        
        fallback_html += f"""
        
        <h2 class="section-title">Data Tables and Results</h2>
        <div class="insight-box">
            <h3>Generated Data Assets</h3>
            <p>The analysis generated <span class="metric-highlight">{len(analysis_result.get('dataframes', {}))}</span> data table(s) with processed results and insights.</p>
            <p>These tables contain the analytical results that support the findings and recommendations presented in this report.</p>
        </div>
        
        <h2 class="section-title">Strategic Recommendations</h2>
        <div class="recommendation-item">
            <h3>1. Data-Driven Decision Making</h3>
            <p>Leverage the identified patterns for strategic planning and operational improvements.</p>
        </div>
        <div class="recommendation-item">
            <h3>2. Continuous Monitoring</h3>
            <p>Implement regular analysis of key metrics to track performance and identify trends.</p>
        </div>
        <div class="recommendation-item">
            <h3>3. Action Implementation</h3>
            <p>Execute recommendations based on the findings with clear timelines and ownership.</p>
        </div>
        <div class="recommendation-item">
            <h3>4. Performance Tracking</h3>
            <p>Monitor outcomes and adjust strategies based on performance indicators.</p>
        </div>
        
        <h2 class="section-title">Implementation Plan</h2>
        <div class="insight-box">
            <h3>Next Steps</h3>
            <p>To maximize the value of these insights:</p>
            <ul>
                <li>Review findings with key stakeholders within the next week</li>
                <li>Prioritize recommendations based on business impact and resource availability</li>
                <li>Develop detailed implementation timeline with milestones</li>
                <li>Establish monitoring and evaluation processes for continuous improvement</li>
            </ul>
        </div>
        
        <h2 class="section-title">Risk Assessment</h2>
        <p>Key risks and mitigation strategies have been identified:</p>
        <div class="recommendation-item">
            <h4>Data Quality Risk</h4>
            <p>Ensure ongoing data validation and quality control processes.</p>
        </div>
        <div class="recommendation-item">
            <h4>Implementation Risk</h4>
            <p>Establish clear project management and change management protocols.</p>
        </div>
        
        <h2 class="section-title">Conclusion</h2>
        <p>This comprehensive analysis provides a solid foundation for data-driven business decisions. The findings should be reviewed by stakeholders and incorporated into strategic planning processes.</p>
        <div class="insight-box">
            <p><strong>Key Takeaway:</strong> The analysis demonstrates significant opportunities for business improvement through data-driven insights and strategic implementation.</p>
        </div>
        
        <div style="margin-top: 3rem; padding-top: 2rem; border-top: 2px solid #ecf0f1; text-align: center; color: #7f8c8d;">
            <p><strong>Report Generation Details</strong></p>
            <p>Method: Fallback structured HTML generation | Sections: 8 core sections | Visualizations: {len(image_sas_urls)} | Generated: {datetime.now().isoformat()}</p>
        </div>
        
    </div>
</body>
</html>"""
        
        return {
            "success": True,
            "html_report": fallback_html,
            "embedded_images": image_sas_urls,
            "report_type": "fallback_structured_html_report",
            "sections_generated": 8,
            "generation_method": "fallback_html"
        }


# Integration functions for Enhanced Analyzer

def integrate_structured_html_report_generator(enhanced_analyzer_class):
    """
    Integration function to add structured HTML report generation to EnhancedStreamingAnalyzer
    """
    
    def _generate_structured_html_report_with_sections(self, user_query: str, analysis_result: Dict[str, Any], 
                                                     image_sas_urls: List[str]) -> Dict[str, Any]:
        """
        NEW METHOD: Generate structured HTML report using iterative section generation
        
        This replaces the existing _generate_plain_text_report_with_images method
        with HTML output that matches your frontend expectations.
        """
        try:
            self.emit_stream('status', '🏗️ Initializing structured HTML report generation...')
            
            # Initialize structured report generator
            structured_generator = StructuredReportGenerator(
                self.assistant_manager,
                self.thread_manager, 
                self.session_id
            )
            
            # Generate comprehensive structured HTML report
            self.emit_stream('status', '📋 Generating HTML report structure and sections...')
            
            report_result = structured_generator.generate_comprehensive_report(
                user_query,
                analysis_result,
                image_sas_urls
            )
            
            if report_result.get("success"):
                self.emit_stream('status', '✅ Structured HTML report generation completed!')
                
                # Stream the final HTML report (matching your existing frontend structure)
                self.emit_stream('report', {
                    'type': 'structured_comprehensive_html_report',
                    'html': report_result.get("html_report", ""),  # HTML content for frontend
                    'images': image_sas_urls,
                    'sections_generated': report_result.get("sections_generated", 0),
                    'generation_method': 'structured_iterative_html_sections'
                })
                
                # Return in the format expected by your existing code
                return {
                    "success": True,
                    "plain_text_report": report_result.get("html_report", ""),  # Actually HTML content
                    "embedded_images": image_sas_urls,
                    "report_type": "structured_iterative_html_report",
                    "sections_generated": report_result.get("sections_generated", 0),
                    "generation_method": "structured_html_sections"
                }
            else:
                # Fallback to original method
                self.emit_stream('status', '⚠️ Structured HTML generation failed, using fallback...')
                return self._original_generate_plain_text_report_with_images(
                    user_query, analysis_result, image_sas_urls
                )
                
        except Exception as e:
            print(f"❌ Error in structured HTML report generation: {e}")
            logging.exception("Structured HTML report generation failed")
            
            # Fallback to original method
            return self._original_generate_plain_text_report_with_images(
                user_query, analysis_result, image_sas_urls
            )
    
    # Add the new method to the class
    enhanced_analyzer_class._generate_structured_html_report_with_sections = _generate_structured_html_report_with_sections
    
    # Backup original method and replace
    if hasattr(enhanced_analyzer_class, '_generate_plain_text_report_with_images'):
        enhanced_analyzer_class._original_generate_plain_text_report_with_images = enhanced_analyzer_class._generate_plain_text_report_with_images
        enhanced_analyzer_class._generate_plain_text_report_with_images = _generate_structured_html_report_with_sections
    
    print("✅ Structured HTML report generator integrated into EnhancedStreamingAnalyzer")
    
    return enhanced_analyzer_class


# Example usage and testing function

def test_structured_report_generator():
    """
    Test function to validate the structured report generator
    """
    print("🧪 Testing Structured HTML Report Generator...")
    
    # Mock data for testing
    mock_user_query = "Analyze sales performance and generate strategic recommendations"
    mock_analysis_result = {
        "type": "fully_analytical",
        "success": True,
        "response": "Analysis completed successfully. Key findings include revenue growth of 15% and customer acquisition improvements.",
        "generated_code": "import pandas as pd\ndf_analysis = df.groupby('category').sum()",
        "dataframes": {
            "sales_summary": {
                "type": "dataframe",
                "shape": (100, 5),
                "columns": ["category", "revenue", "growth", "customers", "retention"]
            }
        }
    }
    mock_image_sas_urls = [
        "https://example.blob.core.windows.net/charts/revenue_chart.png?sas=token1",
        "https://example.blob.core.windows.net/charts/growth_chart.png?sas=token2"
    ]
    
    try:
        # Test fallback generation (since we don't have real assistants)
        generator = StructuredReportGenerator(None, None, "test_session")
        result = generator._fallback_html_report_generation(
            mock_user_query, 
            mock_analysis_result, 
            mock_image_sas_urls
        )
        
        if result.get("success"):
            html_content = result.get("html_report", "")
            print(f"✅ Test successful! Generated HTML report ({len(html_content)} characters)")
            print(f"📊 Embedded images: {len(mock_image_sas_urls)}")
            print(f"🔍 Contains charts: {'chart-container' in html_content}")
            print(f"🎨 Has styling: {'<style>' in html_content}")
            return True
        else:
            print("❌ Test failed: Report generation unsuccessful")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False


if __name__ == "__main__":
    # Run test if script is executed directly
    test_structured_report_generator()