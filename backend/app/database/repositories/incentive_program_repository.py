import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.enums import IncentiveLevel, RenewableTechnology, TariffConsumerCategory
from app.models.incentive_program import IncentiveProgram


class IncentiveProgramRepository:
    """Raw persistence access for incentive programmes. No eligibility,
    version-selection, or DISCOM-ambiguity handling here — see
    app.services.incentive_evaluation_service and app.engines.incentive.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def find_candidates(
        self,
        *,
        state: str | None,
        union_territory: str | None,
        technology: RenewableTechnology,
    ) -> list[IncentiveProgram]:
        """CENTRAL programmes (state-independent) plus STATE/DISCOM
        programmes scoped to this state/UT, for the requested technology.
        DISCOM-specific rows are included here regardless of which exact
        DISCOM — only the service layer knows whether the assessment's
        DISCOM was actually identified, ambiguous, or unresolved, and it
        never guesses.

        Deliberately NOT filtered by consumer_category: a programme that
        doesn't match the assessment's category must still come back so
        the engine can report it as "not_eligible" — hiding it at the
        query level would violate the "never hide an ineligible or
        uncertain programme" rule (see the README's Phase 6 notes).
        """
        query = select(IncentiveProgram).where(
            IncentiveProgram.active.is_(True),
            IncentiveProgram.technology == technology,
        )

        location_filters = [IncentiveProgram.level == IncentiveLevel.CENTRAL]
        if state:
            location_filters.append(IncentiveProgram.state == state)
        if union_territory:
            location_filters.append(IncentiveProgram.union_territory == union_territory)
        query = query.where(or_(*location_filters))

        return list(self.db.execute(query).scalars())

    def find_filtered(
        self,
        *,
        state: str | None = None,
        union_territory: str | None = None,
        discom_id: uuid.UUID | None = None,
        technology: RenewableTechnology | None = None,
        consumer_category: TariffConsumerCategory | None = None,
        level: IncentiveLevel | None = None,
        active_only: bool = True,
    ) -> list[IncentiveProgram]:
        """Unscoped filtered lookup backing GET /api/v1/incentives."""
        query = select(IncentiveProgram)
        if active_only:
            query = query.where(IncentiveProgram.active.is_(True))
        if state:
            query = query.where(IncentiveProgram.state == state)
        if union_territory:
            query = query.where(IncentiveProgram.union_territory == union_territory)
        if discom_id:
            query = query.where(IncentiveProgram.discom_id == discom_id)
        if technology:
            query = query.where(IncentiveProgram.technology == technology)
        if consumer_category:
            query = query.where(IncentiveProgram.consumer_category == consumer_category)
        if level:
            query = query.where(IncentiveProgram.level == level)

        return list(self.db.execute(query).scalars())
