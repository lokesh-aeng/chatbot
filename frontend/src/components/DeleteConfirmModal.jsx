import React from "react";
import './DeleteConfirmModal.css'
const DeleteConfirmModal = ({ title, onConfirm, onCancel }) => {
  return (
    <div className="modal-backdrop">
      <div className="modal">
        <h3>Delete Chat</h3>
        <p>Are you sure you want to delete <strong>{title || "Untitled Chat"}</strong>?</p>
        <div className="modal-buttons">
          <button className="confirm-btn" onClick={onConfirm}>Yes, Delete</button>
          <button className="cancel-btn" onClick={onCancel}>Cancel</button>
        </div>
      </div>
    </div>
  );
};

export default DeleteConfirmModal;
