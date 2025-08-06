import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, Tuple, List, Optional
from pathlib import Path
import re

class EnhancedFileStructureDetector:
    """
    Intelligent file structure detection that handles poorly formatted files
    while maintaining backward compatibility with existing code.
    """
    
    def __init__(self):
        self.structure_cache = {}
        self.metadata_cache = {}
        
    def detect_and_load_file(self, file_path: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Main entry point that detects file structure and returns clean DataFrame.
        Returns (dataframe, metadata) tuple.
        
        This replaces the simple pd.read_csv/pd.read_excel calls.
        """
        try:
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext == '.csv':
                return self._process_csv_file(file_path)
            elif file_ext in ['.xlsx', '.xls', '.xlsm', '.xlsb']:
                return self._process_excel_file(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_ext}")
                
        except Exception as e:
            logging.error(f"Error processing file {file_path}: {e}")
            raise
    
    def _process_csv_file(self, file_path: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Process CSV files with intelligent structure detection."""
        
        # First pass: Read raw data to analyze structure
        try:
            raw_df = pd.read_csv(file_path, header=None, dtype=str, keep_default_na=False)
        except Exception as e:
            # Fallback with different encoding
            raw_df = pd.read_csv(file_path, header=None, dtype=str, keep_default_na=False, encoding='latin-1')
        
        # Detect structure
        structure_info = self._analyze_file_structure(raw_df)
        
        # Extract clean data
        clean_df = self._extract_clean_dataframe(raw_df, structure_info)
        
        # Generate metadata
        metadata = self._generate_file_metadata(clean_df, structure_info, file_path)
        
        return clean_df, metadata
    
    def _process_excel_file(self, file_path: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Process Excel files with intelligent structure detection."""
        
        # Read all sheets first to analyze
        try:
            excel_file = pd.ExcelFile(file_path)
            sheet_analyses = {}
            
            # Analyze each sheet
            for sheet_name in excel_file.sheet_names:
                try:
                    raw_df = pd.read_excel(file_path, sheet_name=sheet_name, header=None, dtype=str)
                    structure_info = self._analyze_file_structure(raw_df)
                    sheet_analyses[sheet_name] = {
                        'raw_df': raw_df,
                        'structure': structure_info,
                        'data_density': self._calculate_data_density(raw_df, structure_info)
                    }
                except Exception as e:
                    logging.warning(f"Could not analyze sheet {sheet_name}: {e}")
                    continue
            
            # Select best sheet (highest data density)
            if not sheet_analyses:
                raise ValueError("No readable sheets found in Excel file")
            
            best_sheet = max(sheet_analyses.items(), 
                           key=lambda x: x[1]['data_density'])[0]
            
            # Extract clean data from best sheet
            best_analysis = sheet_analyses[best_sheet]
            clean_df = self._extract_clean_dataframe(
                best_analysis['raw_df'], 
                best_analysis['structure']
            )
            
            # Generate metadata
            metadata = self._generate_file_metadata(
                clean_df, 
                best_analysis['structure'], 
                file_path,
                sheet_name=best_sheet,
                all_sheets=list(excel_file.sheet_names)
            )
            
            return clean_df, metadata
            
        except Exception as e:
            logging.error(f"Error processing Excel file: {e}")
            raise
    
    def _analyze_file_structure(self, raw_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze the structure of raw file data."""
        
        structure_info = {
            'total_rows': len(raw_df),
            'total_cols': len(raw_df.columns),
            'header_row': None,
            'data_start_row': None,
            'data_end_row': None,
            'empty_rows': [],
            'empty_cols': [],
            'merged_regions': [],
            'data_regions': [],
            'confidence_score': 0.0
        }
        
        # Find likely header row
        header_candidates = self._find_header_candidates(raw_df)
        structure_info['header_candidates'] = header_candidates
        
        if header_candidates:
            best_header = max(header_candidates.items(), key=lambda x: x[1]['score'])
            structure_info['header_row'] = best_header[0]
            structure_info['confidence_score'] = best_header[1]['score']
        
        # Find data boundaries
        if structure_info['header_row'] is not None:
            structure_info['data_start_row'] = structure_info['header_row'] + 1
            structure_info['data_end_row'] = self._find_data_end_row(
                raw_df, structure_info['data_start_row']
            )
        
        # Identify empty rows and columns
        structure_info['empty_rows'] = self._find_empty_rows(raw_df)
        structure_info['empty_cols'] = self._find_empty_columns(raw_df)
        
        # Find data regions
        structure_info['data_regions'] = self._identify_data_regions(raw_df, structure_info)
        
        return structure_info
    
    def _find_header_candidates(self, raw_df: pd.DataFrame) -> Dict[int, Dict[str, Any]]:
        """Find potential header rows and score them."""
        
        candidates = {}
        max_rows_to_check = min(20, len(raw_df))  # Check first 20 rows max
        
        for row_idx in range(max_rows_to_check):
            row_data = raw_df.iloc[row_idx]
            
            # Calculate header probability score
            score_components = {
                'text_ratio': self._calculate_text_ratio(row_data),
                'uniqueness': self._calculate_uniqueness_score(row_data),
                'position_bonus': self._calculate_position_bonus(row_idx),
                'pattern_consistency': self._check_pattern_consistency(raw_df, row_idx),
                'non_empty_ratio': self._calculate_non_empty_ratio(row_data)
            }
            
            # Weighted total score
            total_score = (
                score_components['text_ratio'] * 0.3 +
                score_components['uniqueness'] * 0.25 +
                score_components['position_bonus'] * 0.15 +
                score_components['pattern_consistency'] * 0.2 +
                score_components['non_empty_ratio'] * 0.1
            )
            
            candidates[row_idx] = {
                'score': total_score,
                'components': score_components,
                'row_content': row_data.tolist()
            }
        
        return candidates
    
    def _calculate_text_ratio(self, row_data: pd.Series) -> float:
        """Calculate ratio of text vs numeric values in row."""
        non_empty = row_data[row_data.str.strip() != '']
        if len(non_empty) == 0:
            return 0.0
        
        text_count = 0
        for val in non_empty:
            try:
                float(val)
            except (ValueError, TypeError):
                text_count += 1
        
        return text_count / len(non_empty)
    
    def _calculate_uniqueness_score(self, row_data: pd.Series) -> float:
        """Calculate uniqueness score (headers should be mostly unique)."""
        non_empty = row_data[row_data.str.strip() != '']
        if len(non_empty) == 0:
            return 0.0
        
        unique_count = len(set(non_empty))
        return unique_count / len(non_empty)
    
    def _calculate_position_bonus(self, row_idx: int) -> float:
        """Give bonus to rows closer to the top (but not row 0 if it's likely title)."""
        if row_idx == 0:
            return 0.5  # Might be title
        elif row_idx <= 5:
            return 1.0 - (row_idx * 0.1)  # Diminishing bonus for early rows
        else:
            return 0.1  # Very low bonus for late rows
    
    def _check_pattern_consistency(self, raw_df: pd.DataFrame, row_idx: int) -> float:
        """Check if rows below follow consistent data patterns."""
        if row_idx >= len(raw_df) - 2:
            return 0.0
        
        # Check next few rows for data consistency
        consistency_score = 0.0
        rows_to_check = min(5, len(raw_df) - row_idx - 1)
        
        header_row = raw_df.iloc[row_idx]
        non_empty_cols = [i for i, val in enumerate(header_row) if str(val).strip()]
        
        for check_row_idx in range(row_idx + 1, row_idx + 1 + rows_to_check):
            data_row = raw_df.iloc[check_row_idx]
            
            # Check if data appears in same columns as headers
            data_in_header_cols = sum(1 for i in non_empty_cols 
                                    if i < len(data_row) and str(data_row.iloc[i]).strip())
            
            if len(non_empty_cols) > 0:
                consistency_score += data_in_header_cols / len(non_empty_cols)
        
        return consistency_score / rows_to_check if rows_to_check > 0 else 0.0
    
    def _calculate_non_empty_ratio(self, row_data: pd.Series) -> float:
        """Calculate ratio of non-empty cells."""
        total_cells = len(row_data)
        non_empty_cells = len(row_data[row_data.str.strip() != ''])
        return non_empty_cells / total_cells if total_cells > 0 else 0.0
    
    def _find_data_end_row(self, raw_df: pd.DataFrame, start_row: int) -> int:
        """Find where the actual data ends."""
        if start_row >= len(raw_df):
            return len(raw_df)
        
        # Look for patterns that indicate end of data
        consecutive_empty = 0
        for row_idx in range(start_row, len(raw_df)):
            row_data = raw_df.iloc[row_idx]
            non_empty_count = len(row_data[row_data.str.strip() != ''])
            
            if non_empty_count == 0:
                consecutive_empty += 1
                if consecutive_empty >= 3:  # 3 consecutive empty rows = end of data
                    return row_idx - 2
            else:
                consecutive_empty = 0
        
        return len(raw_df)
    
    def _find_empty_rows(self, raw_df: pd.DataFrame) -> List[int]:
        """Identify completely empty rows."""
        empty_rows = []
        for idx, row in raw_df.iterrows():
            if row.str.strip().eq('').all():
                empty_rows.append(idx)
        return empty_rows
    
    def _find_empty_columns(self, raw_df: pd.DataFrame) -> List[int]:
        """Identify completely empty columns."""
        empty_cols = []
        for col_idx in range(len(raw_df.columns)):
            if raw_df.iloc[:, col_idx].str.strip().eq('').all():
                empty_cols.append(col_idx)
        return empty_cols
    
    def _identify_data_regions(self, raw_df: pd.DataFrame, structure_info: Dict) -> List[Dict]:
        """Identify distinct data regions in the file."""
        regions = []
        
        if structure_info['header_row'] is not None:
            main_region = {
                'type': 'main_data',
                'start_row': structure_info['header_row'],
                'end_row': structure_info['data_end_row'],
                'start_col': 0,
                'end_col': len(raw_df.columns),
                'description': 'Primary data table'
            }
            regions.append(main_region)
        
        return regions
    
    def _extract_clean_dataframe(self, raw_df: pd.DataFrame, structure_info: Dict) -> pd.DataFrame:
        """Extract and clean the main data table."""
        
        if structure_info['header_row'] is None:
            # Fallback: use first row as header
            logging.warning("No clear header detected, using first row")
            clean_df = raw_df.copy()
            clean_df.columns = [f"Column_{i}" if str(val).strip() == '' else str(val).strip() 
                              for i, val in enumerate(raw_df.iloc[0])]
            clean_df = clean_df.iloc[1:].reset_index(drop=True)
        else:
            header_row = structure_info['header_row']
            data_start = structure_info['data_start_row']
            data_end = structure_info['data_end_row']
            
            # Extract headers
            headers = raw_df.iloc[header_row]
            
            # Clean and create meaningful column names
            clean_headers = []
            for i, header in enumerate(headers):
                header_str = str(header).strip()
                if header_str == '' or header_str == 'nan':
                    # Check if there's data in this column
                    col_data = raw_df.iloc[data_start:data_end, i]
                    if col_data.str.strip().ne('').any():
                        clean_headers.append(f"Unnamed_Column_{i}")
                    else:
                        clean_headers.append(f"Empty_Column_{i}")
                else:
                    clean_headers.append(header_str)
            
            # Extract data
            data_df = raw_df.iloc[data_start:data_end].copy()
            data_df.columns = clean_headers
            
            # Remove completely empty columns
            non_empty_cols = []
            for col in data_df.columns:
                if data_df[col].str.strip().ne('').any():
                    non_empty_cols.append(col)
            
            clean_df = data_df[non_empty_cols].reset_index(drop=True)
        
        # Additional cleaning
        clean_df = self._apply_data_cleaning(clean_df)
        
        return clean_df
    
    def _apply_data_cleaning(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply intelligent data cleaning while preserving original data integrity."""
        
        cleaned_df = df.copy()
        
        # Clean each column based on its content pattern
        for col in cleaned_df.columns:
            col_data = cleaned_df[col].copy()
            
            # Remove leading/trailing whitespace
            col_data = col_data.str.strip()
            
            # Replace empty strings with NaN for better handling
            col_data = col_data.replace('', np.nan)
            
            # Try to detect and convert numeric columns
            if self._is_likely_numeric_column(col_data):
                # Clean numeric data
                col_data = col_data.str.replace(',', '')  # Remove thousands separators
                col_data = col_data.str.replace('$', '')  # Remove currency symbols
                col_data = col_data.str.replace('%', '')  # Remove percentage symbols
                col_data = col_data.str.replace('(', '-').str.replace(')', '')  # Handle negative numbers
                
                # Convert to numeric
                cleaned_df[col] = pd.to_numeric(col_data, errors='coerce')
            else:
                cleaned_df[col] = col_data
        
        return cleaned_df
    
    def _is_likely_numeric_column(self, series: pd.Series) -> bool:
        """Determine if a column likely contains numeric data."""
        non_null_series = series.dropna()
        if len(non_null_series) == 0:
            return False
        
        # Sample some values to test
        sample_size = min(10, len(non_null_series))
        sample_data = non_null_series.head(sample_size)
        
        numeric_count = 0
        for val in sample_data:
            # Clean the value and try to convert
            clean_val = str(val).strip().replace(',', '').replace('$', '').replace('%', '')
            clean_val = clean_val.replace('(', '-').replace(')', '')
            
            try:
                float(clean_val)
                numeric_count += 1
            except (ValueError, TypeError):
                continue
        
        # If more than 70% of sample values are numeric, consider it numeric
        return (numeric_count / sample_size) > 0.7
    
    def _calculate_data_density(self, raw_df: pd.DataFrame, structure_info: Dict) -> float:
        """Calculate data density score for sheet selection."""
        if structure_info['data_start_row'] is None:
            return 0.0
        
        data_region = raw_df.iloc[
            structure_info['data_start_row']:structure_info['data_end_row']
        ]
        
        total_cells = data_region.size
        non_empty_cells = (data_region.str.strip() != '').sum().sum()
        
        return non_empty_cells / total_cells if total_cells > 0 else 0.0
    
    def _generate_file_metadata(self, clean_df: pd.DataFrame, structure_info: Dict, 
                              file_path: str, sheet_name: str = None, 
                              all_sheets: List[str] = None) -> Dict[str, Any]:
        """Generate comprehensive metadata for the processed file."""
        
        metadata = {
            'file_info': {
                'path': file_path,
                'name': Path(file_path).name,
                'extension': Path(file_path).suffix.lower(),
                'sheet_name': sheet_name,
                'all_sheets': all_sheets
            },
            'structure_analysis': structure_info,
            'data_summary': {
                'shape': clean_df.shape,
                'columns': list(clean_df.columns),
                'numeric_columns': list(clean_df.select_dtypes(include=[np.number]).columns),
                'categorical_columns': list(clean_df.select_dtypes(include=['object']).columns),
                'date_columns': self._detect_date_columns(clean_df),
                'missing_data_summary': dict(clean_df.isnull().sum()),
                'data_types': dict(clean_df.dtypes.astype(str))
            },
            'quality_metrics': {
                'completeness': 1 - (clean_df.isnull().sum().sum() / clean_df.size),
                'structure_confidence': structure_info.get('confidence_score', 0.0),
                'column_utilization': len([col for col in clean_df.columns 
                                         if not clean_df[col].isnull().all()]) / len(clean_df.columns)
            },
            'processing_notes': []
        }
        
        # Add processing notes
        if structure_info['header_row'] != 0:
            metadata['processing_notes'].append(
                f"Header detected at row {structure_info['header_row']} instead of row 0"
            )
        
        if structure_info['empty_rows']:
            metadata['processing_notes'].append(
                f"Removed {len(structure_info['empty_rows'])} empty rows"
            )
        
        if structure_info['empty_cols']:
            metadata['processing_notes'].append(
                f"Removed {len(structure_info['empty_cols'])} empty columns"
            )
        
        return metadata
    
    def _detect_date_columns(self, df: pd.DataFrame) -> List[str]:
        """Detect columns that likely contain date data."""
        date_columns = []
        
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ['date', 'time', 'year', 'month', 'day']):
                date_columns.append(col)
                continue
            
            # Try to convert a sample to datetime
            sample_data = df[col].dropna().head(10)
            if len(sample_data) > 0:
                try:
                    pd.to_datetime(sample_data, errors='raise')
                    date_columns.append(col)
                except:
                    continue
        
        return date_columns