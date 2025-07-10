from langgraph.graph import StateGraph
from langchain_ollama import OllamaLLM
from typing import Annotated
from typing_extensions import TypedDict
import logging

# ✅ Setup logging to file
logging.basicConfig(filename="agent_log.txt", level=logging.INFO, format="%(asctime)s - %(message)s")

# ✅ Define enhanced agent state
class AgentState(TypedDict):
    input_text: Annotated[str, "replace"]
    result: Annotated[str, "replace"]
    last_node: Annotated[str, "replace"]

# ✅ Load local Mistral model
llm = OllamaLLM(model="mistral")

# ✅ Router Node: routes input to specific handlers
def router_node(state: AgentState) -> dict:
    prompt = state["input_text"].lower()
    if "summarize" in prompt:
        logging.info("Routing to: summarizer")
        return {"next": "summarizer"}
    elif any(op in prompt for op in ["+", "-", "*", "/"]):
        logging.info("Routing to: math")
        return {"next": "math"}
    elif "translate" in prompt:
        logging.info("Routing to: translator")
        return {"next": "translator"}
    else:
        logging.info("Routing to: fallback")
        return {"next": "fallback"}

# ✅ Math Node
def math_node(state: AgentState) -> AgentState:
    expr = state["input_text"]
    result = llm.invoke(f"Solve this: {expr}")
    print("\033[94m📐 Math Node Activated\033[0m")
    return {"input_text": expr, "result": result, "last_node": "math"}

# ✅ Summary Node
def summarizer_node(state: AgentState) -> AgentState:
    text = state["input_text"].replace("summarize:", "").strip()
    result = llm.invoke(f"Summarize this: {text}")
    print("\033[96m📝 Summary Node Activated\033[0m")
    return {"input_text": state["input_text"], "result": result, "last_node": "summarizer"}

# ✅ Translator Node
def translator_node(state: AgentState) -> AgentState:
    text = state["input_text"].replace("translate", "").strip()
    result = llm.invoke(f"Translate this to English: {text}")
    print("\033[93m🌐 Translator Node Activated\033[0m")
    return {"input_text": state["input_text"], "result": result, "last_node": "translator"}

# ✅ Fallback Node
def fallback_node(state: AgentState) -> AgentState:
    result = llm.invoke(f"Cannot identify action for: {state['input_text']}")
    print("\033[91m❓ Fallback Node Activated\033[0m")
    return {"input_text": state["input_text"], "result": result, "last_node": "fallback"}

# ✅ Printer Node
def printer_node(state: AgentState) -> AgentState:
    print("\033[92m✅ Final Output:", state["result"], f"(\033[90mfrom {state['last_node']} node\033[0m)\n")
    logging.info(f"[{state['last_node'].upper()}] Input: {state['input_text']} | Output: {state['result']}")
    return state

# ✅ Build the LangGraph
graph = StateGraph(AgentState)

graph.add_node("router", router_node)
graph.add_node("math", math_node)
graph.add_node("summarizer", summarizer_node)
graph.add_node("translator", translator_node)
graph.add_node("fallback", fallback_node)
graph.add_node("printer", printer_node)

graph.set_entry_point("router")

graph.add_conditional_edges(
    "router",
    lambda x: x["next"],
    {
        "math": "math",
        "summarizer": "summarizer",
        "translator": "translator",
        "fallback": "fallback"
    }
)

graph.add_edge("math", "printer")
graph.add_edge("summarizer", "printer")
graph.add_edge("translator", "printer")
graph.add_edge("fallback", "printer")

# ✅ Compile graph
app = graph.compile()

# ✅ Enhanced test runner
def test():
    test_cases = [
        ("🔎 Summary", "summarize: LangGraph helps orchestrate LLMs with nodes."),
        ("➕ Math", "34 + 12 / 2"),
        ("🌐 Translation", "translate bonjour le monde"),
        ("❓ Fallback", "tell me a joke")
    ]

    for label, text in test_cases:
        print(f"\n--- {label} ---")
        app.invoke({"input_text": text, "result": "", "last_node": ""})

test()
