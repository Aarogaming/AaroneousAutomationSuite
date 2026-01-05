"""
Automated Task Decomposition using LangGraph.

This module implements a state graph for breaking down complex goals into
actionable sub-tasks with dependency mapping.
"""

import json
from typing import List, Dict, Any, TypedDict, Annotated, Sequence
from operator import add
from loguru import logger

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, END

class DecompositionState(TypedDict):
    """State for the decomposition graph."""
    goal: str
    context: Dict[str, Any]
    subtasks: Annotated[List[Dict[str, Any]], add]
    dependencies: Annotated[List[Dict[str, str]], add]
    messages: Annotated[Sequence[BaseMessage], add]
    is_complete: bool

class TaskDecomposer:
    """
    Uses LangGraph to decompose complex goals into a Directed Acyclic Graph (DAG) of tasks.
    """
    
    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(model=model_name, temperature=0)
        self.graph = self._build_graph()
        
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine."""
        workflow = StateGraph(DecompositionState)
        
        # Define nodes
        workflow.add_node("analyze", self._analyze_goal)
        workflow.add_node("decompose", self._generate_subtasks)
        workflow.add_node("map_dependencies", self._map_dependencies)
        
        # Define edges
        workflow.set_entry_point("analyze")
        workflow.add_edge("analyze", "decompose")
        workflow.add_edge("decompose", "map_dependencies")
        workflow.add_edge("map_dependencies", END)
        
        return workflow.compile()
    
    async def _analyze_goal(self, state: DecompositionState) -> Dict[str, Any]:
        """Analyze the high-level goal for complexity and scope."""
        logger.info(f"Analyzing goal: {state['goal']}")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a senior technical architect. Analyze the following goal and identify key technical components and potential challenges."),
            ("user", "{goal}")
        ])
        
        chain = prompt | self.llm
        response = await chain.ainvoke({"goal": state["goal"]})
        
        return {
            "messages": [response]
        }
    
    async def _generate_subtasks(self, state: DecompositionState) -> Dict[str, Any]:
        """Generate a list of actionable sub-tasks."""
        logger.info("Generating sub-tasks...")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Break down the goal into 3-7 actionable sub-tasks. 
For each task, provide:
- title: Short, descriptive title
- description: Detailed technical instructions
- priority: low, medium, high, or urgent
- type: feature, bug, infrastructure, or documentation

Format as a JSON list of objects."""),
            MessagesPlaceholder(variable_name="messages"),
            ("user", "Generate the sub-tasks for the goal: {goal}")
        ])
        
        chain = prompt | self.llm
        response = await chain.ainvoke({"goal": state["goal"], "messages": state["messages"]})
        
        # Extract JSON
        try:
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            subtasks = json.loads(content)
        except Exception as e:
            logger.error(f"Failed to parse subtasks: {e}")
            subtasks = [{"title": "Execute Goal", "description": state["goal"], "priority": "medium", "type": "feature"}]
            
        return {
            "subtasks": subtasks,
            "messages": [response]
        }
    
    async def _map_dependencies(self, state: DecompositionState) -> Dict[str, Any]:
        """Map dependencies between generated sub-tasks."""
        logger.info("Mapping dependencies...")
        
        subtasks_str = json.dumps(state["subtasks"], indent=2)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Given the following list of sub-tasks, identify dependencies between them.
A dependency means Task B cannot start until Task A is finished.
Format as a JSON list of objects with 'task_title' and 'depends_on_title'.

Sub-tasks:
{subtasks}"""),
            ("user", "Map the dependencies.")
        ])
        
        chain = prompt | self.llm
        response = await chain.ainvoke({"subtasks": subtasks_str})
        
        try:
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            dependencies = json.loads(content)
        except Exception as e:
            logger.error(f"Failed to parse dependencies: {e}")
            dependencies = []
            
        return {
            "dependencies": dependencies,
            "messages": [response],
            "is_complete": True
        }
    
    async def decompose(self, goal: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run the decomposition graph."""
        initial_state = {
            "goal": goal,
            "context": context or {},
            "subtasks": [],
            "dependencies": [],
            "messages": [],
            "is_complete": False
        }
        
        final_state = await self.graph.ainvoke(initial_state)
        
        # Post-process to link dependencies by ID (to be generated by TaskManager)
        return {
            "subtasks": final_state["subtasks"],
            "dependencies": final_state["dependencies"]
        }
