"""Create or update an account from the terminal.

```powershell
uv run python -m app.cli.bootstrap-user you@example.com
uv run python -m app.cli.bootstrap-user you@example.com --open-registration
```

The prompt reads the password with `getpass` so it never reaches shell history
or the scrollback buffer. Existing accounts are refused rather than silently
re-keyed; a forgotten password is reset with `--reset-password`, which also
revokes that account's sessions.
"""

from __future__ import annotations

import argparse
import getpass
import sys

from sqlalchemy import delete

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import hash_password
from app.db.models import Session as SessionRow
from app.db.session import create_database_engine, create_session_factory
from app.services.auth import create_user, find_user, normalize_email


def _read_password(prompt: str = "Password: ") -> str:
    first = getpass.getpass(prompt)
    if first != getpass.getpass("Confirm password: "):
        raise SystemExit("The passwords did not match.")
    return first


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create or reset a Curated Space account.")
    parser.add_argument("email", help="Login address for the account.")
    parser.add_argument(
        "--reset-password",
        action="store_true",
        help="Replace the password of an existing account and revoke its sessions.",
    )
    parser.add_argument(
        "--open-registration",
        action="store_true",
        help="Also allow self-registration in the API from now on.",
    )
    args = parser.parse_args(argv)

    settings = get_settings()
    engine = create_database_engine(settings)
    session_factory = create_session_factory(engine)
    try:
        with session_factory() as session:
            existing = find_user(session, args.email)
            if existing is not None and not args.reset_password:
                print(f"An account already exists for {normalize_email(args.email)}.")
                return 1

            if existing is None:
                password = _read_password()
                try:
                    user, is_first = create_user(
                        session, settings, email=args.email, password=password
                    )
                except AppError as exc:
                    print(f"{exc.public_message} ({exc.code})")
                    return 1
                print(
                    f"Created {user.email}"
                    + (" and claimed the pre-auth items." if is_first else ".")
                )
            else:
                password = _read_password()
                user = existing
                user.password_hash = hash_password(
                    password, iterations=settings.password_hash_iterations
                )
                session.execute(delete(SessionRow).where(SessionRow.user_id == user.id))
                session.commit()
                print(f"Reset the password for {user.email} and revoked its sessions.")

            if args.open_registration:
                print(
                    "To keep registration open, set AUTH_ALLOW_REGISTRATION=true in backend/.env."
                )
    finally:
        engine.dispose()
    return 0


if __name__ == "__main__":
    sys.exit(main())
