import enum


class BuildingType(str, enum.Enum):
    """Also used as the consumer category for tariff/incentive matching
    (app.models.electricity_tariff, app.models.incentive_program) — kept as
    one enum rather than a duplicate "ConsumerCategory" so a future engine
    never needs a translation table between the two concepts.
    """

    HOME = "home"
    SCHOOL = "school"
    COLLEGE = "college"
    OFFICE = "office"
    SHOP = "shop"
    SMALL_INSTITUTION = "small_institution"
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
