import React, { useState, useRef, useEffect } from "react";
import HeaderDropdown from "./components/HeaderDropdown.jsx";
import Chatbotlogo from "./components/Chatbotlogo.jsx";
import Chatform from "./components/Chatform.jsx";
import ChatTitleModal from "./components/ChatModal";
import ChatHistory from "./components/ChatHistory.jsx";
import ConfirmModal from "./components/ConfirmModal.jsx";
import ThemeToggleButton from "./components/ThemeToggleButton.jsx";
import { Pencil, Clipboard, ChevronLeft, ChevronRight, Search, ArrowRight, Menu } from 'lucide-react';

const App = () => {
  const [messages, setMessages] = useState([
    {
      role: "bot",
      text: "Hey! How can I help you?",
      cached: false,
      time: 0,
    },
  ]);
  const [isTyping, setIsTyping] = useState(false);
  const chatBodyRef = useRef(null);
  const [sessionId, setSessionId] = useState(() => sessionStorage.getItem("chat_session") || null);
  const [confirmType, setConfirmType] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [showHistoryPanel, setShowHistoryPanel] = useState(false);
  const [hoveredIndex, setHoveredIndex] = useState(null);
  const [expandedIndex, setExpandedIndex] = useState(null);
  const [showSearchInput, setShowSearchInput] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [showFunctionsDropdown, setShowFunctionsDropdown] = useState(false);

  const [editablePrompt, setEditablePrompt] = useState("");
  const inputRef = useRef(null);

  useEffect(() => {
    if (chatBodyRef.current) {
      chatBodyRef.current.scrollTop = chatBodyRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  const confirmClearChat = () => setConfirmType("clear");
  const confirmNewChat = () => setConfirmType("new");

  const handleClearChat = () => {
    setMessages([]);
    setConfirmType(null);
  };

  const handleNewChat = () => {
    setMessages([]);
    const newSession = crypto.randomUUID();
    sessionStorage.setItem("chat_session", newSession);
    setSessionId(newSession);
    setConfirmType(null);
  };

  const saveConversation = (title) => {
    const savedConvos = JSON.parse(localStorage.getItem("chatHistory")) || [];
    const timestamp = new Date().toISOString();
    savedConvos.push({ id: timestamp, title, messages });
    localStorage.setItem("chatHistory", JSON.stringify(savedConvos));
    alert("Conversation saved!");
  };

  const handleSendMessage = async (userText) => {
    const trimmed = userText.trim();
    if (!trimmed) return;

    setMessages((m) => [...m, { role: "user", text: trimmed }]);
    setIsTyping(true);

    const payload = sessionId ? { session_id: sessionId, message: trimmed } : { message: trimmed };

    try {
      const res = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const { session_id, response, cached, elapsed_time, suggestions = [] } = await res.json();

      if (session_id && session_id !== sessionId) {
        sessionStorage.setItem("chat_session", session_id);
        setSessionId(session_id);
      }

      setMessages((m) => [
        ...m,
        { role: "bot", text: response, cached: Boolean(cached), time: elapsed_time ?? 0, suggestions }
      ]);
    } catch (err) {
      console.error("Chat API error:", err);
      setMessages((m) => [
        ...m,
        { role: "bot", text: "⚠️ Server error, please try again.", cached: false, time: 0 },
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    // alert("Copied to clipboard");
  };

  const handleEditPrompt = (text) => {
    setEditablePrompt(text);
    setTimeout(() => {
      inputRef.current?.focus();
    }, 100);
  };

  const startEditing = async (index) => {
    const userMsg = prompt("Edit your message:", messages[index].text);
    if (!userMsg || !userMsg.trim()) return;

    const updatedMessages = [...messages];
    updatedMessages[index].text = userMsg.trim();

    const trimmedMessages = updatedMessages.slice(0, index + 1);
    setMessages(trimmedMessages);
    setIsTyping(true);

    const payload = sessionId
      ? { session_id: sessionId, message: userMsg.trim() }
      : { message: userMsg.trim() };

    try {
      const res = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const { session_id, response, cached, elapsed_time, suggestions = [] } = await res.json();

      if (session_id && session_id !== sessionId) {
        sessionStorage.setItem("chat_session", session_id);
        setSessionId(session_id);
      }

      setMessages((m) => [
        ...trimmedMessages,
        {
          role: "bot",
          text: response,
          cached: Boolean(cached),
          time: elapsed_time ?? 0,
          suggestions,
        },
      ]);
    } catch (err) {
      console.error("Chat API error (edit resend):", err);
      setMessages((m) => [
        ...trimmedMessages,
        { role: "bot", text: "⚠️ Server error on reprocessing edit.", cached: false, time: 0 },
      ]);
    } finally {
      setIsTyping(false);
    }
  };
  const handleSearch = (query) => {
    if (!query) return;

    const lowerQuery = query.toLowerCase();
    const matchIndex = messages.findIndex(msg => msg.text.toLowerCase().includes(lowerQuery));

    if (matchIndex !== -1) {
      const messageElement = document.querySelectorAll(".chat-body .message")[matchIndex];
      if (messageElement) {
        messageElement.scrollIntoView({ behavior: "smooth", block: "center" });
        messageElement.classList.add("highlight");
        setTimeout(() => messageElement.classList.remove("highlight"), 2000);
      }
    } else {
      alert("No messages found matching your query.");
    }
  };
  const toggleFunctions = () => setShowFunctionsDropdown(open => !open);
  return (
    <div className="container">
      <div className="chatbot-popup">
        <div className="chatbot-header">
          <div className="header-container">
            {/* Theme toggle moved to left side */}
            <ThemeToggleButton className="theme-toggle-header" />
            
            {/* Centered logo and title */}
            <div className="header-center">
              <Chatbotlogo />
              <h2 className="logo-text">Chatbot</h2>
            </div>
            
            {/* Dropdown menu on the right */}
            <HeaderDropdown 
              onClear={confirmClearChat}
              onNewChat={confirmNewChat}
              onSave={() => setShowModal(true)}
              onToggleHistory={() => setShowHistoryPanel(!showHistoryPanel)}
              onSearch={handleSearch}
              searchQuery={searchQuery}
              setSearchQuery={setSearchQuery}
            />
          </div>
        </div>

        <ChatHistory
          visible={showHistoryPanel}
          onClose={() => setShowHistoryPanel(false)}
          onLoadHistory={(msgs) => setMessages(msgs)}
        />

        <div className="chat-body" ref={chatBodyRef}>
          {messages.map((msg, index) => {
            const isLong = msg.text.length > 300;
            const displayText = isLong && expandedIndex !== index
              ? msg.text.slice(0, 300) + "..."
              : msg.text;
            return (
              <div
                key={index}
                className={`message ${msg.role}-message`}
                onMouseEnter={() => setHoveredIndex(index)}
                onMouseLeave={() => setHoveredIndex(null)}
              >
                {msg.role === "bot" && <Chatbotlogo />}
                <p className="message-text">{displayText}</p>
                {isLong && (
                  <button className="show-more-btn" onClick={() => setExpandedIndex(expandedIndex === index ? null : index)}>
                    {expandedIndex === index ? "Show Less" : "Show More"}
                  </button>
                )}

                {msg.role === "bot" && (
                  <div className="message-meta">
                    {msg.cached ? <span className="cache-badge">CACHE</span> : <span className="live-badge">LIVE</span>}
                    <span className="elapsed-time">{msg.time.toFixed(3)} s</span>
                  </div>
                )}

                {msg.role === "user" && hoveredIndex === index && (
                  <button className="icon-button edit-icon" onClick={() => handleEditPrompt(msg.text)}><Pencil size={14} /></button>
                )}
                {msg.role === "bot" && hoveredIndex === index && (
                  <button className="icon-button copy-icon" onClick={() => copyToClipboard(msg.text)}><Clipboard size={14} /></button>
                )}

                {msg.role === "bot" && msg.suggestions && (
                  <div className="suggestion-chips">
                    {msg.suggestions.map((sugg, i) => (
                      <button key={i} className="chip" onClick={() => handleSendMessage(sugg)}>
                        {sugg}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            );
          })}

          {isTyping && (
            <div className="message bot-message typing-indicator">
              <Chatbotlogo />
              <p className="message-text">Bot is typing...</p>
            </div>
          )}
        </div>

        <div className="chat-footer">
          <Chatform onSendMessage={handleSendMessage} 
            editablePrompt={editablePrompt}  
            inputRef={inputRef}/>
        </div>
      </div>

      {showModal && (
        <ChatTitleModal onSave={saveConversation} onClose={() => setShowModal(false)} />
      )}

      {confirmType && (
        <ConfirmModal
          message={confirmType === "clear" ? "Are you sure you want to clear the chat?" : "Start a new chat? This will erase current messages."}
          onConfirm={confirmType === "clear" ? handleClearChat : handleNewChat}
          onCancel={() => setConfirmType(null)}
        />
      )}
    </div>
  );
};

export default App;
