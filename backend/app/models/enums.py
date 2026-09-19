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
    """How an incentive's amount is calculated — distinct from IncentiveType
    (what kind of instrument it is) below.
    """

    PERCENTAGE = "percentage"
    FIXED_AMOUNT = "fixed_amount"
    PER_KW = "per_kw"
    # Phase 6 additions — see app.engines.incentive.calculator.
    SLAB_BASED = "slab_based"
    BENCHMARK_COST_BASED = "benchmark_cost_based"
    OTHER = "other"


class IncentiveType(str, enum.Enum):
    """What kind of instrument an incentive is — distinct from SubsidyType
    (how its amount is calculated) and IncentiveLevel (who offers it).
    """

    CAPITAL_SUBSIDY = "capital_subsidy"
    CENTRAL_FINANCIAL_ASSISTANCE = "central_financial_assistance"
    STATE_SUBSIDY = "state_subsidy"
    DISCOM_INCENTIVE = "discom_incentive"
    REBATE = "rebate"
    INTEREST_SUBVENTION = "interest_subvention"
    GRANT = "grant"
    PERFORMANCE_INCENTIVE = "performance_incentive"
    OTHER = "other"


class IncentiveVerificationStatus(str, enum.Enum):
    """Distinct from IncentiveProgram.active: `active` says whether a row
    should be considered at all; this says how much to trust it. Only
    VERIFIED programmes may be used for automatic eligibility/calculation
    (see app.engines.incentive.eligibility) — the others exist so a
    partially-researched scheme can be recorded honestly instead of either
    fabricated or silently omitted.
    """

    VERIFIED = "verified"
    PENDING_REVIEW = "pending_review"
    EXPIRED = "expired"
    SUPERSEDED = "superseded"
    UNAVAILABLE = "unavailable"


class FixedChargeBasis(str, enum.Enum):
    """What a tariff's fixed charge is charged *per*. Real Indian tariffs
    quote fixed charges per connection, per kW of sanctioned load, per kVA,
    or per HP — only the flat-monthly bases can be billed from the data
    this app collects. A per-kW/kVA/HP charge is never turned into a flat
    monthly amount (see app.engines.tariff.bill_calculation).
    """

    INR_PER_MONTH = "inr_per_month"
    INR_PER_CONNECTION_PER_MONTH = "inr_per_connection_per_month"
    INR_PER_KW_PER_MONTH = "inr_per_kw_per_month"
    INR_PER_KVA_PER_MONTH = "inr_per_kva_per_month"
    INR_PER_HP_PER_MONTH = "inr_per_hp_per_month"
