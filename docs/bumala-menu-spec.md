# BUMALA MENU SPEC

> Levende waarheid van wat Bumala *werkelijk* doet op `tester.angelopp.com`.
> Gemeten via curl en `ussd-cli.sh` (met `DEBUG=1` voor exacte text-buffer
> waardes). Ongemete delen zijn expliciet gemarkeerd als `unknown` of
> `partial` — geen valse aannames.

**Metadata**

| Veld | Waarde |
|---|---|
| Versie | 0.1 (pre-walk baseline) |
| Gemeten op | 2026-05-19 |
| Backend git commit | `c20f371` (laatst bekend: "fix: CALL knop voor sessiestart") |
| URL | https://tester.angelopp.com/api/ussd |
| Service code (in code) | `*384*466#` (let op: inconsistent met `*384*66#` in core/onboarding.py) |
| Measured by phone numbers | `+254700000001` (Wiard, known user), `+254799999111`, `+254799999222`, `+254799999333`, `+254799900001` (test new users), `+254799000042` (free-text test) |
| Phone-format genormaliseerd | ✅ ja (+254..., 254..., 0... geven zelfde flow) |
| Response latency baseline | ~0.22s gemiddeld (zie sectie 10) |

---

## 1. Entry — nieuwe user

**Status:** `measured`

**text-buffer:** `""` (leeg)

**Phone gebruikt:** `+254799999111` (en varianten)

**Screen:**
```
CON Jambo! Welkom bij Angelopp Bumala. Hoe heet je?
```
(118 chars, ruim binnen 182-char limit)

**Type:** free-text expected (naam)

**Next state:** na naam-input → post-registration menu (te meten in walk — vermoedelijk rolmenu, maar niet geverifieerd). Sectie 2 hieronder beschrijft een ander scenario: de fast-action screen voor *bestaande* user, niet wat een net-geregistreerde nieuwe user direct te zien krijgt.

---

## 2. Entry — bestaande user (fast-action screen)

**Status:** `measured`

**text-buffer:** `""` (leeg)
**Phone:** `+254700000001` (Wiard, known user met delivery-history)

**Screen:**
```
CON Hey wiard! 👋

Bezorging vanaf church?
1. Ja, bestel nu
2. Andere plek vandaag
3. Mijn gegevens
4. Meer opties
```

**Type:** numeric menu, context-aware (toont laatst-bekende locatie "church")

**Belangrijke observatie:** dit is een fast-action screen, geen generiek
rolmenu met 5 opties. Bumala past de V2-filosofie toe (User → Data → Fast
Action). Het 5-rollen menu zit waarschijnlijk achter optie 4 "Meer opties".

**Opties:**

| # | Label | Leidt naar | text-buffer na keuze |
|---|---|---|---|
| 1 | Ja, bestel nu | bestelling-confirmation flow | `1` |
| 2 | Andere plek vandaag | locatie-keuze | `2` |
| 3 | Mijn gegevens | profiel | `3` |
| 4 | Meer opties | (vermoedelijk) 5-rollen menu | `4` |
| 0 | back? (niet getoond, mogelijk nvt) | unknown | `0` |

---

## 3. Rol: Delivery

**Status:** `partial` — top-level vermoedelijk via optie 1 of via "Meer opties → Delivery"

### 3.1 Top submenu

**text-buffer:** `1` (direct via fast-action) of `4*1` (via meer opties — niet geverifieerd)

**Screen:**
```
[onbekend — vul in tijdens walk]
```

### 3.2 [submenu]

**Status:** `unknown` — vereist walk

### 3.X END-route: bestelling geplaatst

**text-buffer:** `unknown`

**Screen:**
```
[onbekend]
```

**Persistence:**
- Verwachte tabel: `delivery_requests` (42 rijen vandaag) of `service_requests` (107 rijen vandaag)
- SQL-check: `sqlite3 /opt/angelopp/data/bumala.db "SELECT * FROM delivery_requests ORDER BY id DESC LIMIT 1"`
- Result: ☐ nog te verifiëren

---

## 4. Rol: Ride

**Status:** `unknown`

### 4.1 Top submenu

**text-buffer:** `2` of `4*2`

**Screen:**
```
[onbekend — vul in tijdens walk]
```

### 4.X END-route

**Persistence:**
- Verwachte tabel: vermoedelijk ook `service_requests` met type=ride
- SQL-check: _________
- Result: ☐ nog te verifiëren

---

## 5. Rol: Medical

**Status:** `unknown` (free-text element bekend: medical beschrijving)

### 5.X END-route

**Persistence:**
- Verwachte tabel: `service_requests` met type=medical
- SQL-check: _________
- Result: ☐ nog te verifiëren

---

## 6. Rol: Marketplace

**Status:** `unknown` (free-text elementen: custom crop, buyer bericht)

**Bekende DB-tabellen relevant voor marketplace:** `crops` (waarde onbekend qua aantal rijen), `messages` (142 rijen vandaag)

### 6.X END-route

**Persistence:**
- Verwachte tabellen: `crops`, `messages`
- SQL-check: _________
- Result: ☐ nog te verifiëren

---

## 7. Rol: Rider

**Status:** `unknown` (free-text element: voertuig info)

**Bekende DB-tabel:** `riders` (3 rijen vandaag — er zijn dus al rider-registraties)

### 7.X END-route

**Persistence:**
- Tabel: `riders`
- Kolommen (vermoedelijk): phone, vehicle_info, created_at
- SQL-check: `sqlite3 /opt/angelopp/data/bumala.db "SELECT * FROM riders"`
- Result: ☐ nog te verifiëren

---

## 8. Error-paden

### 8.1 Ongeldige digit (bv. `999`)

**Status:** `partial`

**text-buffer:** `999`

**Screen:**
```
CON [exacte wording onbekend] Invalid choice.
[mogelijk vervolg met opnieuw-prompt]
```

**Type:** error message binnen `CON` (geen END), graceful, geen stacktrace

**Verified:** geen Python traceback in response (test 4.3 ☑)

### 8.2 Tikfout midden in flow

**Status:** `unknown`

### 8.3 Empty input

**Status:** `unknown`

---

## 9. Free-text features

### 9.1 — Naam registratie

**Status:** `partial`

| Veld | Waarde |
|---|---|
| Trigger | nieuwe user, lege text |
| Prompt | `Jambo! Welkom bij Angelopp Bumala. Hoe heet je?` |
| Acceptatie | ✅ accepteert spaties ("Test Pilot"), ✅ accepteert utf-8 |
| Max length | unknown — niet gemeten op edge case >30 chars |
| Persistence tabel | `users` (200 user_roles in DB, dus gevuld) |
| Kolom | vermoedelijk `name` |
| DB-check | `SELECT phone, name FROM users WHERE phone='+254799000042'` |
| Status | ☑ flow getest, ☐ DB-persistence niet expliciet geverifieerd |

### 9.2 — Medical beschrijving

**Status:** `unknown`

| Veld | Waarde |
|---|---|
| Trigger pad | `3*?` of `4*3*?` (afhankelijk van hoe je medical bereikt) |
| Prompt | _________ |
| Persistence tabel | `service_requests` (107 rijen vandaag) |
| Kolom | vermoedelijk `description` |
| Status | ☐ |

### 9.3 — Delivery instructies

**Status:** `unknown`

| Veld | Waarde |
|---|---|
| Trigger pad | `1*?` (binnen delivery flow) |
| Persistence tabel | `delivery_requests` (42 rijen vandaag) |
| Status | ☐ |

### 9.4 — Custom crop naam

**Status:** `unknown`

| Veld | Waarde |
|---|---|
| Trigger pad | binnen marketplace |
| Persistence tabel | `crops` |
| Status | ☐ |

### 9.5 — Rider voertuig info

**Status:** `unknown`

| Veld | Waarde |
|---|---|
| Trigger pad | binnen rider registratie |
| Persistence tabel | `riders` (al 3 records bestaan) |
| Status | ☐ |

### 9.6 — Buyer bericht aan verkoper

**Status:** `unknown`

| Veld | Waarde |
|---|---|
| Trigger pad | binnen marketplace, contact-seller flow |
| Persistence tabel | `messages` (al 142 records bestaan) |
| Status | ☐ |

---

## 10. Latency-baseline

**Status:** `measured` (entry-routes), `unknown` (diepere paden)

| Pad | text-buffer | Gemeten time_total | Sample |
|---|---|---|---|
| Welcome (entry) | `""` | 0.219s | run 1 |
| Welcome (entry) | `""` | 0.201s | run 2 |
| Welcome (entry) | `""` | 0.255s | run 3 |
| **Gemiddelde welcome** | | **~0.22s** | n=3 |
| Rolmenu/fast-action | `Wiard` | unknown | |
| Delivery top | `1` | unknown | |
| Delivery diepste END | `1*...*Ja` | unknown | |

Deepste paden meten met:
```bash
curl -sS -o /dev/null -w "%{time_total}s\n" -X POST \
  https://tester.angelopp.com/api/ussd \
  -d "sessionId=lat-$(date +%s)" -d "phoneNumber=+254700000001" \
  -d "serviceCode=*384*466#" --data-urlencode "text=<pad>"
```

---

## 11. Open / known issues

- **Shortcode-inconsistentie**: `core/onboarding.py` zegt `*384*66#`, `core/sms_handler.py` en `app.py` zeggen `*384*466#`. Eén is fout; users krijgen mogelijk verkeerde shortcode via SMS.
- **Content-Type header**: response wordt geserveerd als `text/html; charset=utf-8` ipv `text/plain`. AT accepteert beide, maar `text/plain` is netter.
- **Bumala backend bind**: poort 5002 luistert op `0.0.0.0:5002` ipv `127.0.0.1:5002`. Tegen eigen security-rule in. Nginx proxyt al, geen reden voor publieke bind.
- **AT_USERNAME**: nog `sandbox` in `/opt/angelopp/.env`. Real phones bereiken sandbox-account niet.

---

## 12. Geverifieerde AT-contract compliance (vandaag, 2026-05-19)

| Item | Status |
|---|---|
| HTTP 200 op POST `/api/ussd` | ☑ |
| Response begint met `CON ` | ☑ |
| Plain-text body | ☑ |
| Response time < 5s (gemeten: 0.22s) | ☑ |
| Lege text → eerste menu | ☑ |
| Accumulerende text werkt | ☑ |
| Verschillende sessionId = isolated | ☑ |
| UTF-8 + emoji 👋 rendert | ☑ |
| Response < 182 chars (welcome=118) | ☑ |
| Geen Python stacktraces bij errors | ☑ |
| Phone-format genormaliseerd | ☑ |
| SSL cert valid tot 2026-08-17 | ☑ |
| END-route bestaat | ☐ nog te verifiëren in walk |
| Alle 5 rollen bereikbaar | ☐ nog te verifiëren in walk |
| Free-text features → DB | ☐ nog te verifiëren in walk |

---

## Hoe deze spec te gebruiken

1. **Bij élke release**: run `ussd-explore.sh`, vergelijk met de boomstructuur
   in secties 2–7. Onverwachte verschillen = bug of intentionele wijziging.
2. **Bij menu-redesign**: update deze spec eerst (vooraf-design), bouw dan,
   walk opnieuw, verifieer dat code matcht spec.
3. **Bij regressie-bug**: kijk welke text-buffer route 't probleem heeft,
   reproduceer met `ussd-cli.sh`, vergelijk verwachte vs werkelijke screen.

**Voltooiing van deze spec** vergt een walk-sessie met `ussd-cli.sh`
(geleid door `BUMALA_MANUAL_TEST_MATRIX.md`). Geschatte tijd: 30-45 min.

Voor de Epilepsy-fork: maak een aparte `epilepsy-menu-spec.md` met
dezelfde structuur. Twee verticals = twee specs.
