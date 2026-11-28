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
        if "rag" in lowered or "retrieval" in lowered or "simplest" in lowered:
            return [1.0, 0.0]
        return [0.0, 1.0]

    def answer(self, question: str, context: str, history: str = "") -> str:
        self.questions.append(question)
        self.contexts.append(context)
        self.histories.append(history)
        return "RAG combines retrieval with grounded generation. [screenshot-one]"

    def answer_stream(self, question: str, context: str, history: str = ""):
        answer = self.answer(question, context, history)
        for word in answer.split(" "):
            yield word + " "

    def route(self, question: str) -> str:
        return "hybrid"

    def rewrite_query(self, question: str, history: str = "") -> str:
        if "second one" in question.lower() and "invoice" in history.lower():
            return "second invoice reference"
        return question


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

        def answer_stream(self, question: str, context: str, history: str = ""):
            raise RuntimeError("Gemini answer failure")

        def route(self, question: str) -> str:
            raise RuntimeError("Gemini route failure")

        def rewrite_query(self, question: str, history: str = "") -> str:
            raise RuntimeError("Gemini rewrite failure")

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


def test_semantic_cutoff_excludes_low_similarity(client):
    provider = FakeEmbeddingProvider()
    client.app.state.embedding_provider = provider
    # Query for RAG gets [1.0, 0.0]
    # screenshot-low gets [0.0, 1.0], cosine similarity is 0.0 < 0.35
    _add_item(
        client.app.state.session_factory,
        item_id="screenshot-low",
        owner_id="legacy-owner",
        title="Unrelated cooking recipe",
        vector=[0.0, 1.0],
    )

    response = client.get(
        "/api/v1/intelligence/search",
        params={"q": "RAG architecture", "mode": "semantic"},
        headers={"X-API-Key": "test-api-key"},
    )
    assert response.status_code == 200
    assert response.json()["items"] == []


def test_follow_up_question_rewriting(client):
    provider = FakeEmbeddingProvider()
    client.app.state.embedding_provider = provider
    _add_item(
        client.app.state.session_factory,
        item_id="second-invoice",
        owner_id="legacy-owner",
        title="Second invoice reference",
        vector=[0.0, 1.0],
    )

    response = client.post(
        "/api/v1/intelligence/agent",
        json={
            "question": "What about the second one?",
            "history": [
                {"role": "user", "content": "Show me invoice screenshots"},
                {"role": "assistant", "content": "Here is the first invoice [first-invoice]."},
            ],
        },
        headers={"X-API-Key": "test-api-key"},
    )
    assert response.status_code == 200
    body = response.json()
    # Query was rewritten to "second invoice reference" which matches "second-invoice" item!
    assert any(s["id"] == "second-invoice" for s in body["sources"])


def test_agent_stream_emits_sse_events(client):
    import json

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
        "/api/v1/intelligence/agent/stream",
        json={"question": "Compare RAG approaches"},
        headers={"X-API-Key": "test-api-key"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    events = []
    for line in response.text.split("\n\n"):
        if not line.strip():
            continue
        parts = {}
        for field in line.strip().split("\n"):
            if field.startswith("event: "):
                parts["event"] = field[7:]
            elif field.startswith("data: "):
                parts["data"] = json.loads(field[6:])
        if parts:
            events.append(parts)

    event_types = [e["event"] for e in events]
    assert "tool_trace" in event_types
    assert "answer_chunk" in event_types
    assert "sources" in event_types
    assert "done" in event_types

    # tool_trace comes first
    tool_event = next(e for e in events if e["event"] == "tool_trace")
    assert tool_event["data"]["tools"] == ["hybrid_search"]

    # Sources include the matching item
    source_event = next(e for e in events if e["event"] == "sources")
    source_ids = [s["id"] for s in source_event["data"]["sources"]]
    assert "screenshot-one" in source_ids

    # Answer chunks reassemble into the full answer
    chunks = [e["data"]["chunk"] for e in events if e["event"] == "answer_chunk"]
    full_answer = "".join(chunks)
    assert "[screenshot-one]" in full_answer


def test_agent_stream_error_on_provider_failure(client):
    import json

    class CrashingStreamProvider:
        model = "crashing-model"
        is_configured = True

        def embed_text(self, text: str) -> list[float]:
            raise RuntimeError("Gemini embed failure")

        def answer(self, question: str, context: str, history: str = "") -> str:
            raise RuntimeError("Gemini answer failure")

        def answer_stream(self, question: str, context: str, history: str = ""):
            raise RuntimeError("Gemini answer failure")

        def route(self, question: str) -> str:
            raise RuntimeError("Gemini route failure")

        def rewrite_query(self, question: str, history: str = "") -> str:
            raise RuntimeError("Gemini rewrite failure")

    client.app.state.embedding_provider = CrashingStreamProvider()

    response = client.post(
        "/api/v1/intelligence/agent/stream",
        json={"question": "anything"},
        headers={"X-API-Key": "test-api-key"},
    )
    assert response.status_code == 200

    events = []
    for line in response.text.split("\n\n"):
        if not line.strip():
            continue
        parts = {}
        for field in line.strip().split("\n"):
            if field.startswith("event: "):
                parts["event"] = field[7:]
            elif field.startswith("data: "):
                parts["data"] = json.loads(field[6:])
        if parts:
            events.append(parts)

    error_events = [e for e in events if e["event"] == "error"]
    assert len(error_events) >= 1
    assert "could not reach the answer service" in error_events[0]["data"]["message"]


def test_agent_stream_no_results(client):
    import json

    provider = FakeEmbeddingProvider()
    client.app.state.embedding_provider = provider

    response = client.post(
        "/api/v1/intelligence/agent/stream",
        json={"question": "What about quantum computing?"},
        headers={"X-API-Key": "test-api-key"},
    )
    assert response.status_code == 200

    events = []
    for line in response.text.split("\n\n"):
        if not line.strip():
            continue
        parts = {}
        for field in line.strip().split("\n"):
            if field.startswith("event: "):
                parts["event"] = field[7:]
            elif field.startswith("data: "):
                parts["data"] = json.loads(field[6:])
        if parts:
            events.append(parts)

    source_event = next(e for e in events if e["event"] == "sources")
    assert source_event["data"]["sources"] == []
    assert source_event["data"]["insufficient_evidence"] is True
