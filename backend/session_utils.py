"""
Session management utilities and stop signal handling
"""
import os
import time
import threading
from datetime import datetime
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np

# Global storage for stop signals per session
stop_signals = {}

class StopAnalysisException(Exception):
    """Custom exception for stopping analysis"""
    pass

def generate_tailwind_table(df):
    """Generate a clean, theme-aware HTML table that works with your ThemeProvider"""
    import pandas as pd
    
    # Limit rows for performance
    display_df = df.head(100) if len(df) > 100 else df
    total_rows = len(df)
    
    html = f'''
    <div class="w-full space-y-4">
        <!-- Table Info Header -->
        <div class="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 transition-all duration-300">
            <div class="flex items-center space-x-6">
                <div class="flex items-center space-x-2">
                    <div class="w-2 h-2 bg-blue-500 rounded-full"></div>
                    <span class="text-sm font-medium text-gray-900 dark:text-white">
                        {total_rows:,} rows
                    </span>
                </div>
                <div class="flex items-center space-x-2">
                    <div class="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span class="text-sm font-medium text-gray-900 dark:text-white">
                        {len(df.columns)} columns
                    </span>
                </div>
            </div>
            {f'<span class="text-xs px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full">Showing first {len(display_df)} rows</span>' if total_rows > 100 else ''}
        </div>
        
        <!-- Table Container -->
        <div class="bg-white dark:bg-black rounded-2xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden transition-all duration-300">
            <div class="overflow-x-auto">
                <table class="w-full">
                    <thead class="bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
                        <tr>
    '''
    
    # Add headers
    for col in df.columns:
        html += f'''
                            <th class="px-6 py-4 text-left text-sm font-semibold text-gray-900 dark:text-white">
                                {col}
                            </th>
        '''
    
    html += '''
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-200 dark:divide-gray-800">
    '''
    
    # Add rows
    for idx, row in display_df.iterrows():
        html += '''
                        <tr class="hover:bg-gray-50 dark:hover:bg-gray-900 transition-colors duration-150">
        '''
        
        for val in row:
            # Format values based on type
            if pd.isna(val):
                formatted_val = '<span class="text-gray-400 dark:text-gray-500 italic">—</span>'
            elif isinstance(val, bool):
                if val:
                    formatted_val = '<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200">True</span>'
                else:
                    formatted_val = '<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200">False</span>'
            elif isinstance(val, (int, float)) and not isinstance(val, bool):
                # Format numbers
                if isinstance(val, float):
                    if abs(val) >= 1000000:
                        display_num = f'{val/1000000:.1f}M'
                    elif abs(val) >= 1000:
                        display_num = f'{val/1000:.1f}K'
                    else:
                        display_num = f'{val:.2f}'
                else:
                    if abs(val) >= 1000000:
                        display_num = f'{val/1000000:.1f}M'
                    elif abs(val) >= 1000:
                        display_num = f'{val/1000:.1f}K'
                    else:
                        display_num = f'{val:,}'
                
                formatted_val = f'<span class="font-mono text-gray-900 dark:text-white">{display_num}</span>'
            else:
                # String values
                str_val = str(val)
                if len(str_val) > 30:
                    formatted_val = f'<span class="text-gray-900 dark:text-white" title="{str_val}">{str_val[:27]}...</span>'
                else:
                    formatted_val = f'<span class="text-gray-900 dark:text-white">{str_val}</span>'
            
            html += f'''
                            <td class="px-6 py-4 text-sm whitespace-nowrap">
                                {formatted_val}
                            </td>
            '''
        
        html += '''
                        </tr>
        '''
    
    html += '''
                    </tbody>
                </table>
            </div>
        </div>
    '''
    
    # Add pagination info if needed
    if total_rows > 100:
        html += f'''
        <div class="text-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-2xl border border-blue-200 dark:border-blue-800">
            <span class="text-sm text-blue-700 dark:text-blue-300">
                Showing {len(display_df)} of {total_rows:,} total rows
            </span>
        </div>
        '''
    
    html += '''
    </div>
    '''
    
    return html

def generate_simple_table(df):
    """Generate a minimal, clean table for better theme compatibility"""
    import pandas as pd
    
    display_df = df.head(50) if len(df) > 50 else df
    
    html = f'''
    <div class="w-full">
        <div class="mb-4 text-sm text-gray-600 dark:text-gray-400">
            {len(df)} rows × {len(df.columns)} columns
        </div>
        
        <div class="overflow-x-auto rounded-xl border border-gray-200 dark:border-gray-700">
            <table class="w-full bg-white dark:bg-black">
                <thead>
                    <tr class="bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
    '''
    
    # Simple headers
    for col in df.columns:
        html += f'''
                        <th class="px-4 py-3 text-left text-sm font-medium text-gray-900 dark:text-white">
                            {col}
                        </th>
        '''
    
    html += '''
                    </tr>
                </thead>
                <tbody>
    '''
    
    # Simple rows
    for idx, row in display_df.iterrows():
        bg_class = "bg-white dark:bg-black" if idx % 2 == 0 else "bg-gray-50 dark:bg-gray-900"
        html += f'''
                    <tr class="{bg_class} hover:bg-gray-100 dark:hover:bg-gray-800 border-b border-gray-100 dark:border-gray-800">
        '''
        
        for val in row:
            if pd.isna(val):
                cell_content = '<span class="text-gray-400">—</span>'
            else:
                cell_content = str(val)
            
            html += f'''
                        <td class="px-4 py-3 text-sm text-gray-900 dark:text-white">
                            {cell_content}
                        </td>
            '''
        
        html += '''
                    </tr>
        '''
    
    html += '''
                </tbody>
            </table>
        </div>
    </div>
    '''
    
    return html

def generate_intelligent_suggestions(df: pd.DataFrame) -> List[Dict[str, str]]:
    """Generate intelligent query suggestions based on DataFrame structure"""
    suggestions = []
    
    if df is None:
        return suggestions
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    date_cols = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
    
    suggestions.extend([
        {
            'category': 'Basic Analysis',
            'suggestion': 'Show me a summary of the data',
            'description': 'Get basic statistics and data overview'
        },
        {
            'category': 'Basic Analysis', 
            'suggestion': 'What are the data quality issues?',
            'description': 'Identify missing values, duplicates, and outliers'
        }
    ])
    
    if date_cols and numeric_cols:
        target_col = numeric_cols[0]
        suggestions.extend([
            {
                'category': 'Forecasting',
                'suggestion': f'Forecast {target_col} for the next 12 months',
                'description': 'Predict future values using time series models'
            },
            {
                'category': 'Forecasting',
                'suggestion': f'Predict {target_col} trends for next quarter',
                'description': 'Short-term forecasting with confidence intervals'
            }
        ])
    
    if date_cols and numeric_cols:
        suggestions.extend([
            {
                'category': 'Trend Analysis',
                'suggestion': f'Analyze trends in {numeric_cols[0]} over time',
                'description': 'Identify patterns and seasonal behavior'
            },
            {
                'category': 'Trend Analysis',
                'suggestion': 'Show growth rates and trend indicators',
                'description': 'Calculate growth metrics and trend directions'
            }
        ])
    
    if categorical_cols and numeric_cols:
        cat_col = categorical_cols[0]
        num_col = numeric_cols[0]
        suggestions.extend([
            {
                'category': 'Comparison',
                'suggestion': f'Compare {num_col} across {cat_col} categories',
                'description': 'Analyze performance differences between groups'
            },
            {
                'category': 'Comparison',
                'suggestion': f'Which {cat_col} has the highest {num_col}?',
                'description': 'Identify top performers and rankings'
            }
        ])
    
    if len(numeric_cols) > 1:
        suggestions.extend([
            {
                'category': 'Correlation',
                'suggestion': f'What is the correlation between {numeric_cols[0]} and {numeric_cols[1]}?',
                'description': 'Analyze relationships between variables'
            },
            {
                'category': 'Correlation',
                'suggestion': 'Find all strong correlations in the data',
                'description': 'Identify significant relationships across all variables'
            }
        ])
    
    suggestions.extend([
        {
            'category': 'Reporting',
            'suggestion': 'Generate a comprehensive business report',
            'description': 'Create detailed strategic analysis with insights'
        },
        {
            'category': 'Reporting',
            'suggestion': 'Create an executive summary of key findings',
            'description': 'High-level overview for leadership decision-making'
        }
    ])
    
    return suggestions

def stop_analysis_for_session(session_id: str):
    """Set stop signal for a specific session"""
    global stop_signals
    stop_signals[session_id] = True
    print(f"🛑 Stop signal set for session: {session_id}")

def clear_stop_signal_for_session(session_id: str):
    """Clear stop signal for a specific session"""
    global stop_signals
    if session_id in stop_signals:
        stop_signals[session_id] = False
    print(f"✅ Stop signal cleared for session: {session_id}")

def cleanup_session_data(session_id: str, session_data: dict, analyzers: dict):
    """Clean up session data and resources"""
    deleted_items = []
    
    # Remove from analyzers
    if session_id in analyzers:
        # Clean up any file handles or resources
        analyzer = analyzers[session_id]
        if hasattr(analyzer, 'cleanup'):
            analyzer.cleanup()
        del analyzers[session_id]
        deleted_items.append('analyzer')
        print(f"🗑️  Deleted analyzer for session: {session_id}")
    
    # Remove from session data
    if session_id in session_data:
        # Optionally clean up uploaded files
        file_path = session_data[session_id].get('filepath')
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                deleted_items.append('uploaded_file')
                print(f"🗑️  Deleted uploaded file: {file_path}")
            except Exception as e:
                print(f"⚠️  Could not delete file {file_path}: {e}")
        
        del session_data[session_id]
        deleted_items.append('session_data')
        print(f"🗑️  Deleted session data for: {session_id}")
    
    # Clear stop signals
    if session_id in stop_signals:
        del stop_signals[session_id]
        deleted_items.append('stop_signal')
        print(f"🗑️  Cleared stop signal for: {session_id}")
    
    return deleted_items

def is_session_inactive(session_info: dict, max_inactive_hours: float = 6.0) -> bool:
    """Check if a session is inactive based on last activity"""
    try:
        last_activity = session_info.get('last_activity', session_info.get('upload_time'))
        if not last_activity:
            return True
            
        last_activity_time = datetime.fromisoformat(last_activity)
        current_time = datetime.now()
        inactive_hours = (current_time - last_activity_time).total_seconds() / 3600
        
        return inactive_hours > max_inactive_hours
    except Exception as e:
        print(f"⚠️ Error checking session inactivity: {e}")
        return True  # Consider it inactive if we can't determine

def is_session_too_old(session_info: dict, max_age_hours: float = 24.0) -> bool:
    """Check if a session is too old based on upload time"""
    try:
        upload_time = session_info.get('upload_time')
        if not upload_time:
            return True
            
        upload_time_dt = datetime.fromisoformat(upload_time)
        current_time = datetime.now()
        age_hours = (current_time - upload_time_dt).total_seconds() / 3600
        
        return age_hours > max_age_hours
    except Exception as e:
        print(f"⚠️ Error checking session age: {e}")
        return True  # Consider it too old if we can't determine

def update_session_activity(session_id: str, session_data: dict):
    """Update last activity timestamp for a session"""
    if session_id in session_data:
        session_data[session_id]['last_activity'] = datetime.now().isoformat()
        return True
    return False

def get_session_stats(session_data: dict, analyzers: dict) -> dict:
    """Get comprehensive session statistics"""
    current_time = datetime.now()
    active_sessions = 0
    inactive_sessions = 0
    old_sessions = 0
    total_conversations = 0
    
    for session_id, session_info in session_data.items():
        # Check if session is active
        if is_session_inactive(session_info):
            inactive_sessions += 1
        else:
            active_sessions += 1
            
        # Check if session is old
        if is_session_too_old(session_info):
            old_sessions += 1
            
        # Count conversations
        if session_id in analyzers:
            total_conversations += len(analyzers[session_id].conversation_history.history)
    
    return {
        'total_sessions': len(session_data),
        'active_sessions': active_sessions,
        'inactive_sessions': inactive_sessions,
        'old_sessions': old_sessions,
        'total_conversations': total_conversations,
        'server_time': current_time.isoformat(),
        'analyzers_count': len(analyzers),
        'stop_signals_count': len(stop_signals)
    }

def validate_session_exists(session_id: str, analyzers: dict, session_data: dict) -> tuple[bool, str]:
    """Validate that a session exists and is properly initialized"""
    if not session_id:
        return False, "No session ID provided"
    
    if session_id not in analyzers:
        return False, f"Session {session_id} not found in analyzers"
    
    if session_id not in session_data:
        return False, f"Session {session_id} not found in session data"
    
    analyzer = analyzers[session_id]
    if analyzer.df is None:
        return False, f"Session {session_id} has no loaded data"
    
    return True, "Session is valid"

def create_session_summary(session_id: str, session_data: dict, analyzers: dict) -> dict:
    """Create a comprehensive session summary"""
    if session_id not in session_data or session_id not in analyzers:
        return {"error": "Session not found"}
    
    session_info = session_data[session_id]
    analyzer = analyzers[session_id]
    
    # Calculate session metrics
    current_time = datetime.now()
    upload_time = datetime.fromisoformat(session_info.get('upload_time', current_time.isoformat()))
    age_hours = (current_time - upload_time).total_seconds() / 3600
    
    last_activity = session_info.get('last_activity', session_info.get('upload_time'))
    last_activity_time = datetime.fromisoformat(last_activity)
    inactive_hours = (current_time - last_activity_time).total_seconds() / 3600
    
    # Get conversation history summary
    history_summary = analyzer.conversation_history.get_summary()
    
    # Get NLP statistics if available
    nlp_stats = {}
    if hasattr(analyzer, 'get_nlp_statistics'):
        try:
            nlp_stats = analyzer.get_nlp_statistics()
        except Exception as e:
            print(f"⚠️ Could not get NLP stats: {e}")
    
    return {
        'sessionId': session_id,
        'filename': session_info.get('filename'),
        'uploadTime': session_info.get('upload_time'),
        'lastActivity': last_activity,
        'ageHours': round(age_hours, 2),
        'inactiveHours': round(inactive_hours, 2),
        'shape': session_info.get('shape'),
        'columns': session_info.get('columns'),
        'conversationCount': len(analyzer.conversation_history.history),
        'createdBy': session_info.get('created_by', 'unknown'),
        'historySummary': history_summary,
        'isAnalyzing': getattr(analyzer, 'is_analyzing', False),
        'hasStopSignal': session_id in stop_signals and stop_signals[session_id],
        'langchainEnabled': getattr(analyzer.conversation_history, 'langchain_enabled', False),
        'nlpStats': nlp_stats
    }

# Session cleanup configuration
SESSION_CLEANUP_ENABLED = True
SESSION_MAX_AGE_HOURS = 24
SESSION_MAX_INACTIVE_HOURS = 24

def periodic_cleanup(session_data: dict, analyzers: dict):
    """Periodic cleanup of old sessions (runs in background)."""
    if not SESSION_CLEANUP_ENABLED:
        return
    
    try:
        print("🧹 Running periodic session cleanup...")
        
        sessions_to_delete = []
        current_time = datetime.now()
        
        for session_id in list(analyzers.keys()):
            if session_id in session_data:
                session_info = session_data[session_id]
                
                if (is_session_too_old(session_info, SESSION_MAX_AGE_HOURS) or 
                    is_session_inactive(session_info, SESSION_MAX_INACTIVE_HOURS)):
                    sessions_to_delete.append(session_id)
        
        # Clean up old sessions
        cleaned_count = 0
        for session_id in sessions_to_delete:
            try:
                deleted_items = cleanup_session_data(session_id, session_data, analyzers)
                if deleted_items:
                    cleaned_count += 1
                    print(f"🗑️  Auto-cleaned session: {session_id}")
            except Exception as e:
                print(f"⚠️  Failed to auto-clean session {session_id}: {e}")
        
        if cleaned_count > 0:
            print(f"🧹 Periodic cleanup completed: {cleaned_count} sessions cleaned")
        
    except Exception as e:
        print(f"❌ Periodic cleanup error: {e}")

def schedule_periodic_cleanup(session_data: dict, analyzers: dict):
    """Schedule periodic cleanup to run every 30 minutes."""
    def cleanup_loop():
        while True:
            time.sleep(1800)  # 30 minutes
            periodic_cleanup(session_data, analyzers)
    
    cleanup_thread = threading.Thread(target=cleanup_loop)
    cleanup_thread.daemon = True
    cleanup_thread.start()
    print("🕐 Scheduled periodic cleanup every 30 minutes")