import React from "react";
import "./ConfirmModal.css"; // optional for custom styles

const ConfirmModal = ({ message, onConfirm, onCancel }) => {
  return (
    <div className="confirm-modal-backdrop">
      <div className="confirm-modal">
        <p>{message}</p>
        <div className="confirm-buttons">
          <button onClick={onConfirm} className="confirm">Yes</button>
          <button onClick={onCancel} className="cancel">Cancel</button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmModal;