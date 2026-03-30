from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from ken.config import Settings
from ken.graph.nodes.deliver import deliver_node
from ken.graph.nodes.disambiguate import disambiguate_node
from ken.graph.nodes.download import download_node
from ken.graph.nodes.identify import identify_node
from ken.graph.nodes.process import process_node
from ken.graph.nodes.scrape import scrape_node
from ken.graph.state import AgentState

_checkpointer = MemorySaver()


def _route_next(state: AgentState) -> str:
    """Shared router: error → deliver, needs_choice → disambiguate, else fall through."""
    if state.get("error"):
        return "deliver"
    if state.get("needs_user_choice"):
        return "disambiguate"
    return "__next__"


def _route_after_identify(state: AgentState) -> str:
    r = _route_next(state)
    return "download" if r == "__next__" else r


def _route_after_download(state: AgentState) -> str:
    r = _route_next(state)
    return "process" if r == "__next__" else r


def _route_after_process(state: AgentState) -> str:
    if state.get("needs_user_choice"):
        return "disambiguate"
    return "deliver"


def _route_after_disambiguate(state: AgentState) -> str:
    context = state.get("choice_context", "links")
    return "download" if context == "links" else "process"


def build_graph(settings: Settings):
    graph = StateGraph(AgentState)

    graph.add_node("scrape", scrape_node)
    graph.add_node("identify", identify_node)
    graph.add_node("disambiguate", disambiguate_node)
    graph.add_node("download", download_node)
    graph.add_node("process", process_node)
    graph.add_node("deliver", deliver_node)

    graph.set_entry_point("scrape")
    graph.add_edge("scrape", "identify")
    graph.add_conditional_edges("identify", _route_after_identify)
    graph.add_conditional_edges("download", _route_after_download)
    graph.add_conditional_edges("process", _route_after_process)
    graph.add_conditional_edges("disambiguate", _route_after_disambiguate)
    graph.add_edge("deliver", END)

    return graph.compile(checkpointer=_checkpointer)
