Project: research-agent-v2 

A LangGraph agent with these nodes:

generate_subquestions — takes a topic string, returns exactly 3 specific search-style sub-questions
search — for each sub-question, calls the real Tavily search API and collects results (this is the new part — an actual tool call, not a stub)
synthesize — takes the topic + sub-questions + real search results, drafts a short structured brief with inline references to which sub-question each point came from


Here's a full worked example — topic in, structured brief out, showing what each node produces along the way.

Input:

python
result = app.invoke({"topic": "impact of remote work on commercial real estate"})

Node 1 — generate_subquestions output:

json
{
  "topic": "impact of remote work on commercial real estate",
  "subquestions": [
    "What is the current office vacancy rate in major US cities in 2026?",
    "How have commercial real estate valuations changed since 2023 due to remote work?",
    "What are landlords doing to convert or repurpose vacant office space?"
  ]
}

Node 2 — search output (real Tavily call per sub-question, results collected into state):

json
{
  "search_results": {
    "What is the current office vacancy rate in major US cities in 2026?": [
      {
        "title": "US Office Vacancy Hits Record High in Q2 2026",
        "url": "https://example.com/office-vacancy-2026",
        "content": "National office vacancy reached 20.1% in Q2 2026, with San Francisco and Houston posting the highest rates among major metros..."
      },
      {
        "title": "CBRE Office Market Report 2026",
        "url": "https://example.com/cbre-report",
        "content": "Sublease availability has stabilized but direct vacancy continues to climb in secondary markets..."
      }
    ],
    "How have commercial real estate valuations changed since 2023 due to remote work?": [
      {
        "title": "Office Property Values Down 30% From 2019 Peak",
        "url": "https://example.com/valuations-drop",
        "content": "Class B and C office buildings have seen the steepest declines, with some properties selling at 40-50% below pre-pandemic assessed value..."
      }
    ],
    "What are landlords doing to convert or repurpose vacant office space?": [
      {
        "title": "Office-to-Residential Conversions Accelerate in 2026",
        "url": "https://example.com/conversions",
        "content": "Cities including New York and Chicago have introduced tax incentives for converting outdated office towers into apartments..."
      }
    ]
  }
}

Node 3 — synthesize output (final brief, with references back to which sub-question grounded each point):

markdown
## Research Brief: Impact of Remote Work on Commercial Real Estate

- **Vacancy is still climbing, not stabilizing.** National office vacancy hit 20.1% in Q2 2026, 
  with the steepest rates in cities like San Francisco and Houston. 
  [from: "What is the current office vacancy rate..."]

- **Valuations have taken a severe hit, unevenly.** Office properties are down roughly 30% from 
  their 2019 peak on average, but Class B/C buildings are seeing 40-50% drops — the damage is 
  concentrated in older, lower-tier stock rather than spread evenly across the market. 
  [from: "How have commercial real estate valuations changed..."]

- **Landlords are pivoting to conversion rather than waiting out the market.** Office-to-residential 
  conversions are accelerating, helped by new tax incentives in cities like New York and Chicago. 
  [from: "What are landlords doing to convert or repurpose..."]

What your test should actually check here:

python
def test_synthesize_references_all_subquestions():
    state = {
        "topic": "impact of remote work on commercial real estate",
        "subquestions": [...],
        "search_results": {...}  # mocked, same shape as above
    }
    result = synthesize(state)
    assert "brief" in result
    # every sub-question should be traceable in the output
    for q in state["subquestions"]:
        assert q in result["brief"] or some_reference_marker(q) in result["brief"]

def test_synthesize_handles_empty_search_results():
    state = {
        "topic": "some topic",
        "subquestions": ["q1", "q2", "q3"],
        "search_results": {"q1": [], "q2": [], "q3": []}  # Tavily returned nothing
    }
    result = synthesize(state)
    # should not crash, and should say something honest about missing data
    assert "brief" in result
    assert len(result["brief"]) > 0