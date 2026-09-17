import pytest

from app.engines.tariff.consumer_category_mapping import (
    BUILDING_TYPE_TO_CONSUMER_CATEGORY,
    map_building_type_to_consumer_category,
)
from app.models.enums import BuildingType, TariffConsumerCategory


def test_mapping_covers_every_building_type():
    assert set(BUILDING_TYPE_TO_CONSUMER_CATEGORY.keys()) == set(BuildingType)


@pytest.mark.parametrize(
    ("building_type", "expected_category"),
    [
        (BuildingType.HOME, TariffConsumerCategory.RESIDENTIAL),
        (BuildingType.SCHOOL, TariffConsumerCategory.EDUCATIONAL_INSTITUTION),
        (BuildingType.COLLEGE, TariffConsumerCategory.EDUCATIONAL_INSTITUTION),
        (BuildingType.OFFICE, TariffConsumerCategory.COMMERCIAL),
        (BuildingType.SHOP, TariffConsumerCategory.COMMERCIAL),
        (BuildingType.SMALL_INSTITUTION, TariffConsumerCategory.PUBLIC_SERVICE),
        (BuildingType.OTHER, TariffConsumerCategory.OTHER),
    ],
)
def test_map_building_type_to_consumer_category(building_type, expected_category):
    assert map_building_type_to_consumer_category(building_type) == expected_category


def test_school_and_college_both_map_to_educational_institution_not_home():
    assert (
        map_building_type_to_consumer_category(BuildingType.SCHOOL)
        == map_building_type_to_consumer_category(BuildingType.COLLEGE)
        == TariffConsumerCategory.EDUCATIONAL_INSTITUTION
    )
    assert map_building_type_to_consumer_category(BuildingType.HOME) != TariffConsumerCategory.EDUCATIONAL_INSTITUTION
