import logging

from langgraph.graph import END, START, StateGraph
from src.service.graph.state import GraphState
from src.service.graph.subagents import SubAgentNodes
from src.service.graph.supervisor import SupervisorNode
from src.utilities.exception_utils import NormalExceptions

logger = logging.getLogger(__name__)


class GraphBuilder:
    def __init__(self, tools):
        self.tools = tools

    def build(self):
        try:
            nodes = SubAgentNodes(self.tools)
            supervisor = SupervisorNode()

            graph = StateGraph(GraphState)
            graph.add_node("supervisor", supervisor.route)
            graph.add_node("chat", nodes.chat_node)
            graph.add_node("desktop", nodes.desktop_node)
            graph.add_node("screen", nodes.screen_node)

            graph.add_edge(START, "supervisor")
            graph.add_conditional_edges(
                "supervisor",
                lambda state: state["route"],
                {"chat": "chat", "desktop": "desktop", "screen": "screen"},
            )
            graph.add_edge("chat", END)
            graph.add_edge("desktop", END)
            graph.add_edge("screen", END)

            return graph.compile()
        except NormalExceptions:
            raise
        except Exception as e:
            raise NormalExceptions(message="exception occurred in build_graph.py", error=str(e), log=True)
