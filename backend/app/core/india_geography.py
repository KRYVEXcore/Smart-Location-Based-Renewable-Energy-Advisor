"""Canonical India states/UTs.

This is static, universally-known administrative geography — not a
government policy value that can go stale or needs a source citation, so
it is a plain constant rather than a database table. Contrast with
electricity_tariff / incentive_program data, which genuinely does need
effective dates and a source (see app/models/electricity_tariff.py and
app/models/incentive_program.py).
"""

INDIAN_STATES: list[str] = [
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chhattisgarh",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
]

INDIAN_UNION_TERRITORIES: list[str] = [
    "Andaman and Nicobar Islands",
    "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi",
    "Jammu and Kashmir",
    "Ladakh",
    "Lakshadweep",
    "Puducherry",
]

# Handles the common spelling/naming variants a geocoder is likely to return.
_STATE_ALIASES: dict[str, str] = {
    "orissa": "Odisha",
    "pondicherry": "Puducherry",
    "nct of delhi": "Delhi",
    "national capital territory of delhi": "Delhi",
    "dadra and nagar haveli": "Dadra and Nagar Haveli and Daman and Diu",
    "daman and diu": "Dadra and Nagar Haveli and Daman and Diu",
    "andaman & nicobar islands": "Andaman and Nicobar Islands",
    "jammu & kashmir": "Jammu and Kashmir",
}

_CANONICAL_BY_LOWER: dict[str, str] = {
    name.lower(): name for name in (*INDIAN_STATES, *INDIAN_UNION_TERRITORIES)
}


def normalize_state_name(raw: str | None) -> str | None:
    """Maps a free-text state/UT name (as returned by a geocoder) to the
    canonical spelling in INDIAN_STATES / INDIAN_UNION_TERRITORIES.

    Returns None if it doesn't match any known state or UT — callers must
    treat that as "not identified", never guess a fallback.
    """
    if not raw:
        return None

    key = raw.strip().lower()
    if key in _CANONICAL_BY_LOWER:
        return _CANONICAL_BY_LOWER[key]
    if key in _STATE_ALIASES:
        return _STATE_ALIASES[key]
    return None


def is_union_territory(canonical_name: str) -> bool:
    return canonical_name in INDIAN_UNION_TERRITORIES
