import '/src/components/SaveButton.css';
import savechat from "/src/images/savechat.png";

const SaveButton = ({ onSave }) => (
  <button className="save-chat-btn" onClick={onSave} title="Save Chat">
    <img src={savechat} alt="Save chat" className="theme-adaptive-icon" />
    <span className="action-text">Save Chat</span>
  </button>
);

export default SaveButton;