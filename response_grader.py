import os
import logging
import json
from mistralai import Mistral
from pathlib import Path
from helper_functions import load_config

# Initialize logger
logger = logging.getLogger("chatbot.response_grader")

def get_mistral_client():
    """Get Mistral client instance"""
    api_key = os.environ.get("MISTRAL_API_KEY", "")
    if not api_key:
        logger.error("Missing API key")
        return None
    return Mistral(api_key=api_key)

def grade_response(user_response, context=None, criteria=None, reference_answer=None, client=None):
    """
    Grade a user's response based on specified criteria or a reference answer.
    
    Parameters:
    - user_response: The user's response to evaluate
    - context: Optional context for the question
    - criteria: Optional grading criteria (dict or list)
    - reference_answer: Optional reference/model answer to compare against
    - client: Optional Mistral client instance
    
    Returns:
    Dictionary with grading results
    """
    if not user_response:
        return {
            "score": 0,
            "feedback": "No response provided.",
            "strengths": [],
            "weaknesses": [],
            "suggestions": []
        }
    
    if client is None:
        client = get_mistral_client()
        if not client:
            logger.error("Could not initialize Mistral client for grading")
            return None
    
    config = load_config()
    
    # Prepare default criteria if none provided
    if not criteria:
        criteria = {
            "accuracy": "Correctness of the information and concepts",
            "completeness": "Coverage of all relevant points",
            "clarity": "Clear explanation and logical structure",
            "depth": "Depth of understanding and insight"
        }
    
    # Build the prompt for grading
    prompt = f"""
    You are an expert evaluator tasked with grading a user's response objectively and providing constructive feedback.
    
    """
    
    # Add context if provided
    if context:
        prompt += f"""
        CONTEXT/QUESTION:
        {context}
        
        """
    
    # Add reference answer if provided
    if reference_answer:
        prompt += f"""
        REFERENCE ANSWER (for comparison):
        {reference_answer}
        
        """
    
    # Add criteria for evaluation
    prompt += "GRADING CRITERIA:\n"
    if isinstance(criteria, dict):
        for criterion, description in criteria.items():
            prompt += f"- {criterion.capitalize()}: {description}\n"
    elif isinstance(criteria, list):
        for criterion in criteria:
            prompt += f"- {criterion}\n"
    else:
        prompt += "- Accuracy: Correctness of the information and concepts\n"
        prompt += "- Completeness: Coverage of all relevant points\n"
        prompt += "- Clarity: Clear explanation and logical structure\n"
        prompt += "- Depth: Depth of understanding and insight\n"
    
    # Add the user's response
    prompt += f"""
    USER'S RESPONSE TO EVALUATE:
    {user_response}
    
    INSTRUCTIONS:
    1. Score the response on a scale of 1-10.
    2. Provide a brief overall assessment (1-2 sentences).
    3. List 2-3 strengths of the response.
    4. List 2-3 areas for improvement.
    5. Provide 1-2 specific suggestions to improve the response.
    
    Format your evaluation as a JSON object with the following structure:
    {{
        "score": [score as a number between 1-10],
        "feedback": "[brief overall assessment]",
        "strengths": ["strength1", "strength2", ...],
        "weaknesses": ["weakness1", "weakness2", ...],
        "suggestions": ["suggestion1", "suggestion2", ...]
    }}
    
    Return ONLY the JSON object, with no additional text.
    """
    
    try:
        # Get response from Mistral
        response = client.chat.complete(
            model=config.get("model", "mistral-large-latest"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,  # Lower temperature for more consistent grading
            max_tokens=1000
        )
        
        result_text = response.choices[0].message.content
        
        # Extract JSON from the response
        try:
            # Clean up the response to ensure it's valid JSON
            result_text = result_text.strip()
            # Remove any markdown code block indicators
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
                
            result_text = result_text.strip()
            
            # Parse JSON
            grading_result = json.loads(result_text)
            
            # Validate required fields
            required_fields = ["score", "feedback", "strengths", "weaknesses", "suggestions"]
            for field in required_fields:
                if field not in grading_result:
                    grading_result[field] = [] if field != "score" and field != "feedback" else ""
            
            # Ensure score is a number
            if not isinstance(grading_result["score"], (int, float)):
                try:
                    grading_result["score"] = float(grading_result["score"])
                except:
                    grading_result["score"] = 0
            
            return grading_result
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing grading result JSON: {str(e)}")
            # Return a basic result with the raw response
            return {
                "score": 0,
                "feedback": "Error parsing grading result.",
                "strengths": [],
                "weaknesses": [],
                "suggestions": [],
                "raw_response": result_text
            }
    
    except Exception as e:
        logger.error(f"Error grading response: {str(e)}")
        return {
            "score": 0,
            "feedback": f"Error grading response: {str(e)}",
            "strengths": [],
            "weaknesses": [],
            "suggestions": []
        }

def create_grading_criteria(subject, difficulty="medium", custom_criteria=None):
    """
    Create appropriate grading criteria based on subject and difficulty.
    
    Parameters:
    - subject: The subject area (e.g., "math", "science", "history")
    - difficulty: The difficulty level ("easy", "medium", "hard")
    - custom_criteria: Optional custom criteria to include
    
    Returns:
    Dictionary of criteria and their descriptions
    """
    # Base criteria for all subjects
    base_criteria = {
        "accuracy": "Correctness of the information and concepts",
        "completeness": "Coverage of all relevant points",
        "clarity": "Clear explanation and logical structure"
    }
    
    # Subject-specific criteria
    subject_criteria = {
        "math": {
            "methodology": "Correct application of mathematical methods and procedures",
            "calculation": "Accuracy of calculations and final answers",
            "problem_solving": "Effectiveness of the approach to solving the problem"
        },
        "science": {
            "scientific_thinking": "Application of scientific principles and methods",
            "evidence_use": "Proper use of evidence to support claims",
            "concept_application": "Application of scientific concepts to the question"
        },
        "history": {
            "historical_context": "Understanding of the historical context",
            "source_analysis": "Analysis and evaluation of historical sources",
            "causal_connections": "Identifying cause-and-effect relationships"
        },
        "english": {
            "grammar_usage": "Correct grammar, spelling, and punctuation",
            "expression": "Clarity and effectiveness of expression",
            "textual_analysis": "Depth of textual analysis and interpretation"
        },
        "programming": {
            "code_functionality": "Whether the code works as expected",
            "code_efficiency": "Efficiency and optimization of the code",
            "coding_standards": "Adherence to coding conventions and standards"
        }
    }
    
    # Difficulty-specific adjustments
    difficulty_additions = {
        "easy": {},
        "medium": {
            "analysis": "Depth of analysis and critical thinking"
        },
        "hard": {
            "analysis": "Depth of analysis and critical thinking",
            "synthesis": "Integration of concepts and information",
            "evaluation": "Critical evaluation of different perspectives"
        }
    }
    
    # Start with base criteria
    criteria = base_criteria.copy()
    
    # Add subject-specific criteria if available
    if subject.lower() in subject_criteria:
        criteria.update(subject_criteria[subject.lower()])
    
    # Add difficulty-specific criteria
    if difficulty.lower() in difficulty_additions:
        criteria.update(difficulty_additions[difficulty.lower()])
    
    # Add custom criteria if provided
    if custom_criteria and isinstance(custom_criteria, dict):
        criteria.update(custom_criteria)
    
    return criteria

def load_grading_templates():
    """Load grading templates from templates directory."""
    templates_dir = Path("grading_templates")
    templates = {}
    
    if not templates_dir.exists():
        return templates
    
    for file_path in templates_dir.glob("*.json"):
        try:
            with open(file_path, "r") as f:
                template = json.load(f)
                templates[file_path.stem] = template
        except Exception as e:
            logger.error(f"Error loading grading template {file_path}: {str(e)}")
    
    return templates

def save_grading_template(template_name, criteria, reference_answer=None, context=None):
    """Save a grading template for future use."""
    templates_dir = Path("grading_templates")
    templates_dir.mkdir(exist_ok=True)
    
    template = {
        "name": template_name,
        "criteria": criteria,
        "reference_answer": reference_answer,
        "context": context
    }
    
    try:
        file_path = templates_dir / f"{template_name}.json"
        with open(file_path, "w") as f:
            json.dump(template, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving grading template {template_name}: {str(e)}")
        return False