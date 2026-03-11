import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./Landing.css";

const Landing = () => {
  const navigate = useNavigate();
  const [agentType, setAgentType] = useState("female"); // Default to male agent

  const handleAgentSelection = (type) => {
    setAgentType(type);
    localStorage.setItem("agentType", type); // Save the agent type to localStorage
  };

  const handleEnterAgent = () => {
    navigate("/agent"); // Redirect to the agent page
  };

  return (
    <div className="landing-container">
      <h2>Welcome to your Brave Dialogue Tool</h2>
      <p>Choose your agent and start interacting:</p>
      <div className="agent-selection">
        <button
          onClick={() => handleAgentSelection("female")}
          className={agentType === "female" ? "selected" : ""}
        >Female Agent</button>
        <button
          onClick={() => handleAgentSelection("male")}
          className={agentType === "male" ? "selected" : ""}
        >Male Agent</button>
      </div>
      <button onClick={handleEnterAgent} className="enter-agent-button">Start a Dialogue</button>
    </div>
  );
};

export default Landing;
