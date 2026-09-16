"""Resolves a geocoded location to India's administrative hierarchy
(state/UT -> district -> city -> DISCOM) for future tariff/incentive
matching.

This never guesses: a state/UT that doesn't match the canonical list in
app.core.india_geography, or a DISCOM that can't be uniquely identified,
comes back as None with an honest status — never a fabricated value.
"""

from app.core.india_geography import is_union_territory, normalize_state_name
from app.database.repositories.discom_repository import DiscomRepository
from app.models.discom import Discom
from app.schemas.location import DiscomInfo, GeocodingCandidate, IndiaLocationContext


class IndiaLocationResolver:
    def __init__(self, discom_repository: DiscomRepository | None) -> None:
        self._discoms = discom_repository

    def resolve(self, candidate: GeocodingCandidate | None) -> IndiaLocationContext:
        if candidate is None:
            return IndiaLocationContext()

        canonical = normalize_state_name(candidate.state)
        state = None
        union_territory = None
        if canonical:
            if is_union_territory(canonical):
                union_territory = canonical
            else:
                state = canonical

        discom, status = self._resolve_discom(state, union_territory)

        return IndiaLocationContext(
            state=state,
            union_territory=union_territory,
            district=candidate.district,
            city=candidate.city,
            discom=discom,
            discom_status=status,
        )

    def _resolve_discom(
        self, state: str | None, union_territory: str | None
    ) -> tuple[DiscomInfo | None, str]:
        if self._discoms is None or (not state and not union_territory):
            return None, "not_identified"

        matches: list[Discom] = self._discoms.find_by_state(state, union_territory)

        if len(matches) == 1:
            match = matches[0]
            return DiscomInfo(id=str(match.id), name=match.name, short_code=match.short_code), "identified"
        if len(matches) > 1:
            return None, "ambiguous"
        return None, "not_identified"
