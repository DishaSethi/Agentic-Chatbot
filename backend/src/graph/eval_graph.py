from typing import TypedDict
from langgraph.graph import StateGraph, END
from google import genai
from langsmith import wrappers
# Initialize Gemini client just for the graph nodes
gemini_client = wrappers.wrap_gemini(genai.Client())

class EvaluateState(TypedDict):
    user_architecture: str
    context: str
    draft_scorecard: str
    is_hallucinated: bool
    iterations: int

def generate_scorecard(state: EvaluateState):
    print(f"🔄 [LangGraph] Generator Node (Attempt {state['iterations'] + 1})...")

    system_prompt = f"""You are a strict but constructive Staff Engineer grading a student's proposed personal project architecture.
Evaluate their design strictly based on these retrieved engineering best practices and free-tier constraints:
{state['context']}

CRITICAL INSTRUCTION FOR CITATIONS:
Whenever you enforce a constraint, flag over-engineering, or apply a rule from the provided context, you MUST cite it inline using the category name in brackets.
Example: "Deploying a Kubernetes cluster for this is over-engineered [Free-Tier Limits]."
Do not invent rules, cloud limits, or cite things not in the context.

Generate a comprehensive Markdown evaluation scorecard structured EXACTLY as follows:
## 📊 Architecture Evaluation Scorecard
**Overall Score: [X]/10**

### 1. Pragmatism & Cost
*(Evaluate if this is buildable by one person and uses free-tier friendly tools, or if it is over-engineered)*
### 2. Strengths & Good Choices
*(What did they do well? Proper database selection? Good decoupled logic?)*
### 3. Red Flags & Fixes
*(Did they forget authentication? Pick the wrong database? Cite the context and provide an actionable fix.)*
"""
    if state['iterations'] > 0:
        system_prompt += "\n\nWARNING: Your previous draft hallucinated rules. STICK STRICTLY TO THE PROVIDED CONTEXT AND DO NOT INVENT BEST PRACTICES."

    response = gemini_client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=f"{system_prompt}\n\nUser Architecture:\n{state['user_architecture']}"
    )
    return {"draft_scorecard": response.text, "iterations": state['iterations'] + 1}

def grade_hallucinations(state: EvaluateState):
    print("🕵️ [LangGraph] Grader Node checking for hallucinations...")

    grader_prompt = f"""You are a strict Hallucination Grader.
RETRIEVED BEST PRACTICES & CONSTRAINTS:
{state['context']}

DRAFT SCORECARD:
{state['draft_scorecard']}

Did the draft scorecard invent any rules, constraints, cloud limits, or anti-patterns that are NOT explicitly mentioned in the RETRIEVED BEST PRACTICES?
Respond with ONLY 'YES' (it hallucinated) or 'NO' (it is clean).
"""
    response = gemini_client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=grader_prompt
    )
    answer = response.text.strip().upper()
    is_hallucinated = "YES" in answer

    if is_hallucinated:
        print("🚨 HALLUCINATION DETECTED! Rejecting draft and looping back...")
    else:
        print("✅ DRAFT APPROVED! Clean architecture evaluation ready.")

    return {"is_hallucinated": is_hallucinated}

# Compile the graph
workflow = StateGraph(EvaluateState)
workflow.add_node("generator", generate_scorecard)
workflow.add_node("grader", grade_hallucinations)
workflow.set_entry_point("generator")
workflow.add_edge("generator", "grader")

def router(state: EvaluateState):
    if state["is_hallucinated"] and state["iterations"] < 3:
        return "generator"
    return END

workflow.add_conditional_edges("grader", router)
eval_app = workflow.compile()