# WestfalenWIND Tarifdynamik - Home Assistant Integration

Diese Custom Integration ermöglicht es, die dynamischen Strompreise von WestfalenWIND / EnergieDock in Home Assistant zu integrieren.

## Features

- **Aktueller Strompreis**: Zeigt den aktuellen Preis in ct/kWh
- **Tarifmodus**: Zeigt ob gerade SMART (günstig) oder STANDARD aktiv ist
- **Nächster Preis**: Preis der nächsten 15-Minuten-Periode
- **Bestes Sparfenster**: Zeigt das günstigste 2-Stunden-Fenster des Tages
- **Smart-Tarif Aktiv**: Einfacher Indikator ob gerade der günstige Tarif läuft
- **Alle Preise als Attribute**: Für Automationen und Graphen
- **Konfigurierbare Preise**: SMART- und STANDARD-Preise können individuell eingestellt werden

## Installation

### Manuell

1. Kopiere den Ordner `custom_components/wws_tarifdynamik` in dein Home Assistant `config/custom_components/` Verzeichnis

2. Starte Home Assistant neu

3. Gehe zu **Einstellungen** → **Geräte & Dienste** → **Integration hinzufügen**

4. Suche nach "WestfalenWIND Tarifdynamik"

5. Gib deine Zugangsdaten ein (die gleichen wie in der App)

6. Gib deine Tarifpreise ein:
   - **SMART-Preis**: Der günstige Preis (z.B. 19,96 ct/kWh)
   - **STANDARD-Preis**: Der normale Preis (z.B. 29,96 ct/kWh)
   
   Die Preise findest du in deinem Vertrag oder in der App.

### Preise nachträglich ändern

Du kannst die Preise jederzeit anpassen:

1. **Einstellungen** → **Geräte & Dienste**
2. Klicke auf "WestfalenWIND Tarifdynamik"
3. Klicke auf **Konfigurieren**
4. Passe die Preise an

### HACS (empfohlen)

*Noch nicht verfügbar - kann als Custom Repository hinzugefügt werden*

## Sensoren

| Sensor | Beschreibung | Beispielwert |
|--------|--------------|--------------|
| `strompreis_aktuell` | Aktueller Strompreis | 19,96 ct/kWh |
| `tarifmodus` | SMART oder STANDARD | SMART |
| `strompreis_nachste_periode` | Preis der nächsten 15 Min | 29,96 ct/kWh |
| `bestes_sparfenster` | Startzeit des günstigsten 2h-Fensters | 03:00 |
| `smart_tarif_aktiv` | Ja/Nein | Ja |
| `preise_heute` | Übersicht aller Preise heute | 96 Perioden, 12 SMART |
| `preise_morgen` | Übersicht aller Preise morgen | 96 Perioden, 8 SMART |
| `nachste_smart_periode` | Wann startet nächste SMART-Zeit | 14:00 |
| `smart_zeiten_heute` | Alle SMART-Zeiträume heute | 03-05, 14-16 Uhr |

## Attribute

### `preise_heute` / `preise_morgen`
- `prices`: Liste aller 15-Min-Perioden mit Preis und Modus
- `hourly`: Stündliche Übersicht für einfache Visualisierung
- `min_price` / `max_price` / `avg_price`: Statistiken

### `nachste_smart_periode`
- `start`: Startzeitpunkt
- `price_ct_kwh`: Preis
- `time_until`: Zeit bis zum Start (z.B. "2h 15min")
- `minutes_until`: Minuten bis zum Start (für Automationen)

### `smart_zeiten_heute`
- `smart_periods`: Liste aller SMART-Perioden mit Start/Ende
- `smart_hours`: Anzahl SMART-Stunden heute

## Beispiel-Automationen

### Benachrichtigung bei Smart-Tarif

```yaml
automation:
  - alias: "Benachrichtigung Smart-Tarif"
    trigger:
      - platform: state
        entity_id: sensor.westfalenwind_stromtarif_tarifmodus
        to: "SMART"
    action:
      - service: notify.mobile_app
        data:
          message: "Jetzt günstig Strom verbrauchen! Preis: {{ states('sensor.westfalenwind_stromtarif_strompreis_aktuell') }} ct/kWh"
```

### Benachrichtigung 15 Min vor SMART

```yaml
automation:
  - alias: "Warnung vor SMART-Periode"
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
          message: "SMART-Tarif startet in {{ state_attr('sensor.westfalenwind_stromtarif_nachste_smart_periode', 'time_until') }}!"
```

### Wallbox bei günstigem Strom einschalten

```yaml
automation:
  - alias: "Wallbox bei Smart-Tarif"
    trigger:
      - platform: state
        entity_id: sensor.westfalenwind_stromtarif_smart_tarif_aktiv
        to: "Ja"
    condition:
      - condition: state
        entity_id: binary_sensor.auto_angeschlossen
        state: "on"
    action:
      - service: switch.turn_on
        entity_id: switch.wallbox
  
  - alias: "Wallbox bei Standard-Tarif ausschalten"
    trigger:
      - platform: state
        entity_id: sensor.westfalenwind_stromtarif_smart_tarif_aktiv
        to: "Nein"
    action:
      - service: switch.turn_off
        entity_id: switch.wallbox
```

### Waschmaschine zum Sparfenster starten

```yaml
automation:
  - alias: "Waschmaschine zum Sparfenster"
    trigger:
      - platform: template
        value_template: >
          {{ now().strftime('%H:%M') == states('sensor.westfalenwind_stromtarif_bestes_sparfenster') }}
    condition:
      - condition: state
        entity_id: input_boolean.waschmaschine_geplant
        state: "on"
    action:
      - service: switch.turn_on
        entity_id: switch.waschmaschine
      - service: input_boolean.turn_off
        entity_id: input_boolean.waschmaschine_geplant
```

### Tägliche Zusammenfassung

```yaml
automation:
  - alias: "Tägliche Strompreis-Zusammenfassung"
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - service: notify.mobile_app
        data:
          title: "Strompreise heute"
          message: >
            SMART-Zeiten: {{ states('sensor.westfalenwind_stromtarif_smart_zeiten_heute') }}
            Bestes Fenster: {{ states('sensor.westfalenwind_stromtarif_bestes_sparfenster') }} Uhr
            (Ø {{ state_attr('sensor.westfalenwind_stromtarif_bestes_sparfenster', 'avg_price_ct_kwh') }} ct/kWh)
```

## ApexCharts Karte

Mit der [ApexCharts Card](https://github.com/RomRider/apexcharts-card) kannst du einen schönen Preisgraphen erstellen:

```yaml
type: custom:apexcharts-card
header:
  show: true
  title: Strompreise Heute
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

### Kombinierter Graph (Heute + Morgen)

```yaml
type: custom:apexcharts-card
header:
  show: true
  title: Strompreise 48h
graph_span: 48h
span:
  start: day
series:
  - entity: sensor.westfalenwind_stromtarif_preise_heute
    name: Heute
    data_generator: |
      return (entity.attributes.prices || []).map(p => 
        [new Date(p.valid_from).getTime(), p.price_ct_kwh]
      );
    type: area
    color: '#2196F3'
  - entity: sensor.westfalenwind_stromtarif_preise_morgen
    name: Morgen
    data_generator: |
      return (entity.attributes.prices || []).map(p => 
        [new Date(p.valid_from).getTime(), p.price_ct_kwh]
      );
    type: area
    color: '#9C27B0'
```

## Troubleshooting

### Token läuft ab
Die Integration erneuert den Token automatisch. Falls Probleme auftreten, entferne die Integration und füge sie neu hinzu.

### Keine Daten
Stelle sicher, dass dein Vertrag aktiv ist und du dich in der App einloggen kannst.

## API Dokumentation

Die Integration nutzt die inoffizielle API von EnergieDock. Eine detaillierte Dokumentation der API findest du unter [docs/API.md](docs/API.md).

**Kurzübersicht:**

- Basis-URL: `https://api.wws.tarifdynamik.de`
- Auth: OAuth2 Password Grant
- Endpoints:
  - `/tokens/` - Login
  - `/tariffs/prognosis` - Preisprognose
  - `/tariffs/periods/saving_window` - Bestes Sparfenster

## 🤖 KI-generiertes Projekt

Dieses Projekt wurde mit Hilfe von **GitHub Copilot (Claude)** erstellt. Der Code, die Dokumentation und die Automationsbeispiele wurden durch KI generiert.
## Disclaimer

Dies ist eine inoffizielle Integration und steht in keiner Verbindung zu WestfalenWIND oder EnergieDock. Die Nutzung erfolgt auf eigene Verantwortung.
