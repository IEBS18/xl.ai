# table_generator.py
"""
Table generation utilities for displaying pandas DataFrames in web interface
"""

import pandas as pd


def generate_tailwind_table(df):
    """
    Generate a clean, theme-aware HTML table that works with your ThemeProvider
    """
    
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
    """
    Generate a minimal, clean table for better theme compatibility
    """
    
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


def format_value_for_display(val):
    """
    Format a single value for display in tables
    """
    if pd.isna(val):
        return '<span class="text-gray-400 dark:text-gray-500 italic">—</span>'
    elif isinstance(val, bool):
        if val:
            return '<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200">True</span>'
        else:
            return '<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200">False</span>'
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
        
        return f'<span class="font-mono text-gray-900 dark:text-white">{display_num}</span>'
    else:
        # String values
        str_val = str(val)
        if len(str_val) > 30:
            return f'<span class="text-gray-900 dark:text-white" title="{str_val}">{str_val[:27]}...</span>'
        else:
            return f'<span class="text-gray-900 dark:text-white">{str_val}</span>'