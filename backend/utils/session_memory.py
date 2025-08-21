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