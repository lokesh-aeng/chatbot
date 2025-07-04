
import React, { useState,useEffect } from "react";
import send from "/src/images/send.png"
import clearinputdark from "/src/images/clearinputdark.png"
import senddark from "/src/images/senddark.png"
import './ChatForm.css'

const Chatform = ({ onSendMessage,editablePrompt, inputRef }) => {
  const [message, setMessage] = useState("");
  useEffect(() => {
    if (editablePrompt !== "") {
      setMessage(editablePrompt);
    }
  }, [editablePrompt]);
  const handleSubmit = (e) => {
    e.preventDefault();
    if (message.trim() === "") return;
    onSendMessage(message);
    setMessage("");
  };

  const clearInput = () => {
    setMessage("");
  };
  

  return (
    <form onSubmit={handleSubmit} className="chat-form">
      <div className="ip">
      <div className="input-wrapper">
        <input
          ref={inputRef}
          type="text"
          className="message-input"
          placeholder="Type your message..."
          maxLength={500}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
        />
          <button type="button" className="clear-btn" onClick={clearInput}>
            <img src={clearinputdark} alt="❌" />
          </button>
          
      </div>
      </div>   

      <div className="submit">
        <button type="submit" className="submit-btn" >
      <img  src={senddark} alt="" />
      </button>
      </div>
      
    </form>
  );
};

export default Chatform;




