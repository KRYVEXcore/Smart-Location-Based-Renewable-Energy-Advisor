import enum


class BuildingType(str, enum.Enum):
    """The app's own assessment classification.

    Still used as-is by app.models.incentive_program (unchanged in Phase 5 —
    a future Incentive Engine phase can revisit that separately). For
    electricity tariffs, Phase 5 introduced TariffConsumerCategory below and
    an explicit mapping (app.engines.tariff.consumer_category_mapping)
    instead of reusing this enum directly: a building type and a real Indian
    DISCOM tariff category are not automatically equivalent (e.g. a "school"
    is billed as an educational-institution tariff, not a residential one).
    """

    HOME = "home"
    SCHOOL = "school"
    COLLEGE = "college"
    OFFICE = "office"
    SHOP = "shop"
    SMALL_INSTITUTION = "small_institution"
    OTHER = "other"


class TariffConsumerCategory(str, enum.Enum):
    """A real Indian electricity-tariff consumer category, as used by DISCOM
    tariff orders — distinct from BuildingType (the app's own assessment
    classification). See app.engines.tariff.consumer_category_mapping for
    the explicit, testable mapping between the two.
    """

    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    EDUCATIONAL_INSTITUTION = "educational_institution"
    PUBLIC_SERVICE = "public_service"
    INDUSTRIAL = "industrial"
    AGRICULTURE = "agriculture"
    OTHER = "other"


class AssessmentStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    COMPLETED = "completed"


class IncentiveLevel(str, enum.Enum):
    """Which authority offers the scheme — kept distinct so a state incentive
    is never confused with (or silently combined with) the central one.
    """

    CENTRAL = "central"
    STATE = "state"
    DISCOM = "discom"


class RenewableTechnology(str, enum.Enum):
    SOLAR = "solar"
    WIND = "wind"
    HYBRID = "hybrid"
    BATTERY = "battery"
    OTHER = "other"


class SubsidyType(str, enum.Enum):
    PERCENTAGE = "percentage"
    FIXED_AMOUNT = "fixed_amount"
    PER_KW = "per_kw"
    OTHER = "other"
