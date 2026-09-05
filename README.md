# Research Agent

A small [LangGraph](https://github.com/langchain-ai/langgraph) pipeline that turns a topic into a grounded research brief.

## How it works

The graph runs three nodes in sequence:

1. **`generate_subquestions`** — asks Claude to break the topic into 3 specific, search-style sub-questions.
2. **`search`** — runs each sub-question through the [Tavily](https://tavily.com/) search API and collects the results.
3. **`synthesize_output`** — feeds the topic, sub-questions, and search results back to Claude, which writes a short markdown brief with one bullet per finding, each citing the sub-question it came from.

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file with:

```
ANTHROPIC_API_KEY=your-key
TAVILY_API_KEY=your-key
```

## Usage

```bash
python research_agent.py
```

Edit the `topic` passed to `app.invoke(...)` at the bottom of `research_agent.py` to research a different subject.
