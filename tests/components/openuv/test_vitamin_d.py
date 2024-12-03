"""Test Openuv Vitamin D intake sensor."""

from unittest.mock import MagicMock

import pytest

from homeassistant.components.openuv.coordinator import OpenUvCoordinator
from homeassistant.components.openuv.sensor import VitaminDSensor  # SUN_EXPOSURE


@pytest.fixture
def coordinator_instance() -> OpenUvCoordinator:
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


# initialization:
# check the name
# check that it has an id

# get sun exposure test
# set up skintype and uv_index
# check different values (for loop)
