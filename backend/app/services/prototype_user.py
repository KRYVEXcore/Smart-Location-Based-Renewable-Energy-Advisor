"""Centralized prototype-only user resolution.

This project has no authentication yet (see app.core.security). Every
request is attributed to a single, deterministically-created "prototype"
user so the data model already has real, non-null foreign keys to a User.
This must be replaced by real authentication in a future phase — nothing
elsewhere in the app should hard-code a user id; it must come from here.
"""

import uuid

from sqlalchemy.orm import Session

from app.models.user import User

PROTOTYPE_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def get_or_create_prototype_user(db: Session) -> User:
    user = db.get(User, PROTOTYPE_USER_ID)
    if user is not None:
        return user

    user = User(id=PROTOTYPE_USER_ID)
    db.add(user)
    db.flush()
    return user
