#!/usr/bin/env python3
"""
Kicker-Kurt – Fußball-Tipp-Bot für "KI gegen das System".
Tippt NUR mit Spielgeld. Es wird nirgendwo echt gewettet.

Strategie Version 2 ("Value-Tipps", seit Update #3 am 20.11.2026):
- Kurt holt sich die Quoten vieler Anbieter für die Spiele der nächsten 3 Tage
  in 5 Ligen (Bundesliga, Premier League, La Liga, Serie A, Ligue 1) und seit 25.11. auch
  Champions League, Europa League und Conference League (Spiele unter der Woche).
- Aus allen Quoten zusammen berechnet er die "faire" Chance jedes Ausgangs
  (Heimsieg, Unentschieden, Auswärtssieg).
- "Value" = wie viel besser eine Quote ist als fair.
  Beispiel Münzwurf: Chance 50 %, faire Quote 2,00. Quote 2,04 -> im Schnitt 102 € pro 100 € -> +2 % Value.
- Ab +2 % Value tippt Kurt mit 100 €. Quoten über 6,00 sind ihm zu riskant.
- Notfall-Tipp: Hat Kurt bis Freitag für das ganze Wochenende keinen einzigen Tipp,
  tippt er sein bestes Spiel mit nur 50 € – und sagt das offen.
- Startgeld: 10.000 €.

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
STAKE = 100.0                    # Einsatz pro Value-Tipp
STAKE_NOTFALL = 50.0             # Einsatz für den Notfall-Tipp
MIN_VALUE = 1.02                 # Quote muss mind. 2 % besser als fair sein
MAX_ODDS = 6.0                   # keine wilden Außenseiter-Tipps
MIN_BOOKMAKERS = 5               # mind. 5 Anbieter für eine faire Einschätzung
LOOKAHEAD_HOURS = 72             # Spiele der nächsten 3 Tage tippen
CREDIT_RESERVE = 30              # so viele API-Abfragen immer übrig lassen
# Reihenfolge = Wichtigkeit (wenn Abfragen knapp werden, fallen die hinteren weg)
LEAGUES = {
    "soccer_germany_bundesliga": "Bundesliga",
    "soccer_uefa_champs_league": "Champions League",
    "soccer_epl": "Premier League",
    "soccer_spain_la_liga": "La Liga",
    "soccer_italy_serie_a": "Serie A",
    "soccer_france_ligue_one": "Ligue 1",
    "soccer_uefa_europa_league": "Europa League",
    "soccer_uefa_europa_conference_league": "Conference League",
}
EXCLUDE_BOOKS = ("betfair", "matchbook", "smarkets", "_ex")  # Wettbörsen ausschließen

API = "https://api.the-odds-api.com/v4"
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
STATE_FILE = os.path.join(DATA_DIR, "kurt_state.json")
BETS_FILE = os.path.join(DATA_DIR, "kurt_tipps.csv")
EQUITY_FILE = os.path.join(DATA_DIR, "kurt_kontostand.csv")
LOG_FILE = os.path.join(DATA_DIR, "kurt_entscheidungen.csv")
ANALYSE_FILE = os.path.join(DATA_DIR, "kurt_analyse.csv")

BETS_HEADER = ["spiel_id", "liga", "liga_key", "getippt_am", "anstoss", "heim", "gast", "tipp", "quote",
               "faire_chance_prozent", "value_prozent", "einsatz_eur", "status", "ergebnis",
               "auszahlung_eur", "gewinn_eur", "art"]
EQUITY_HEADER = ["zeit", "kontostand_eur", "offene_einsaetze_eur", "gewinn_eur", "gewinn_prozent",
                 "tipps_gesamt", "gewonnen", "verloren", "offen"]
LOG_HEADER = ["zeit", "liga", "spiel", "anstoss", "entscheidung", "grund"]
ANALYSE_HEADER = ["zeit", "liga", "heim", "gast", "anstoss", "bester_tipp", "quote", "faire_chance_prozent",
                  "faire_quote", "value_prozent", "anbieter", "entscheidung", "grund"]

credits_left = None  # wird nach jeder Abfrage aktualisiert


# ---------------------------------------------------------------- Hilfsfunktionen
def call(path, params):
    global credits_left
    params = dict(params, apiKey=os.environ["ODDS_API_KEY"])
    url = API + path + "?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            rem = r.headers.get("x-requests-remaining")
            if rem is not None:
                try:
                    credits_left = float(rem)
                except ValueError:
                    pass
            print(f"API-Credits übrig: {rem}")
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        print(f"API-Fehler {e.code} bei {path}: {e.read().decode(errors='replace')}")
        raise


def credits_ok(cost):
    return credits_left is None or credits_left - cost >= CREDIT_RESERVE


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
        w = csv.DictWriter(f, fieldnames=header, restval="", extrasaction="ignore")
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
    state = {"kasse": START_BANKROLL, "gecheckt": []}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding="utf-8") as f:
            state.update(json.load(f))
    state.setdefault("kandidaten", {})
    state.setdefault("notfall_wochenenden", [])
    return state


def save_state(state, now):
    state["gecheckt"] = state["gecheckt"][-800:]
    # alte Kandidaten (Anstoß vorbei) wegwerfen
    state["kandidaten"] = {k: v for k, v in state["kandidaten"].items()
                           if parse_ts(v["anstoss"]) > now - timedelta(days=1)}
    state["notfall_wochenenden"] = state["notfall_wochenenden"][-20:]
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
        if not credits_ok(2):
            print("Zu wenige API-Abfragen übrig – Auswertung später.")
            break
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


# ---------------------------------------------------------------- Spiele bewerten
def analyse(event):
    """Rechnet für jeden Ausgang faire Chance, Quote und Value aus.
    Gibt (liste, anzahl_anbieter) zurück; liste = [(name, quote, faire_chance, value), ...]"""
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
    out = []
    for name, plist in probs.items():
        fair = statistics.mean(plist)
        top = sorted(prices[name], reverse=True)
        odds = top[1] if len(top) > 1 else top[0]   # zweitbeste Quote = Ausreißer ignorieren
        out.append((name, odds, fair, odds * fair))
    return out, n_books


def decide(outcomes):
    """Gibt (tipp_oder_None, kandidat_für_notfall_oder_None, grund) zurück."""
    if not outcomes:
        return None, None, "keine Quoten"
    allowed = [o for o in outcomes if o[1] <= MAX_ODDS]
    best_any = max(outcomes, key=lambda o: o[3])
    best_ok = max(allowed, key=lambda o: o[3]) if allowed else None
    if best_ok and best_ok[3] >= MIN_VALUE:
        return best_ok, best_ok, ""
    if best_any[3] >= MIN_VALUE:
        return None, best_ok, (f"Value bei {tip_label(best_any[0])}, aber Quote {best_any[1]:.2f} zu riskant")
    shown = best_ok or best_any
    return None, best_ok, f"kein Value (bester Tipp {tip_label(shown[0])} nur {(shown[3] - 1) * 100:+.1f} %)"


def add_bet(state, bets, ev_like, league_key, league_name, tip_tuple, stake, art, now):
    name, odds, fair, value = tip_tuple
    state["kasse"] -= stake
    bets.append({
        "spiel_id": ev_like["id"], "liga": league_name, "liga_key": league_key,
        "getippt_am": local(now), "anstoss": ev_like["commence_time"],
        "heim": ev_like["home_team"], "gast": ev_like["away_team"], "tipp": tip_label(name),
        "quote": f"{odds:.2f}", "faire_chance_prozent": f"{fair * 100:.1f}",
        "value_prozent": f"{(value - 1) * 100:.1f}", "einsatz_eur": f"{stake:.2f}",
        "status": "offen", "ergebnis": "", "auszahlung_eur": "", "gewinn_eur": "", "art": art,
    })


def place_tips(state, bets, now):
    checked = set(state["gecheckt"])
    for league_key, league_name in LEAGUES.items():
        if not credits_ok(1):
            print(f"Zu wenige API-Abfragen übrig – {league_name} heute ausgelassen.")
            continue
        events = call(f"/sports/{league_key}/odds", {
            "regions": "eu", "markets": "h2h", "oddsFormat": "decimal", "dateFormat": "iso",
            "commenceTimeFrom": iso_z(now), "commenceTimeTo": iso_z(now + timedelta(hours=LOOKAHEAD_HOURS)),
        })
        for ev in sorted(events, key=lambda e: e["commence_time"]):
            if ev["id"] in checked:
                continue
            kickoff = parse_ts(ev["commence_time"])
            match = f"{ev['home_team']} – {ev['away_team']}"
            outcomes, n_books = analyse(ev)
            if n_books < MIN_BOOKMAKERS:
                continue  # später nochmal versuchen, wenn mehr Quoten da sind
            tip, cand, reason = decide(outcomes)
            shown = tip or cand or max(outcomes, key=lambda o: o[3])
            if tip and state["kasse"] < STAKE:
                tip, reason = None, "Kasse leer"
            if tip:
                add_bet(state, bets, ev, league_key, league_name, tip, STAKE, "Value", now)
                why = f"Quote {tip[1]:.2f}, faire Chance {tip[2] * 100:.0f} %, Value +{(tip[3] - 1) * 100:.1f} %"
                decision = f"TIPP: {tip_label(tip[0])}"
            else:
                why, decision = reason, "kein Tipp"
                if cand:  # für einen möglichen Notfall-Tipp merken
                    state["kandidaten"][ev["id"]] = {
                        "liga": league_name, "liga_key": league_key, "heim": ev["home_team"],
                        "gast": ev["away_team"], "anstoss": ev["commence_time"], "tipp": cand[0],
                        "quote": cand[1], "fair": cand[2], "value": cand[3]}
            append_csv(LOG_FILE, LOG_HEADER, [local(now), league_name, match, local(kickoff), decision, why])
            append_csv(ANALYSE_FILE, ANALYSE_HEADER, [
                local(now), league_name, ev["home_team"], ev["away_team"], local(kickoff), tip_label(shown[0]),
                f"{shown[1]:.2f}", f"{shown[2] * 100:.1f}", f"{1 / shown[2]:.2f}", f"{(shown[3] - 1) * 100:+.1f}",
                n_books, decision, why])
            print(f"{match}: {decision} – {why}")
            checked.add(ev["id"])
            state["gecheckt"].append(ev["id"])


# ---------------------------------------------------------------- Notfall-Tipp
def weekend_window(now):
    """Freitag 00:00 bis Montag 06:00 (deutsche Zeit) des aktuellen Wochenendes."""
    loc = now.astimezone(BERLIN)
    wd = loc.weekday()  # Mo=0 … So=6
    if wd < 4:
        return None
    friday = (loc - timedelta(days=wd - 4)).replace(hour=0, minute=0, second=0, microsecond=0)
    return friday, friday + timedelta(days=3, hours=6)


def notfall_tipp(state, bets, now):
    win = weekend_window(now)
    if not win:
        return
    start, end = win
    wk = start.strftime("%Y-%m-%d")
    if wk in state["notfall_wochenenden"]:
        return
    def in_win(iso):
        k = parse_ts(iso).astimezone(BERLIN)
        return start <= k < end
    if any(in_win(b["anstoss"]) for b in bets):
        state["notfall_wochenenden"].append(wk)  # es gibt schon Tipps -> kein Notfall nötig
        return
    cands = [(cid, c) for cid, c in state["kandidaten"].items()
             if in_win(c["anstoss"]) and parse_ts(c["anstoss"]) > now + timedelta(hours=1)]
    if not cands:
        print("Kein Kandidat für einen Notfall-Tipp.")
        return
    cid, c = max(cands, key=lambda x: x[1]["value"])
    if state["kasse"] < STAKE_NOTFALL:
        return
    ev_like = {"id": cid, "commence_time": c["anstoss"], "home_team": c["heim"], "away_team": c["gast"]}
    tup = (c["tipp"], c["quote"], c["fair"], c["value"])
    add_bet(state, bets, ev_like, c["liga_key"], c["liga"], tup, STAKE_NOTFALL, "Notfall", now)
    match = f"{c['heim']} – {c['gast']}"
    why = (f"Notfall-Tipp: am ganzen Wochenende kein Value ab 2 %. Bestes Spiel: Quote {c['quote']:.2f}, "
           f"faire Chance {c['fair'] * 100:.0f} %, Value {(c['value'] - 1) * 100:+.1f} %, nur 50 € Einsatz")
    append_csv(LOG_FILE, LOG_HEADER, [local(now), c["liga"], match, local(parse_ts(c["anstoss"])),
                                      f"NOTFALL-TIPP: {tip_label(c['tipp'])}", why])
    print(f"{match}: NOTFALL-TIPP {tip_label(c['tipp'])} – {why}")
    state["notfall_wochenenden"].append(wk)


# ---------------------------------------------------------------- Hauptprogramm
def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    now = datetime.now(timezone.utc)
    state = load_state()
    bets = read_csv(BETS_FILE)
    for b in bets:
        b.setdefault("art", "")
        if not b["art"]:
            b["art"] = "Value"

    settle(state, bets, now)
    place_tips(state, bets, now)
    notfall_tipp(state, bets, now)

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
    save_state(state, now)


if __name__ == "__main__":
    main()
