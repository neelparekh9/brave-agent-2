# ai_negotiator_api.py

from flask import Flask, request, jsonify
from negotiation_bot_kg import get_memory, conversation, extract_preferences, extract_structured_offer, get_dynamic_context_from_kg, NegotiationKnowledgeGraph, INITIAL_SUBJECTIVE_LIMIT, TRUE_MAX_SALARY
import datetime
import logging
import json
import re

app = Flask(__name__)

# Basic logging setup for the Flask app
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Global state for the negotiation (for demonstration purposes)
# In a production environment, this would be managed per user session.
negotiation_sessions = {}

class NegotiationSessionState:
    def __init__(self, session_id):
        self.session_id = session_id
        self.kg = NegotiationKnowledgeGraph(session_id)
        self.current_turn = 0
        self.subjective_limit = INITIAL_SUBJECTIVE_LIMIT
        self.last_agent_offer_node_id = None
        self.last_agent_offer_details = None

    def get_agent_reply(self, user_input):
        self.current_turn += 1
        
        # Logic for acceptance handling (from negotiation_bot_kg.py)
        accepted = False
        if self.last_agent_offer_node_id and re.search(r"\b(deal|accept|agree|sounds good|let\'?s do it|i\'?ll take it|happy to take it|ok)\b", user_input, re.IGNORECASE):
            prev_base = self.last_agent_offer_details.get("base") if self.last_agent_offer_details else None
            user_offer_details = extract_structured_offer(user_input)
            user_base = user_offer_details.get("base")
            
            if isinstance(prev_base, int) and (user_base is None or user_base == prev_base):
                accepted = True
                self.kg.update_offer_status(self.last_agent_offer_node_id, "accepted")
                self.kg.add_turn(user_input, "Agreement Reached.", self.subjective_limit) 
                
                if user_offer_details:
                    self.kg.add_offer(self.current_turn, user_offer_details, "candidate", status="accepted_trigger")
                else:
                    self.kg.add_offer(self.current_turn, {"status_trigger": "acceptance"}, "candidate", status="accepted_trigger")
                    
                concluding_reply = f"Great! Then we have a deal based on our last offer: {json.dumps(self.last_agent_offer_details)}. I\'?m thrilled to have you join the team and will follow up with the formal offer letter shortly."
                self.kg.graph.nodes[self.kg._get_turn_node_id(self.current_turn)]["agent_response"] = concluding_reply
                return concluding_reply

        if accepted:
            return ""

        extract_preferences(user_input, self.kg)
        candidate_offer_details = extract_structured_offer(user_input)

        last_candidate_offer_info = self.kg.get_last_offer_details("candidate")
        rejected_agent_offers_count = len(self.kg.get_offers_by_status("rejected", "agent"))
        prev_limit_from_kg = self.kg.get_current_limit() or INITIAL_SUBJECTIVE_LIMIT

        if self.current_turn == 1:
            self.subjective_limit = INITIAL_SUBJECTIVE_LIMIT
        elif rejected_agent_offers_count == 0 and last_candidate_offer_info:
            _, candidate_offer, _ = last_candidate_offer_info
            candidate_base = candidate_offer.get("base")
            if isinstance(candidate_base, int):
                midpoint = (prev_limit_from_kg + candidate_base) // 2
                self.subjective_limit = min(TRUE_MAX_SALARY, midpoint)
            else:
                self.subjective_limit = min(TRUE_MAX_SALARY, int(prev_limit_from_kg * 1.05))
        elif rejected_agent_offers_count == 1:
            self.subjective_limit = min(TRUE_MAX_SALARY, int(prev_limit_from_kg * 1.08))
        else: 
            self.subjective_limit = TRUE_MAX_SALARY
            
        self.subjective_limit = max(self.subjective_limit, prev_limit_from_kg)

        kg_context_for_prompt = get_dynamic_context_from_kg(self.kg)

        inputs = {
            "message": user_input,
            "subjective_limit": self.subjective_limit,
            "kg_context": kg_context_for_prompt
        }

        try:
            result = conversation.invoke(
                inputs,
                config={"configurable": {"session_id": self.session_id}}
            )
            reply = result.content.strip()
            
            self.kg.add_turn(user_input, reply, self.subjective_limit)

            if candidate_offer_details:
                new_candidate_offer_node_id = self.kg.add_offer(self.current_turn, candidate_offer_details, "candidate")
                if self.last_agent_offer_node_id and self.kg.graph.nodes[self.last_agent_offer_node_id].get("status") == "proposed":
                    self.kg.update_offer_status(self.last_agent_offer_node_id, "rejected")

            agent_offer_details = extract_structured_offer(reply)
            if agent_offer_details:
                agent_base = agent_offer_details.get("base")
                if isinstance(agent_base, int) and agent_base <= self.subjective_limit:
                    new_agent_offer_node_id = self.kg.add_offer(self.current_turn, agent_offer_details, "agent")
                    self.last_agent_offer_node_id = new_agent_offer_node_id
                    self.last_agent_offer_details = agent_offer_details
                    
                    rejected_agent_offers = self.kg.get_offers_by_status("rejected", "agent")
                    for _, rejected_details, rejected_node_id in rejected_agent_offers:
                        if rejected_details.get("base") == agent_base:
                            self.kg.add_similar_offer_relation(new_agent_offer_node_id, rejected_node_id)
                            break
                elif isinstance(agent_base, int):
                    self.last_agent_offer_node_id = None
                    self.last_agent_offer_details = None
                else:
                    self.kg.add_offer(self.current_turn, agent_offer_details, "agent")
                    self.last_agent_offer_node_id = None
                    self.last_agent_offer_details = None
            else:
                self.last_agent_offer_node_id = None
                self.last_agent_offer_details = None
            return reply

        except Exception as e:
            logging.error(f"Error during invocation: {e}")
            return f"Error: {str(e)}"

@app.route("/negotiate", methods=["POST"])
def negotiate():
    data = request.json
    user_input = data.get("userInput")
    session_id = data.get("sessionId", "default_session") # Use a session ID from the frontend

    if not user_input:
        return jsonify({"error": "No userInput provided"}), 400

    if session_id not in negotiation_sessions:
        negotiation_sessions[session_id] = NegotiationSessionState(session_id)
        logging.info(f"New negotiation session created: {session_id}")

    session_state = negotiation_sessions[session_id]
    agent_reply = session_state.get_agent_reply(user_input)
    
    return jsonify({"reply": agent_reply})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)


