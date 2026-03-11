import React, { useState, useEffect, useRef } from "react";
import ButtonPanel from "./ButtonPanel";
import VirtualAgent from "./VirtualAgent";

const ChatInterface = () => {
  const [chatHistory, setChatHistory] = useState([]);
  const [currentNode, setCurrentNode] = useState("initial");
  const [currentNodeData, setCurrentNodeData] = useState(null);
  const [hasStarted, setHasStarted] = useState(false);
  const chatBoxRef = useRef(null);

  useEffect(() => {
    if (currentNode && hasStarted) {
      fetch("http://localhost:3001/api/next-turn", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nodeId: currentNode })
      })
        .then((res) => res.json())
        .then((data) => {
          if (data.error) {
            console.error("API Error:", data.error);
            return;
          }
          setCurrentNodeData(data);
          // Only add to history if it's not a duplicate of the last agent message
          setChatHistory((prev) => {
            const lastMsg = prev[prev.length - 1];
            if (lastMsg && lastMsg.sender === "agent" && lastMsg.text === data.agentResponse) {
              return prev; // Prevent double renders in StrictMode
            }
            return [...prev, { sender: "agent", text: data.agentResponse }];
          });
        })
        .catch((err) => console.error("Fetch error:", err));
    }
  }, [currentNode, hasStarted]);

  // Auto-scroll to bottom of chat
  useEffect(() => {
    if (chatBoxRef.current) {
      chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight;
    }
  }, [chatHistory]);

  const handleUserSelection = (nextNode, text, action) => {
    if (action?.type === "RESET") {
      setChatHistory([]);
      setCurrentNode("initial");
      setCurrentNodeData(null);
      setHasStarted(false);
      return;
    }
    setChatHistory((prev) => [...prev, { sender: "user", text }]);
    setCurrentNode(nextNode);
  };

  if (!hasStarted) {
    return (
      <div className="chat-container start-screen">
        <button className="start-btn" onClick={() => setHasStarted(true)}>
          Start Conversation
        </button>
      </div>
    );
  }

  return (
    <div className="chat-container">
      <div className="main-content">
        <VirtualAgent nodeData={currentNodeData} />
        <div className="chat-box" ref={chatBoxRef}>
          {chatHistory.map((msg, index) => (
            <div key={index} className={msg.sender === "agent" ? "agent-msg" : "user-msg"}>
              {msg.text}
            </div>
          ))}
        </div>
      </div>
      <ButtonPanel nodeData={currentNodeData} handleUserSelection={handleUserSelection} />
    </div>
  );
};

export default ChatInterface;
