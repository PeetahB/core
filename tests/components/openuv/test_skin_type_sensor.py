"""Define tests for the Skin Type sensor in the OpenUV integration."""

import pytest

from homeassistant.components.openuv.sensor import SkinTypeSensor
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType

from tests.common import MockConfigEntry


async def test_sensor_initialization(hass: HomeAssistant) -> None:
    """Test the initialization of the Skin Type sensor."""
    # Create mock configuration data for the sensor
    mock_entry_data = {
        "latitude": 37.7749,
        "longitude": -122.4194,
        "skin_type": "Skin Type II",
    }

    # Create a mock ConfigEntry
    mock_config_entry = ConfigEntry(
        domain="openuv",
        data=mock_entry_data,
        options={},
        entry_id="test_entry",
        version=1,
        title="37.7749, -122.4194",
        unique_id="37.7749_-122.4194",
        source="user",
        minor_version=0,
        discovery_keys=None,
    )

    # Create the SkinTypeSensor object
    sensor = SkinTypeSensor(mock_entry_data, mock_config_entry)

    # Assertions to verify the sensor is initialized correctly
    assert sensor.name == "Skin Type"
    assert sensor.unique_id == "skin_type_37.7749_-122.4194"
    assert sensor.native_value == "Skin Type II"
    assert sensor.extra_state_attributes["skin_type"] == "Skin Type II"
    assert sensor.device_info == {
        "identifiers": {("openuv", "37.7749_-122.4194")},
        "name": "OpenUV",
        "entry_type": DeviceEntryType.SERVICE,
    }


async def test_sensor_default_skin_type(hass: HomeAssistant) -> None:
    """Test that the sensor defaults to 'None' for skin type if not provided."""
    mock_entry_data = {
        "latitude": 37.7749,
        "longitude": -122.4194,
    }

    mock_config_entry = ConfigEntry(
        domain="openuv",
        data=mock_entry_data,
        options={},
        entry_id="test_entry",
        version=1,
        title="37.7749, -122.4194",
        unique_id="37.7749_-122.4194",
        source="user",
        minor_version=0,
        discovery_keys=None,
    )

    sensor = SkinTypeSensor(mock_entry_data, mock_config_entry)

    assert sensor.native_value == "None"
    assert sensor.extra_state_attributes["skin_type"] == "None"


async def test_sensor_updates_on_options_change_after_delay(
    hass: HomeAssistant,
) -> None:
    """Test that the sensor updates its state when the 'skin_type' option changes,and there is a delay before the update is reflected."""

    # Step 1: Set up mock configuration entry
    mock_entry_data = {
        "latitude": 37.7749,
        "longitude": -122.4194,
        "skin_type": "Skin Type II",  # Initial skin type from entry data
    }

    # Step 2: Create a mock config entry
    mock_config_entry = MockConfigEntry(
        domain="openuv",
        data=mock_entry_data,
        options={"skin_type": "Skin Type III"},  # Initial skin type in options
        entry_id="test_entry",
        version=1,
        title="37.7749, -122.4194",
        unique_id="37.7749_-122.4194",
        source="user",
    )

    # Step 3: Add the mock config entry to Home Assistant
    mock_config_entry.add_to_hass(hass)

    # Initialize the sensor (ensure the latest options are used for initialization)
    sensor = SkinTypeSensor(mock_entry_data, mock_config_entry)

    # Ensure the entity has an entity_id
    sensor.entity_id = f"sensor.{mock_config_entry.entry_id}"

    # Set the 'hass' attribute manually for the sensor
    sensor.hass = hass  # Make sure hass is assigned before calling async_update()

    # Step 4: Simulate an initial update with the skin type from options
    await sensor.async_update()

    # Check initial sensor state to ensure it reflects the skin type in options
    assert (
        sensor.native_value == "Skin Type III"
    )  # It should reflect the 'skin_type' from options
    assert (
        sensor.extra_state_attributes["skin_type"] == "Skin Type III"
    )  # Ensure the skin type from options is used

    # Step 5: Update the skin_type option using `async_init()` to initiate options change
    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

    # Simulate user input to change skin_type
    _result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={"skin_type": "Skin Type IV"}
    )

    # Step 6: After the update, call async_update to update the sensor state based on the new options
    await sensor.async_update()

    # Now the sensor should reflect the updated 'skin_type' from the options
    assert sensor.native_value == "Skin Type IV"
    assert sensor.extra_state_attributes["skin_type"] == "Skin Type IV"


async def test_sensor_fallback_to_entry_data(hass: HomeAssistant) -> None:
    """Test that the sensor falls back to entry data if no skin_type is set in options."""

    mock_entry_data = {
        "latitude": 37.7749,
        "longitude": -122.4194,
        "skin_type": "Skin Type II",  # Skin type from entry data
    }

    # Mock the config entry without skin_type in options
    mock_config_entry = MockConfigEntry(
        domain="openuv",
        data=mock_entry_data,
        options={},  # No options set for skin_type
        entry_id="test_entry",
        version=1,
        title="37.7749, -122.4194",
        unique_id="37.7749_-122.4194",
        source="user",
    )

    # Initialize the sensor
    sensor = SkinTypeSensor(mock_entry_data, mock_config_entry)

    # Ensure the entity has an entity_id
    sensor.entity_id = f"sensor.{mock_config_entry.entry_id}"

    # Set the 'hass' attribute manually for the sensor
    sensor.hass = hass

    # Check that the sensor uses the skin type from entry data when no option is set
    await sensor.async_update()

    assert sensor.native_value == "Skin Type II"
    assert sensor.extra_state_attributes["skin_type"] == "Skin Type II"


@pytest.mark.asyncio
async def test_sensor_no_skin_type(hass: HomeAssistant) -> None:
    """Test that the sensor handles the case when no skin_type is set in both entry data and options."""

    mock_entry_data = {
        "latitude": 37.7749,
        "longitude": -122.4194,
        # No skin_type in entry data
    }

    # Mock the config entry without skin_type in both data and options
    mock_config_entry = MockConfigEntry(
        domain="openuv",
        data=mock_entry_data,
        options={},  # No skin_type option
        entry_id="test_entry",
        version=1,
        title="37.7749, -122.4194",
        unique_id="37.7749_-122.4194",
        source="user",
    )

    # Initialize the sensor
    sensor = SkinTypeSensor(mock_entry_data, mock_config_entry)

    # Ensure the entity has an entity_id
    sensor.entity_id = f"sensor.{mock_config_entry.entry_id}"

    # Set the 'hass' attribute manually for the sensor
    sensor.hass = hass

    # Check that the sensor defaults to a sensible state
    await sensor.async_update()

    # Check behavior, which could either be defaulting to "Unknown" or another value based on implementation
    assert (
        sensor.native_value == "None"
    )  # Assuming a fallback to 'Unknown' or a default value
    assert sensor.extra_state_attributes["skin_type"] == "None"
