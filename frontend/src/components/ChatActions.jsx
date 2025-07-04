// src/components/ChatActions.jsx
import React from "react";
import clearchat from "/src/images/clearchat.png";
import newchat from "/src/images/newchat.png";
import "./ChatActions.css";

const ChatActions = ({ onClear, onNewChat }) => {
  return (
    <div className="chat-actions">
      <button onClick={onClear} title="Clear Chat">
        <img 
          src={clearchat} 
          alt="Clear chat" 
          className="theme-adaptive-icon" 
        />
        <span className="action-text">Clear Chat</span>
      </button>
      <button onClick={onNewChat} title="New Chat">
        <img 
          src={newchat} 
          alt="New chat" 
          className="theme-adaptive-icon" 
        />
        <span className="action-text">New Chat</span>
      </button>
    </div>
  );
};

export default ChatActions;