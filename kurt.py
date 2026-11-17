#!/usr/bin/env python3
"""
Kicker-Kurt – Fußball-Tipp-Bot für "KI gegen das System".
Tippt NUR mit Spielgeld. Es wird nirgendwo echt gewettet.

Strategie Version 1 ("Value-Tipps"):
- Kurt holt sich die Quoten vieler Anbieter für die nächsten Spiele.
- Aus allen Quoten zusammen berechnet er die "faire" Siegchance jedes Ausgangs
  (Heimsieg, Unentschieden, Auswärtssieg).
- Ist eine Quote mindestens 3 % besser als fair, ist das ein "Value-Tipp" -> Kurt tippt.
- Sonst lässt er das Spiel aus.
- Einsatz: 100 € pro Tipp. Startgeld: 10.000 €.

Läuft automatisch über GitHub Actions (.github/workflows/kurt.yml), 1x pro Tag.
Nur Python-Standardbibliothek, keine Installation nötig.
"""
import csv
import json
import os
import statistics
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo
    BERLIN = ZoneInfo("Europe/Berlin")
except Exception:  # pragma: no cover
    BERLIN = timezone.utc

# ---------------------------------------------------------------- Einstellungen
START_BANKROLL = 10_000.0        # Startgeld in Euro
STAKE = 100.0                    # Einsatz pro Tipp
MIN_VALUE = 1.03                 # Quote muss mind. 3 % besser als fair sein
MAX_ODDS = 6.0                   # keine wilden Außenseiter-Tipps
MIN_BOOKMAKERS = 5               # mind. 5 Anbieter für eine faire Einschätzung
LOOKAHEAD_HOURS = 72             # Spiele der nächsten 3 Tage tippen
# Ligen: In der Bundesliga-Winterpause "soccer_epl" (Premier League) dazunehmen.
LEAGUES = {
    "soccer_germany_bundesliga": "Bundesliga",
}
EXCLUDE_BOOKS = ("betfair", "matchbook", "smarkets", "_ex")  # Wettbörsen ausschließen

API = "https://api.the-odds-api.com/v4"
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
STATE_FILE = os.path.join(DATA_DIR, "kurt_state.json")
BETS_FILE = os.path.join(DATA_DIR, "kurt_tipps.csv")
EQUITY_FILE = os.path.join(DATA_DIR, "kurt_kontostand.csv")
LOG_FILE = os.path.join(DATA_DIR, "kurt_entscheidungen.csv")

BETS_HEADER = ["spiel_id", "liga", "liga_key", "getippt_am", "anstoss", "heim", "gast", "tipp", "quote",
               "faire_chance_prozent", "value_prozent", "einsatz_eur", "status", "ergebnis",
               "auszahlung_eur", "gewinn_eur"]
EQUITY_HEADER = ["zeit", "kontostand_eur", "offene_einsaetze_eur", "gewinn_eur", "gewinn_prozent",
                 "tipps_gesamt", "gewonnen", "verloren", "offen"]
LOG_HEADER = ["zeit", "liga", "spiel", "anstoss", "entscheidung", "grund"]


# ---------------------------------------------------------------- Hilfsfunktionen
def call(path, params):
    params = dict(params, apiKey=os.environ["ODDS_API_KEY"])
    url = API + path + "?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            print(f"API-Credits übrig: {r.headers.get('x-requests-remaining')}")
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        print(f"API-Fehler {e.code} bei {path}: {e.read().decode(errors='replace')}")
        raise


def parse_ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def iso_z(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def local(dt):
    return dt.astimezone(BERLIN).strftime("%Y-%m-%d %H:%M")


def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        w.writerows(rows)


def append_csv(path, header, row):
    new = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(header)
        w.writerow(row)


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"kasse": START_BANKROLL, "gecheckt": []}


def save_state(state):
    state["gecheckt"] = state["gecheckt"][-500:]
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def tip_label(name):
    return "Unentschieden" if name.lower() == "draw" else name


# ---------------------------------------------------------------- Tipps auswerten
def settle(state, bets, now):
    due = [b for b in bets if b["status"] == "offen"
           and parse_ts(b["anstoss"]) + timedelta(hours=2) < now]
    if not due:
        print("Keine Tipps zum Auswerten.")
        return
    for league_key in {b["liga_key"] for b in due}:
        scores = call(f"/sports/{league_key}/scores", {"daysFrom": 3, "dateFormat": "iso"})
        by_id = {s["id"]: s for s in scores}
        for b in due:
            if b["liga_key"] != league_key:
                continue
            s = by_id.get(b["spiel_id"])
            if not s or not s.get("completed") or not s.get("scores"):
                continue
            goals = {x["name"]: int(x["score"]) for x in s["scores"]}
            h, a = goals.get(b["heim"]), goals.get(b["gast"])
            if h is None or a is None:
                continue
            winner = b["heim"] if h > a else b["gast"] if a > h else "Unentschieden"
            stake, odds = float(b["einsatz_eur"]), float(b["quote"])
            b["ergebnis"] = f"{h}:{a}"
            if b["tipp"] == winner:
                payout = stake * odds
                b["status"], b["auszahlung_eur"] = "gewonnen", f"{payout:.2f}"
                b["gewinn_eur"] = f"{payout - stake:.2f}"
                state["kasse"] += payout
            else:
                b["status"], b["auszahlung_eur"], b["gewinn_eur"] = "verloren", "0.00", f"{-stake:.2f}"
            print(f"{b['heim']} – {b['gast']} {b['ergebnis']}: Tipp {b['tipp']} -> {b['status']}")


# ---------------------------------------------------------------- Neue Tipps
def evaluate(event):
    """Sucht den besten Value-Tipp für ein Spiel. Gibt (Tipp, Quote, faire Chance, Value) oder Grund zurück."""
    probs, prices = {}, {}
    for b in event.get("bookmakers", []):
        if any(x in b["key"] for x in EXCLUDE_BOOKS):
            continue
        m = next((m for m in b.get("markets", []) if m["key"] == "h2h"), None)
        if not m or len(m["outcomes"]) != 3:
            continue
        inv = {o["name"]: 1 / float(o["price"]) for o in m["outcomes"]}
        total = sum(inv.values())
        for name, v in inv.items():
            probs.setdefault(name, []).append(v / total)
        for o in m["outcomes"]:
            prices.setdefault(o["name"], []).append(float(o["price"]))
    n_books = min((len(v) for v in probs.values()), default=0)
    if n_books < MIN_BOOKMAKERS:
        return None, f"nur {n_books} Anbieter mit Quoten"
    best = None
    for name, plist in probs.items():
        fair = statistics.mean(plist)
        top = sorted(prices[name], reverse=True)
        odds = top[1] if len(top) > 1 else top[0]   # zweitbeste Quote = Ausreißer ignorieren
        value = odds * fair
        if best is None or value > best[3]:
            best = (name, odds, fair, value)
    name, odds, fair, value = best
    if value < MIN_VALUE:
        return None, f"kein Value (bester Tipp {tip_label(name)} nur {(value - 1) * 100:+.1f} %)"
    if odds > MAX_ODDS:
        return None, f"Value bei {tip_label(name)}, aber Quote {odds:.2f} zu riskant"
    return best, ""


def place_tips(state, bets, now):
    checked = set(state["gecheckt"])
    for league_key, league_name in LEAGUES.items():
        events = call(f"/sports/{league_key}/odds", {
            "regions": "eu", "markets": "h2h", "oddsFormat": "decimal", "dateFormat": "iso",
            "commenceTimeFrom": iso_z(now), "commenceTimeTo": iso_z(now + timedelta(hours=LOOKAHEAD_HOURS)),
        })
        for ev in sorted(events, key=lambda e: e["commence_time"]):
            if ev["id"] in checked:
                continue
            kickoff = parse_ts(ev["commence_time"])
            match = f"{ev['home_team']} – {ev['away_team']}"
            result, reason = evaluate(ev)
            if result is None:
                if "Anbieter" in reason:
                    continue  # später nochmal versuchen, wenn mehr Quoten da sind
                append_csv(LOG_FILE, LOG_HEADER, [local(now), league_name, match, local(kickoff), "kein Tipp", reason])
                print(f"{match}: kein Tipp – {reason}")
            elif state["kasse"] < STAKE:
                append_csv(LOG_FILE, LOG_HEADER, [local(now), league_name, match, local(kickoff), "kein Tipp", "Kasse leer"])
            else:
                name, odds, fair, value = result
                tip = tip_label(name)
                state["kasse"] -= STAKE
                bets.append({
                    "spiel_id": ev["id"], "liga": league_name, "liga_key": league_key,
                    "getippt_am": local(now), "anstoss": ev["commence_time"],
                    "heim": ev["home_team"], "gast": ev["away_team"], "tipp": tip,
                    "quote": f"{odds:.2f}", "faire_chance_prozent": f"{fair * 100:.1f}",
                    "value_prozent": f"{(value - 1) * 100:.1f}", "einsatz_eur": f"{STAKE:.2f}",
                    "status": "offen", "ergebnis": "", "auszahlung_eur": "", "gewinn_eur": "",
                })
                why = f"Quote {odds:.2f}, faire Chance {fair * 100:.0f} %, Value +{(value - 1) * 100:.1f} %"
                append_csv(LOG_FILE, LOG_HEADER, [local(now), league_name, match, local(kickoff), f"TIPP: {tip}", why])
                print(f"{match}: TIPP {tip} – {why}")
            checked.add(ev["id"])
            state["gecheckt"].append(ev["id"])


# ---------------------------------------------------------------- Hauptprogramm
def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    now = datetime.now(timezone.utc)
    state = load_state()
    bets = read_csv(BETS_FILE)

    settle(state, bets, now)
    place_tips(state, bets, now)

    write_csv(BETS_FILE, BETS_HEADER, bets)

    open_stakes = sum(float(b["einsatz_eur"]) for b in bets if b["status"] == "offen")
    balance = state["kasse"] + open_stakes
    pnl = balance - START_BANKROLL
    won = sum(b["status"] == "gewonnen" for b in bets)
    lost = sum(b["status"] == "verloren" for b in bets)
    append_csv(EQUITY_FILE, EQUITY_HEADER, [
        local(now), f"{balance:.2f}", f"{open_stakes:.2f}", f"{pnl:.2f}",
        f"{pnl / START_BANKROLL * 100:.2f}", len(bets), won, lost, len(bets) - won - lost])
    print(f"Kurts Kontostand: {balance:,.2f} € ({pnl:+,.2f} €) | {won} gewonnen, {lost} verloren")
    save_state(state)


if __name__ == "__main__":
    main()
