import React, { useState, useEffect } from 'react';
import { Send, Database, Table, Loader2, Code, MessageSquare, X, ChevronDown, ChevronUp } from 'lucide-react';

const DatabaseQueryInterface = ({ connectionId, connectionName, database, onDisconnect }) => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([]);
  const [tables, setTables] = useState([]);
  const [showTables, setShowTables] = useState(true);
  const [showSql, setShowSql] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('active');

  useEffect(() => {
    if (connectionId) {
      fetchTables();
      checkConnectionStatus();
    }
  }, [connectionId]);

  const fetchTables = async () => {
    try {
      const response = await fetch(`http://localhost:5000/api/connectors/postgres/tables/${connectionId}`);
      const data = await response.json();
      if (data.success) {
        setTables(data.tables);
      }
    } catch (error) {
      console.error('Failed to fetch tables:', error);
    }
  };

  const checkConnectionStatus = async () => {
    try {
      const response = await fetch(`http://0/api/connectors/postgres/status/${connectionId}`);
      const data = await response.json();
      setConnectionStatus(data.status);
    } catch (error) {
      setConnectionStatus('disconnected');
    }
  };

  const handleQuerySubmit = async (e) => {
    e.preventDefault();
    if (!query.trim() || loading) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: query,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setLoading(true);
    setQuery('');

    try {
      const response = await fetch('http://localhost:5000/api/connectors/postgres/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          connectionId,
          query: query
        })
      });

      const data = await response.json();

      if (data.success) {
        const assistantMessage = {
          id: Date.now() + 1,
          type: 'assistant',
          content: data.result,
          sql: data.sql,
          timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, assistantMessage]);
      } else {
        throw new Error(data.message);
      }
    } catch (error) {
      const errorMessage = {
        id: Date.now() + 1,
        type: 'error',
        content: error.message || 'Failed to process query',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const executeSql = async (sql) => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:5000/api/connectors/postgres/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          connectionId,
          sql
        })
      });

      const data = await response.json();

      if (data.success) {
        const resultMessage = {
          id: Date.now(),
          type: 'sql-result',
          content: data.rows || `Query executed successfully. ${data.rowCount} rows affected.`,
          timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, resultMessage]);
      }
    } catch (error) {
      const errorMessage = {
        id: Date.now(),
        type: 'error',
        content: error.message || 'Failed to execute SQL',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      await fetch('http://localhost:5000/api/connectors/postgres/disconnect', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          connectionId
        })
      });
      onDisconnect();
    } catch (error) {
      console.error('Failed to disconnect:', error);
    }
  };

  const suggestedQueries = [
    "Show me all tables in the database",
    "What are the top 10 records in the users table?",
    "How many total records are there?",
    "Show me the schema of the main table",
    "What are the relationships between tables?"
  ];

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar with tables */}
      <div className={`${showTables ? 'w-80' : 'w-0'} transition-all duration-300 bg-white border-r border-gray-200 overflow-hidden`}>
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <Database className="w-5 h-5 mr-2 text-blue-600" />
              <div>
                <h3 className="font-semibold text-sm">{database}</h3>
                <p className="text-xs text-gray-500">{connectionName}</p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <span className={`w-2 h-2 rounded-full ${connectionStatus === 'active' ? 'bg-green-500' : 'bg-red-500'}`} />
              <button
                onClick={() => setShowTables(false)}
                className="p-1 hover:bg-gray-100 rounded"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        <div className="p-4 overflow-y-auto h-full">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">Tables ({tables.length})</h4>
          <div className="space-y-2">
            {tables.map((table) => (
              <div key={table.name} className="border border-gray-200 rounded-lg">
                <button
                  className="w-full px-3 py-2 text-left hover:bg-gray-50 flex items-center justify-between"
                  onClick={() => {
                    const updatedTables = tables.map(t => 
                      t.name === table.name ? { ...t, expanded: !t.expanded } : t
                    );
                    setTables(updatedTables);
                  }}
                >
                  <div className="flex items-center">
                    <Table className="w-4 h-4 mr-2 text-gray-500" />
                    <span className="text-sm font-medium">{table.name}</span>
                  </div>
                  {table.expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                </button>
                {table.expanded && (
                  <div className="px-3 py-2 bg-gray-50 border-t border-gray-200">
                    <p className="text-xs font-semibold text-gray-600 mb-1">Columns:</p>
                    {table.columns?.map((col) => (
                      <div key={col.name} className="text-xs text-gray-600 ml-2 py-0.5">
                        • {col.name} <span className="text-gray-400">({col.type})</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Main query interface */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              {!showTables && (
                <button
                  onClick={() => setShowTables(true)}
                  className="mr-4 p-2 hover:bg-gray-100 rounded-lg"
                >
                  <Database className="w-5 h-5" />
                </button>
              )}
              <div>
                <h2 className="text-xl font-semibold">Database Query Assistant</h2>
                <p className="text-sm text-gray-500">Ask questions about your data in natural language</p>
              </div>
            </div>
            <button
              onClick={handleDisconnect}
              className="px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
            >
              Disconnect
            </button>
          </div>
        </div>

        {/* Messages area */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {messages.length === 0 ? (
            <div className="text-center py-12">
              <MessageSquare className="w-12 h-12 mx-auto text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Start asking questions</h3>
              <p className="text-gray-500 mb-6">Query your database using natural language</p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl mx-auto">
                {suggestedQueries.map((sq, index) => (
                  <button
                    key={index}
                    onClick={() => setQuery(sq)}
                    className="text-left px-4 py-3 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <p className="text-sm text-gray-700">{sq}</p>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-4 max-w-4xl mx-auto">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-3xl px-4 py-3 rounded-lg ${
                      message.type === 'user'
                        ? 'bg-blue-600 text-white'
                        : message.type === 'error'
                        ? 'bg-red-50 text-red-800 border border-red-200'
                        : message.type === 'sql-result'
                        ? 'bg-gray-100'
                        : 'bg-white border border-gray-200'
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{
                      typeof message.content === 'object' 
                        ? JSON.stringify(message.content, null, 2)
                        : message.content
                    }</p>
                    
                    {message.sql && (
                      <div className="mt-3 pt-3 border-t border-gray-200">
                        <button
                          onClick={() => setShowSql(!showSql)}
                          className="flex items-center text-sm text-gray-600 hover:text-gray-800"
                        >
                          <Code className="w-4 h-4 mr-1" />
                          {showSql ? 'Hide' : 'Show'} SQL Query
                        </button>
                        {showSql && (
                          <div className="mt-2 p-3 bg-gray-900 text-gray-100 rounded-lg">
                            <pre className="text-xs overflow-x-auto">{message.sql}</pre>
                            <button
                              onClick={() => executeSql(message.sql)}
                              className="mt-2 text-xs px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                            >
                              Execute SQL
                            </button>
                          </div>
                        )}
                      </div>
                    )}
                    
                    <p className="text-xs opacity-70 mt-2">
                      {new Date(message.timestamp).toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              ))}
              
              {loading && (
                <div className="flex justify-start">
                  <div className="bg-white border border-gray-200 px-4 py-3 rounded-lg">
                    <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Input area */}
        <div className="border-t border-gray-200 bg-white px-6 py-4">
          <form onSubmit={handleQuerySubmit} className="flex space-x-4">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask a question about your data..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={loading || connectionStatus !== 'active'}
            />
            <button
              type="submit"
              disabled={loading || !query.trim() || connectionStatus !== 'active'}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center"
            >
              {loading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <>
                  <Send className="w-5 h-5 mr-2" />
                  Send
                </>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default DatabaseQueryInterface;