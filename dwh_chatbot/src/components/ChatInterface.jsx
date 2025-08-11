import { useState, useEffect, useRef } from "react";
import { Plus, MessageSquare, Database, BarChart3, Wheat, Menu, X, Leaf, TrendingUp, Users, Settings } from "lucide-react";

const FarmChatbot = () => {
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [currentChatId, setCurrentChatId] = useState("chat-1");
  const messagesEndRef = useRef(null);

  // Mock data for demonstration
  const [chats, setChats] = useState([
    {
      id: "chat-1",
      title: "Q3 Yield Performance Review",
      lastMessage: "Corn yields increased 12% this quarter",
      timestamp: new Date(Date.now() - 1000 * 60 * 30),
      messages: []
    },
    {
      id: "chat-2", 
      title: "Feed Inventory Optimization",
      lastMessage: "Current stock levels analysis",
      timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2),
      messages: [
        {
          role: "user",
          content: "What's our current feed inventory status?",
          timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2)
        },
        {
          role: "assistant", 
          content: "Your current feed inventory shows 2,450 tons of corn feed, 1,200 tons of soybean meal, and 800 tons of alfalfa. Based on consumption patterns, you have approximately 45 days of supply remaining. I recommend reordering corn feed within the next 2 weeks to maintain optimal stock levels.",
          timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2)
        }
      ]
    },
    {
      id: "chat-3",
      title: "Weather Impact Assessment", 
      lastMessage: "Rainfall correlation with productivity",
      timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24),
      messages: []
    }
  ]);

  const currentChat = chats.find(chat => chat.id === currentChatId);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [currentChat?.messages, isLoading]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = {
      role: "user",
      content: input.trim(),
      timestamp: new Date()
    };

    // Add user message
    setChats(prevChats => 
      prevChats.map(chat => 
        chat.id === currentChatId 
          ? { ...chat, messages: [...chat.messages, userMessage], lastMessage: input.trim() }
          : chat
      )
    );

    setInput("");
    setIsLoading(true);

    // Simulate API response
    setTimeout(() => {
      const responses = [
        "Based on your farm's data warehouse, I can provide detailed analytics on crop performance, livestock metrics, and operational efficiency. What specific insights would you like me to analyze?",
        "I've analyzed your latest agricultural data. Your current metrics show strong performance across key indicators. Would you like me to dive deeper into any specific area?",
        "Your farm's data indicates optimal conditions for the current season. I can provide recommendations for resource allocation and yield optimization based on historical patterns.",
        "I've processed the latest sensor data from your fields. The soil moisture levels and nutrient distribution suggest excellent conditions for the upcoming planting cycle."
      ];

      const botResponse = {
        role: "assistant",
        content: responses[Math.floor(Math.random() * responses.length)],
        timestamp: new Date()
      };

      setChats(prevChats => 
        prevChats.map(chat => 
          chat.id === currentChatId 
            ? { ...chat, messages: [...chat.messages, botResponse] }
            : chat
        )
      );
      setIsLoading(false);
    }, 1500);
  };

  const createNewChat = () => {
    const newChat = {
      id: `chat-${Date.now()}`,
      title: "New Analytics Session",
      lastMessage: "",
      timestamp: new Date(),
      messages: []
    };
    setChats(prev => [newChat, ...prev]);
    setCurrentChatId(newChat.id);
  };

  const suggestedPrompts = [
    {
      text: "Show me this month's crop yield analysis",
      icon: <TrendingUp className="w-4 h-4" />
    },
    {
      text: "What's our current livestock health status?",
      icon: <Users className="w-4 h-4" />
    },
    {
      text: "Analyze feed inventory and consumption trends",
      icon: <Database className="w-4 h-4" />
    },
    {
      text: "Compare weather impact on yield performance",
      icon: <BarChart3 className="w-4 h-4" />
    }
  ];

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div className={`${isSidebarOpen ? 'w-72' : 'w-0'} transition-all duration-300 bg-white border-r border-gray-200 flex flex-col overflow-hidden shadow-sm`}>
        {/* Sidebar Header */}
        <div className="p-6 border-b border-gray-100 bg-gradient-to-r from-green-50 to-emerald-50">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-green-600 rounded-xl flex items-center justify-center">
                <Leaf className="w-6 h-6 text-white" />
              </div>
              <div>
                <h2 className="font-bold text-gray-900">AgriData Pro</h2>
                <p className="text-xs text-green-600 font-medium">Enterprise Analytics</p>
              </div>
            </div>
            <button
              onClick={() => setIsSidebarOpen(false)}
              className="lg:hidden p-1.5 rounded-lg hover:bg-gray-100"
            >
              <X className="w-4 h-4 text-gray-500" />
            </button>
          </div>
          <button
            onClick={createNewChat}
            className="w-full mt-4 flex items-center justify-center space-x-2 px-4 py-2.5 text-sm bg-green-600 hover:bg-green-700 text-white rounded-xl transition-colors font-medium"
          >
            <Plus className="w-4 h-4" />
            <span>New Analysis</span>
          </button>
        </div>

        {/* Navigation */}
        <div className="p-4 border-b border-gray-100">
          <div className="space-y-1">
            <button className="w-full flex items-center space-x-3 px-3 py-2.5 text-sm text-green-700 bg-green-50 rounded-lg font-medium">
              <MessageSquare className="w-4 h-4" />
              <span>Analytics Chat</span>
            </button>
            <button className="w-full flex items-center space-x-3 px-3 py-2.5 text-sm text-gray-600 hover:bg-gray-50 rounded-lg">
              <Database className="w-4 h-4" />
              <span>Data Sources</span>
            </button>
            <button className="w-full flex items-center space-x-3 px-3 py-2.5 text-sm text-gray-600 hover:bg-gray-50 rounded-lg">
              <BarChart3 className="w-4 h-4" />
              <span>Reports</span>
            </button>
          </div>
        </div>

        {/* Chat History */}
        <div className="flex-1 overflow-y-auto p-4">
          <div className="space-y-2">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Recent Sessions</h3>
            {chats.map((chat) => (
              <button
                key={chat.id}
                onClick={() => setCurrentChatId(chat.id)}
                className={`w-full text-left p-3 rounded-xl transition-all ${
                  currentChatId === chat.id
                    ? 'bg-green-50 border border-green-200 shadow-sm'
                    : 'hover:bg-gray-50 border border-transparent'
                }`}
              >
                <div className="flex items-start space-x-3">
                  <div className={`w-2 h-2 rounded-full mt-2 ${
                    currentChatId === chat.id ? 'bg-green-500' : 'bg-gray-300'
                  }`} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {chat.title}
                    </p>
                    {chat.lastMessage && (
                      <p className="text-xs text-gray-500 truncate mt-1">
                        {chat.lastMessage}
                      </p>
                    )}
                    <p className="text-xs text-gray-400 mt-1">
                      {chat.timestamp.toLocaleDateString()}
                    </p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Sidebar Footer */}
        <div className="p-4 border-t border-gray-100 bg-gray-50">
          <div className="flex items-center justify-between text-xs text-gray-500">
            <div className="flex items-center space-x-2">
              <Wheat className="w-4 h-4" />
              <span>v2.1.3</span>
            </div>
            <button className="p-1 hover:bg-gray-200 rounded">
              <Settings className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              {!isSidebarOpen && (
                <button
                  onClick={() => setIsSidebarOpen(true)}
                  className="p-2 rounded-lg hover:bg-gray-100"
                >
                  <Menu className="w-5 h-5 text-gray-600" />
                </button>
              )}
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                  <BarChart3 className="w-4 h-4 text-green-600" />
                </div>
                <div>
                  <h1 className="text-lg font-semibold text-gray-900">
                    {currentChat?.title || "Agricultural Data Analytics"}
                  </h1>
                  <p className="text-sm text-gray-500">AI-powered farm intelligence platform</p>
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-sm text-gray-600">Connected</span>
            </div>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto bg-gradient-to-br from-green-50/30 to-emerald-50/30">
          {!currentChat?.messages?.length ? (
            <div className="flex flex-col items-center justify-center h-full px-6">
              <div className="max-w-2xl w-full text-center">
                <div className="w-20 h-20 bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl flex items-center justify-center mb-6 mx-auto shadow-lg">
                  <Database className="w-10 h-10 text-white" />
                </div>
                <h2 className="text-2xl font-bold text-gray-900 mb-3">
                  Welcome to AgriData Pro
                </h2>
                <p className="text-gray-600 mb-8 text-lg leading-relaxed">
                  Your intelligent farming assistant powered by advanced analytics. 
                  Ask me about crop performance, livestock management, resource optimization, 
                  or any farm data insights you need.
                </p>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-8">
                  {suggestedPrompts.map((prompt, index) => (
                    <button 
                      key={index}
                      onClick={() => setInput(prompt.text)}
                      className="flex items-center space-x-3 p-4 bg-white hover:bg-green-50 border border-gray-200 hover:border-green-200 rounded-xl transition-all text-left group shadow-sm"
                    >
                      <div className="w-10 h-10 bg-green-100 group-hover:bg-green-200 rounded-lg flex items-center justify-center transition-colors">
                        {prompt.icon}
                      </div>
                      <span className="text-sm font-medium text-gray-700 group-hover:text-green-700 transition-colors">
                        {prompt.text}
                      </span>
                    </button>
                  ))}
                </div>

                <div className="flex items-center justify-center space-x-6 text-sm text-gray-500">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span>Real-time data processing</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                    <span>Predictive analytics</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                    <span>Custom reports</span>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="px-6 py-8">
              <div className="max-w-4xl mx-auto space-y-6">
                {currentChat.messages.map((message, index) => (
                  <div
                    key={index}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-xs md:max-w-2xl px-5 py-4 rounded-2xl shadow-sm ${
                        message.role === 'user'
                          ? 'bg-green-600 text-white'
                          : 'bg-white border border-gray-200 text-gray-900'
                      }`}
                    >
                      <p className="whitespace-pre-wrap text-sm leading-relaxed">{message.content}</p>
                      <div className={`text-xs mt-3 ${
                        message.role === 'user' ? 'text-green-100' : 'text-gray-500'
                      }`}>
                        {message.timestamp.toLocaleTimeString([], { 
                          hour: '2-digit', 
                          minute: '2-digit' 
                        })}
                      </div>
                    </div>
                  </div>
                ))}

                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-white border border-gray-200 rounded-2xl px-5 py-4 shadow-sm">
                      <div className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                        <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                        <span className="text-sm text-gray-500 ml-2">Analyzing data...</span>
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
        <div className="border-t border-gray-200 bg-white px-6 py-4 shadow-sm">
          <div className="max-w-4xl mx-auto">
            <div className="flex space-x-4">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask me anything about your farm data..."
                disabled={isLoading}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit(e);
                  }
                }}
                className="flex-1 border border-gray-300 rounded-xl px-5 py-3 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500 disabled:bg-gray-50 disabled:text-gray-500 text-sm placeholder-gray-400"
              />
              <button
                onClick={handleSubmit}
                disabled={isLoading || !input.trim()}
                className="px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-xl disabled:bg-gray-300 disabled:cursor-not-allowed transition-all shadow-sm hover:shadow-md"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </button>
            </div>
            <div className="flex items-center justify-between mt-3 text-xs text-gray-500">
              <p>Press Enter to send, Shift + Enter for new line</p>
              <p>Powered by AgriData Pro AI</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FarmChatbot;