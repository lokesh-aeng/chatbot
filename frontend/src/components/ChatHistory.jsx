import React, { useEffect, useState } from "react";
import deletechat from "/src/images/deletechat.png"
import './ChatHistory.css'
import DeleteConfirmModal from "./DeleteConfirmModal";

const ChatHistory = ({ onLoadHistory, visible, onClose }) => {
  const [history, setHistory] = useState([]);
  const [pendingDelete, setPendingDelete] = useState(null);

  useEffect(() => {
    const saved = JSON.parse(localStorage.getItem("chatHistory")) || [];
    setHistory(saved);
  }, [visible]); // refresh history every time it's opened

  const handleClick = (messages) => {
    onLoadHistory(messages);
    onClose(); // close panel when chat is loaded
  };

  const handleConfirmDelete = () => {
    const updated = history.filter((chat) => chat.id !== pendingDelete.id);
    setHistory(updated);
    localStorage.setItem("chatHistory", JSON.stringify(updated));
    setPendingDelete(null);
  };

  const confirmDelete = (chat) => {
    setPendingDelete(chat);
  };

  return (
    <>
      <div className={`chat-history-panel ${visible ? "visible" : ""}`}>
        <div className="chat-history-header">
          <h2>🕘 Chat History</h2>
          <button className="close-history" onClick={onClose}>❌</button>
        </div>

        <div>
          {history.map((chat, index) => (
            <div key={chat.id}>
              <div onClick={() => handleClick(chat.messages)} className="chat-entry">
                <div className="chatinfo">
                <strong>{chat.title || `Chat ${index + 1}`}</strong>
                <br />
                <small>{new Date(chat.id).toLocaleString()}</small>
                </div>
              <div className="delete-button">
              <button
                className="delete-button"
                onClick={() => confirmDelete(chat)}
                title="Delete chat"
              >
                
                <img src={deletechat} alt="🗑️" />
              </button>
              </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {visible && <div className="chat-history-overlay" onClick={onClose}></div>}

      {pendingDelete && (
        <DeleteConfirmModal
          title={pendingDelete.title}
          onConfirm={handleConfirmDelete}
          onCancel={() => setPendingDelete(null)}
        />
      )}
    </>
  );
};

export default ChatHistory;
