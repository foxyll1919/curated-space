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


def test_keyword_search_natural_language_fallback(client):
    _add_item(
        client.app.state.session_factory,
        item_id="invoice-screenshot",
        owner_id="legacy-owner",
        title="Monthly billing invoice",
        vector=[0.0, 1.0],
    )

    response = client.get(
        "/api/v1/intelligence/search",
        params={"q": "show me the screenshot about invoice", "mode": "keyword"},
        headers={"X-API-Key": "test-api-key"},
    )
    assert response.status_code == 200
    body = response.json()
    assert [source["id"] for source in body["items"]] == ["invoice-screenshot"]


def test_gemini_failure_returns_200_with_insufficient_evidence(client):
    class CrashingProvider:
        model = "crashing-model"
        is_configured = True

        def embed_text(self, text: str) -> list[float]:
            raise RuntimeError("Gemini embed failure")

        def answer(self, question: str, context: str, history: str = "") -> str:
            raise RuntimeError("Gemini answer failure")

        def route(self, question: str) -> str:
            raise RuntimeError("Gemini route failure")

    client.app.state.embedding_provider = CrashingProvider()

    # Test /ask
    ask_resp = client.post(
        "/api/v1/intelligence/ask",
        json={"question": "anything"},
        headers={"X-API-Key": "test-api-key"},
    )
    assert ask_resp.status_code == 200
    ask_body = ask_resp.json()
    assert ask_body["insufficient_evidence"] is True
    assert "could not reach the answer service" in ask_body["answer"]

    # Test /agent
    agent_resp = client.post(
        "/api/v1/intelligence/agent",
        json={"question": "anything"},
        headers={"X-API-Key": "test-api-key"},
    )
    assert agent_resp.status_code == 200
    agent_body = agent_resp.json()
    assert agent_body["insufficient_evidence"] is True
    assert "could not reach the answer service" in agent_body["answer"]


def test_agent_embed_called_once_for_semantic_route(client):
    class CountingProvider(FakeEmbeddingProvider):
        def __init__(self) -> None:
            super().__init__()
            self.embed_call_count = 0

        def route(self, question: str) -> str:
            return "semantic"

        def embed_text(self, text: str) -> list[float]:
            self.embed_call_count += 1
            return super().embed_text(text)

    provider = CountingProvider()
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
        json={"question": "semantic test question"},
        headers={"X-API-Key": "test-api-key"},
    )
    assert response.status_code == 200
    assert provider.embed_call_count == 1
