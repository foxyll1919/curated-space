"""Account routes, session cookies and ownership for signed-in browsers."""

from __future__ import annotations

from app.core.security import hash_password, hash_session_token, verify_password
from tests.conftest import FakeClassifier, FakeExtractor, make_image


REGISTRATION = {"email": "Owner@Example.com ", "password": "correct horse battery"}


def register(client, **overrides: str) -> dict:
    payload = {**REGISTRATION, **overrides}
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_first_registration_is_allowed_and_normalizes_the_email(make_client, auth_settings):
    client = make_client(auth_settings)
    body = register(client)
    assert body["user"]["email"] == "owner@example.com"
    assert "password" not in body["user"]
    assert client.get("/api/v1/auth/me").json() == body["user"]


def test_password_hash_is_salted_and_never_stored_in_the_clear(make_client, auth_settings):
    client = make_client(auth_settings)
    register(client)

    from app.db.models import User
    from app.db.session import create_database_engine, create_session_factory

    engine = create_database_engine(auth_settings)
    try:
        with create_session_factory(engine)() as session:
            stored = session.query(User).one()
    finally:
        engine.dispose()

    assert REGISTRATION["password"] not in stored.password_hash
    assert stored.password_hash.startswith("pbkdf2_sha256$")
    assert verify_password(REGISTRATION["password"], stored.password_hash)
    assert not verify_password("something else", stored.password_hash)


def test_registration_closes_after_the_first_account(make_client, auth_settings):
    client = make_client(auth_settings)
    register(client)
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "second@example.com", "password": "another long one"},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"


def test_open_registration_allows_more_accounts(make_client, migrated_settings):
    settings = migrated_settings.model_copy(
        update={"api_key": None, "auth_allow_registration": True}
    )
    client = make_client(settings)
    register(client)
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "second@example.com", "password": "another long one"},
    )
    assert response.status_code == 201


def test_duplicate_email_is_rejected(make_client, auth_settings):
    client = make_client(auth_settings)
    register(client)
    client.post("/api/v1/auth/logout")
    response = client.post("/api/v1/auth/register", json=REGISTRATION)
    assert response.status_code == 409


def test_short_password_and_bad_address_are_rejected(make_client, auth_settings):
    client = make_client(auth_settings)
    assert (
        client.post("/api/v1/auth/register", json={**REGISTRATION, "password": "short"}).status_code
        == 400
    )
    assert (
        client.post("/api/v1/auth/register", json={**REGISTRATION, "email": "nope"}).status_code
        == 400
    )
    # A rejected attempt must not create a half-built account.
    assert client.get("/api/v1/auth/status").json()["users"] == 0


def test_login_sets_an_httponly_cookie_and_me_reads_it(make_client, auth_settings):
    client = make_client(auth_settings)
    register(client)
    client.post("/api/v1/auth/logout")

    response = client.post("/api/v1/auth/login", json=REGISTRATION)
    assert response.status_code == 200
    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie
    assert "samesite=lax" in cookie
    # The token must never be readable by page scripts.
    assert "password" not in response.text
    assert client.get("/api/v1/auth/me").status_code == 200


def test_wrong_password_and_unknown_address_answer_identically(make_client, auth_settings):
    client = make_client(auth_settings)
    register(client)
    client.post("/api/v1/auth/logout")

    wrong_password = client.post(
        "/api/v1/auth/login", json={**REGISTRATION, "password": "not the password"}
    )
    unknown_user = client.post(
        "/api/v1/auth/login", json={"email": "nobody@example.com", "password": "whatever long"}
    )
    assert wrong_password.status_code == unknown_user.status_code == 401
    # Same code and message; only the request id may differ.
    assert wrong_password.json()["error"]["code"] == unknown_user.json()["error"]["code"]
    assert wrong_password.json()["error"]["message"] == unknown_user.json()["error"]["message"]
    assert client.get("/api/v1/auth/me").status_code == 401


def test_logout_clears_the_session_and_the_cookie(make_client, auth_settings):
    client = make_client(auth_settings)
    register(client)
    assert client.post("/api/v1/auth/logout").status_code == 204
    assert client.get("/api/v1/auth/me").status_code == 401
    # Idempotent: signing out twice is not an error.
    assert client.post("/api/v1/auth/logout").status_code == 204


def test_logout_all_revokes_every_session(make_client, auth_settings):
    first = make_client(auth_settings)
    register(first)
    second = make_client(auth_settings)
    second.post("/api/v1/auth/login", json=REGISTRATION)
    assert second.get("/api/v1/auth/me").status_code == 200

    assert first.post("/api/v1/auth/logout-all").status_code == 204
    assert second.get("/api/v1/auth/me").status_code == 401


def test_expired_session_is_refused_and_cleaned_up(make_client, auth_settings):
    from datetime import UTC, datetime, timedelta

    from app.db.models import Session as SessionRow
    from app.db.session import create_database_engine, create_session_factory

    client = make_client(auth_settings)
    register(client)

    engine = create_database_engine(auth_settings)
    try:
        with create_session_factory(engine)() as session:
            row = session.query(SessionRow).one()
            row.expires_at = datetime.now(UTC) - timedelta(minutes=1)
            token_hash = row.token_hash
            session.commit()
    finally:
        engine.dispose()

    assert client.get("/api/v1/auth/me").status_code == 401
    engine = create_database_engine(auth_settings)
    try:
        with create_session_factory(engine)() as session:
            assert (
                session.query(SessionRow).filter(SessionRow.token_hash == token_hash).count() == 0
            )
    finally:
        engine.dispose()


def test_login_is_rate_limited_per_ip(make_client, migrated_settings):
    settings = migrated_settings.model_copy(
        update={"api_key": None, "login_rate_limit": 3, "rate_limit_window_seconds": 60}
    )
    client = make_client(settings)
    statuses = [client.post("/api/v1/auth/login", json=REGISTRATION).status_code for _ in range(4)]
    assert statuses[:3] == [401, 401, 401]
    assert statuses[3] == 429


def test_one_user_cannot_read_or_delete_another_users_item(
    make_client, migrated_settings, extractor: FakeExtractor, classifier: FakeClassifier
):
    settings = migrated_settings.model_copy(
        update={"api_key": None, "auth_allow_registration": True}
    )
    owner = make_client(settings)
    register(owner)
    upload = owner.post("/api/v1/items", files={"file": ("a.png", make_image(), "image/png")})
    assert upload.status_code == 202
    item_id = upload.json()["id"]

    intruder = make_client(settings)
    register(intruder, email="intruder@example.com")
    assert intruder.get(f"/api/v1/items/{item_id}").status_code == 404
    assert intruder.get(f"/api/v1/items/{item_id}/image").status_code == 404
    assert intruder.patch(f"/api/v1/items/{item_id}", json={"title": "mine now"}).status_code == 404
    assert intruder.delete(f"/api/v1/items/{item_id}").status_code == 404
    assert intruder.get("/api/v1/items").json()["items"] == []
    # The owner's item is untouched.
    assert owner.get(f"/api/v1/items/{item_id}").status_code == 200


def test_api_key_still_authenticates_without_a_session(make_client, migrated_settings):
    client = make_client(migrated_settings)
    response = client.post(
        "/api/v1/items",
        files={"file": ("a.png", make_image(), "image/png")},
        headers={"X-API-Key": "test-api-key"},
    )
    assert response.status_code == 202
    assert client.get("/api/v1/auth/me").status_code == 401


def test_first_account_claims_pre_auth_items(make_client, migrated_settings):
    """Items saved through the API key before accounts existed belong to account one."""
    from app.db.models import Item
    from app.db.session import create_database_engine, create_session_factory

    key_client = make_client(migrated_settings)
    created = key_client.post(
        "/api/v1/items",
        files={"file": ("a.png", make_image(), "image/png")},
        headers={"X-API-Key": "test-api-key"},
    ).json()

    user_client = make_client(migrated_settings)
    body = register(user_client)

    engine = create_database_engine(migrated_settings)
    try:
        with create_session_factory(engine)() as session:
            item = session.get(Item, created["id"])
    finally:
        engine.dispose()
    assert item.owner_id == body["user"]["id"]
    assert user_client.get(f"/api/v1/items/{created['id']}").status_code == 200


def test_auth_status_reports_registration_availability(make_client, auth_settings):
    client = make_client(auth_settings)
    empty = client.get("/api/v1/auth/status").json()
    assert empty == {"users": 0, "registration_open": True}
    register(client)
    assert client.get("/api/v1/auth/status").json() == {"users": 1, "registration_open": False}


def test_session_cookie_holds_a_raw_token_and_the_db_holds_only_its_digest(
    make_client, auth_settings
):
    from app.db.models import Session as SessionRow
    from app.db.session import create_database_engine, create_session_factory

    client = make_client(auth_settings)
    register(client)
    raw_token = client.cookies[auth_settings.auth_cookie_name]

    engine = create_database_engine(auth_settings)
    try:
        with create_session_factory(engine)() as session:
            stored = session.query(SessionRow).one().token_hash
    finally:
        engine.dispose()
    assert stored == hash_session_token(raw_token)
    assert raw_token not in stored


def test_verify_password_rejects_a_corrupted_hash():
    assert not verify_password("anything", "not-a-hash")
    assert not verify_password("anything", "pbkdf2_sha256$notanint$AAAA$AAAA")
    assert not verify_password("anything", "bcrypt$600000$AAAA$AAAA")


def test_hash_password_round_trips():
    encoded = hash_password("a real password", iterations=1_000)
    assert verify_password("a real password", encoded)
    assert not verify_password("a real passwore", encoded)
