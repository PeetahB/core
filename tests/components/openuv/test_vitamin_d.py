"""Test Openuv Vitamin D intake sensor."""

from unittest.mock import MagicMock

import pytest

from homeassistant.components.openuv.coordinator import OpenUvCoordinator
from homeassistant.components.openuv.sensor import (
    SKIN_TYPE_TRANSLATION,
    UV_INDEX_LABEL_TRANSLATION,
    VitaminDSensor,
)

SUN_EXPOSURE_TEST: list[list[tuple[int, int] | None]] = [
    [(15, 20), (20, 30), (30, 40), (40, 60), (60, 80), None],
    [(10, 15), (15, 20), (20, 30), (30, 40), (40, 60), (60, 80)],
    [(5, 10), (10, 15), (15, 20), (20, 30), (30, 40), (40, 60)],
    [(2, 8), (5, 10), (10, 15), (15, 20), (20, 30), (30, 40)],
    [(1, 5), (2, 8), (5, 10), (10, 15), (15, 20), (20, 30)],
]


@pytest.fixture
def coordinator_instance() -> MagicMock:
    """Fixture to create a HomeAssistant instance."""
    coordinator = MagicMock(spec=OpenUvCoordinator)
    coordinator.latitude = 25
    coordinator.longitude = 25
    return coordinator


@pytest.fixture
def vitamin_d_instance(coordinator_instance) -> VitaminDSensor:
    """Fixture to create a mock VitaminDSensor instance."""
    return VitaminDSensor(coordinator_instance)


def test_initialize_vitamin_d_sensor(vitamin_d_instance) -> None:
    """Test that checks the basic attributes of the vitamin D sensor after initialization."""
    assert hasattr(vitamin_d_instance, "_attr_name")
    assert hasattr(vitamin_d_instance, "_attr_unique_id")
    assert hasattr(vitamin_d_instance, "coordinator")
    assert hasattr(vitamin_d_instance, "_attr_device_info")


def test_sun_exposure_skin_type_none(vitamin_d_instance) -> None:
    """Test for unexisting skin type."""
    # Mock necessary objects
    entry = MagicMock()
    entry.data = {
        "skin_type": "None",  # Skin type is None, so all safe exposure sensors should be added
        "latitude": 37.7749,
        "longitude": -122.4194,
    }
    entry.options = {"skin_type": "None"}  # Skin type explicitly set to None
    entry.entry_id = "test_entry"
    skin_type = (
        entry.options["skin_type"]
        if entry.options["skin_type"] is not None
        else entry.data["skin_type"]
    )
    uv_index = 0
    assert (
        vitamin_d_instance.get_sun_exposure(skin_type, uv_index) == "Set your skin type"
    )


def test_sun_exposure_interval_is_none(vitamin_d_instance) -> None:
    """Test for undefined sun exposure."""
    # Mock necessary objects
    entry = MagicMock()
    entry.data = {
        "skin_type": "None",  # Skin type is None, so all safe exposure sensors should be added
        "latitude": 37.7749,
        "longitude": -122.4194,
    }
    entry.options = {"skin_type": "Skin Type VI"}  # Skin type explicitly set to None
    entry.entry_id = "test_entry"
    skin_type = (
        entry.options["skin_type"]
        if entry.options["skin_type"] is not None
        else entry.data["skin_type"]
    )
    uv_index = 0
    assert vitamin_d_instance.get_sun_exposure(skin_type, uv_index) == "-"


def test_sun_exposure_time(vitamin_d_instance) -> None:
    """Checks correctness of sun exposure times."""
    for uv_label in UV_INDEX_LABEL_TRANSLATION:
        for skin_type in SKIN_TYPE_TRANSLATION:
            uv_label_translated = UV_INDEX_LABEL_TRANSLATION.get(uv_label)
            skin_type_translated = SKIN_TYPE_TRANSLATION.get(skin_type)
            if uv_label_translated == 0 and skin_type_translated == 5:  # None case
                continue
            sun_exposure_interval = SUN_EXPOSURE_TEST[uv_label_translated][
                skin_type_translated
            ]
            assert (
                vitamin_d_instance.get_sun_exposure(skin_type, uv_label)
                == f"{sun_exposure_interval[0]} - {sun_exposure_interval[1]} min"
            )
