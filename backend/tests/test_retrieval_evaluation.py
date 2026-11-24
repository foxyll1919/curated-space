from app.services.retrieval_evaluation import evaluate_retrieval, recall_at, reciprocal_rank


def test_retrieval_metrics():
    assert recall_at(["a", "b", "c"], {"b", "c", "d"}, 2) == 1 / 3
    assert reciprocal_rank(["a", "b", "c"], {"c"}) == 1 / 3


def test_synthetic_retrieval_comparison():
    # Synthetic fixture with realistic screenshot-library questions.
    queries = [
        "RAG architecture approaches",
        "LangGraph supervisor workflow",
        "Python recursion explanation",
        "React server component notes",
        "FastAPI authentication pattern",
        "SQLAlchemy session design",
        "vector database comparison",
        "embedding model pricing",
        "prompt injection example",
        "machine learning interview preparation",
        "placement aptitude schedule",
        "resume project summary",
        "Docker deployment diagram",
        "CI pipeline configuration",
        "database migration checklist",
        "REST API error handling",
        "JWT security notes",
        "CORS troubleshooting",
        "Gemini structured output",
        "Pydantic validation example",
        "FTS5 search syntax",
        "hybrid retrieval formula",
        "retrieval evaluation metrics",
        "screenshot privacy warning",
        "GitHub pull request checklist",
        "Python async task example",
        "React query cache notes",
        "Vite environment variables",
        "SQLite ownership query",
        "Agent tool routing decision",
    ]
    cases = [
        (query, {f"screenshot-{index}", f"screenshot-{index + 100}"})
        for index, query in enumerate(queries)
    ]

    keyword_rankings = []
    semantic_rankings = []
    hybrid_rankings = []
    for index, (_, relevant) in enumerate(cases):
        keyword = [f"screenshot-{index}", *[f"noise-{n}" for n in range(12)]]
        semantic = [
            f"screenshot-{index + 100}",
            f"screenshot-{index}",
            *[f"noise-{n}" for n in range(12)],
        ]
        hybrid = [
            f"screenshot-{index}",
            f"screenshot-{index + 100}",
            *[f"noise-{n}" for n in range(12)],
        ]
        keyword_rankings.append((keyword, relevant))
        semantic_rankings.append((semantic, relevant))
        hybrid_rankings.append((hybrid, relevant))

    keyword = evaluate_retrieval(keyword_rankings)
    semantic = evaluate_retrieval(semantic_rankings)
    hybrid = evaluate_retrieval(hybrid_rankings)

    assert keyword.recall_at_5 == 0.5
    assert semantic.recall_at_5 == 1.0
    assert hybrid.recall_at_5 == 1.0
    assert 0.0 < hybrid.mrr <= 1.0
