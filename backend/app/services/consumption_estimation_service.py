import logging

from sqlalchemy.orm import Session

from app.models.assessment import Assessment
from app.services.location.location_service import LocationService
from app.services.tariff_calculation_service import TariffCalculationService

logger = logging.getLogger(__name__)

BILL_ESTIMATE_SOURCE = "user_bill_estimate"


class ConsumptionEstimationService:
    """Bill-first assessments: fills in the kWh figure the other engines use.

    Only assessments whose consumption_source is 'user_bill_estimate' are touched; a value the
    user entered (units) is never overwritten. When no estimate can be made, consumption stays
    unknown (NULL) with the reason recorded - it is never defaulted.
    """

    def __init__(self, db: Session, location_service: LocationService) -> None:
        self._db = db
        self._tariff = TariffCalculationService(db, location_service)

    def apply(self, assessment: Assessment) -> None:
        energy = assessment.energy
        if energy.consumption_source != BILL_ESTIMATE_SOURCE or energy.monthly_electricity_bill_inr is None:
            return
        estimate = self._tariff.estimate_consumption_from_bill(assessment)
        energy.consumption_estimate = estimate.model_dump(mode="json")
        energy.monthly_consumption_kwh = estimate.estimated_monthly_consumption_kwh
        self._db.commit()
