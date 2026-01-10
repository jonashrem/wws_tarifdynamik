# WestfalenWIND Tarifdynamik - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

🇩🇪 [Deutsche Version](README_DE.md)

This custom integration allows you to integrate dynamic electricity prices from WestfalenWIND / EnergieDock into Home Assistant.

## Features

- **Current Electricity Price**: Shows the current price in ct/kWh
- **Tariff Mode**: Shows whether SMART (cheap) or STANDARD is currently active
- **Next Price**: Price for the next 15-minute period
- **Best Saving Window**: Shows the cheapest time window of the day (configurable length, default: 2 hours)
- **Smart Tariff Active**: Simple indicator whether the cheap tariff is active
- **All Prices as Attributes**: For automations and graphs
- **Configurable Prices**: SMART and STANDARD prices can be individually configured
- **Configurable Saving Window**: Length of the saving window can be adjusted (1-24 hours)

## Installation

### Manual

1. Copy the folder `custom_components/wws_tarifdynamik` to your Home Assistant `config/custom_components/` directory

2. Restart Home Assistant

3. Go to **Settings** → **Devices & Services** → **Add Integration**

4. Search for "WestfalenWIND Tarifdynamik"

5. Enter your credentials (same as in the app)

6. Enter your tariff prices:
   - **SMART Price**: The cheap price (e.g., 19.96 ct/kWh)
   - **STANDARD Price**: The normal price (e.g., 29.96 ct/kWh)
   - **Saving Window Length**: Duration in hours (default: 2)
   
   You can find the prices in your contract or in the app.

### Adjust Settings Later

You can adjust prices and saving window anytime:

1. **Settings** → **Devices & Services**
2. Click on "WestfalenWIND Tarifdynamik"
3. Click on **Configure**
4. Adjust the settings

### HACS (recommended)

*Not yet available - can be added as a Custom Repository*

## Sensors

| Sensor | Description | Example Value |
|--------|-------------|---------------|
| `strompreis_aktuell` | Current electricity price | 19.96 ct/kWh |
| `tarifmodus` | SMART or STANDARD | SMART |
| `strompreis_nachste_periode` | Price for next 15 min | 29.96 ct/kWh |
| `bestes_sparfenster` | Start time of cheapest window | 03:00 |
| `smart_tarif_aktiv` | Yes/No | Yes |
| `preise_heute` | Overview of all prices today | 96 periods, 12 SMART |
| `preise_morgen` | Overview of all prices tomorrow | 96 periods, 8 SMART |
| `nachste_smart_periode` | When next SMART time starts | 14:00 |
| `smart_zeiten_heute` | All SMART time ranges today | 03-05, 14-16 |

## Attributes

### `preise_heute` / `preise_morgen`
- `prices`: List of all 15-min periods with price and mode
- `hourly`: Hourly overview for easy visualization
- `min_price` / `max_price` / `avg_price`: Statistics

### `nachste_smart_periode`
- `start`: Start time
- `price_ct_kwh`: Price
- `time_until`: Time until start (e.g., "2h 15min")
- `minutes_until`: Minutes until start (for automations)

### `smart_zeiten_heute`
- `smart_periods`: List of all SMART periods with start/end
- `smart_hours`: Number of SMART hours today

## Example Automations

### Notification on Smart Tariff

```yaml
automation:
  - alias: "Smart Tariff Notification"
    trigger:
      - platform: state
        entity_id: sensor.westfalenwind_stromtarif_tarifmodus
        to: "SMART"
    action:
      - service: notify.mobile_app
        data:
          message: "Cheap electricity now! Price: {{ states('sensor.westfalenwind_stromtarif_strompreis_aktuell') }} ct/kWh"
```

### Notification 15 Min Before SMART

```yaml
automation:
  - alias: "SMART Period Warning"
    trigger:
      - platform: numeric_state
        entity_id: sensor.westfalenwind_stromtarif_nachste_smart_periode
        attribute: minutes_until
        below: 15
    condition:
      - condition: template
        value_template: "{{ state_attr('sensor.westfalenwind_stromtarif_nachste_smart_periode', 'minutes_until') > 0 }}"
    action:
      - service: notify.mobile_app
        data:
          message: "SMART tariff starts in {{ state_attr('sensor.westfalenwind_stromtarif_nachste_smart_periode', 'time_until') }}!"
```

### Enable EV Charger on Cheap Electricity

```yaml
automation:
  - alias: "Wallbox on Smart Tariff"
    trigger:
      - platform: state
        entity_id: sensor.westfalenwind_stromtarif_smart_tarif_aktiv
        to: "Ja"
    condition:
      - condition: state
        entity_id: binary_sensor.car_connected
        state: "on"
    action:
      - service: switch.turn_on
        entity_id: switch.wallbox
  
  - alias: "Wallbox off on Standard Tariff"
    trigger:
      - platform: state
        entity_id: sensor.westfalenwind_stromtarif_smart_tarif_aktiv
        to: "Nein"
    action:
      - service: switch.turn_off
        entity_id: switch.wallbox
```

### Start Washing Machine at Saving Window

```yaml
automation:
  - alias: "Washing Machine at Saving Window"
    trigger:
      - platform: template
        value_template: >
          {{ now().strftime('%H:%M') == states('sensor.westfalenwind_stromtarif_bestes_sparfenster') }}
    condition:
      - condition: state
        entity_id: input_boolean.washing_scheduled
        state: "on"
    action:
      - service: switch.turn_on
        entity_id: switch.washing_machine
      - service: input_boolean.turn_off
        entity_id: input_boolean.washing_scheduled
```

### Daily Summary

```yaml
automation:
  - alias: "Daily Electricity Price Summary"
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - service: notify.mobile_app
        data:
          title: "Electricity Prices Today"
          message: >
            SMART times: {{ states('sensor.westfalenwind_stromtarif_smart_zeiten_heute') }}
            Best window: {{ states('sensor.westfalenwind_stromtarif_bestes_sparfenster') }}
            (Ø {{ state_attr('sensor.westfalenwind_stromtarif_bestes_sparfenster', 'avg_price_ct_kwh') }} ct/kWh)
```

## ApexCharts Card

With the [ApexCharts Card](https://github.com/RomRider/apexcharts-card) you can create a nice price graph:

```yaml
type: custom:apexcharts-card
header:
  show: true
  title: Electricity Prices Today
graph_span: 24h
span:
  start: day
yaxis:
  - min: 0
    max: ~40
series:
  - entity: sensor.westfalenwind_stromtarif_preise_heute
    data_generator: |
      const prices = entity.attributes.prices || [];
      return prices.map(p => {
        return [new Date(p.valid_from).getTime(), p.price_ct_kwh];
      });
    type: column
    color: >
      function(value) {
        return value < 25 ? '#4CAF50' : '#FF9800';
      }
```

### Combined Graph (Today + Tomorrow)

```yaml
type: custom:apexcharts-card
header:
  show: true
  title: Electricity Prices 48h
graph_span: 48h
span:
  start: day
series:
  - entity: sensor.westfalenwind_stromtarif_preise_heute
    name: Today
    data_generator: |
      return (entity.attributes.prices || []).map(p => 
        [new Date(p.valid_from).getTime(), p.price_ct_kwh]
      );
    type: area
    color: '#2196F3'
  - entity: sensor.westfalenwind_stromtarif_preise_morgen
    name: Tomorrow
    data_generator: |
      return (entity.attributes.prices || []).map(p => 
        [new Date(p.valid_from).getTime(), p.price_ct_kwh]
      );
    type: area
    color: '#9C27B0'
```

## Troubleshooting

### Token Expires
The integration automatically renews the token. If problems occur, remove the integration and add it again.

### No Data
Make sure your contract is active and you can log in to the app.

## API Documentation

The integration uses the unofficial EnergieDock API. Detailed API documentation can be found at [docs/API.md](docs/API.md).

**Quick overview:**

- Base URL: `https://api.wws.tarifdynamik.de`
- Auth: OAuth2 Password Grant
- Endpoints:
  - `/tokens/` - Login
  - `/tariffs/prognosis` - Price prognosis
  - `/tariffs/periods/saving_window` - Best saving window

## 🤖 AI-Generated Project

This project was created with the help of **GitHub Copilot (Claude)**. The code, documentation, and automation examples were AI-generated and reviewed by the developer.

## Disclaimer

This is an unofficial integration and is not affiliated with WestfalenWIND or EnergieDock. Use at your own risk.
