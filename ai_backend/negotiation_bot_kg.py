import os
import re
import logging
import json
import datetime
from dotenv import load_dotenv
from typing import List, Optional, Dict, Any

from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain_core.runnables.history import RunnableWithMessageHistory

from negotiation_kg import NegotiationKnowledgeGraph

# Configure logging to file and stdout for debugging and auditability.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("conversation_kg_enhanced.log", "a", encoding="utf-8")
    ]
)

# Project constants used by heuristics and the prompt.
MAX_BUDGET = 100_000
INITIAL_BUDGET_LIMIT = 20_000
MAX_TIMELINE_MONTHS = 5
INITIAL_TIMELINE_MONTHS = 2

# Load environment variables for LLM credentials / API base.
load_dotenv()
use_litellm = os.getenv("LITELLM_ENABLED", "").lower() in {"1", "true", "yes"}
api_base = os.getenv("LITELLM_API_BASE")
model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

if use_litellm:
    api_key = os.getenv("OPENAI_API_KEY1") or os.getenv("OPENAI_API_KEY")
else:
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY1")

if not api_key:
    print("Error: OPENAI_API_KEY environment variable not set.")
    exit()

# Function: extract_structured_offer
# Purpose: Parse freeform PM/stakeholder text to extract project requirements
#          dictionary (budget, timeline, features, etc.). Returns {} if no
#          valid requirements found.
def extract_structured_offer(text: str) -> Dict[str, Any]:
    requirements = {}
    
    # Extract budget mentions
    budget_matches = re.findall(r"(?:budget|cost|price|spend|allocation|funding|pay|paying)\s*(?:of|is|at|around|for|about)?\s*\$?(\d{1,3}(?:,\d{3})*|\d+)[kK]?", text, re.IGNORECASE)
    all_numeric_matches = re.findall(r"\$?(\d{1,3}(?:,\d{3})*|\d+)[kK]?\b", text)

    potential_budgets = []
    processed_matches = set()

    # Prefer explicit budget phrases first
    for m in budget_matches:
        num_str = m.replace(",", "").lower()
        if num_str in processed_matches:
            continue
        multiplier = 1000 if 'k' in num_str else 1
        try:
            budget = int(re.sub(r"[k$]", "", num_str)) * multiplier
            if 1000 < budget < 1000000:
                 potential_budgets.append(budget)
                 processed_matches.add(num_str)
        except ValueError:
            continue
            
    # Fallback: other budget-like numeric mentions
    if not potential_budgets and all_numeric_matches:
         try:
             numeric_values = [int(m.replace(",", "")) for m in all_numeric_matches if m not in processed_matches]
             valid_budgets = [s for s in numeric_values if 1000 < s < 1000000]
             if valid_budgets:
                 potential_budgets.append(max(valid_budgets))
         except ValueError:
             pass

    if potential_budgets:
        requirements["budget"] = max(potential_budgets)

    # Extract timeline mentions (in months)
    timeline_matches = re.findall(r"(\d+)\s*(?:month|months|mo)", text, re.IGNORECASE)
    if timeline_matches:
        try:
            timeline = int(timeline_matches[0])
            if 1 <= timeline <= 12:
                requirements["timeline_months"] = timeline
        except ValueError:
            pass

    # Detect feature mentions
    features = []
    if re.search(r"\b(?:mobile|phone|smartphone|app|application)\b", text, re.IGNORECASE):
        features.append("mobile access")
    if re.search(r"\b(?:status|track|tracking|progress|update|state)\b", text, re.IGNORECASE):
        features.append("status tracking")
    if re.search(r"\b(?:simple|easy|user-friendly|intuitive|straightforward)\b", text, re.IGNORECASE):
        features.append("simplicity")
    if re.search(r"\b(?:overview|dashboard|view|see|monitor)\b", text, re.IGNORECASE):
        features.append("overview/dashboard")
             
    # Deduplicate features and clean up empty lists
    if features:
        requirements["features"] = sorted(list(set(features)))
            
    # If no budget or timeline identified, return empty dict to signal "no structured requirements".
    if "budget" not in requirements and "timeline_months" not in requirements:
        return {}
        
    return requirements

# Function: extract_preferences
# Purpose: Detect stakeholder preference mentions (mobile access, status tracking, simplicity) and
#          register them in the provided NegotiationKnowledgeGraph instance.
def extract_preferences(text: str, kg: NegotiationKnowledgeGraph):
    if re.search(r"\b(?:mobile|phone|smartphone|app|application|on the go|convenience)\b", text, re.IGNORECASE):
        kg.add_candidate_preference("mobile access")
    if re.search(r"\b(?:status|track|tracking|progress|update|state|in process|completed)\b", text, re.IGNORECASE):
        kg.add_candidate_preference("status tracking")
    if re.search(r"\b(?:simple|easy|user-friendly|intuitive|straightforward|not complicated)\b", text, re.IGNORECASE):
        kg.add_candidate_preference("simplicity")
    if re.search(r"\b(?:overview|dashboard|view|see|monitor|clear overview)\b", text, re.IGNORECASE):
        kg.add_candidate_preference("overview/dashboard")

# Class: CustomConversationBufferMemory
# Purpose: Wrapper around ConversationBufferMemory to handle different memory backend shapes.
#          Provides compatibility helpers for older/newer LangChain memory types.
class CustomConversationBufferMemory(ConversationBufferMemory):
    @property
    def messages(self):
        # Return messages from wrapped chat_memory if available, otherwise adapt stored buffer.
        if hasattr(self, "chat_memory") and hasattr(self.chat_memory, "messages"):
            return self.chat_memory.messages
        if isinstance(self.buffer, str):
            return [msg for msg in self.buffer.split("\n") if msg] 
        return self.buffer

    def add_messages(self, messages: List):
        # Append messages to underlying memory storage, preserving compatibility.
        if hasattr(self, "chat_memory") and hasattr(self.chat_memory, "add_messages"):
            self.chat_memory.add_messages(messages)
        else:
            if not isinstance(self.buffer, list):
                self.buffer = []
            self.buffer.extend(messages)

# LLM configuration and initialization
llm_params = {
    "openai_api_key": api_key,
    "temperature": 0.6,
    "model": model_name
}
# If a custom API base is provided (e.g., internal LiteLLM), only use it when explicitly enabled.
if api_base and use_litellm:
    llm_params["openai_api_base"] = api_base
    print(f"Using API Base: {api_base} with Model: {llm_params['model']}")
else:
    if api_base and not use_litellm:
        print("LITELLM_API_BASE is set but LITELLM_ENABLED is not true; using OpenAI default base.")

llm = ChatOpenAI(**llm_params)

# Stakeholder meeting prompt template: instructs the agent, supplies KG context and limits.
stakeholder_template = f'''
## Dialogue So Far
{{history}}

## Knowledge Graph Context
{{kg_context}}

# Stakeholder Simulation Agent: Jack Collins (CEO)

## Agent Identity
You are **Jack Collins**, the Consumer and CEO of Systems Solutions. You are participating in a kickoff meeting for "Project Vector," a new mobile application that seamlessly tracks client requests. The person you're speaking with is the Project Manager and System Engineer for this project. Your goal is to get alignment on scope, timeline, and budget.

## Your Persona
- **Goal:** Get a tool that is simple for my team to use and that gives me a clear overview of all client requests.
- **Concern:** You hate overly complicated software that requires a lot of training. You're worried the project will go over budget.
- **Style:** Pragmatic, data-driven, cautious. You will push back on features that seem overly complex for the timeline.

## Meeting Context
- **Scenario:** This is the kickoff meeting for Project Vector
- **Your Role:** CEO and primary stakeholder
- **PM's Goal:** Get alignment on scope, timeline, and budget
- **Your Budget:** Starting at $20,000, but you understand it may need to be higher. You're willing to negotiate up to around $100,000 if the PM makes a strong case.
- **Your Timeline:** You expect 2 months initially. This is easily negotiable to 3 months. You're willing to go to 5 months but do NOT want to go past that.
- **Key Requirements:** 
  - Simple tool for your team (not complicated)
  - Clear overview of all client requests
  - Mobile access capability (you're always on the go and need convenience)
  - Status tracking ("In process" or "Completed" status)

## Problem Statement
When asked what problem you're trying to solve, you should say: "The team needs a way to track client requests more easily. Right now, it's all in spreadsheets and it's hard to see status updates."

## Behavioral Rules
- Begin the conversation by introducing yourself and saying "I really appreciate your willingness to work on this project for me." Then ask the user to start the meeting.
- Respond based on the user's message, staying in character as Jack Collins.
- Create realistic, challenging dialogue. If the user makes a request that conflicts with your goals (simplicity, budget, timeline), voice your concerns.
- You can disagree if the user provides misunderstanding of the problem. A realistic meeting involves debate and negotiation of the requirements.
- Keep your responses concise and conversational (2-4 sentences typically).
- When asked what problem you're trying to solve, ensure you say: "The team needs a way to track client requests more easily. Right now, it's all in spreadsheets and it's hard to see status updates."
- When asked for timeline expectations, you say 2 months. 2 months is easily negotiable to 3 months. You're willing to go to 5 months but do not want to go past that.
- If asked what other capabilities are needed, add: "I could get updates from my phone, that would be great too. I'm always on the go and I need convenience. Also, perhaps if the system tracks 'In process' or 'Completed' it would definitely be helpful."
- If asked for budget considerations, give a budget of $20,000. The user may argue that the budget is too small. They would be correct but you should negotiate with them. The appropriate budget should be around $100,000 if they make a strong case.
- Use prior conversation context ({{history}}) and KG context ({{kg_context}}) to guide each new reply.
- Avoid repeating introductions or expressing excitement more than once unless tone shifts.
- Respond differently as the conversation progresses—deepen the discussion instead of restarting.

## Response Format
Always preface your response with "**Jack:**" followed by your response. Keep responses concise (2-4 sentences), conversational, and in character. Be pragmatic and data-driven. Show your concerns about complexity and budget when appropriate.

PM says: "{{message}}"

## Your Response:
'''
prompt = PromptTemplate.from_template(stakeholder_template)

# Memory factory: used by RunnableWithMessageHistory to supply conversation history
def get_memory(session_id: str):
    return CustomConversationBufferMemory(
        memory_key="history",
        return_messages=True,
        input_key="message"
    )

# Build the runnable conversation chain and wire it to message-history handling.
chain = prompt | llm
conversation = RunnableWithMessageHistory(
    runnable=chain,
    get_session_history=get_memory,
    input_messages_key="message",
    history_messages_key="history"
)

# Function: get_dynamic_context_from_kg
# Purpose: Build a concise, human-readable context string from the KG that
#          the prompt can include to inform the LLM about preferences, project requirements, etc.
def get_dynamic_context_from_kg(kg: NegotiationKnowledgeGraph) -> str:
    context_parts = []
    prefs = kg.get_candidate_preferences()
    if prefs:
        context_parts.append(f"Stakeholder Preferences/Requirements: {', '.join(prefs)}.")
        
    rejected_stakeholder_requirements = kg.get_offers_by_status("rejected", "agent")
    if rejected_stakeholder_requirements:
        req_summaries = []
        for turn, details, node_id in rejected_stakeholder_requirements[:2]: # Limit context
             req_summaries.append(f"Turn {turn}: {json.dumps(details)}")
        context_parts.append(f"Recently Rejected Stakeholder Requirements: [{'; '.join(req_summaries)}]. Be aware of these concerns.")

    last_stakeholder_req_info = None
    stakeholder_reqs_proposed = kg.get_offers_by_status("proposed", "agent")
    if stakeholder_reqs_proposed:
        last_stakeholder_req_info = stakeholder_reqs_proposed[0]
    else:
        all_stakeholder_reqs = kg.get_last_offer_details("agent") 
        if all_stakeholder_reqs:
            last_stakeholder_req_info = all_stakeholder_reqs
            
    if last_stakeholder_req_info:
        turn, details, node_id = last_stakeholder_req_info
        status = kg.graph.nodes[node_id].get("status", "proposed")
        context_parts.append(f"Last Stakeholder Requirements (Turn {turn}, Status: {status}): {json.dumps(details)}.")
        
    last_pm_requirements_info = kg.get_last_offer_details("candidate")
    if last_pm_requirements_info:
        turn, details, node_id = last_pm_requirements_info
        context_parts.append(f"Last PM Proposal (Turn {turn}): {json.dumps(details)}.")
        
    if not context_parts:
        return "No specific context from Knowledge Graph yet."
        
    return " ".join(context_parts)

# Command-line debug harness
# When executed directly, provide an interactive CLI for manually testing the negotiation agent.
if __name__ == "__main__":
    print("\nEnhanced Negotiation Agent Active! Type your message as the candidate.\nType 'exit' to stop.\n")
    logging.info("=== Enhanced Negotiation Agent Active ===")
    session_id = f"negotiation-session-kg-enhanced-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

    kg = NegotiationKnowledgeGraph(session_id)

    current_turn = 0
    subjective_limit = INITIAL_SUBJECTIVE_LIMIT
    last_agent_offer_node_id = None 
    last_agent_offer_details = None 

    while True:
        previous_agent_offer_node_id = last_agent_offer_node_id
        previous_agent_offer_details = last_agent_offer_details
        
        user_input = input(f"Candidate (Turn {current_turn + 1}): ").strip()
        if user_input.lower() in ["exit", "quit"]:
            logging.info("Session ended by user.")
            print("Session ended.")
            print("\n--- Final Negotiation Summary ---")
            print(kg.get_negotiation_summary())
            break

        logging.info(f"Candidate (Turn {current_turn + 1}): {user_input}")

        # Acceptance detection: handle explicit acceptances of the last agent offer.
        accepted = False
        if previous_agent_offer_node_id and re.search(r"\b(deal|accept|agree|sounds good|let'?s do it|i'?ll take it|happy to take it|ok)\b", user_input, re.IGNORECASE):
            prev_base = previous_agent_offer_details.get("base") if previous_agent_offer_details else None
            user_offer_details = extract_structured_offer(user_input)
            user_base = user_offer_details.get("base")
            
            if isinstance(prev_base, int) and (user_base is None or user_base == prev_base):
                accepted = True
                logging.info(f"Detected acceptance of previous agent offer: {previous_agent_offer_node_id}")
                kg.update_offer_status(previous_agent_offer_node_id, "accepted")
                current_turn = kg.add_turn(user_input, "Agreement Reached.", current_subjective_limit) 
                
                # Add candidate acceptance offer node to the KG for traceability.
                if user_offer_details:
                    kg.add_offer(current_turn, user_offer_details, "candidate", status="accepted_trigger")
                else:
                     kg.add_offer(current_turn, {"status_trigger": "acceptance"}, "candidate", status="accepted_trigger")
                     
                concluding_reply = f"Great! Then we have a deal based on our last offer: {json.dumps(previous_agent_offer_details)}. I'm thrilled to have you join the team and will follow up with the formal offer letter shortly."
                print(f"\nEmployer Agent (Conclusion):", concluding_reply, "\n")
                logging.info(f"Employer Agent (Conclusion): {concluding_reply}")
                kg.graph.nodes[kg._get_turn_node_id(current_turn)]["agent_response"] = concluding_reply
                
                print("\n--- Negotiation Concluded (Accepted) ---")
                print(kg.get_negotiation_summary())
                logging.info("Negotiation concluded successfully (Accepted).")
                break 

        if accepted:
            continue # Should not be reached due to break, but kept for safety

        # Record any stated preferences and parse possible candidate offers from input.
        extract_preferences(user_input, kg)
        candidate_offer_details = extract_structured_offer(user_input)

        # Gather KG-derived context and counters used to update subjective_limit heuristics.
        last_candidate_offer_info = kg.get_last_offer_details("candidate")
        rejected_agent_offers_count = len(kg.get_offers_by_status("rejected", "agent"))
        prev_limit_from_kg = kg.get_current_limit() or INITIAL_SUBJECTIVE_LIMIT

        # Heuristics to set the current subjective limit for this turn.
        if current_turn == 0:
            current_subjective_limit = INITIAL_SUBJECTIVE_LIMIT
        elif rejected_agent_offers_count == 0 and last_candidate_offer_info:
            _, candidate_offer, _ = last_candidate_offer_info
            candidate_base = candidate_offer.get("base")
            if isinstance(candidate_base, int):
                midpoint = (prev_limit_from_kg + candidate_base) // 2
                current_subjective_limit = min(TRUE_MAX_SALARY, midpoint)
            else:
                current_subjective_limit = min(TRUE_MAX_SALARY, int(prev_limit_from_kg * 1.05))
        elif rejected_agent_offers_count == 1:
             current_subjective_limit = min(TRUE_MAX_SALARY, int(prev_limit_from_kg * 1.08))
        else: 
            current_subjective_limit = TRUE_MAX_SALARY
            
        # Never lower the subjective limit below what the KG already indicates.
        current_subjective_limit = max(current_subjective_limit, prev_limit_from_kg)

        # Build KG context for the LLM prompt.
        kg_context_for_prompt = get_dynamic_context_from_kg(kg)

        inputs = {
            "message": user_input,
            "subjective_limit": current_subjective_limit,
            "kg_context": kg_context_for_prompt
        }

        try:
            # Invoke the conversation runnable which will use stored history + KG context.
            result = conversation.invoke(
                inputs,
                config={"configurable": {"session_id": session_id}}
            )
            reply = result.content.strip()
            logging.info(f"Employer Agent (Turn {current_turn + 1}, Limit: ${current_subjective_limit}): {reply}")
            print(f"\nEmployer Agent (Limit: ${current_subjective_limit}):", reply, "\n")

            # Store turn and agent reply in the KG.
            current_turn = kg.add_turn(user_input, reply, current_subjective_limit)

            # If candidate provided a concrete offer, add it and mark prior agent offers rejected when applicable.
            if candidate_offer_details:
                new_candidate_offer_node_id = kg.add_offer(current_turn, candidate_offer_details, "candidate")
                logging.info(f"KG: Added Candidate Offer: {candidate_offer_details} for Turn {current_turn}")
                if previous_agent_offer_node_id and kg.graph.nodes[previous_agent_offer_node_id].get("status") == "proposed":
                     kg.update_offer_status(previous_agent_offer_node_id, "rejected")
                     logging.info(f"KG: Marked previous agent offer {previous_agent_offer_node_id} as rejected due to candidate counter.")

            # Parse any structured offer from the agent's reply and update KG bookkeeping.
            agent_offer_details = extract_structured_offer(reply)
            if agent_offer_details:
                agent_base = agent_offer_details.get("base")
                if isinstance(agent_base, int) and agent_base <= current_subjective_limit:
                    new_agent_offer_node_id = kg.add_offer(current_turn, agent_offer_details, "agent")
                    logging.info(f"KG: Added Agent Offer: {agent_offer_details} for Turn {current_turn}")
                    last_agent_offer_node_id = new_agent_offer_node_id
                    last_agent_offer_details = agent_offer_details
                    
                    # If a previously rejected agent offer had the same base, create a 'similar' relation.
                    rejected_agent_offers = kg.get_offers_by_status("rejected", "agent")
                    for _, rejected_details, rejected_node_id in rejected_agent_offers:
                        if rejected_details.get("base") == agent_base:
                             kg.add_similar_offer_relation(new_agent_offer_node_id, rejected_node_id)
                             logging.warning(f"KG: Agent offer {new_agent_offer_node_id} is similar to rejected offer {rejected_node_id}.")
                             break
                elif isinstance(agent_base, int):
                     logging.warning(f"KG: Agent offer base ${agent_base} exceeded limit ${current_subjective_limit} in Turn {current_turn}. Not adding to KG.")
                     last_agent_offer_node_id = None
                     last_agent_offer_details = None
                else:
                     new_agent_offer_node_id = kg.add_offer(current_turn, agent_offer_details, "agent")
                     logging.info(f"KG: Added Agent Offer (no base salary found): {agent_offer_details} for Turn {current_turn}")
                     last_agent_offer_node_id = None
                     last_agent_offer_details = None
            else:
                 last_agent_offer_node_id = None
                 last_agent_offer_details = None

        except Exception as e:
            # Log invocation errors and continue the interactive loop.
            logging.error(f"Error during invocation: {e}")
            print("⚠️ Error:", str(e))
            continue
