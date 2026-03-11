# Standard file header
# Project: integrated_virtual_agent_final 3
# File: ai_negotiator_api_cors.py
# Brief: Flask CORS-enabled API that manages stakeholder meeting sessions and forwards user messages
#        to the stakeholder conversation model and a knowledge graph (KG).
# Notes: This file maintains simple in-memory session state (not production-safe).
# Author: (auto-added comments)

from flask import Flask, request, jsonify
from flask_cors import CORS
from negotiation_bot_kg import get_memory, conversation, extract_preferences, extract_structured_offer, get_dynamic_context_from_kg, NegotiationKnowledgeGraph, INITIAL_BUDGET_LIMIT, MAX_BUDGET, INITIAL_TIMELINE_MONTHS, MAX_TIMELINE_MONTHS
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
import datetime
import logging
import json
import re
import os

# Create Flask app and enable Cross-Origin Resource Sharing for all routes.
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Basic logging setup for the Flask app
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("flask_api.log", "a", encoding="utf-8")
    ]
)

logger = logging.getLogger(__name__)

# LLM invocation timeout (seconds) to prevent hanging requests
LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", "25"))
_llm_executor = ThreadPoolExecutor(max_workers=4)


class LLMTimeoutError(Exception):
    pass


class LLMInvocationError(Exception):
    pass


def invoke_conversation_with_timeout(inputs, session_id):
    future = _llm_executor.submit(
        conversation.invoke,
        inputs,
        config={"configurable": {"session_id": session_id}}
    )
    try:
        return future.result(timeout=LLM_TIMEOUT_SECONDS)
    except FuturesTimeoutError as e:
        future.cancel()
        raise LLMTimeoutError(f"LLM response timed out after {LLM_TIMEOUT_SECONDS} seconds") from e
    except Exception as e:
        raise LLMInvocationError(str(e)) from e

# Request logging middleware
@app.before_request
def log_request_info():
    client_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', 'Unknown')
    referer = request.headers.get('Referer', 'Direct')
    
    logger.info(f"=== Incoming Request ===")
    logger.info(f"Method: {request.method} | Path: {request.path}")
    logger.info(f"Client IP: {client_ip} | Referer: {referer}")
    logger.info(f"User-Agent: {user_agent[:100]}")  # Truncate long user agents
    
    # Track frontend connections
    if 'localhost:3000' in referer or '127.0.0.1:3000' in referer:
        logger.info(f"✓ Frontend connection detected from browser")
    
    if request.is_json:
        try:
            body_preview = json.dumps(request.json, indent=2)
            # Truncate very long bodies
            if len(body_preview) > 500:
                body_preview = body_preview[:500] + "... (truncated)"
            logger.info(f"Request Body: {body_preview}")
        except Exception as e:
            logger.warning(f"Could not log request body: {e}")

@app.after_request
def log_response_info(response):
    logger.info(f"Response: {response.status_code} for {request.method} {request.path}")
    return response

# Global state for the stakeholder meetings (for demonstration purposes)
# In a production environment, this would be managed per user session storage.
stakeholder_sessions = {}

# Class representing per-session stakeholder meeting state and interaction helpers
class StakeholderSessionState:
    # Initialize a new session state, including a knowledge graph.
    def __init__(self, session_id):
        self.session_id = session_id
        self.kg = NegotiationKnowledgeGraph(session_id)
        self.current_turn = 0

    # Process a user's input and produce the agent's reply.
    # Responsibilities:
    # - extract preferences and structured requirements from the user input
    # - invoke the conversation model to generate the agent reply
    # - add turns and requirements into the KG
    def get_agent_reply(self, user_input):
        self.current_turn += 1

        # Update KG with any preferences expressed by the user input.
        extract_preferences(user_input, self.kg)
        pm_requirements = extract_structured_offer(user_input)

        # Build dynamic context from KG for the conversation model prompt.
        kg_context_for_prompt = get_dynamic_context_from_kg(self.kg)

        inputs = {
            "message": user_input,
            "kg_context": kg_context_for_prompt
        }

        try:
            # Invoke the conversation model with session-specific config and inputs.
            result = invoke_conversation_with_timeout(inputs, self.session_id)
            reply = result.content.strip()
            
            # Record the turn in the KG (using budget limit as placeholder for now)
            self.kg.add_turn(user_input, reply, INITIAL_BUDGET_LIMIT)

            # If the user submitted PM requirements, add them to the KG
            if pm_requirements:
                self.kg.add_offer(self.current_turn, pm_requirements, "candidate")

            # If the agent reply contains structured requirements, record them
            stakeholder_requirements = extract_structured_offer(reply)
            if stakeholder_requirements:
                self.kg.add_offer(self.current_turn, stakeholder_requirements, "agent")

            return reply

        except (LLMTimeoutError, LLMInvocationError):
            raise
        except Exception as e:
            raise LLMInvocationError(str(e)) from e

# Route: /negotiate
# Expects JSON { "userInput": "...", "sessionId": "optional" }
# Creates or resumes a session and returns the agent's reply for the provided input.
@app.route("/negotiate", methods=["POST"])
def negotiate():
    request_timestamp = datetime.datetime.now().isoformat()
    logger.info("=" * 80)
    logger.info(f"[STEP 7: FLASK] Negotiate endpoint called at {request_timestamp}")
    logger.info("=" * 80)
    
    try:
        logger.info(f"[STEP 7: FLASK] Request method: {request.method}")
        logger.info(f"[STEP 7: FLASK] Request headers: {dict(request.headers)}")
        logger.info(f"[STEP 7: FLASK] Request remote address: {request.remote_addr}")
        
        data = request.json
        logger.info(f"[STEP 7: FLASK] Request JSON received: {data is not None}")
        
        if not data:
            logger.error("=" * 80)
            logger.error(f"[STEP 7: FLASK] ❌ ERROR: No JSON data received in request!")
            logger.error("=" * 80)
            return jsonify({"error": "No JSON data provided"}), 400
            
        user_input = data.get("userInput")
        session_id = data.get("sessionId", "default_session")
        
        logger.info(f"[STEP 7: FLASK] Parsed request data:")
        logger.info(f"[STEP 7: FLASK]   - Session ID: {session_id}")
        logger.info(f"[STEP 7: FLASK]   - User input length: {len(user_input) if user_input else 0}")
        logger.info(f"[STEP 7: FLASK]   - User input preview: {user_input[:100] if user_input else 'None'}...")

        if not user_input:
            logger.warning("=" * 80)
            logger.warning(f"[STEP 7: FLASK] ⚠️ WARNING: No userInput provided!")
            logger.warning("=" * 80)
            return jsonify({"error": "No userInput provided"}), 400

        # Lazily create a session state for this session_id
        if session_id not in stakeholder_sessions:
            logger.info(f"[STEP 7: FLASK] Creating new session: {session_id}")
            stakeholder_sessions[session_id] = StakeholderSessionState(session_id)
            logger.info(f"[STEP 7: FLASK] ✓ New stakeholder meeting session created: {session_id}")
        else:
            logger.info(f"[STEP 7: FLASK] Using existing session: {session_id}")

        session_state = stakeholder_sessions[session_id]
        logger.info(f"[STEP 7: FLASK] Session state retrieved:")
        logger.info(f"[STEP 7: FLASK]   - Current turn: {session_state.current_turn}")
        logger.info(f"[STEP 7: FLASK]   - Next turn will be: {session_state.current_turn + 1}")
        
        logger.info(f"[STEP 7: FLASK] Calling get_agent_reply...")
        try:
            agent_reply = session_state.get_agent_reply(user_input)
        except LLMTimeoutError as e:
            logger.error(f"[STEP 7: FLASK] ❌ LLM TIMEOUT: {e}")
            return jsonify({
                "error": "LLM response timed out",
                "details": str(e)
            }), 504
        except LLMInvocationError as e:
            logger.error(f"[STEP 7: FLASK] ❌ LLM INVOCATION ERROR: {e}")
            return jsonify({
                "error": "LLM invocation failed",
                "details": str(e)
            }), 502
        
        logger.info(f"[STEP 7: FLASK] ✓ Agent reply generated!")
        logger.info(f"[STEP 7: FLASK] Reply length: {len(agent_reply) if agent_reply else 0}")
        logger.info(f"[STEP 7: FLASK] Reply preview: {agent_reply[:200] if agent_reply else 'None'}...")
        
        response_data = {"reply": agent_reply}
        logger.info(f"[STEP 7: FLASK] Preparing response JSON...")
        logger.info(f"[STEP 7: FLASK] Response keys: {list(response_data.keys())}")
        
        logger.info("=" * 80)
        logger.info(f"[STEP 7: FLASK] ✓ Sending response back to Node.js")
        logger.info("=" * 80)
        return jsonify(response_data)
        
    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"[STEP 7: FLASK] ❌ EXCEPTION in negotiate endpoint!")
        logger.error(f"[STEP 7: FLASK] Error type: {type(e).__name__}")
        logger.error(f"[STEP 7: FLASK] Error message: {str(e)}")
        logger.error(f"[STEP 7: FLASK] Error traceback:", exc_info=True)
        logger.error("=" * 80)
        return jsonify({
            "error": "Internal server error during negotiation",
            "details": str(e)
        }), 500

# Route: /health
# Simple health endpoint for monitoring and readiness checks.
@app.route("/health", methods=["GET"])
def health():
    logger.info("Health check requested")
    return jsonify({
        "status": "healthy", 
        "message": "AI Stakeholder Simulator API is running",
        "timestamp": datetime.datetime.now().isoformat(),
        "active_sessions": len(stakeholder_sessions)
    })

# Route: /handshake
# Handshake endpoint for connection verification between frontend and backend
@app.route("/handshake", methods=["POST", "GET"])
def handshake():
    try:
        client_info = {
            "method": request.method,
            "timestamp": datetime.datetime.now().isoformat(),
            "remote_addr": request.remote_addr,
            "user_agent": request.headers.get("User-Agent", "Unknown")
        }
        
        if request.method == "POST" and request.is_json:
            client_info["message"] = request.json.get("message", "")
            client_info["session_id"] = request.json.get("sessionId", "none")
        
        logger.info(f"Handshake received from {client_info['remote_addr']}: {json.dumps(client_info, indent=2)}")
        
        return jsonify({
            "status": "success",
            "message": "Handshake successful - Backend is ready",
            "server_timestamp": datetime.datetime.now().isoformat(),
            "client_info": client_info,
            "backend_status": {
                "flask_running": True,
                "port": 5000,
                "active_sessions": len(stakeholder_sessions)
            }
        })
    except Exception as e:
        logger.error(f"Error during handshake: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"Handshake failed: {str(e)}"
        }), 500

if __name__ == "__main__":
    # Run the Flask app (bind to all interfaces on port 5000).
    logger.info("=" * 50)
    logger.info("Starting Flask AI Negotiator API Server")
    logger.info(f"Server will run on http://0.0.0.0:5000")
    logger.info(f"Health check: http://localhost:5000/health")
    logger.info(f"Handshake: http://localhost:5000/handshake")
    logger.info("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=False)
