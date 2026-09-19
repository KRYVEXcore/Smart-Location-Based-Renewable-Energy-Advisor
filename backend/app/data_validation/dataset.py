"""Loading and cross-record checks for the whole seed dataset.

`check_*` functions return a list of human-readable problems (empty = clean)
instead of raising, so a report can show every problem at once. The seed
scripts refuse to write anything while problems exist.
"""

from datetime import date
from itertools import combinations
from pathlib import Path
from types import SimpleNamespace

from app.core.india_geography import INDIAN_STATES, INDIAN_UNION_TERRITORIES
from app.data_validation.records import (
    DiscomRecord,
    IncentiveRecord,
    TariffScheduleRecord,
    load_json,
)
from app.engines.incentive.scope import applies_to_region
from app.engines.incentive.validation import validate_capacity_slabs
from app.engines.incentive.calculator import parse_capacity_slabs
from app.engines.tariff.validation import validate_slabs
from app.models.enums import IncentiveVerificationStatus, SubsidyType
from app.schemas.tariff import TariffSlabInput

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
TARIFF_ROOT = DATA_DIR / "tariffs" / "india"
INCENTIVE_ROOT = DATA_DIR / "incentives" / "india"
DISCOM_ROOT = DATA_DIR / "discoms" / "india"

INCENTIVE_GLOBS = ("central/*.json", "states/*/*.json", "discom/*/*.json")

LoadedTariff = tuple[Path, TariffScheduleRecord]
LoadedIncentive = tuple[Path, IncentiveRecord]
LoadedDiscom = tuple[Path, DiscomRecord]


def load_tariff_schedules(root: Path = TARIFF_ROOT) -> list[LoadedTariff]:
    return [(path, TariffScheduleRecord.model_validate(load_json(path))) for path in sorted(root.glob("*/*.json"))]


def load_incentive_records(root: Path = INCENTIVE_ROOT) -> list[LoadedIncentive]:
    paths = sorted(path for pattern in INCENTIVE_GLOBS for path in root.glob(pattern))
    return [(path, IncentiveRecord.model_validate(load_json(path))) for path in paths]


def load_discom_records(root: Path = DISCOM_ROOT) -> list[LoadedDiscom]:
    records: list[LoadedDiscom] = []
    for path in sorted(root.glob("*.json")):
        for item in load_json(path):
            records.append((path, DiscomRecord.model_validate(item)))
    return records


def _periods_overlap(a_from: date, a_to: date | None, b_from: date, b_to: date | None) -> bool:
    a_end = a_to or date.max
    b_end = b_to or date.max
    return a_from <= b_end and b_from <= a_end


def to_slab_inputs(schedule: TariffScheduleRecord) -> list[TariffSlabInput]:
    return [
        TariffSlabInput(
            tariff_version=schedule.tariff_version,
            tariff_name=schedule.tariff_name,
            slab_min_kwh=slab.slab_min_kwh,
            slab_max_kwh=slab.slab_max_kwh,
            energy_charge_inr_per_kwh=slab.energy_charge_inr_per_kwh,
            fixed_charge_inr=slab.fixed_charge_inr,
            fixed_charge_basis=schedule.fixed_charge_basis,
            wheeling_charge_inr_per_kwh=slab.wheeling_charge_inr_per_kwh,
            effective_from=schedule.effective_from,
            effective_to=schedule.effective_to,
        )
        for slab in schedule.slabs
    ]


def check_tariff_dataset(
    loaded: list[LoadedTariff], known_discoms: set[tuple[str, str]] | None = None
) -> list[str]:
    """`known_discoms` is a set of (short_code, state-or-UT) pairs; when given,
    every schedule naming a DISCOM must reference one of them.
    """
    problems: list[str] = []

    seen_keys: dict[tuple, Path] = {}
    for path, schedule in loaded:
        key = schedule.natural_key()
        if key in seen_keys:
            problems.append(f"{path.name}: duplicate schedule {key} (also in {seen_keys[key].name})")
        seen_keys[key] = path

        try:
            validate_slabs(to_slab_inputs(schedule))
        except ValueError as error:
            problems.append(f"{path.name}: invalid slabs: {error}")

        if schedule.discom_short_code and known_discoms is not None:
            region = schedule.state or schedule.union_territory or ""
            if (schedule.discom_short_code, region) not in known_discoms:
                problems.append(
                    f"{path.name}: DISCOM {schedule.discom_short_code!r} is not registered for {region!r}"
                )

    for (path_a, a), (path_b, b) in combinations(loaded, 2):
        same_scope = (
            (a.state, a.union_territory, a.discom_short_code, a.consumer_category)
            == (b.state, b.union_territory, b.discom_short_code, b.consumer_category)
        )
        if same_scope and _periods_overlap(a.effective_from, a.effective_to, b.effective_from, b.effective_to):
            problems.append(
                f"{path_a.name} and {path_b.name}: overlapping effective periods for the same "
                f"jurisdiction/DISCOM/category"
            )

    return problems


def _applicable_regions(record: IncentiveRecord) -> set[str]:
    regions: set[str] = set()
    for name in INDIAN_STATES:
        probe = SimpleNamespace(state=record.state, union_territory=record.union_territory, eligibility_rules=record.eligibility_rules)
        if applies_to_region(probe, state=name, union_territory=None):
            regions.add(name)
    for name in INDIAN_UNION_TERRITORIES:
        probe = SimpleNamespace(state=record.state, union_territory=record.union_territory, eligibility_rules=record.eligibility_rules)
        if applies_to_region(probe, state=None, union_territory=name):
            regions.add(name)
    return regions


def check_incentive_dataset(loaded: list[LoadedIncentive]) -> list[str]:
    problems: list[str] = []

    seen_keys: dict[tuple, Path] = {}
    for path, record in loaded:
        key = record.natural_key()
        if key in seen_keys:
            problems.append(f"{path.name}: duplicate scheme version {key} (also in {seen_keys[key].name})")
        seen_keys[key] = path

        if record.subsidy_type == SubsidyType.SLAB_BASED:
            slabs = parse_capacity_slabs(record.calculation_rules)
            if slabs is None:
                problems.append(f"{path.name}: slab_based scheme has no calculation_rules.slabs")
            else:
                try:
                    validate_capacity_slabs(slabs)
                except ValueError as error:
                    problems.append(f"{path.name}: invalid capacity slabs: {error}")
        if record.subsidy_type in (SubsidyType.FIXED_AMOUNT, SubsidyType.PER_KW) and record.subsidy_value is None:
            problems.append(f"{path.name}: {record.subsidy_type.value} scheme has no subsidy_value")

    for (path_a, a), (path_b, b) in combinations(loaded, 2):
        same_scheme = (a.scheme_name, a.level, a.technology) == (b.scheme_name, b.level, b.technology)
        if not same_scheme or not _periods_overlap(a.effective_from, a.effective_to, b.effective_from, b.effective_to):
            continue
        shared = _applicable_regions(a) & _applicable_regions(b)
        if shared and (a.consumer_category == b.consumer_category):
            problems.append(
                f"{path_a.name} and {path_b.name}: overlapping periods and both apply in {sorted(shared)[:3]}"
            )

    return problems


def check_discom_dataset(loaded: list[LoadedDiscom]) -> list[str]:
    problems: list[str] = []
    seen: set[tuple[str, str]] = set()
    for path, record in loaded:
        key = (record.short_code, record.state or record.union_territory or "")
        if key in seen:
            problems.append(f"{path.name}: duplicate DISCOM {key}")
        seen.add(key)
    return problems


def known_discom_keys(loaded: list[LoadedDiscom]) -> set[tuple[str, str]]:
    return {(r.short_code, r.state or r.union_territory or "") for _, r in loaded}


def is_verified(record: TariffScheduleRecord | IncentiveRecord) -> bool:
    return record.verification_status == IncentiveVerificationStatus.VERIFIED
