from __future__ import annotations

from typing import TypedDict

from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph
from sqlalchemy.orm import Session

from app.services.embeddings import EmbeddingProvider
from app.services.retrieval import SearchResult, hybrid_search, keyword_search, semantic_search


class AgentState(TypedDict, total=False):
    question: str
    owner_id: str
    session: Session
    provider: EmbeddingProvider
    route: str
    tool_trace: list[str]
    results: list[SearchResult]
    answer: str


def run_agent(
    *,
    session: Session,
    owner_id: str,
    provider: EmbeddingProvider,
    question: str,
    history: str = "",
) -> tuple[str, list[SearchResult], list[str]]:
    if not provider.is_configured:
        return "Semantic retrieval and answer generation are not configured.", [], []

    @tool
    def keyword_search_tool(query: str) -> list[str]:
        """Search screenshot metadata with exact and AND-matched FTS5 keywords."""
        found = keyword_search(session, owner_id=owner_id, query=query, limit=8)
        return [result.item.id for result in found]

    @tool
    def semantic_search_tool(query: str) -> list[str]:
        """Search screenshot meaning with vector similarity embeddings."""
        vector = provider.embed_text(query)
        found = semantic_search(session, owner_id=owner_id, query_vector=vector, limit=8)
        return [result.item.id for result in found]

    @tool
    def hybrid_search_tool(query: str) -> list[str]:
        """Combine keyword and semantic screenshot search and rank unique results."""
        keyword = keyword_search(session, owner_id=owner_id, query=query, limit=8)
        vector = provider.embed_text(query)
        semantic = semantic_search(session, owner_id=owner_id, query_vector=vector, limit=8)
        found = hybrid_search(keyword, semantic, 8)
        return [result.item.id for result in found]

    def supervisor(state: AgentState) -> AgentState:
        route = provider.route(state["question"])
        return {
            **state,
            "route": route,
            "tool_trace": [f"{route}_search"],
        }

    def retrieval(state: AgentState) -> AgentState:
        route = state["route"]
        if route == "keyword":
            tool = keyword_search_tool
        elif route == "semantic":
            tool = semantic_search_tool
        else:
            tool = hybrid_search_tool
        tool.invoke({"query": state["question"]})

        if route == "keyword":
            found = keyword_search(session, owner_id=owner_id, query=state["question"], limit=8)
        else:
            vector = provider.embed_text(state["question"])
            semantic = semantic_search(
                session,
                owner_id=owner_id,
                query_vector=vector,
                limit=8,
            )
            if route == "semantic":
                found = semantic
            else:
                keyword = keyword_search(
                    session,
                    owner_id=owner_id,
                    query=state["question"],
                    limit=8,
                )
                found = hybrid_search(keyword, semantic, 8)

        return {**state, "results": found}

    def answer(state: AgentState) -> AgentState:
        results = state.get("results", [])
        if not results:
            return {
                **state,
                "answer": "I could not find enough information in your screenshot library.",
            }
        context_lines = []
        for result in results:
            item = result.item
            context_lines.append(
                f"[screenshot {item.id}] Title: {item.title or ''}\n"
                f"Description: {item.description or ''}\n"
                f"Tags: {', '.join(item.tags)}"
            )
        answer = provider.answer(
            state["question"],
            "\n\n".join(context_lines),
            history,
        )
        return {**state, "answer": answer}

    builder = StateGraph(AgentState)
    builder.add_node("supervisor", supervisor)
    builder.add_node("retrieval", retrieval)
    builder.add_node("answer", answer)
    builder.add_edge(START, "supervisor")
    builder.add_edge("supervisor", "retrieval")
    builder.add_edge("retrieval", "answer")
    builder.add_edge("answer", END)
    graph = builder.compile()
    state = graph.invoke(
        {
            "question": question,
            "owner_id": owner_id,
            "session": session,
            "provider": provider,
        }
    )
    return state["answer"], state.get("results", []), state.get("tool_trace", [])
