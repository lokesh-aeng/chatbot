import React, { useState } from "react";
import ChatActions from "./ChatActions";
import SaveChatButton from "./SaveButton.jsx";
import  historyicon from "/src/images/historyicon.png";
import { Search, Menu, ChevronDown } from 'lucide-react';
import "./HeaderDropdown.css"; // Add this CSS file

const HeaderDropdown = ({ 
  onClear, 
  onNewChat, 
  onSave, 
  onToggleHistory,
  onSearch,
  searchQuery,
  setSearchQuery
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [showSearch, setShowSearch] = useState(false);

  return (
    <div className="header-dropdown">
      <button 
        className="dropdown-toggle"
        onClick={() => setIsOpen(!isOpen)}
      >
        <Menu size={20} className="dropdown-icon" />
      </button>

      {isOpen && (
        <div className="dropdown-menu">
          <div className="search-container">
            <button 
              className="search-btn" 
              onClick={() => setShowSearch(!showSearch)}
            >
              <Search size={16} className="theme-adaptive-icon" />
            </button>
            {showSearch && (
              <input
                type="text"
                className="search-input"
                placeholder="Search messages..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && onSearch(searchQuery)}
              />
            )}
          </div>
          
          <ChatActions onClear={onClear} onNewChat={onNewChat} />
          <SaveChatButton onSave={onSave} />
          
          <button 
            className="history-toggle-btn"
            onClick={() => {
              onToggleHistory();
              setIsOpen(false);
            }}
            title="History"
          >
            <img src={historyicon} alt="History" className="theme-adaptive-icon" />
            History
          </button>
        </div>
      )}
    </div>
  );
};

export default HeaderDropdown;