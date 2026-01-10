# WestfalenWIND Tarifdynamik API Documentation

Diese Dokumentation beschreibt die REST-API von WestfalenWIND/EnergieDock für dynamische Stromtarife.

## Base URL

```
https://api.wws.tarifdynamik.de
```

---

## Authentifizierung

Die API verwendet OAuth2 mit Password Grant für die Authentifizierung.

### Token abrufen

**Endpoint:** `POST /tokens/`

**Content-Type:** `application/x-www-form-urlencoded`

**Request Body:**

| Parameter    | Typ    | Beschreibung                          |
|--------------|--------|---------------------------------------|
| `grant_type` | string | Muss `password` sein                  |
| `username`   | string | E-Mail-Adresse des Benutzerkontos     |
| `password`   | string | Passwort des Benutzerkontos           |

**Beispiel Request:**

```bash
curl -X POST "https://api.wws.tarifdynamik.de/tokens/" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password&username=user@example.com&password=geheim"
```

**Erfolgreiche Antwort (200 OK):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

| Feld           | Typ    | Beschreibung                                    |
|----------------|--------|-------------------------------------------------|
| `access_token` | string | JWT Token für authentifizierte Anfragen         |
| `token_type`   | string | Token-Typ (immer `bearer`)                      |
| `expires_in`   | int    | Gültigkeit des Tokens in Sekunden (~24 Stunden) |

**Fehler-Antworten:**

| Status | Beschreibung                    |
|--------|---------------------------------|
| 401    | Ungültige Zugangsdaten          |

---

## Tarif-Endpunkte

Alle folgenden Endpunkte erfordern einen gültigen Bearer Token im Authorization Header:

```
Authorization: Bearer <access_token>
```

---

### Preis-Prognose abrufen

Liefert die Tarifprognose für einen bestimmten Zeitraum in 15-Minuten-Intervallen.

**Endpoint:** `GET /tariffs/prognosis`

**Query Parameter:**

| Parameter   | Typ    | Erforderlich | Beschreibung                                                     |
|-------------|--------|--------------|------------------------------------------------------------------|
| `timezone`  | string | Ja           | Zeitzone (z.B. `Europe/Berlin`)                                  |
| `page_size` | int    | Nein         | Anzahl der zurückgegebenen Einträge (Standard: ?)                |
| `filters`   | string | Nein         | Filter im Format `field:operator:value` (z.B. `valid_from:gte:2024-01-01`) |

**Filter-Operatoren:**

| Operator | Beschreibung              |
|----------|---------------------------|
| `gte`    | Größer oder gleich        |
| `lte`    | Kleiner oder gleich       |
| `eq`     | Gleich                    |

**Beispiel Request:**

```bash
curl -X GET "https://api.wws.tarifdynamik.de/tariffs/prognosis?timezone=Europe/Berlin&page_size=192&filters=valid_from:gte:2024-01-15" \
  -H "Authorization: Bearer <access_token>"
```

**Erfolgreiche Antwort (200 OK):**

```json
{
  "data": [
    {
      "start": "2024-01-15T00:00:00+01:00",
      "end": "2024-01-15T00:15:00+01:00",
      "tariff_name": "SMART",
      "price_ct_kwh": 19.96
    },
    {
      "start": "2024-01-15T00:15:00+01:00",
      "end": "2024-01-15T00:30:00+01:00",
      "tariff_name": "STANDARD",
      "price_ct_kwh": 29.96
    }
  ]
}
```

**Datenstruktur je Eintrag:**

| Feld           | Typ    | Beschreibung                                      |
|----------------|--------|---------------------------------------------------|
| `start`        | string | Beginn des Intervalls (ISO 8601 mit Zeitzone)     |
| `end`          | string | Ende des Intervalls (ISO 8601 mit Zeitzone)       |
| `tariff_name`  | string | Tarifname: `SMART` oder `STANDARD`                |
| `price_ct_kwh` | float  | Preis in Cent pro kWh (API-interner Referenzwert) |

**Hinweis:** Die `price_ct_kwh` aus der API ist ein interner Referenzwert. Der tatsächliche Preis richtet sich nach dem individuellen Vertrag des Kunden.

---

### Sparfenster abrufen

Ermittelt das beste zusammenhängende Zeitfenster mit den niedrigsten Durchschnittspreisen (SMART-Tarif).

**Endpoint:** `GET /tariffs/periods/saving_window`

**Query Parameter:**

| Parameter  | Typ    | Erforderlich | Beschreibung                                           |
|------------|--------|--------------|--------------------------------------------------------|
| `timezone` | string | Ja           | Zeitzone (z.B. `Europe/Berlin`)                        |
| `hours`    | int    | Ja           | Gewünschte Länge des Sparfensters in Stunden (1-24)    |
| `start`    | string | Ja           | Beginn des Suchzeitraums (ISO 8601, z.B. `2024-01-15T00:00:00`) |
| `end`      | string | Ja           | Ende des Suchzeitraums (ISO 8601, z.B. `2024-01-16T23:59:59`)   |

**Beispiel Request:**

```bash
curl -X GET "https://api.wws.tarifdynamik.de/tariffs/periods/saving_window?timezone=Europe/Berlin&hours=2&start=2024-01-15T00:00:00&end=2024-01-16T23:59:59" \
  -H "Authorization: Bearer <access_token>"
```

**Erfolgreiche Antwort (200 OK):**

```json
{
  "start": "2024-01-15T14:00:00+01:00",
  "end": "2024-01-15T16:00:00+01:00",
  "avg_price_ct_kwh": 19.96,
  "hours": 2
}
```

**Datenstruktur:**

| Feld              | Typ    | Beschreibung                                               |
|-------------------|--------|------------------------------------------------------------|
| `start`           | string | Beginn des optimalen Sparfensters (ISO 8601 mit Zeitzone)  |
| `end`             | string | Ende des optimalen Sparfensters (ISO 8601 mit Zeitzone)    |
| `avg_price_ct_kwh`| float  | Durchschnittspreis im Fenster in ct/kWh                    |
| `hours`           | int    | Länge des Fensters in Stunden                              |

---

## Tarifmodell

WestfalenWIND verwendet ein zweistufiges Tarifmodell:

| Tarif      | Beschreibung                                                                 |
|------------|------------------------------------------------------------------------------|
| `SMART`    | Günstiger Tarif, aktiv wenn viel erneuerbare Energie im Netz verfügbar ist   |
| `STANDARD` | Normaltarif, aktiv wenn weniger erneuerbare Energie verfügbar ist            |

Die Tarifwechsel erfolgen in 15-Minuten-Intervallen basierend auf der Prognose der erneuerbaren Energieerzeugung.

---

## Fehlerbehandlung

| HTTP Status | Bedeutung                                       |
|-------------|-------------------------------------------------|
| 200         | Erfolgreiche Anfrage                            |
| 401         | Ungültiger oder abgelaufener Token              |
| 400         | Ungültige Anfrageparameter                      |
| 500         | Serverfehler                                    |

Bei Status 401 sollte ein neuer Token angefordert werden.

---

## Rate Limiting

Es sind keine offiziellen Rate Limits dokumentiert. Es wird empfohlen, Anfragen auf ein sinnvolles Minimum zu beschränken (z.B. alle 15 Minuten).

---

## Beispiel: Python-Client

```python
import aiohttp

async def get_tariff_prognosis(token: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://api.wws.tarifdynamik.de/tariffs/prognosis",
            params={
                "timezone": "Europe/Berlin",
                "page_size": "192",
                "filters": "valid_from:gte:2024-01-15",
            },
            headers={"Authorization": f"Bearer {token}"},
        ) as response:
            return await response.json()
```

---

## Hinweise

- Die API wird von WestfalenWIND Strom GmbH betrieben
- Diese Dokumentation wurde durch Reverse-Engineering der EnergieDock-App erstellt
- Änderungen an der API sind jederzeit möglich
- Die Nutzung erfolgt auf eigene Verantwortung

---

## Changelog

| Datum      | Änderung                              |
|------------|---------------------------------------|
| 2026-01-10 | Initiale Dokumentation erstellt       |
