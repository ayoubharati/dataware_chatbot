import { useState, useEffect, useRef } from "react";
import { Plus, MessageSquare, Database, BarChart3, Menu, X, Settings, ChevronDown, ChevronUp, Clock, Code, RefreshCw } from "lucide-react";
import Chart from "./Chart";
import DataTable from "./Datatable";

// Advanced word-by-word typing animation with blinking cursor
const TypingText = ({ text, speed = 100, onComplete, onProgress }) => {
  const [displayedText, setDisplayedText] = useState('');
  const [currentWordIndex, setCurrentWordIndex] = useState(0);
  const [showCursor, setShowCursor] = useState(true);
  const [isComplete, setIsComplete] = useState(false);

  const words = text.split(' ');

  useEffect(() => {
    if (currentWordIndex < words.length) {
      const timer = setTimeout(() => {
        const nextIndex = currentWordIndex + 1;
        setDisplayedText(prev => (prev ? `${prev} ${words[currentWordIndex]}` : words[currentWordIndex]));
        setCurrentWordIndex(nextIndex);
        if (onProgress) {
          const progress = Math.min(1, nextIndex / words.length);
          try { onProgress(progress); } catch {}
        }
      }, speed);

      return () => clearTimeout(timer);
    } else if (!isComplete) {
      setIsComplete(true);
      setShowCursor(false);
      if (onProgress) { try { onProgress(1); } catch {} }
      if (onComplete) {
        onComplete();
      }
    }
  }, [currentWordIndex, words, speed, onComplete, onProgress, isComplete]);

  useEffect(() => {
    const cursorTimer = setInterval(() => {
      setShowCursor(prev => !prev);
    }, 500);

    return () => clearInterval(cursorTimer);
  }, []);

  return (
    <span>
      {displayedText}
      {!isComplete && (
        <span
          className={`inline-block w-0.5 h-5 bg-gray-800 ml-1 ${showCursor ? 'opacity-100' : 'opacity-0'}`}
          style={{ animation: 'blink 1s infinite' }}
        />
      )}
    </span>
  );
};

// Query details dropdown component
const QueryDetails = ({ message }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!message.resolvable || !message.query) {
    return null;
  }

  return (
    <div className="mt-4 border border-gray-200 rounded-lg bg-gray-50">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 flex items-center justify-between text-sm font-medium text-gray-700 hover:bg-gray-100 transition-colors"
      >
        <div className="flex items-center space-x-2">
          <Code className="w-4 h-4" />
          <span>Query Details</span>
          {message.workflow_steps && message.workflow_steps.length > 0 && (
            <div className="flex items-center space-x-1 bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs">
              <Database className="w-3 h-3" />
              <span>7-Step Workflow</span>
            </div>
          )}
        </div>
        {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
      </button>

      {isExpanded && (
        <div className="px-4 pb-4 space-y-3 border-t border-gray-200">
          {/* Workflow Steps */}
          {message.workflow_steps && message.workflow_steps.length > 0 && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <h4 className="text-xs font-semibold text-blue-800 uppercase tracking-wide mb-2 flex items-center">
                <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
                7-Step Workflow Execution
              </h4>
              <div className="space-y-2">
                {message.workflow_steps.map((step, index) => (
                  <div key={index} className="flex items-center space-x-2 text-sm">
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                      step.status === 'success' ? 'bg-green-100 text-green-800' : 
                      step.status === 'failed' ? 'bg-red-100 text-red-800' : 
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {index + 1}
                </div>
                    <span className="text-gray-700">{step.name}</span>
                    <span className={`text-xs px-2 py-1 rounded ${
                      step.status === 'success' ? 'bg-green-100 text-green-800' : 
                      step.status === 'failed' ? 'bg-red-100 text-red-800' : 
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {step.status}
                    </span>
                    {step.execution_time && (
                      <span className="text-xs text-gray-500">({step.execution_time}s)</span>
                    )}
                  </div>
                ))}
                </div>
            </div>
          )}

          {/* SQL Query */}
          <div>
            <h4 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2">
              Generated SQL Query
            </h4>
            <pre className="bg-gray-800 text-green-400 p-3 rounded text-sm overflow-x-auto">
              <code>{message.query}</code>
            </pre>
          </div>

          {/* Result Type */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <h4 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1">Result Type</h4>
              <p className="text-gray-800">{message.result_type || 'N/A'}</p>
            </div>
            <div>
              <h4 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1">Resolvable</h4>
              <p className={`font-medium ${message.resolvable ? 'text-green-600' : 'text-red-600'}`}>
                {message.resolvable ? 'Yes' : 'No'}
              </p>
            </div>
            <div>
              <h4 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1">Execution Time</h4>
              <p className="text-gray-800">{message.execution_time || 0}s</p>
            </div>
            <div>
              <h4 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1">Data Format</h4>
              <p className="text-gray-800">
                {message.result_type === 'chart' ? 'Chart.js JSON' : 
                 message.result_type === 'table' ? 'Table Data' : 
                 message.result_type === 'summary' ? 'Summary Stats' : 
                 'Text Response'}
              </p>
            </div>
          </div>

          {/* Chart Data Preview (if available) */}
          {message.chart_data && (
            <div>
              <h4 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2">Chart Configuration</h4>
              <div className="bg-gray-100 p-3 rounded text-xs text-gray-700">
                <p><strong>Type:</strong> {message.chart_data.type || 'Unknown'}</p>
                <p><strong>Datasets:</strong> {message.chart_data.data?.datasets?.length || 0}</p>
                <p><strong>Labels:</strong> {message.chart_data.data?.labels?.length || 0}</p>
              </div>
            </div>
          )}

          {/* Result Data Preview (if available) */}
          {message.result && message.result_type !== 'chart' && (
            <div>
              <h4 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2">Result Data</h4>
              <div className="bg-gray-100 p-3 rounded text-xs text-gray-700 max-h-32 overflow-y-auto">
                <pre>{JSON.stringify(message.result, null, 2)}</pre>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const AssistantMessage = ({ message }) => {
  const [messageDone, setMessageDone] = useState(false);
  const [showChart, setShowChart] = useState(false);
  const [showTable, setShowTable] = useState(false);

  const canShowChart = messageDone && message.result_type === 'chart' && message.chart_data;
  const canShowTable = messageDone && message.result_type === 'table' && message.result;

  return (
    <div className="max-w-3xl self-start rounded-2xl px-6 py-5 bg-white text-gray-800 border border-gray-200 shadow-2xl transition-all duration-300">
      {/* Message text with typing animation */}
      <p className="text-lg text-gray-800 font-medium leading-relaxed whitespace-pre-wrap">
        <TypingText
          text={message.message || 'Here is the result of your query:'}
          speed={100}
          onComplete={() => { 
            setMessageDone(true); 
            setShowChart(true); 
            setShowTable(true);
          }}
        />
      </p>

      {/* Chart appears below message after typing completes */}
      {canShowChart && (
        <div className="mt-6">
          <Chart plotlyJson={message.chart_data} />
        </div>
      )}

      {/* Table appears below message after typing completes */}
      {canShowTable && (
        <div className="mt-6">
          <DataTable 
            data={message.result}
            title="Query Results"
          />
        </div>
      )}

      {/* Query details dropdown */}
      {messageDone && <QueryDetails message={message} />}
    </div>
  );
};

const Page = () => {
  const [chatHistory, setChatHistory] = useState([]);
  const [currentChatId, setCurrentChatId] = useState("1");
  const [isLoading, setIsLoading] = useState(false);
  const [input, setInput] = useState("");
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [backendStatus, setBackendStatus] = useState('checking');
  const messagesEndRef = useRef(null);

  // Initialize with a default chat
  useEffect(() => {
    const defaultChat = {
      id: "1",
      title: "DataWare Assistant",
      messages: [],
    };
    setChatHistory([defaultChat]);
  }, []);

  // Check backend status on component mount
  useEffect(() => {
    checkBackendStatus();
  }, []);

  const checkBackendStatus = async () => {
    try {
      const response = await fetch('http://localhost:5001/health');
      if (response.ok) {
        setBackendStatus('connected');
      } else {
        setBackendStatus('error');
      }
    } catch (error) {
      setBackendStatus('error');
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatHistory, isLoading]);

  const handleNewChat = () => {
    const newChatId = Date.now().toString();
    const newChat = {
      id: newChatId,
      title: "New Chat",
      messages: [],
    };
    setChatHistory((prev) => [newChat, ...prev]);
    setCurrentChatId(newChatId);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    await handleSendMessage(input.trim());
    setInput("");
  };

  const handleSendMessage = async (messageContent) => {
    if (!currentChatId) return;

    const userMessage = {
      role: "user",
      content: messageContent,
      timestamp: new Date().toISOString(),
    };

    // Add user message
    setChatHistory((prev) =>
      prev.map((chat) =>
        chat.id === currentChatId
          ? { ...chat, messages: [...chat.messages, userMessage] }
          : chat
      )
    );

    // Update chat title on first message
    if (
      chatHistory.find((chat) => chat.id === currentChatId)?.messages.length ===
      0
    ) {
      setChatHistory((prev) =>
        prev.map((chat) =>
          chat.id === currentChatId
            ? {
                ...chat,
                title:
                  messageContent.slice(0, 30) +
                  (messageContent.length > 30 ? "..." : ""),
              }
            : chat
        )
      );
    }

    setIsLoading(true);

    try {
      // Make POST request to new query_generation_app.py backend
      const response = await fetch('http://localhost:5001/query/advanced', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: messageContent,
          options: {
            max_retries: 3,
            chart_preference: 'auto'
          }
        }),
      });

      if (!response.ok) {
        throw new Error(`Backend returned ${response.status}`);
      }

      const payload = await response.json();
      console.log('Backend payload:', payload);

      // Build assistant message based on new API contract
      let aiMessage;
      
      if (payload.success && payload.resolvable) {
        // Query was successful and resolvable
        aiMessage = {
          role: 'assistant',
          message: payload.message || 'Here is the result of your query:',
          timestamp: new Date().toISOString(),
          resolvable: true,
          result_type: payload.result_type || 'unknown',
          query: payload.query || '',
          chart_data: payload.chart_data || null,
          result: payload.result || null,
          workflow_steps: payload.workflow_steps || [],
          execution_time: payload.execution_time || 0
        };
      } else if (payload.success && !payload.resolvable) {
        // Query was processed but not resolvable
        aiMessage = {
          role: 'assistant',
          message: payload.message || "I couldn't resolve that query with the available data.",
          timestamp: new Date().toISOString(),
          resolvable: false,
          result_type: null,
          query: payload.query || '',
          chart_data: null,
          result: null,
          workflow_steps: payload.workflow_steps || [],
          execution_time: payload.execution_time || 0
        };
      } else {
        // Query failed
          aiMessage = {
            role: 'assistant',
          message: payload.message || 'Sorry, I encountered an error while processing your request.',
            timestamp: new Date().toISOString(),
          resolvable: false,
          result_type: null,
          query: '',
          chart_data: null,
          result: null,
          workflow_steps: [],
          execution_time: payload.execution_time || 0
        };
      }

      console.log('AI message:', aiMessage);

      setChatHistory((prev) =>
        prev.map((chat) =>
          chat.id === currentChatId
            ? { ...chat, messages: [...chat.messages, aiMessage] }
            : chat
        )
      );
    } catch (error) {
      console.error('Error calling backend:', error);
      const errorMessage = {
        role: "assistant",
        message: "Sorry, I couldn't connect to the backend service. Please make sure the query generation service is running on port 5001.",
        timestamp: new Date().toISOString(),
        resolvable: false,
        result_type: null,
        query: '',
        chart_data: null,
        result: null,
        workflow_steps: [],
        execution_time: 0
      };

      setChatHistory((prev) =>
        prev.map((chat) =>
          chat.id === currentChatId
            ? { ...chat, messages: [...chat.messages, errorMessage] }
            : chat
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  const currentChat = chatHistory.find((chat) => chat.id === currentChatId);

  return (
    <div className="flex h-screen bg-gray-50">
      <style>{`
        @keyframes blink {
          0%, 50% { opacity: 1; }
          51%, 100% { opacity: 0; }
        }
        @keyframes barLaunch {
          0% {
            height: 0 !important;
            opacity: 0;
            transform: scale(0.8);
          }
          70% {
            transform: scale(1.1);
            opacity: 1;
          }
          100% {
            opacity: 1;
            transform: scale(1);
          }
        }
        @keyframes chartReveal {
          0% {
            opacity: 0;
            transform: scale(0.9) translateY(20px);
          }
          60% {
            transform: scale(1.02) translateY(-5px);
          }
          100% {
            opacity: 1;
            transform: scale(1) translateY(0);
          }
        }
        @keyframes bounceIn {
          0% {
            opacity: 0;
            transform: scale(0.3);
          }
          50% {
            opacity: 1;
            transform: scale(1.05);
          }
          70% {
            transform: scale(0.9);
          }
          100% {
            opacity: 1;
            transform: scale(1);
          }
        }
      `}</style>

      {/* Sidebar */}
      <div className={`${isSidebarOpen ? 'w-72' : 'w-0'} transition-all duration-300 bg-white border-r border-gray-200 flex flex-col overflow-hidden shadow-sm`}>
        {/* Sidebar Header */}
        <div className="p-6 border-b border-gray-100 bg-gradient-to-r from-blue-50 to-indigo-50">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center">
                <Database className="w-6 h-6 text-white" />
              </div>
              <div>
                <h2 className="font-bold text-gray-900">DataWare Chatbot</h2>
                <p className="text-xs text-blue-600 font-medium">AI Analytics</p>
              </div>
            </div>
            <button
              onClick={() => setIsSidebarOpen(false)}
              className="p-2 hover:bg-blue-100 rounded-lg transition-colors"
            >
              <X className="w-4 h-4 text-gray-600" />
            </button>
          </div>
        </div>

        {/* New Chat Button */}
        <div className="p-4">
          <button
            onClick={handleNewChat}
            className="w-full flex items-center space-x-3 px-4 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl hover:from-blue-700 hover:to-blue-800 transition-all duration-200 shadow-lg hover:shadow-xl"
          >
            <Plus className="w-5 h-5" />
            <span className="font-medium">New Chat</span>
          </button>
        </div>

        {/* Chat History */}
        <div className="flex-1 overflow-y-auto px-4 pb-4">
          <div className="space-y-2">
            {chatHistory.map((chat) => (
              <button
                key={chat.id}
                onClick={() => setCurrentChatId(chat.id)}
                className={`w-full text-left px-4 py-3 rounded-xl transition-all duration-200 group ${
                  currentChatId === chat.id
                    ? 'bg-blue-50 border-2 border-blue-200 shadow-sm'
                    : 'hover:bg-gray-50 border-2 border-transparent'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <MessageSquare className={`w-4 h-4 ${
                    currentChatId === chat.id ? 'text-blue-600' : 'text-gray-400'
                  }`} />
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm font-medium truncate ${
                      currentChatId === chat.id ? 'text-blue-900' : 'text-gray-700'
                    }`}>
                      {chat.title}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {chat.messages.length} messages
                    </p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between shadow-sm">
          <div className="flex items-center space-x-4">
            {!isSidebarOpen && (
              <button
                onClick={() => setIsSidebarOpen(true)}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <Menu className="w-5 h-5 text-gray-600" />
              </button>
            )}
            <div>
              <h1 className="text-xl font-bold text-gray-900">
                {currentChat?.title || "DataWare Assistant"}
              </h1>
              <p className="text-sm text-gray-500">
                Advanced AI-powered query generation with 7-step workflow
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <div className={`flex items-center space-x-2 px-3 py-1.5 rounded-full ${
              backendStatus === 'connected' ? 'bg-green-50 text-green-700' :
              backendStatus === 'error' ? 'bg-red-50 text-red-700' :
              'bg-yellow-50 text-yellow-700'
            }`}>
              <div className={`w-2 h-2 rounded-full ${
                backendStatus === 'connected' ? 'bg-green-500' :
                backendStatus === 'error' ? 'bg-red-500' :
                'bg-yellow-500'
              }`}></div>
              <span className="text-xs font-medium">
                {backendStatus === 'connected' ? 'Connected' :
                 backendStatus === 'error' ? 'Disconnected' :
                 'Checking...'}
              </span>
            </div>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto bg-gray-50">
          {!currentChat?.messages?.length ? (
            <div className="flex flex-col items-center justify-center h-full px-6">
              <div className="max-w-2xl w-full text-center">
                <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl flex items-center justify-center mb-6 mx-auto shadow-lg">
                  <Database className="w-10 h-10 text-white" />
                </div>
                <h2 className="text-2xl font-bold text-gray-900 mb-3">
                  Welcome to DataWare Chatbot
                </h2>
                <p className="text-gray-600 mb-8 text-lg leading-relaxed">
                  Your intelligent data analytics assistant powered by advanced AI query generation.
                  Ask me about your data warehouse, generate reports, analyze trends, or get insights from your business data.
                </p>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                  <div className="p-4 bg-white rounded-xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
                    <BarChart3 className="w-8 h-8 text-blue-600 mb-3 mx-auto" />
                    <h3 className="font-semibold text-gray-900 mb-2">Smart Charts</h3>
                    <p className="text-sm text-gray-600">AI-powered chart generation with automatic type selection</p>
                  </div>
                  <div className="p-4 bg-white rounded-xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
                    <Database className="w-8 h-8 text-green-600 mb-3 mx-auto" />
                    <h3 className="font-semibold text-gray-900 mb-2">7-Step Workflow</h3>
                    <p className="text-sm text-gray-600">Advanced query processing with validation and correction</p>
                  </div>
                  <div className="p-4 bg-white rounded-xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
                    <Settings className="w-8 h-8 text-purple-600 mb-3 mx-auto" />
                    <h3 className="font-semibold text-gray-900 mb-2">Auto-Correction</h3>
                    <p className="text-sm text-gray-600">Intelligent SQL generation with error handling</p>
                  </div>
                </div>
                <div className="flex items-center justify-center space-x-6 text-sm text-gray-500">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span>7-step AI workflow</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                    <span>Smart chart generation</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                    <span>Auto-correction</span>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="px-6 py-8">
              <div className="max-w-4xl mx-auto space-y-6">
                {currentChat.messages.map((message, index) => (
                  <div key={index}>
                    {message.role === 'user' ? (
                      <div className="flex justify-end flex-col mb-6">
                        <div
                          className="max-w-2xl self-end rounded-2xl px-6 py-4 shadow-lg bg-gradient-to-r from-blue-600 to-blue-700 text-white"
                          style={{ padding: '15px 20px', marginBottom: '15px', borderRadius: '12px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}
                        >
                          <p className="font-medium">{message.content}</p>
                        </div>
                      </div>
                    ) : (
                      <AssistantMessage message={message} />
                    )}
                  </div>
                ))}
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-white rounded-2xl px-6 py-4 shadow-lg border border-gray-100">
                      <div className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                        <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="bg-white border-t border-gray-200 px-6 py-4">
          <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
            <div className="flex items-end space-x-4">
              <div className="flex-1">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask me anything about your data warehouse..."
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  rows="1"
                  style={{ minHeight: '48px', maxHeight: '120px' }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSubmit(e);
                    }
                  }}
                />
              </div>
              <button
                type="submit"
                disabled={!input.trim() || isLoading || backendStatus !== 'connected'}
                className="px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
              >
                Send
              </button>
            </div>
            {backendStatus !== 'connected' && (
              <div className="mt-2 text-sm text-red-600">
                ⚠️ Backend service not connected. Please start the query generation service on port 5001.
              </div>
            )}
          </form>
        </div>
      </div>
    </div>
  );
};

export default Page;
