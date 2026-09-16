from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.discom import Discom


class DiscomRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def find_by_state(self, state: str | None, union_territory: str | None) -> list[Discom]:
        if not state and not union_territory:
            return []

        query = select(Discom).where(Discom.is_active.is_(True))
        if state:
            query = query.where(Discom.state == state)
        else:
            query = query.where(Discom.union_territory == union_territory)

        return list(self.db.execute(query).scalars())
