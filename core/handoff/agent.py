from typing import Annotated, TypedDict, Union, List
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from loguru import logger
import os

class SubTask(BaseModel):
    """Schema for a single sub-task."""
    priority: str = Field(description="Priority: low, medium, high, or urgent")
    title: str = Field(description="Short summary of the sub-task")
    description: str = Field(description="Detailed instructions and acceptance criteria")
    depends_on: str = Field(description="Comma-separated list of task IDs this sub-task depends on")
    
    class Config:
        extra = "forbid"

class TaskDecomposition(BaseModel):
    """Schema for task decomposition."""
    sub_tasks: List[SubTask] = Field(description="List of sub-tasks to be added to the board")
    confidence_score: float = Field(description="Confidence score (0.0 to 1.0) for the decomposition")
    reasoning: str = Field(description="Reasoning behind the decomposition strategy")
    
    class Config:
        extra = "forbid"

class AgentState(TypedDict):
    """State for the LangGraph agent."""
    task_id: str
    title: str
    description: str
    sub_tasks: List[dict]
    status: str
    confidence_score: float

def decompose_task(state: AgentState):
    """Node to decompose a complex task into sub-tasks."""
    logger.info(f"Decomposing task: {state['title']}")
    
    from core.config.manager import load_config
    config = load_config()
    
    prompt = f"""
    You are the AAS Task Decomposer. 
    Decompose the following task into smaller, actionable sub-tasks for the AAS Active Task Board.
    
    Task ID: {state['task_id']}
    Title: {state['title']}
    Description: {state['description']}
    
    Guidelines:
    1. Each sub-task must be actionable and have clear acceptance criteria.
    2. Use the parent task ID ({state['task_id']}) in the 'depends_on' field if it's the primary dependency.
    3. If sub-tasks depend on each other, use descriptive placeholders for their IDs (e.g., 'SUB-1') and I will resolve them.
    4. Provide a confidence score (0.0 to 1.0) based on how well-defined the decomposition is.
    """

    if config.responses_api_enabled:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=config.openai_api_key.get_secret_value())
            
            response = client.responses.create(
                model=config.openai_model,
                instructions="You are the AAS Task Decomposer.",
                input=prompt,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "task_decomposition",
                        "schema": TaskDecomposition.model_json_schema()
                    }
                },
                store=True
            )
            # Parse JSON from output
            import json
            json_text = next(item.text for item in response.output if hasattr(item, 'text'))
            result = TaskDecomposition.model_validate_json(json_text)
        except Exception as e:
            logger.error(f"Decomposition (Responses API) failed: {e}")
            raise
    else:
        llm = ChatOpenAI(
            model=config.openai_model, 
            api_key=config.openai_api_key.get_secret_value()
        )
        structured_llm = llm.with_structured_output(TaskDecomposition)
        result = structured_llm.invoke(prompt)
    
    # Convert Pydantic models to dicts for the state
    sub_tasks_dict = [st.model_dump() for st in result.sub_tasks]
    
    logger.info(f"Decomposition confidence: {result.confidence_score}")
    logger.info(f"Reasoning: {result.reasoning}")
    
    return {
        "sub_tasks": sub_tasks_dict, 
        "status": "decomposed",
        "confidence_score": result.confidence_score
    }

def write_to_board(state: AgentState):
    """Node to write sub-tasks back to the local board."""
    from core.handoff.manager import HandoffManager
    manager = HandoffManager()
    
    # Only write if confidence is high enough, or if it's a forced run
    if state.get("confidence_score", 0) < 0.5:
        logger.warning(f"Low decomposition confidence ({state['confidence_score']}). Manual review recommended.")
    
    for st in state["sub_tasks"]:
        manager.add_task(
            priority=st.get("priority", "medium"),
            title=st.get("title"),
            description=st.get("description"),
            depends_on=st.get("depends_on", state["task_id"])
        )
    
    logger.success(f"Added {len(state['sub_tasks'])} sub-tasks to the board.")
    return {"status": "completed"}

def create_decomposition_graph():
    """Creates the LangGraph for task decomposition."""
    workflow = StateGraph(AgentState)
    
    workflow.add_node("decompose", decompose_task)
    workflow.add_node("write", write_to_board)
    
    workflow.set_entry_point("decompose")
    workflow.add_edge("decompose", "write")
    workflow.add_edge("write", END)
    
    return workflow.compile()
