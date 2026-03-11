// src/components/Login.js
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./Login.css";
import logo from "../assets/images/peace_agent_logo.jpeg"; // Adjust path as needed

const Login = () => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  const handleLogin = () => {
    if (username && password) {
      navigate("/landing"); // Redirect to landing page
    } else {
      alert("Please enter both username and password.");
    }
  };

  return (
    <div className="login-container">
      <img src={logo} alt="Peace Agent Logo" className="login-logo" /> {/* Add logo here */}
      <h2>Peace Building Login</h2>
      <input
        type="text"
        placeholder="Username"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
      />
      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />
      <button onClick={handleLogin}>Login</button>
    </div>
  );
};

export default Login;
