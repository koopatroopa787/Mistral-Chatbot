import os
import json
import logging
from pathlib import Path
from mistralai import Mistral
from helper_functions import load_config

# Initialize logger
logger = logging.getLogger("chatbot.conversation_flow")

class ConversationStage:
    """Class representing a stage in a conversation flow"""
    def __init__(self, stage_id, name, system_prompt, user_prompt=None, 
                 next_stages=None, completion_criteria=None, max_turns=3):
        self.stage_id = stage_id
        self.name = name
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        self.next_stages = next_stages or []
        self.completion_criteria = completion_criteria or {}
        self.max_turns = max_turns
        
    def to_dict(self):
        """Convert stage to dictionary for serialization"""
        return {
            "stage_id": self.stage_id,
            "name": self.name,
            "system_prompt": self.system_prompt,
            "user_prompt": self.user_prompt,
            "next_stages": self.next_stages,
            "completion_criteria": self.completion_criteria,
            "max_turns": self.max_turns
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create stage from dictionary"""
        return cls(
            stage_id=data.get("stage_id", ""),
            name=data.get("name", ""),
            system_prompt=data.get("system_prompt", ""),
            user_prompt=data.get("user_prompt", ""),
            next_stages=data.get("next_stages", []),
            completion_criteria=data.get("completion_criteria", {}),
            max_turns=data.get("max_turns", 3)
        )


class ConversationFlow:
    """Class representing a multi-stage conversation flow"""
    def __init__(self, flow_id, name, description="", initial_stage=None, stages=None):
        self.flow_id = flow_id
        self.name = name
        self.description = description
        self.initial_stage = initial_stage
        self.stages = stages or {}
        
    def add_stage(self, stage):
        """Add a stage to the flow"""
        self.stages[stage.stage_id] = stage
        
    def get_stage(self, stage_id):
        """Get a stage by ID"""
        return self.stages.get(stage_id)
        
    def to_dict(self):
        """Convert flow to dictionary for serialization"""
        return {
            "flow_id": self.flow_id,
            "name": self.name,
            "description": self.description,
            "initial_stage": self.initial_stage,
            "stages": {stage_id: stage.to_dict() for stage_id, stage in self.stages.items()}
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create flow from dictionary"""
        flow = cls(
            flow_id=data.get("flow_id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            initial_stage=data.get("initial_stage", "")
        )
        
        # Add stages
        for stage_id, stage_data in data.get("stages", {}).items():
            flow.stages[stage_id] = ConversationStage.from_dict(stage_data)
            
        return flow


class ConversationState:
    """Class representing the current state of a conversation flow"""
    def __init__(self, flow_id=None, current_stage_id=None, completed_stages=None, 
                 stage_turns=None, data=None):
        self.flow_id = flow_id
        self.current_stage_id = current_stage_id
        self.completed_stages = completed_stages or []
        self.stage_turns = stage_turns or {}
        self.data = data or {}
        
    def advance_stage(self, new_stage_id):
        """Advance to a new stage"""
        if self.current_stage_id:
            self.completed_stages.append(self.current_stage_id)
        self.current_stage_id = new_stage_id
        self.stage_turns[new_stage_id] = 0
        
    def increment_turns(self):
        """Increment the turn count for the current stage"""
        if self.current_stage_id in self.stage_turns:
            self.stage_turns[self.current_stage_id] += 1
        else:
            self.stage_turns[self.current_stage_id] = 1
        
    def set_data(self, key, value):
        """Set data value"""
        self.data[key] = value
        
    def get_data(self, key, default=None):
        """Get data value"""
        return self.data.get(key, default)
        
    def to_dict(self):
        """Convert state to dictionary for serialization"""
        return {
            "flow_id": self.flow_id,
            "current_stage_id": self.current_stage_id,
            "completed_stages": self.completed_stages,
            "stage_turns": self.stage_turns,
            "data": self.data
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create state from dictionary"""
        return cls(
            flow_id=data.get("flow_id", ""),
            current_stage_id=data.get("current_stage_id", ""),
            completed_stages=data.get("completed_stages", []),
            stage_turns=data.get("stage_turns", {}),
            data=data.get("data", {})
        )


def get_mistral_client():
    """Get Mistral client instance"""
    api_key = os.environ.get("MISTRAL_API_KEY", "")
    if not api_key:
        logger.error("Missing API key")
        return None
    return Mistral(api_key=api_key)


def check_stage_completion(stage, user_message, conversation_state, client=None):
    """
    Check if a stage is complete based on its completion criteria
    
    Returns:
        bool: True if the stage is complete, False otherwise
        str or None: ID of the next stage if available, None otherwise
    """
    # Check if maximum turns reached
    if conversation_state.stage_turns.get(stage.stage_id, 0) >= stage.max_turns:
        # If there's only one next stage, advance to it
        if len(stage.next_stages) == 1:
            return True, stage.next_stages[0]
        # Otherwise, check completion criteria
    
    # If no completion criteria defined, stage is not complete
    if not stage.completion_criteria:
        return False, None
    
    # Initialize Mistral client if not provided
    if client is None:
        client = get_mistral_client()
        if not client:
            logger.error("Could not initialize Mistral client")
            return False, None
    
    config = load_config()
    
    # Create a prompt to evaluate completion
    prompt = f"""
    You are evaluating if a conversation has met the completion criteria for a stage.
    
    Conversation stage: {stage.name}
    
    User's message: "{user_message}"
    
    Completion criteria:
    """
    
    for criterion, description in stage.completion_criteria.items():
        prompt += f"- {criterion}: {description}\n"
    
    prompt += """
    Based on the user's message, determine if the completion criteria have been met.
    If the criteria have been met, respond with "COMPLETE: next_stage_id" where next_stage_id is the ID of the next stage.
    If the criteria have not been met, respond with "INCOMPLETE".
    If the criteria have been partially met but more information is needed, respond with "INCOMPLETE".
    
    Response format:
    COMPLETE: [next_stage_id] or INCOMPLETE
    """
    
    try:
        # Get response from Mistral
        response = client.chat.complete(
            model=config.get("model", "mistral-small-latest"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=50
        )
        
        result = response.choices[0].message.content.strip()
        
        # Parse the result
        if result.startswith("COMPLETE"):
            # Extract the next stage ID if provided
            parts = result.split(":", 1)
            next_stage_id = parts[1].strip() if len(parts) > 1 else None
            
            # Validate the next stage ID
            if next_stage_id and next_stage_id in stage.next_stages:
                return True, next_stage_id
            # If the next stage ID is invalid but completion is confirmed,
            # use the first next stage if available
            elif stage.next_stages:
                return True, stage.next_stages[0]
            else:
                return True, None
        
        return False, None
        
    except Exception as e:
        logger.error(f"Error checking stage completion: {str(e)}")
        return False, None


def process_conversation_turn(user_message, conversation_state, conversation_flow, client=None):
    """
    Process a single turn in a conversation flow
    
    Returns:
        str: System message to be sent to the assistant
        ConversationState: Updated conversation state
    """
    # Initialize Mistral client if not provided
    if client is None:
        client = get_mistral_client()
        if not client:
            logger.error("Could not initialize Mistral client")
            return None, conversation_state
    
    # Get the current stage
    current_stage = conversation_flow.get_stage(conversation_state.current_stage_id)
    if not current_stage:
        logger.error(f"Invalid stage ID: {conversation_state.current_stage_id}")
        return None, conversation_state
    
    # Increment turns for the current stage
    conversation_state.increment_turns()
    
    # Check if the stage is complete
    is_complete, next_stage_id = check_stage_completion(
        current_stage, user_message, conversation_state, client
    )
    
    # If the stage is complete and we have a next stage, advance
    if is_complete and next_stage_id:
        conversation_state.advance_stage(next_stage_id)
        current_stage = conversation_flow.get_stage(next_stage_id)
    
    # Build the system message based on the current stage
    system_message = current_stage.system_prompt
    
    # Return the system message and updated conversation state
    return system_message, conversation_state


def save_conversation_flow(flow, directory="conversation_flows"):
    """Save a conversation flow to a file"""
    flow_dir = Path(directory)
    flow_dir.mkdir(exist_ok=True)
    
    flow_path = flow_dir / f"{flow.flow_id}.json"
    
    try:
        with open(flow_path, "w") as f:
            json.dump(flow.to_dict(), f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving conversation flow: {str(e)}")
        return False


def load_conversation_flow(flow_id, directory="conversation_flows"):
    """Load a conversation flow from a file"""
    flow_path = Path(directory) / f"{flow_id}.json"
    
    if not flow_path.exists():
        logger.error(f"Conversation flow file not found: {flow_path}")
        return None
    
    try:
        with open(flow_path, "r") as f:
            data = json.load(f)
        return ConversationFlow.from_dict(data)
    except Exception as e:
        logger.error(f"Error loading conversation flow: {str(e)}")
        return None


def list_conversation_flows(directory="conversation_flows"):
    """List all available conversation flows"""
    flow_dir = Path(directory)
    
    if not flow_dir.exists():
        return []
    
    flows = []
    
    for flow_path in flow_dir.glob("*.json"):
        try:
            with open(flow_path, "r") as f:
                data = json.load(f)
            flows.append({
                "flow_id": data.get("flow_id", ""),
                "name": data.get("name", ""),
                "description": data.get("description", "")
            })
        except Exception as e:
            logger.error(f"Error loading conversation flow {flow_path}: {str(e)}")
    
    return flows


def create_default_flows():
    """Create and save default conversation flows"""
    flows_dir = Path("conversation_flows")
    flows_dir.mkdir(exist_ok=True)
    
    # Customer Support Flow
    customer_flow = ConversationFlow(
        flow_id="customer_support",
        name="Customer Support Conversation",
        description="A structured flow for handling customer support inquiries",
        initial_stage="greeting"
    )
    
    # Add stages to the customer flow
    greeting_stage = ConversationStage(
        stage_id="greeting",
        name="Greeting",
        system_prompt="""You are a customer support agent. Begin by greeting the customer warmly and asking how you can help them today. Remember to be polite, professional, and empathetic. This is the first stage of the customer support conversation.""",
        next_stages=["problem_identification"],
        max_turns=2
    )
    customer_flow.add_stage(greeting_stage)
    
    problem_stage = ConversationStage(
        stage_id="problem_identification",
        name="Problem Identification",
        system_prompt="""You are now in the problem identification stage. Ask specific questions to understand the customer's issue. Try to gather details about the problem such as when it started, what the customer was doing when it occurred, and any error messages they received. Your goal is to fully understand the problem before moving to solutions.""",
        next_stages=["solution_proposal", "escalation"],
        completion_criteria={
            "problem_understanding": "The user has provided enough details about their problem",
            "severity_assessment": "The severity/urgency of the problem is clear"
        },
        max_turns=4
    )
    customer_flow.add_stage(problem_stage)
    
    solution_stage = ConversationStage(
        stage_id="solution_proposal",
        name="Solution Proposal",
        system_prompt="""You are now in the solution proposal stage. Based on the problem identified, suggest one or more solutions to the customer. Explain the solutions clearly and guide the customer through any steps they need to take. Confirm whether the solution worked for them.""",
        next_stages=["resolution_confirmation", "escalation"],
        completion_criteria={
            "solution_provided": "At least one solution has been suggested",
            "customer_understanding": "The customer understands the proposed solution"
        },
        max_turns=5
    )
    customer_flow.add_stage(solution_stage)
    
    resolution_stage = ConversationStage(
        stage_id="resolution_confirmation",
        name="Resolution Confirmation",
        system_prompt="""You are now in the resolution confirmation stage. Confirm with the customer that their issue has been resolved. Ask if there's anything else they need help with. If they're satisfied, thank them for contacting support.""",
        next_stages=["closing", "problem_identification"],
        completion_criteria={
            "problem_resolved": "The customer confirms their problem is resolved",
            "satisfaction_confirmed": "The customer expresses satisfaction with the solution"
        },
        max_turns=3
    )
    customer_flow.add_stage(resolution_stage)
    
    escalation_stage = ConversationStage(
        stage_id="escalation",
        name="Escalation",
        system_prompt="""You are now in the escalation stage. The issue requires specialized assistance. Explain to the customer that you'll need to escalate their issue to a specialist. Collect any additional information needed for the escalation, and provide the customer with an estimate of when they can expect a response.""",
        next_stages=["closing"],
        max_turns=3
    )
    customer_flow.add_stage(escalation_stage)
    
    closing_stage = ConversationStage(
        stage_id="closing",
        name="Closing",
        system_prompt="""You are now in the closing stage. Thank the customer for their time and patience. Provide any final instructions or information they might need. Let them know how they can get back in touch if they have further questions or issues in the future.""",
        next_stages=[],
        max_turns=2
    )
    customer_flow.add_stage(closing_stage)
    
    # Save the customer support flow
    save_conversation_flow(customer_flow)
    
    # Interview Flow
    interview_flow = ConversationFlow(
        flow_id="job_interview",
        name="Job Interview Conversation",
        description="A structured flow for conducting a job interview",
        initial_stage="introduction"
    )
    
    # Add stages to the interview flow
    intro_stage = ConversationStage(
        stage_id="introduction",
        name="Introduction",
        system_prompt="""You are an interviewer conducting a job interview. Begin by introducing yourself, explaining the interview process, and asking the candidate to briefly introduce themselves. Be professional but friendly. This is the first stage of the job interview.""",
        next_stages=["background_experience"],
        max_turns=2
    )
    interview_flow.add_stage(intro_stage)
    
    background_stage = ConversationStage(
        stage_id="background_experience",
        name="Background & Experience",
        system_prompt="""You are now in the background and experience stage of the interview. Ask the candidate about their relevant work experience, skills, and educational background. Focus on experiences that are relevant to the position they're applying for. Ask follow-up questions to get detailed examples.""",
        next_stages=["technical_questions"],
        completion_criteria={
            "experience_covered": "The candidate has discussed their relevant experience",
            "skills_covered": "The candidate has mentioned their key skills"
        },
        max_turns=4
    )
    interview_flow.add_stage(background_stage)
    
    technical_stage = ConversationStage(
        stage_id="technical_questions",
        name="Technical Questions",
        system_prompt="""You are now in the technical questions stage of the interview. Ask the candidate specific technical questions related to the position. These should test their knowledge, problem-solving abilities, and technical skills. Give them time to think through complex questions and clarify if needed.""",
        next_stages=["behavioral_questions"],
        completion_criteria={
            "technical_knowledge": "The candidate has demonstrated technical knowledge",
            "problem_solving": "The candidate has shown problem-solving abilities"
        },
        max_turns=5
    )
    interview_flow.add_stage(technical_stage)
    
    behavioral_stage = ConversationStage(
        stage_id="behavioral_questions",
        name="Behavioral Questions",
        system_prompt="""You are now in the behavioral questions stage of the interview. Ask the candidate about specific situations from their past experience that demonstrate key competencies like teamwork, leadership, conflict resolution, etc. Encourage them to use the STAR method (Situation, Task, Action, Result) in their responses.""",
        next_stages=["candidate_questions"],
        completion_criteria={
            "behavioral_examples": "The candidate has provided specific examples of past behavior",
            "key_competencies": "The candidate has demonstrated key competencies"
        },
        max_turns=4
    )
    interview_flow.add_stage(behavioral_stage)
    
    questions_stage = ConversationStage(
        stage_id="candidate_questions",
        name="Candidate Questions",
        system_prompt="""You are now in the candidate questions stage of the interview. Ask the candidate if they have any questions about the position, company, team, or work environment. Answer their questions thoughtfully and honestly, providing additional context where appropriate.""",
        next_stages=["closing_next_steps"],
        max_turns=4
    )
    interview_flow.add_stage(questions_stage)
    
    closing_stage = ConversationStage(
        stage_id="closing_next_steps",
        name="Closing & Next Steps",
        system_prompt="""You are now in the closing stage of the interview. Thank the candidate for their time and interest in the position. Explain the next steps in the hiring process, including when they can expect to hear back. Ask if they have any final questions or concerns.""",
        next_stages=[],
        max_turns=2
    )
    interview_flow.add_stage(closing_stage)
    
    # Save the interview flow
    save_conversation_flow(interview_flow)
    
    return [customer_flow, interview_flow]