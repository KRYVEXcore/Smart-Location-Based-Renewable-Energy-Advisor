"""Explicit BuildingType -> TariffConsumerCategory mapping.

The app's assessment BuildingType and a real Indian DISCOM tariff category
are different concepts and must never be treated as automatically
equivalent (a "school" is billed under an educational-institution tariff,
not the residential tariff a "home" gets). This table is the single place
that decision is made, so it stays visible, editable, and unit-tested
rather than implicit in query logic.
"""

from app.models.enums import BuildingType, TariffConsumerCategory

BUILDING_TYPE_TO_CONSUMER_CATEGORY: dict[BuildingType, TariffConsumerCategory] = {
    BuildingType.HOME: TariffConsumerCategory.RESIDENTIAL,
    BuildingType.SCHOOL: TariffConsumerCategory.EDUCATIONAL_INSTITUTION,
    BuildingType.COLLEGE: TariffConsumerCategory.EDUCATIONAL_INSTITUTION,
    BuildingType.OFFICE: TariffConsumerCategory.COMMERCIAL,
    BuildingType.SHOP: TariffConsumerCategory.COMMERCIAL,
    # A generic "small institution" (e.g. a community hall, NGO office) maps
    # to the public-service tariff category rather than commercial or
    # residential — the closest real-world equivalent without more detail
    # about the institution's actual use.
    BuildingType.SMALL_INSTITUTION: TariffConsumerCategory.PUBLIC_SERVICE,
    BuildingType.OTHER: TariffConsumerCategory.OTHER,
}


def map_building_type_to_consumer_category(building_type: BuildingType) -> TariffConsumerCategory:
    """Raises KeyError if a BuildingType is ever added without updating the
    mapping above — deliberately not a silent fallback to OTHER.
    """
    return BUILDING_TYPE_TO_CONSUMER_CATEGORY[building_type]
