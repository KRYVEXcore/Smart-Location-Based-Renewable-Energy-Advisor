import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.electricity_tariff import ElectricityTariff
from app.models.enums import TariffConsumerCategory


class TariffRepository:
    """Raw persistence access for electricity tariffs. No DISCOM-scoping or
    date-selection logic here — see app.services.tariff_calculation_service
    and app.engines.tariff for that.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def find_candidates(
        self,
        *,
        state: str | None,
        union_territory: str | None,
        consumer_category: TariffConsumerCategory,
    ) -> list[ElectricityTariff]:
        """All active rows for a state/UT + category, regardless of DISCOM or
        effective date — narrowing by DISCOM and date happens afterwards
        (see TariffCalculationService and app.engines.tariff.version_selection).
        """
        if not state and not union_territory:
            return []

        query = select(ElectricityTariff).where(
            ElectricityTariff.active.is_(True),
            ElectricityTariff.consumer_category == consumer_category,
        )
        if state:
            query = query.where(ElectricityTariff.state == state)
        else:
            query = query.where(ElectricityTariff.union_territory == union_territory)

        return list(self.db.execute(query).scalars())

    def find_filtered(
        self,
        *,
        state: str | None = None,
        union_territory: str | None = None,
        consumer_category: TariffConsumerCategory | None = None,
        discom_id: uuid.UUID | None = None,
        active_only: bool = True,
    ) -> list[ElectricityTariff]:
        """Unscoped filtered lookup backing GET /api/v1/tariffs."""
        query = select(ElectricityTariff)
        if active_only:
            query = query.where(ElectricityTariff.active.is_(True))
        if state:
            query = query.where(ElectricityTariff.state == state)
        if union_territory:
            query = query.where(ElectricityTariff.union_territory == union_territory)
        if consumer_category:
            query = query.where(ElectricityTariff.consumer_category == consumer_category)
        if discom_id:
            query = query.where(ElectricityTariff.discom_id == discom_id)

        return list(self.db.execute(query).scalars())
