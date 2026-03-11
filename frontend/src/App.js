import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Login from "./components/Login";
import Landing from "./components/Landing";
import ChatInterface from "./components/ChatInterface";
import "./styles.css"; // Ensure styles are imported

function App() {
  return (
    <Router>
      <div className="app">
        <Routes>
          <Route path="/" element={<Login />} />
          <Route path="/landing" element={<Landing />} />
          <Route path="/agent" element={<ChatInterface />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
