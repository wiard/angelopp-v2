# BUMALA MANUAL TEST MATRIX

> Doel: de drie open items uit Deel 1 afronden (2.5 END, 3.3 5 rollen,
> 3.4 free-text) en als bijvangst je menu-tree als spec vastleggen voor
> toekomstige regressie-checks.
>
> Tool: `ussd-cli.sh`. Walking time: 20-40 minuten als de menu's klein zijn,
> langer als je veel free-text wilt testen.

## Setup

```bash
chmod +x ~/Downloads/ussd-cli.sh

# Voor nieuwe-user walks:
PHONE=+254799000001 ~/Downloads/ussd-cli.sh

# Voor known-user walks (wiard met bestaande state):
~/Downloads/ussd-cli.sh
# (default phone = +254700000001 = Wiard)

# Voor debug-mode (toont accumulerende text-buffer per turn):
DEBUG=1 ~/Downloads/ussd-cli.sh
```

Voer je menukeuzes in. Schrijf na elke screen op wat je ziet.

---

## WALK 1 — End-to-end nieuwe user tot END (deckt test 2.5)

Doel: één complete journey doorlopen waarin Bumala uiteindelijk `END ` stuurt.
Bestelling plaatsen is de meest waarschijnlijke END-trigger.

```bash
PHONE=+254799000001 ~/Downloads/ussd-cli.sh
```

| Stap | Input | Wat verwacht je | Wat zie je | OK |
|---|---|---|---|---|
| 1 | (start) | Naam-vraag, `CON ` | ___________________ | ☐ |
| 2 | `TestEinde` | Rolmenu, `CON ` | ___________________ | ☐ |
| 3 | `1` (delivery) | Bestelling-flow | ___________________ | ☐ |
| 4 | doorloop tot eind | Bestelling bevestigd? | ___________________ | ☐ |
| ... | ... | uiteindelijk `END ` | screen begint met `END `? | ☐ |

**Notitie:** noteer het EXACTE pad waar END verschijnt (bv. `1*1*Bumala Market*Ja`).
Dat is je referentie-END-route voor regressie. Als je hier vastloopt en geen END
ziet — bug, bestellingen moeten ergens afsluiten.

---

## WALK 2 — Rolmenu, top-level (deckt 3.3 inventaris)

Doel: bevestigen dat alle 5 rollen vanuit het hoofdmenu bereikbaar zijn.

```bash
~/Downloads/ussd-cli.sh   # known user, skip naamvraag
```

Eerste screen = rolmenu. Noteer:

```
Wat staat er letterlijk op het rolmenu (kopieer):
___________________________________________________________
___________________________________________________________
___________________________________________________________
___________________________________________________________
___________________________________________________________
```

| Rol | Verwachte optie | Werkt? | Eerste submenu screen |
|---|---|---|---|
| Delivery | `1` | ☐ | __________________ |
| Ride | `2` | ☐ | __________________ |
| Medical | `3` | ☐ | __________________ |
| Marketplace | `4` | ☐ | __________________ |
| Rider | `5` | ☐ | __________________ |

(Als de nummering anders is dan 1-5: dan is dat je werkelijke spec.
Noteer het zoals het is, dat IS de waarheid.)

---

## WALK 3 — Per rol: alle subopties (verdere deel van 3.3)

Per rol een aparte cli-sessie. Bij elke submenu: probeer ELKE numerieke
optie minimaal één keer. Noteer waar 'ie naar leidt.

### Walk 3a — Delivery (rol 1)

```bash
~/Downloads/ussd-cli.sh
# input: 1
```

```
Submenu screen (kopieer):
______________________________________________
______________________________________________
______________________________________________
______________________________________________
```

Per submenu-optie:

| Optie | Wat het zou moeten doen | Wat het werkelijk doet | OK |
|---|---|---|---|
| 1 | ___________________ | ___________________ | ☐ |
| 2 | ___________________ | ___________________ | ☐ |
| 3 | ___________________ | ___________________ | ☐ |
| 4 | ___________________ | ___________________ | ☐ |
| 0 (back?) | terug naar rolmenu | ___________________ | ☐ |

### Walk 3b — Ride (rol 2)
(zelfde format als 3a)

### Walk 3c — Medical (rol 3)
(zelfde format)

### Walk 3d — Marketplace (rol 4)
(zelfde format)

### Walk 3e — Rider (rol 5)
(zelfde format)

---

## WALK 4 — Free-text features (deckt 3.4)

Doel: bewijzen dat elke free-text input correct wordt opgeslagen en
gebruikt in volgende screens.

Voor elke free-text feature: lop naar de plek waar 'ie wordt gevraagd,
voer een test-string in, kijk of die later in een bevestigingsscherm
terugkomt OF correct in de DB belandt.

### 4.1 — Naam registratie

Pad: nieuwe user, eerste prompt.

```bash
PHONE=+254799000042 ~/Downloads/ussd-cli.sh
# input: "TestNaam Bumala"
```

- Wordt naam geaccepteerd? ☐
- Komt 'ie terug in een vervolgscreen (bv "Hey TestNaam ...")? ☐
- Edge case: spaties werken? ☐
- Edge case: zeer lange naam (>30 chars)? ☐

### 4.2 — Medical beschrijving

Pad: rol Medical → free-text prompt.

```bash
~/Downloads/ussd-cli.sh
# (door naar medical, dan de free-text)
```

- Wordt beschrijving geaccepteerd? ☐
- Komt 'ie correct terug in bevestigingsscreen? ☐
- DB-check (op de VPS): `sqlite3 /opt/angelopp/data/bumala.db "SELECT * FROM service_requests ORDER BY id DESC LIMIT 1"` — staat je test-input daar? ☐

### 4.3 — Delivery instructies

Pad: rol Delivery → bestelling-flow → instructies prompt.

- Geaccepteerd? ☐
- DB-check: `SELECT * FROM delivery_requests ORDER BY id DESC LIMIT 1` ☐

### 4.4 — Custom crop naam (Marketplace)

Pad: rol Marketplace → custom crop submenu.

- Geaccepteerd? ☐
- DB-check: `SELECT * FROM crops ORDER BY id DESC LIMIT 1` ☐

### 4.5 — Rider voertuig info

Pad: rol Rider → registratie-flow.

- Geaccepteerd? ☐
- DB-check: `SELECT * FROM riders ORDER BY id DESC LIMIT 1` ☐

### 4.6 — Buyer bericht aan verkoper

Pad: rol Marketplace → buy from listing → contact seller.

- Geaccepteerd? ☐
- DB-check: `SELECT * FROM messages ORDER BY id DESC LIMIT 1` ☐

---

## WALK 5 — Spec-output

Na al deze walks heb je iets waardevols: een handgeschreven map van wat
Bumala vandaag *werkelijk* doet. Schrijf 'm op als `bumala-menu-spec.md`:

```
# Bumala Menu Spec — gemeten op YYYY-MM-DD

## Hoofdmenu (nieuwe user)
"CON Jambo! Welkom bij Angelopp Bumala. Hoe heet je?"
→ na free-text naam: rolmenu

## Rolmenu (known user)
"CON Hey <name>! 👋\nBezorging vanaf <last_location>?"
1. Ja, bestel nu → ...
2. Andere plek vandaag → ...
3. Mijn gegevens → ...
4. Meer opties → ...

## Delivery (rol 1)
...

## Ride (rol 2)
...

[etc per rol]

## END-routes
- 1*1*<adres>*Ja → "END Bestelling geplaatst. Ride <ID>."
- ...

## Free-text inputs
- Naam (welcome): geen length limit gemeten, accepteert spaties + utf-8
- ...
```

Deze spec is dan je waarheid voor toekomstige regressie. Run `ussd-explore.sh`
elke release, diff de output tegen deze spec, weet exact wat veranderd is.

---

## Wanneer alles ☑

- Walk 1 ☑ → END-route gevonden (test 2.5 dicht)
- Walks 2-3 ☑ → 5 rollen + alle subopties geïnventariseerd (test 3.3 dicht)
- Walk 4 ☑ → free-text features geverifieerd (test 3.4 dicht)
- Walk 5 ☑ → menu-spec gedocumenteerd (bonus: regressie-baseline)

Daarna: Deel 2 (AT sandbox) van de hoofdchecklist.
