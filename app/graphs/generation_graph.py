"""
LangGraph Definition for Generation Mode.

Defines the state graph that orchestrates:
1. Plan generation (first request)
2. Interactive tutoring (subsequent requests)
"""
import logging

from langgraph.graph import StateGraph, END

from app.graphs.state import GenerationGraphState
from app.graphs.nodes import plan_generator_node, tutor_node

logger = logging.getLogger(__name__)


def should_plan(state: GenerationGraphState) -> str:
    """
    Conditional routing function.
    
    Determines whether to generate a new plan or proceed with tutoring.
    
    Routes:
    - "plan_generator_node": If no lesson plan exists
    - "tutor_node": If lesson plan already exists
    """
    if state.get("lesson_plan") is None:
        logger.info("No lesson plan found - routing to plan generator")
        return "plan_generator_node"
    else:
        logger.info("Lesson plan exists - routing to tutor")
        return "tutor_node"


def create_generation_graph() -> StateGraph:
    """
    Create the LangGraph for Generation Mode.
    
    Graph Structure:
    ┌─────────────────────────────────────────────────────────────┐
    │                                                             │
    │  START                                                      │
    │    │                                                        │
    │    ▼                                                        │
    │  ┌─────────────────┐                                        │
    │  │   should_plan   │ (Conditional Entry Point)              │
    │  └────────┬────────┘                                        │
    │           │                                                 │
    │     ┌─────┴─────┐                                           │
    │     │           │                                           │
    │     ▼           ▼                                           │
    │  ┌──────────┐  ┌──────────┐                                 │
    │  │ Planner  │  │  Tutor   │                                 │
    │  │   Node   │  │   Node   │                                 │
    │  └────┬─────┘  └────┬─────┘                                 │
    │       │             │                                       │
    │       │             │                                       │
    │       ▼             ▼                                       │
    │  ┌──────────┐     END                                       │
    │  │  Tutor   │                                               │
    │  │   Node   │                                               │
    │  └────┬─────┘                                               │
    │       │                                                     │
    │       ▼                                                     │
    │      END                                                    │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘
    
    Returns:
        Compiled StateGraph ready for invocation
    """
    # Create the graph
    graph = StateGraph(GenerationGraphState)
    
    # Add nodes
    graph.add_node("plan_generator_node", plan_generator_node)
    graph.add_node("tutor_node", tutor_node)
    
    # Set conditional entry point
    # This determines the first node based on state
    graph.set_conditional_entry_point(
        should_plan,
        {
            "plan_generator_node": "plan_generator_node",
            "tutor_node": "tutor_node"
        }
    )
    
    # After planning, proceed to tutor for welcome message
    graph.add_edge("plan_generator_node", "tutor_node")
    
    # Tutor always ends (stateless per request)
    graph.add_edge("tutor_node", END)
    
    # Compile the graph
    return graph.compile()


# Create singleton instance
generation_app = create_generation_graph()


async def invoke_generation_graph(state: GenerationGraphState) -> GenerationGraphState:
    """
    Invoke the generation graph with the given state.
    
    This is the main entry point for running the graph.
    
    Args:
        state: Initial or current graph state
        
    Returns:
        Updated graph state after execution
    """
    result = await generation_app.ainvoke(state)
    return result
