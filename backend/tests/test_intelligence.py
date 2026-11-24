from __future__ import annotations

from app.db.models import Item, ItemEmbedding


class FakeEmbeddingProvider:
    model = "fake-embedding"
    is_configured = True

    def __init__(self) -> None:
        self.questions: list[str] = []
        self.contexts: list[str] = []
        self.histories: list[str] = []

    def embed_text(self, text: str) -> list[float]:
        lowered = text.lower()
        if "rag" in lowered or "retrieval" in lowered:
            return [1.0, 0.0]
        return [0.0, 1.0]

    def answer(self, question: str, context: str, history: str = "") -> str:
        self.questions.append(question)
        self.contexts.append(context)
        self.histories.append(history)
        return "RAG combines retrieval with grounded generation. [screenshot-one]"

    def route(self, question: str) -> str:
        return "hybrid"


def _add_item(
    session_factory, *, item_id: str, owner_id: str, title: str, vector: list[float]
) -> None:
    with session_factory() as session:
        item = Item(
            id=item_id,
            owner_id=owner_id,
            status="ready",
            image_key=f"{item_id}.png",
            title=title,
            description="A useful RAG architecture reference.",
            tags=["rag", "architecture"],
        )
        session.add(item)
        session.add(
            ItemEmbedding(
                item_id=item_id,
                model="fake-embedding",
                text_hash="test",
                dimensions=len(vector),
                vector=vector,
            )
        )
        session.commit()


def test_hybrid_search_and_owner_isolation(client, migrated_settings):
    provider = FakeEmbeddingProvider()
    client.app.state.embedding_provider = provider
    _add_item(
        client.app.state.session_factory,
        item_id="screenshot-one",
        owner_id="legacy-owner",
        title="RAG architecture",
        vector=[1.0, 0.0],
    )
    _add_item(
        client.app.state.session_factory,
        item_id="other-owner",
        owner_id="another-owner",
        title="RAG private result",
        vector=[1.0, 0.0],
    )

    response = client.get(
        "/api/v1/intelligence/search",
        params={"q": "RAG architecture", "mode": "hybrid"},
        headers={"X-API-Key": "test-api-key"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "hybrid"
    assert [source["id"] for source in body["items"]] == ["screenshot-one"]


def test_ask_returns_grounded_source(client):
    provider = FakeEmbeddingProvider()
    client.app.state.embedding_provider = provider
    _add_item(
        client.app.state.session_factory,
        item_id="screenshot-one",
        owner_id="legacy-owner",
        title="RAG architecture",
        vector=[1.0, 0.0],
    )

    response = client.post(
        "/api/v1/intelligence/ask",
        json={"question": "Explain RAG architectures"},
        headers={"X-API-Key": "test-api-key"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["insufficient_evidence"] is False
    assert body["sources"][0]["id"] == "screenshot-one"
    assert "[screenshot-one]" in body["answer"]
    assert provider.questions == ["Explain RAG architectures"]
    assert "A useful RAG architecture reference." in provider.contexts[0]


def test_ask_without_relevant_results_is_insufficient(client):
    provider = FakeEmbeddingProvider()
    client.app.state.embedding_provider = provider

    response = client.post(
        "/api/v1/intelligence/ask",
        json={"question": "What did I save about quantum finance?"},
        headers={"X-API-Key": "test-api-key"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["insufficient_evidence"] is True
    assert body["sources"] == []


def test_follow_up_history_reaches_answer_provider(client):
    provider = FakeEmbeddingProvider()
    client.app.state.embedding_provider = provider
    _add_item(
        client.app.state.session_factory,
        item_id="screenshot-one",
        owner_id="legacy-owner",
        title="RAG architecture",
        vector=[1.0, 0.0],
    )

    response = client.post(
        "/api/v1/intelligence/agent",
        json={
            "question": "Which approach is simplest?",
            "history": [
                {"role": "user", "content": "Compare RAG approaches"},
                {"role": "assistant", "content": "The library shows one RAG architecture."},
            ],
        },
        headers={"X-API-Key": "test-api-key"},
    )
    assert response.status_code == 200
    assert provider.histories == [
        "user: Compare RAG approaches\nassistant: The library shows one RAG architecture."
    ]


def test_langgraph_agent_uses_tool_and_returns_source(client):
    provider = FakeEmbeddingProvider()
    client.app.state.embedding_provider = provider
    _add_item(
        client.app.state.session_factory,
        item_id="screenshot-one",
        owner_id="legacy-owner",
        title="RAG architecture",
        vector=[1.0, 0.0],
    )

    response = client.post(
        "/api/v1/intelligence/agent",
        json={"question": "Compare RAG approaches"},
        headers={"X-API-Key": "test-api-key"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["tool_trace"] == ["hybrid_search"]
    assert body["sources"][0]["id"] == "screenshot-one"
