import psycopg2
import pandas as pd
import sqlite3
import logging
from typing import Dict, Any, List
import os


class DatabaseConnector:
    """
    Database connector utility that handles connections to multiple database types
    and provides schema extraction and query execution capabilities.
    
    Based on the pattern from testdb.py but enhanced for production use.
    """
    
    def __init__(self):
        self.supported_databases = {
            'postgresql': self._connect_postgresql,
            'mysql': self._connect_mysql,
            'sqlite': self._connect_sqlite,
            'mssql': self._connect_mssql
        }
    
    def test_connection(self, params: Dict) -> Dict[str, Any]:
        """
        Test database connection and return status with basic info
        
        Args:
            params: Connection parameters dict with keys:
                - connection_type: Database type
                - host, port, database, username, password
        
        Returns:
            Dict with success status, message, and tables count
        """
        try:
            conn = self._create_connection(params)
            
            # Get basic table count
            tables_count = self._get_tables_count(conn, params['connection_type'])
            
            conn.close()
            
            return {
                'status': 'success',
                'message': f'Connected successfully to {params["connection_type"]} database',
                'tables_count': tables_count,
                'database_name': params.get('database', 'N/A')
            }
            
        except Exception as e:
            logging.error(f"Database connection test failed: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def get_database_schema(self, params: Dict) -> Dict[str, List[str]]:
        """
        Extract complete database schema information
        Returns schema in format: {'table_name': ['column (type)', ...]}
        
        Args:
            params: Connection parameters
            
        Returns:
            Dictionary mapping table names to column information
        """
        try:
            conn = self._create_connection(params)
            db_type = params['connection_type']
            
            if db_type == 'postgresql':
                schema = self._get_postgresql_schema(conn)
            elif db_type == 'mysql':
                schema = self._get_mysql_schema(conn, params['database'])
            elif db_type == 'sqlite':
                schema = self._get_sqlite_schema(conn)
            elif db_type == 'mssql':
                schema = self._get_mssql_schema(conn)
            else:
                raise ValueError(f"Unsupported database type: {db_type}")
            
            conn.close()
            
            logging.info(f"Extracted schema for {len(schema)} tables from {db_type}")
            return schema
            
        except Exception as e:
            logging.error(f"Schema extraction failed: {e}")
            raise
    
    def execute_query(self, params: Dict, sql_query: str) -> pd.DataFrame:
        """
        Execute SQL query and return results as pandas DataFrame
        
        Args:
            params: Connection parameters
            sql_query: SQL query string
            
        Returns:
            pandas DataFrame with query results
        """
        try:
            conn = self._create_connection(params)
            
            # Execute query and return as DataFrame
            df = pd.read_sql_query(sql_query, conn)
            
            conn.close()
            
            logging.info(f"Query executed successfully: {len(df)} rows returned")
            return df
            
        except Exception as e:
            logging.error(f"Query execution failed: {e}")
            raise
    
    def _create_connection(self, params: Dict):
        """Create database connection based on type"""
        db_type = params['connection_type']
        
        if db_type not in self.supported_databases:
            raise ValueError(f"Unsupported database type: {db_type}")
        
        return self.supported_databases[db_type](params)
    
    def _connect_postgresql(self, params: Dict):
        """Create PostgreSQL connection"""
        try:
            return psycopg2.connect(
                host=params['host'],
                database=params['database'],
                user=params['username'],
                password=params['password'],
                port=params.get('port', 5432),
                connect_timeout=10
            )
        except ImportError:
            raise ImportError("psycopg2 not installed. Install with: pip install psycopg2-binary")
        except Exception as e:
            raise ConnectionError(f"PostgreSQL connection failed: {str(e)}")
    
    def _connect_mysql(self, params: Dict):
        """Create MySQL connection"""
        try:
            import mysql.connector
            return mysql.connector.connect(
                host=params['host'],
                database=params['database'],
                user=params['username'],
                password=params['password'],
                port=params.get('port', 3306),
                connection_timeout=10
            )
        except ImportError:
            raise ImportError("mysql-connector-python not installed. Install with: pip install mysql-connector-python")
        except Exception as e:
            raise ConnectionError(f"MySQL connection failed: {str(e)}")
    
    def _connect_sqlite(self, params: Dict):
        """Create SQLite connection"""
        try:
            db_path = params.get('database', params.get('host', ':memory:'))
            return sqlite3.connect(db_path, timeout=10)
        except Exception as e:
            raise ConnectionError(f"SQLite connection failed: {str(e)}")
    
    def _connect_mssql(self, params: Dict):
        """Create SQL Server connection"""
        try:
            import pyodbc
            connection_string = f"""
            DRIVER={{ODBC Driver 17 for SQL Server}};
            SERVER={params['host']},{params.get('port', 1433)};
            DATABASE={params['database']};
            UID={params['username']};
            PWD={params['password']}
            """ 
            
            return pyodbc.connect(connection_string, timeout=10)
        except ImportError:
            raise ImportError("pyodbc not installed. Install with: pip install pyodbc")
        except Exception as e:
            raise ConnectionError(f"SQL Server connection failed: {str(e)}")
    
    def _get_tables_count(self, conn, db_type: str) -> int:
        """Get count of tables in database"""
        try:
            cursor = conn.cursor()
            
            if db_type == 'postgresql':
                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_schema='public' AND table_type='BASE TABLE'
                """)
            elif db_type == 'mysql':
                cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE()")
            elif db_type == 'sqlite':
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            elif db_type == 'mssql':
                cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'")
            else:
                return 0
            
            result = cursor.fetchone()
            return result[0] if result else 0
            
        except Exception as e:
            logging.warning(f"Could not get table count: {e}")
            return 0
    
    def _get_postgresql_schema(self, conn) -> Dict[str, List[str]]:
        """Extract PostgreSQL schema information (like testdb.py)"""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name, column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema='public'
            ORDER BY table_name, ordinal_position
        """)
        
        rows = cursor.fetchall()
        schema = {}
        
        for table, column, dtype, nullable in rows:
            null_info = "" if nullable == "YES" else " NOT NULL"
            column_info = f"{column} ({dtype}{null_info})"
            schema.setdefault(table, []).append(column_info)
        
        return schema
    
    def _get_mysql_schema(self, conn, database_name: str) -> Dict[str, List[str]]:
        """Extract MySQL schema information"""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name, column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = %s
            ORDER BY table_name, ordinal_position
        """, (database_name,))
        
        rows = cursor.fetchall()
        schema = {}
        
        for table, column, dtype, nullable in rows:
            null_info = "" if nullable == "YES" else " NOT NULL"
            column_info = f"{column} ({dtype}{null_info})"
            schema.setdefault(table, []).append(column_info)
        
        return schema
    
    def _get_sqlite_schema(self, conn) -> Dict[str, List[str]]:
        """Extract SQLite schema information"""
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        schema = {}
        
        for (table_name,) in tables:
            # Get column info for each table
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            schema[table_name] = []
            for col_info in columns:
                # col_info: (cid, name, type, notnull, dflt_value, pk)
                name = col_info[1]
                dtype = col_info[2]
                not_null = " NOT NULL" if col_info[3] else ""
                column_info = f"{name} ({dtype}{not_null})"
                schema[table_name].append(column_info)
        
        return schema
    
    def _get_mssql_schema(self, conn) -> Dict[str, List[str]]:
        """Extract SQL Server schema information"""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.table_name, c.column_name, c.data_type, c.is_nullable
            FROM information_schema.tables t
            INNER JOIN information_schema.columns c ON t.table_name = c.table_name
            WHERE t.table_type = 'BASE TABLE'
            ORDER BY t.table_name, c.ordinal_position
        """)
        
        rows = cursor.fetchall()
        schema = {}
        
        for table, column, dtype, nullable in rows:
            null_info = "" if nullable == "YES" else " NOT NULL"
            column_info = f"{column} ({dtype}{null_info})"
            schema.setdefault(table, []).append(column_info)
        
        return schema


# Utility functions for query classification (from our earlier plan)
class QueryClassifier:
    """Simple query classifier to determine if LIMIT should be used"""
    
    @staticmethod
    def should_use_limit(user_query: str, sql_query: str) -> bool:
        """
        Determine if a query should use LIMIT based on user intent
        
        Args:
            user_query: Original user question
            sql_query: Generated SQL query
            
        Returns:
            Boolean indicating if LIMIT should be applied
        """
        user_query_lower = user_query.lower()
        sql_query_upper = sql_query.upper()
        
        # Don't use LIMIT for aggregation queries
        aggregation_keywords = ['ratio', 'percentage', 'count', 'total', 'sum', 'average', 'mean']
        if any(keyword in user_query_lower for keyword in aggregation_keywords):
            return False
        
        # Don't use LIMIT if query already has GROUP BY (likely a summary)
        if 'GROUP BY' in sql_query_upper:
            return False
        
        # Don't use LIMIT if query already has aggregation functions
        aggregation_functions = ['COUNT(', 'SUM(', 'AVG(', 'MIN(', 'MAX(']
        if any(func in sql_query_upper for func in aggregation_functions):
            return False
        
        # Use LIMIT for detailed queries
        return True
    
    @staticmethod
    def get_appropriate_limit(user_query: str) -> int:
        """Get appropriate LIMIT value based on query"""
        user_query_lower = user_query.lower()
        
        # Look for specific numbers in query
        import re
        numbers = re.findall(r'\b\d+\b', user_query_lower)
        if numbers:
            # Use the first number found, capped at reasonable limits
            limit = min(int(numbers[0]), 10000)
            return max(limit, 10)  # Minimum 10 rows
        
        # Default limits based on query type
        if any(word in user_query_lower for word in ['sample', 'example', 'few']):
            return 100
        elif any(word in user_query_lower for word in ['recent', 'latest', 'last']):
            return 1000
        else:
            return 10000  # Default limit