"""
Session Memory Management for Chart Persistence
Handles saving and loading session history with chart URLs for report generation
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

class SessionMemoryManager:
    """
    Manages session memory to persist charts and analysis results across queries.
    Enables reports to include actual chart images from previous queries.
    """
    
    def __init__(self, session_id: str, storage_path: str = None):
        self.session_id = session_id
        self.storage_path = storage_path or os.path.join("sessions", session_id)
        self.memory_file = os.path.join(self.storage_path, "session_history.json")
        
        # Ensure storage directory exists
        os.makedirs(self.storage_path, exist_ok=True)
        
        # Initialize memory structure
        self.memory = self._load_memory()
    
    def _load_memory(self) -> Dict[str, Any]:
        """Load existing session memory or create new one"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logging.warning(f"Failed to load session memory: {e}")
        
        # Default memory structure
        return {
            "session_id": self.session_id,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "queries": [],
            "total_charts": 0,
            "total_queries": 0
        }
    
    def _save_memory(self):
        """Save memory to disk"""
        try:
            self.memory["last_updated"] = datetime.now().isoformat()
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.memory, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Failed to save session memory: {e}")
    
    def add_query_result(self, query: str, analysis_result: Dict[str, Any], 
                        chart_urls: List[str], generated_code: str = None):
        """
        Add a new query result to session memory
        
        Args:
            query: The user's query
            analysis_result: The analysis result dictionary
            chart_urls: List of chart blob URLs generated
            generated_code: The code that was generated (optional)
        """
        # Filter out URLs that are already in session memory to avoid duplicates
        existing_urls = self.get_all_chart_urls()
        new_chart_urls = [url for url in chart_urls if url not in existing_urls]
        
        if len(new_chart_urls) != len(chart_urls):
            print(f"[DEBUG] Session memory: Filtered out {len(chart_urls) - len(new_chart_urls)} duplicate URLs from previous queries")
            print(f"[DEBUG] New URLs only: {new_chart_urls}")
        
        query_entry = {
            "query_id": len(self.memory["queries"]) + 1,
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "chart_urls": new_chart_urls,  # Store only new URLs
            "chart_count": len(new_chart_urls),
            "analysis_summary": self._extract_analysis_summary(analysis_result),
            "generated_code": generated_code,
            "dataframes_info": self._extract_dataframes_info(analysis_result),
            "original_chart_count": len(chart_urls)  # Track original count for debugging
        }
        
        self.memory["queries"].append(query_entry)
        self.memory["total_charts"] += len(new_chart_urls)
        self.memory["total_queries"] += 1
        
        self._save_memory()
        logging.info(f"Added query result to session memory: {len(new_chart_urls)} new charts (filtered from {len(chart_urls)} total)")
    
    def _extract_analysis_summary(self, analysis_result: Dict[str, Any]) -> str:
        """Extract a summary of the analysis result"""
        if isinstance(analysis_result.get('response'), str):
            # Truncate long responses for memory efficiency
            response = analysis_result['response']
            return response[:500] + "..." if len(response) > 500 else response
        return "Analysis completed"
    
    def _extract_dataframes_info(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract DataFrame information from analysis result"""
        dataframes = analysis_result.get('dataframes', {})
        df_info = {}
        
        for name, df_data in dataframes.items():
            if isinstance(df_data, dict) and df_data.get('type') == 'dataframe':
                df_info[name] = {
                    "shape": df_data.get('shape', [0, 0]),
                    "columns": df_data.get('columns', [])
                }
            elif hasattr(df_data, 'shape'):
                df_info[name] = {
                    "shape": list(df_data.shape),
                    "columns": list(df_data.columns) if hasattr(df_data, 'columns') else []
                }
        
        return df_info
    
    def get_all_chart_urls(self) -> List[str]:
        """Get all chart URLs from the entire session"""
        all_urls = []
        for query_entry in self.memory["queries"]:
            all_urls.extend(query_entry.get("chart_urls", []))
        return all_urls
    
    def get_recent_chart_urls(self, limit: int = 10) -> List[str]:
        """Get chart URLs from recent queries"""
        recent_urls = []
        for query_entry in reversed(self.memory["queries"][-limit:]):
            recent_urls.extend(query_entry.get("chart_urls", []))
        return recent_urls
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get a summary of the entire session"""
        return {
            "session_id": self.session_id,
            "total_queries": self.memory["total_queries"],
            "total_charts": self.memory["total_charts"],
            "created_at": self.memory["created_at"],
            "last_updated": self.memory["last_updated"],
            "chart_urls": self.get_all_chart_urls(),
            "queries": [
                {
                    "query_id": q["query_id"],
                    "query": q["query"],
                    "timestamp": q["timestamp"],
                    "chart_count": q["chart_count"]
                }
                for q in self.memory["queries"]
            ]
        }
    
    def get_charts_for_report(self) -> List[Dict[str, Any]]:
        """Get all charts with context for report generation"""
        charts = []
        for query_entry in self.memory["queries"]:
            for i, url in enumerate(query_entry.get("chart_urls", [])):
                charts.append({
                    "url": url,
                    "query": query_entry["query"],
                    "timestamp": query_entry["timestamp"],
                    "query_id": query_entry["query_id"],
                    "chart_index": i + 1,
                    "description": f"Chart from: {query_entry['query'][:100]}..."
                })
        return charts
    
    def clear_session(self):
        """Clear all session memory"""
        self.memory = {
            "session_id": self.session_id,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "queries": [],
            "total_charts": 0,
            "total_queries": 0
        }
        self._save_memory()
        logging.info(f"Cleared session memory for {self.session_id}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics"""
        try:
            file_size = os.path.getsize(self.memory_file) if os.path.exists(self.memory_file) else 0
            return {
                "file_size_bytes": file_size,
                "file_size_kb": round(file_size / 1024, 2),
                "total_queries": self.memory["total_queries"],
                "total_charts": self.memory["total_charts"],
                "memory_file": self.memory_file
            }
        except Exception as e:
            logging.error(f"Failed to get memory stats: {e}")
            return {"error": str(e)}
        

     # session_memory.py - ADD this method to SessionMemoryManager class

    def get_comprehensive_session_data_for_report(self) -> Dict[str, Any]:
        """
        🎯 NEW: Get comprehensive session data specifically for sequential report generation.
        
        Returns all accumulated charts, analyses, and context needed for comprehensive reporting.
        """
        try:
            all_charts = []
            all_analyses = []
            total_dataframes = 0
            
            # Collect data from all queries in session
            for query_entry in self.memory["queries"]:
                # Add charts with enhanced context
                for i, url in enumerate(query_entry.get("chart_urls", [])):
                    all_charts.append({
                        "url": url,
                        "query": query_entry["query"],
                        "timestamp": query_entry["timestamp"],
                        "query_id": query_entry["query_id"],
                        "chart_index": i + 1,
                        "description": f"Chart from: {query_entry['query'][:100]}...",
                        "analysis_summary": query_entry.get("analysis_summary", "")
                    })
                
                # Add analysis summaries
                if query_entry.get("analysis_summary"):
                    all_analyses.append({
                        "query": query_entry["query"],
                        "summary": query_entry["analysis_summary"],
                        "timestamp": query_entry["timestamp"],
                        "dataframes_info": query_entry.get("dataframes_info", {}),
                        "chart_count": query_entry.get("chart_count", 0)
                    })
                    
                    # Count DataFrames
                    total_dataframes += len(query_entry.get("dataframes_info", {}))
            
            # Prepare comprehensive context
            comprehensive_data = {
                "session_id": self.session_id,
                "total_queries": len(self.memory["queries"]),
                "total_charts": len(all_charts),
                "total_analyses": len(all_analyses),
                "total_dataframes": total_dataframes,
                "session_timespan": {
                    "created_at": self.memory["created_at"],
                    "last_updated": self.memory["last_updated"]
                },
                "charts": all_charts,
                "analyses": all_analyses,
                "chart_urls": [chart["url"] for chart in all_charts],
                "session_summary": self._generate_session_summary()
            }
            
            logging.info(f"📊 Comprehensive session data prepared: {len(all_charts)} charts, {len(all_analyses)} analyses")
            return comprehensive_data
            
        except Exception as e:
            logging.error(f"❌ Error getting comprehensive session data: {e}")
            return {
                "session_id": self.session_id,
                "error": str(e),
                "charts": [],
                "analyses": [],
                "chart_urls": []
            }

    def _generate_session_summary(self) -> str:
        """Generate a narrative summary of the entire session for report context"""
        try:
            if not self.memory["queries"]:
                return "No previous analyses in this session."
            
            summary_parts = []
            summary_parts.append(f"This session contains {self.memory['total_queries']} analyses")
            summary_parts.append(f"with {self.memory['total_charts']} visualizations generated.")
            
            # Add query summaries
            for i, query_entry in enumerate(self.memory["queries"][-3:], 1):  # Last 3 queries
                summary_parts.append(f"Query {i}: {query_entry['query'][:80]}...")
                if query_entry.get("chart_count", 0) > 0:
                    summary_parts.append(f"  Generated {query_entry['chart_count']} charts.")
            
            return " ".join(summary_parts)
            
        except Exception as e:
            logging.error(f"❌ Error generating session summary: {e}")
            return "Session summary unavailable."

    def mark_query_as_sequential(self, query: str, phase: str):
        """
        🎯 NEW: Mark a query as part of sequential execution.
        
        Args:
            query: The original query
            phase: 'data_analysis' or 'report_generation'
        """
        try:
            # Find the latest query entry
            for query_entry in reversed(self.memory["queries"]):
                if query_entry["query"] == query:
                    if "sequential_execution" not in query_entry:
                        query_entry["sequential_execution"] = {
                            "is_sequential": True,
                            "phases": []
                        }
                    
                    query_entry["sequential_execution"]["phases"].append({
                        "phase": phase,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    self._save_memory()
                    logging.info(f"🔄 Marked query as sequential phase: {phase}")
                    break
                    
        except Exception as e:
            logging.error(f"❌ Error marking query as sequential: {e}")   