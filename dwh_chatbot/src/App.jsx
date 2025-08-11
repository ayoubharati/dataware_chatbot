import { useState } from "react";
import Login from "./components/Login";
import ChatInterface from "./components/ChatInterface";

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const [currentChatId, setCurrentChatId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  // Simulate authentication
  const handleLogin = (credentials) => {
    if (credentials.email && credentials.password) {
      setUser({
        email: credentials.email,
        name: credentials.email.split("@")[0],
      });
      setIsAuthenticated(true);

      // Initialize with a default chat
      const defaultChat = {
        id: "1",
        title: "New Chat",
        messages: [],
      };
      setChatHistory([defaultChat]);
      setCurrentChatId("1");
    }
  };

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

    // Simulated AI response
    setTimeout(() => {
      const aiMessage = {
        role: "assistant",
        content: `This is a simulated farm data warehouse chatbot response to: "${messageContent}".`,        timestamp: new Date().toISOString(),
      };

      setChatHistory((prev) =>
        prev.map((chat) =>
          chat.id === currentChatId
            ? { ...chat, messages: [...chat.messages, aiMessage] }
            : chat
        )
      );

      setIsLoading(false);
    }, 1500);
  };

  if (!isAuthenticated) {
    return <Login onLogin={handleLogin} />;
  }

  const currentChat = chatHistory.find((chat) => chat.id === currentChatId);

  return (
    <div className="h-screen bg-gray-100">
      <ChatInterface
        currentChat={currentChat}
        onSendMessage={handleSendMessage}
        isLoading={isLoading}
      />
    </div>
  );
}

export default App;