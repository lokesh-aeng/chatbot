import React, { useState } from "react";
import'./ChatTitleModal.css'
const ChatTitleModal = ({ onSave, onClose }) => {
  const [title, setTitle] = useState("");

  const handleSubmit = () => {
    if (title.trim()) {
      onSave(title);
      onClose();
    } else {
      alert("Please enter a chat title.");
    }
  };

  return (
    <div className="modal-save-backdrop">
      <div className="modal-save">
        <h3>Name this Chat</h3>
        <input
          type="text"
          placeholder="Enter chat title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />
        <div className="modal-save-buttons">
          <button onClick={handleSubmit} className="confirm-save-btn">Save</button>
          <button onClick={onClose} className="cancel-save-btn">Cancel</button>
        </div>
      </div>
    </div>
  );
};

export default ChatTitleModal;
