# Skin Type Customization in Home Assistant

This repository introduces a **Skin Type Customization Feature** for the Home Assistant OpenUV integration. With this feature, users can personalize their experience by integrating their skin type during the setup process, ensuring accurate safe exposure recommendations tailored to their skin sensitivity levels.

## Key Features

### 1. Skin Type Integration:
- Users can select their skin type (e.g., Skin Type I–VI) during the initial setup of the OpenUV integration.
- The selected skin type is displayed via a dedicated **skin type sensor**.

### 2. Real-Time Safe Exposure Visibility:
- The feature provides personalized guidance by dynamically calculating safe exposure times based on UV index and the selected skin type.
- Tailored safe exposure recommendations enhance user safety and awareness.

### 3. Editable Skin Type Configuration:
- Users can refine or change their skin type settings through the integration’s **Options Flow**.
- Setting the skin type to `None` disables personalized recommendations.

---

## Steps to Select Skin Type:

### 1. Open the Home Assistant Dashboard
- Log in to your Home Assistant instance.

### 2. Install the Open UV Integration
1. Navigate to **Settings > Devices & Services > Integrations** in Home Assistant.
2. Search for **OpenUV** and follow the installation prompts:
   - Enter your OpenUV API Key.
   - Configure your location details (latitude, longitude).
   - Select your Skin Type or leave it as `None`.

### 3. Modify the Skin Type Setting
- In the options dialog, locate the **Skin Type** dropdown menu.
- Select **Skin Type** from the list (Skin Type I–VI or None).

### 4. Save the Changes
- Click **Submit** or **Save** to apply your changes.

### 5. Verify the Skin Type Selection
- After saving, check that the sensor `sensor.openuv_skin_type` reflects the selected **Skin Type**.
- This ensures the safe exposure recommendations are now personalized for the selected Skin Type.

---

## Code Overview

### Configuration Flow (`homeassistant/components/openuv/config_flow.py`)

#### Skin Type Handling:
- The following code snippet manages the user's selection for **Skin Type**:
  ```python
  # Stores the skin type provided by the user during configuration.
  "skin_type": data.skintype,
  
  # Retrieves the skin type selection from user input, defaulting to "None" if not provided.
  skin_type = user_input.get("skin_type", "None")

# Sensor Configuration (`homeassistant/components/openuv/sensor.py`)



# 1. Import Statements
```
import logging
from homeassistant.helpers import entity_registry as er
```

# Initializes a logger for debugging purposes.
```
_LOGGER = logging.getLogger(__name__)
```

# 2. Mapping Roman Numerals to Skin Types
```
roman_to_int = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6}
```

# 3. Setting Up OpenUV Sensors
```
skin_type = entry.options.get("skin_type", None) or entry_data.get("skin_type", "None")

if skin_type == "None":
    add_all_safe_exposure_sensors(existing_entities, async_add_entities, coordinators)
else:
    add_specific_safe_exposure_sensor(skin_type, existing_entities, async_add_entities, coordinators)
```

# 4a. Add All Safe Exposure Sensors
```
def add_all_safe_exposure_sensors(
    existing_entities: set,
    async_add_entities: AddEntitiesCallback,
    coordinators: dict
) -> None:
    """Add all safe exposure time sensors (for skin types I–VI) if they don't already exist."""
    for i in range(1, 7):
        if f"sensor.type_safe_exposure_time_{i}" not in existing_entities:
            sensor_description = get_sensor_description_for_skin_type(i)
            sensor = OpenUvSensor(coordinators[DATA_UV], sensor_description)
            async_add_entities([sensor], update_before_add=True)
```

# 4b. Add Specific Safe Exposure Sensor
```
def add_specific_safe_exposure_sensor(
    skin_type: str,
    existing_entities: set,
    async_add_entities: AddEntitiesCallback,
    coordinators: dict,
) -> None:
    """Add a specific safe exposure time sensor based on the selected skin type."""
    roman_part = skin_type.split(" ")[-1]
    selected_type = roman_to_int.get(roman_part)
    if selected_type:
        if f"sensor.type_safe_exposure_time_{selected_type}" not in existing_entities:
            sensor_description = get_sensor_description_for_skin_type(selected_type)
            sensor = OpenUvSensor(coordinators[DATA_UV], sensor_description)
            async_add_entities([sensor], update_before_add=True)
```

# 5. Sensor Description Retrieval
```
def get_sensor_description_for_skin_type(skin_type_number: int) -> OpenUvSensorEntityDescription:
    """Retrieve the predefined sensor description for a given skin type."""
    for description in SENSOR_DESCRIPTIONS:
        if description.translation_key == f"skin_type_{skin_type_number}_safe_exposure_time":
            return description
    raise ValueError(f"Sensor description for skin type {skin_type_number} not found")
```

# 6. Handling Options Updates
```
async def options_update_listener(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Handle options update for skin type changes."""
    skin_type = entry.options.get("skin_type", "None")
    coordinators = hass.data[DOMAIN][entry.entry_id]
    entity_registry = er.async_get(hass)

    if skin_type == "None":
        for i in range(1, 7):
            entity_id = f"sensor.openuv_skin_type_{i}_safe_exposure_time"
            if not entity_registry.async_is_registered(entity_id):
                sensordescription = get_safe_exposure_sensor(coordinators, i)
                async_add_entities([sensordescription])
    else:
        roman_part = skin_type.split(" ")[-1]
        selected_type = roman_to_int.get(roman_part)
        if selected_type:
            entity_id = f"sensor.openuv_skin_type_{selected_type}_safe_exposure_time"
            if not entity_registry.async_is_registered(entity_id):
                sensordescription = get_safe_exposure_sensor(coordinators, selected_type)
                async_add_entities([sensordescription])

            # Remove all other safe exposure sensors
            for i in range(1, 7):
                if i != selected_type:
                    other_entity_id = f"sensor.openuv_skin_type_{i}_safe_exposure_time"
                    if entity_registry.async_is_registered(other_entity_id):
                        entity_registry.async_remove(other_entity_id)
        else:
            _LOGGER.warning("Invalid skin type")
```

# Conclusion

The sensor configuration code for the Home Assistant OpenUV integration provides a robust framework for handling user-defined skin types and generating personalized UV exposure recommendations. 

### Key Highlights:
1. **Dynamic Sensor Integration**:
   - Supports the creation of sensors for all skin types (I–VI) or a specific skin type based on user configuration.

2. **Efficient Options Management**:
   - Allows users to modify their skin type settings dynamically, with corresponding updates to the sensors.

3. **Tailored Safety Recommendations**:
   - Delivers accurate UV exposure recommendations by leveraging skin type–specific sensors.

By following the implementation outlined above, developers can ensure seamless integration of the skin type customization feature, enhancing user safety and experience in the Home Assistant ecosystem.




