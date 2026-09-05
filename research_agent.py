import json
import os
from typing import TypedDict

from dotenv import load_dotenv

load_dotenv()
from langchain.chat_models import init_chat_model
from langgraph.graph import END, START, StateGraph
from tavily import TavilyClient

model = init_chat_model('claude-sonnet-4-6', temperature=0.3)
tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

class State(TypedDict):
    topic: str
    subquestions: list[str]
    search_results: dict[str,list[dict]]
    brief: str


def generate_subquestions(state: State):
    """takes a topic string, returns exactly 3 specific search-style sub-questions"""
    prompt = f"""Generate exactly 3 specific, search-style sub-questions that would help research this topic.

Topic: {state['topic']}

Each sub-question should read the way someone would type it into a search engine, and be specific
enough to return concrete, current information rather than a vague overview.

Respond with only a JSON array of 3 strings, no other text."""

    result = model.invoke(prompt)
    text = result.content
    text = text[text.index("[") : text.rindex("]") + 1]
    subquestions = json.loads(text)

    return {"subquestions": subquestions}

def search(state: State) -> dict:
    """for each sub-question, calls the real Tavily search API and
    collects results"""
    search_results = {}
    for subquestion in state["subquestions"]:
        response = tavily_client.search(subquestion)
        search_results[subquestion] = [
            {"title": r["title"], "url": r["url"], "content": r["content"]}
            for r in response["results"]
        ]
    return {"search_results": search_results}

def synthesize_output(state: State) -> dict:
    """takes the topic + sub-questions + real search results,
    drafts a short structured brief with inline references to
    which sub-question each point came from"""

    sources_block = ""
    for subquestion in state["subquestions"]:
        results = state["search_results"].get(subquestion, [])
        sources_block += f'\nSub-question: "{subquestion}"\n'
        if not results:
            sources_block += "  (no search results were found for this sub-question)\n"
        else:
            for r in results:
                sources_block += f'  - {r["title"]}: {r["content"][:400]}\n'

    prompt = f"""You are a research analyst. Write a short structured research brief on this topic,
grounded only in the search results below — do not add facts they don't support.

Topic: {state['topic']}

Search results, grouped by sub-question:
{sources_block}

Format the brief as markdown, one bullet per key finding:

## Research Brief: <topic title>

- **<bolded one-sentence takeaway>.** <1-2 sentences of supporting detail.
  [from: "<sub-question text this point came from>"]

Rules:
- Every bullet's `[from: "..."]` line must quote one of the sub-questions above EXACTLY as
  given — verbatim, not paraphrased or shortened.
- If a sub-question has no search results, say so honestly in a bullet instead of inventing a
  finding for it.
- One bullet per sub-question is enough unless a sub-question yields two clearly distinct findings.

Respond with only the markdown brief, no other text."""

    result = model.invoke(prompt)
    return {"brief": result.content}

graph = StateGraph(State)
graph.add_node("generate_subquestions", generate_subquestions)
graph.add_node("search", search)
graph.add_node("synthesize_output", synthesize_output)
graph.add_edge(START, "generate_subquestions")
graph.add_edge("generate_subquestions", "search")
graph.add_edge("search", "synthesize_output")
graph.add_edge("synthesize_output", END)

app = graph.compile()


if __name__=="__main__":
    result = app.invoke({"topic": "impact of remote work on commercial real estate"})
    print(result)