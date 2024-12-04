# Steps to Display the Color-Coded UV Index Graph in the Lovelace Home Assistant Dashboard

## 1. Creating the UV Index Entity

In the `openuv` component of `sensor.py`, we created a new entity called `current_uv_index_with_graph`.  
This entity resides in the core of Home Assistant, and after its creation, it became available for use in the Lovelace dashboard.

---

## 2. Installing and Configuring HACS (Home Assistant Community Store)

### Step 1: Download and Install HACS
1. **Download the .zip file** containing the latest HACS release from [HACS GitHub Releases](https://github.com/hacs/integration/releases).
2. **Extract the downloaded file**.
3. Navigate to the `config` directory in your Home Assistant instance and check for the `custom_components` folder:
   - If it does not exist, create a folder named `custom_components` under `core/config/`.
4. **Copy the extracted HACS folder** into the `custom_components` folder:
   - Path: `core/config/custom_components/hacs`.
5. **Restart Home Assistant** to activate the HACS integration.

---

### Step 2: Adding HACS to Integrations
1. Open Home Assistant and go to **Settings > Devices & Services > Integrations**.
2. Click the **+ Add Integration** button in the bottom-right corner.
3. Search for **HACS** and click to add it.
4. During the setup process, HACS will prompt you to authenticate with GitHub:
   - Follow the instructions to complete the authentication.

Once HACS is installed, it can be used to install additional integrations or frontend elements, such as the **Mini-Graph-Card**  or **ApexCharts-Card** , which are essential for creating custom graphs.   

---

## 3. Installing and Configuring Graph Cards Using HACS

1. Navigate to **HACS** in the Home Assistant sidebar.
2. Use the search or browse feature to locate and install either:
   - **Mini-Graph-Card**, or  
   - **ApexCharts-Card** (recommended for advanced customization).   

These card integrations allows users in creating detailed and color-coded graph displays in the Lovelace dashboard.

---

## 4. Steps to Edit and Configure the UV Index Graph Code

### Step 1: Accessing the Dashboard Configuration
1. In the top-right corner of the screen, select the **Edit** button.
2. If this is your first time editing a dashboard, the **Edit dashboard** dialog will appear.
3. In the dialog, select the **three dots (⋮)** menu, then select **Take control** to enable editing.

---

### Step 2: Adding a Card for the Graph
1. Click the **+ Add Card** button at the bottom-right corner of the view.
2. In the card selection window, choose **Manual Card** or (at the bottom of the list).
3. A text editor will appear where you can input YAML code to configure the graph.

---

### Step 3: Writing the Graph Code for ApexCharts-Card

#### Using the ApexCharts-Card
Enter the following YAML code into the editor to create a detailed color-coded UV Index graph:

```yaml
type: custom:apexcharts-card
apex_config:
  chart:
    height: 100%
  dataLabels:
    background:
      enabled: false
    style:
      colors:
        - var(--primary-text-color)
graph_span: 24h
header:
  show: true
  show_states: true
  title: UV Index
experimental:
  color_threshold: true
yaxis:
  - id: left
    decimals: 1
    apex_config:
      forceNiceScale: true
series:
  - entity: sensor.openuv_current_uv_index_with_graph
    stroke_width: 2
    type: line
    color: rgb(192,192,192)
    yaxis_id: left
    float_precision: 0
    statistics:
      type: max
      period: 5minute
      align: middle
    show:
      datalabels: false
      extremas: false
      name_in_header: false
    color_threshold:
      - color: "#b200ff"
        value: 10.5
      - color: "#e45e65"
        value: 7.5
      - color: "#ff8000"
        value: 5.5
      - color: "#e0b400"
        value: 2.5
      - color: "#0da035"
        value: 0
    header_actions:
      tap_action:
        action: more-info
```

#### Using the Mini-Graph-Card

```yaml
type: custom:mini-graph-card
entities:
  - entity: sensor.openuv_current_uv_index_with_graph
    name: UV Index
name: UV Index
icon: mdi:weather-sunny
show:
  graph: bar
  extrema: true
  labels: true
  points: true
color_thresholds:
  - value: 0
    color: green
  - value: 2.1
    color: yellow
  - value: 5.1
    color: orange
  - value: 7.1
    color: red
  - value: 10.1
    color: purple
hours_to_show: 24
points_per_hour: 2
```

---

### Step 4: Save and Apply the Changes
After pasting the YAML code, click Save to add the graph to your dashboard.
The dashboard will now display the UV index graph with the color-coded thresholds applied.

---

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




