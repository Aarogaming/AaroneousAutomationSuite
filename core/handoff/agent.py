from typing import Annotated, TypedDict, Union, List
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from loguru import logger
import os

class TaskDecomposition(BaseModel):
    """Schema for task decomposition."""
    sub_tasks: List[dict] = Field(description="List of sub-tasks to be added to the board")

class AgentState(TypedDict):
    """State for the LangGraph agent."""
    task_id: str
    title: str
    description: str
    sub_tasks: List[dict]
    status: str

def decompose_task(state: AgentState):
    """Node to decompose a complex task into sub-tasks."""
    logger.info(f"Decomposing task: {state['title']}")
    
    llm = ChatOpenAI(model="gpt-4-turbo-preview")
    structured_llm = llm.with_structured_output(TaskDecomposition)
    
    prompt = f"""
    You are the AAS Task Decomposer. 
    Decompose the following task into smaller, actionable sub-tasks for the AAS Active Task Board.
    
    Task ID: {state['task_id']}
    Title: {state['title']}
    Description: {state['description']}
    
    Each sub-task should have:
    - priority: "low", "medium", "high", or "urgent"
    - title: Short summary
    - description: Detailed instructions
    - depends_on: The parent task ID ({state['task_id']}) or other sub-tasks
    """
    
    result = structured_llm.invoke(prompt)
    return {"sub_tasks": result.sub_tasks, "status": "decomposed"}

def write_to_board(state: AgentState):
    """Node to write sub-tasks back to the local board."""
    from core.handoff.manager import HandoffManager
    manager = HandoffManager()
    
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
