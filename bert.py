#!/usr/bin/env python3
"""
Börsen-Bert – Intraday-Trading-Bot für "KI gegen das System".
Handelt NUR auf dem Alpaca-Demokonto (Paper Trading). Kein echtes Geld.

Strategie Version 1 (einfach erklärbar):
- Bert beobachtet 8 bekannte US-Aktien/ETFs im 15-Minuten-Chart.
- KAUF: Der schnelle Durchschnitt (EMA 9) kreuzt den langsamen (EMA 21) nach oben
  und der RSI liegt unter 70 (Aktie ist nicht "überhitzt").
- VERKAUF: Der schnelle Durchschnitt fällt wieder unter den langsamen,
  oder -1,5 % Verlust (Stop-Loss), oder +3 % Gewinn (Gewinnmitnahme).
- Daytrading: 30 Minuten vor Börsenschluss wird alles verkauft.
- Budget: 10.000 $. Das Demokonto hat 100.000 $, Bert nutzt davon nur 10.000 $.

Läuft automatisch über GitHub Actions (.github/workflows/bert.yml).
Nur Python-Standardbibliothek, keine Installation nötig.
"""
import csv
import json
import math
import os
import re
import time
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
START_BUDGET = 10_000.0          # Startgeld in US-Dollar
SYMBOLS = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "AMZN", "META", "TSLA"]
MAX_POSITIONS = 4                # höchstens 4 Aktien gleichzeitig
POSITION_SIZE = 2_500.0          # so viel Dollar pro Kauf
STOP_LOSS = -0.015               # -1,5 % -> verkaufen
TAKE_PROFIT = 0.03               # +3 %  -> verkaufen
NO_NEW_BUYS_MIN = 90             # keine neuen Käufe in den letzten 90 Minuten
CLOSE_ALL_MIN = 30               # 30 Min vor Schluss alles verkaufen
MOC_CUTOFF_MIN = 12              # Schlusskurs-Orders gehen nur bis 15:50 Uhr New York

API = "https://paper-api.alpaca.markets"
DATA_API = "https://data.alpaca.markets"
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
STATE_FILE = os.path.join(DATA_DIR, "bert_state.json")
TRADES_FILE = os.path.join(DATA_DIR, "bert_trades.csv")
EQUITY_FILE = os.path.join(DATA_DIR, "bert_kontostand.csv")
LOG_FILE = os.path.join(DATA_DIR, "bert_entscheidungen.csv")

TRADES_HEADER = ["zeit", "symbol", "aktion", "stueck", "preis_usd", "gewinn_usd", "gewinn_prozent"]
EQUITY_HEADER = ["zeit", "kontostand_usd", "gewinn_usd", "gewinn_prozent", "offene_positionen"]
LOG_HEADER = ["zeit", "symbol", "aktion", "grund", "preis_usd"]


# ---------------------------------------------------------------- Hilfsfunktionen
def call(method, base, path, params=None, body=None):
    """Ruft die Alpaca-Schnittstelle auf und gibt die Antwort als Python-Objekt zurück."""
    url = base + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"],
        "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"],
        "Content-Type": "application/json",
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            txt = r.read().decode()
            return json.loads(txt) if txt.strip() else None
    except urllib.error.HTTPError as e:
        print(f"API-Fehler {e.code} bei {method} {path}: {e.read().decode(errors='replace')}")
        raise


def parse_ts(s):
    """Liest Zeitangaben wie 2026-11-17T16:00:00.123456789-05:00 oder ...Z."""
    s = s.strip().replace("Z", "+00:00")
    m = re.match(r"^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(\.\d+)?(.*)$", s)
    if not m:
        return datetime.fromisoformat(s)
    base, frac, tz = m.groups()
    frac = (frac or "")[:7]
    return datetime.fromisoformat(base + frac + (tz or "+00:00"))


def iso_z(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def local(dt):
    return dt.astimezone(BERLIN).strftime("%Y-%m-%d %H:%M")


def us_day(dt):
    """Handelstag an der US-Börse (grob, reicht für 'heute gekauft?')."""
    return (dt.astimezone(timezone.utc) - timedelta(hours=5)).date().isoformat()


def append_csv(path, header, row):
    new = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(header)
        w.writerow(row)


def last_csv_row(path):
    if not os.path.exists(path):
        return None
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    return rows[-1] if len(rows) > 1 else None


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def log(now, symbol, action, reason, price=""):
    print(f"[{local(now)}] {symbol}: {action} – {reason}")
    append_csv(LOG_FILE, LOG_HEADER, [local(now), symbol, action, reason,
                                      f"{price:.2f}" if isinstance(price, (int, float)) else price])


# ---------------------------------------------------------------- Indikatoren
def ema(values, n):
    k = 2 / (n + 1)
    out, e = [], None
    for v in values:
        e = v if e is None else v * k + e * (1 - k)
        out.append(e)
    return out


def rsi(values, n=14):
    if len(values) < n + 1:
        return 50.0
    gains, losses = [], []
    for a, b in zip(values[:-1], values[1:]):
        d = b - a
        gains.append(max(d, 0.0))
        losses.append(max(-d, 0.0))
    ag = sum(gains[:n]) / n
    al = sum(losses[:n]) / n
    for g, l in zip(gains[n:], losses[n:]):
        ag = (ag * (n - 1) + g) / n
        al = (al * (n - 1) + l) / n
    if al == 0:
        return 100.0
    return 100 - 100 / (1 + ag / al)


def signal(closes):
    """Gibt ('kaufen' | 'verkaufen' | 'halten', Infos) zurück."""
    if len(closes) < 30:
        return "halten", {"grund": "zu wenig Daten"}
    e9, e21, r = ema(closes, 9), ema(closes, 21), rsi(closes)
    info = {"preis": closes[-1], "ema9": e9[-1], "ema21": e21[-1], "rsi": r}
    crossed_up = any(e9[i - 1] <= e21[i - 1] and e9[i] > e21[i] for i in (-1, -2))
    if e9[-1] > e21[-1] and crossed_up:
        if r < 70:
            info["grund"] = f"Trend dreht nach oben (EMA9 über EMA21), RSI {r:.0f}"
            return "kaufen", info
        info["grund"] = f"Trend dreht nach oben, aber RSI {r:.0f} = überhitzt"
        return "halten", info
    if e9[-1] < e21[-1]:
        info["grund"] = "Trend zeigt nach unten (EMA9 unter EMA21)"
        return "verkaufen", info
    return "halten", info


def get_closes(symbols, now):
    start = iso_z(now - timedelta(days=7))
    bars = {s: [] for s in symbols}
    token = None
    for _ in range(20):
        p = {"symbols": ",".join(symbols), "timeframe": "15Min", "start": start,
             "feed": "iex", "limit": 10000, "adjustment": "raw", "sort": "asc"}
        if token:
            p["page_token"] = token
        r = call("GET", DATA_API, "/v2/stocks/bars", p) or {}
        for s, lst in (r.get("bars") or {}).items():
            bars.setdefault(s, []).extend(lst)
        token = r.get("next_page_token")
        if not token:
            break
    return {s: [float(b["c"]) for b in sorted(lst, key=lambda b: b["t"])] for s, lst in bars.items()}


# ---------------------------------------------------------------- Trades protokollieren
def log_fills(state, now):
    """Holt alle neuen ausgeführten Orders von Alpaca und schreibt sie in bert_trades.csv."""
    after = state.get("last_fill_time") or state["start"]
    after_dt = parse_ts(after) - timedelta(minutes=1)
    seen = set(state.get("seen_fill_ids", []))
    lots = state.setdefault("lots", {})
    fills, token = [], None
    for _ in range(20):
        p = {"direction": "asc", "page_size": 100, "after": iso_z(after_dt)}
        if token:
            p["page_token"] = token
        batch = call("GET", API, "/v2/account/activities/FILL", p) or []
        fills.extend(batch)
        if len(batch) < 100:
            break
        token = batch[-1]["id"]
    seen_list = list(state.get("seen_fill_ids", []))
    groups = []  # Teil-Ausführungen derselben Order zusammenfassen
    for f in fills:
        if f["id"] in seen:
            continue
        seen.add(f["id"])
        seen_list.append(f["id"])
        key = (f.get("order_id") or f["id"], f["side"], f["symbol"])
        if groups and groups[-1]["key"] == key:
            g = groups[-1]
        else:
            g = {"key": key, "qty": 0.0, "cost": 0.0, "t": f["transaction_time"]}
            groups.append(g)
        g["qty"] += float(f["qty"])
        g["cost"] += float(f["qty"]) * float(f["price"])
        state["last_fill_time"] = f["transaction_time"]
    for g in groups:
        _, side, sym = g["key"]
        qty, price = g["qty"], g["cost"] / g["qty"]
        t = parse_ts(g["t"])
        lot = lots.get(sym, {"qty": 0.0, "avg": 0.0})
        if side == "buy":
            total = lot["qty"] + qty
            lot["avg"] = (lot["qty"] * lot["avg"] + qty * price) / total
            lot["qty"] = total
            lots[sym] = lot
            append_csv(TRADES_FILE, TRADES_HEADER, [local(t), sym, "Kauf", f"{qty:g}", f"{price:.2f}", "", ""])
        else:
            avg = lot["avg"] or price
            pnl = (price - avg) * qty
            pct = (price / avg - 1) * 100 if avg else 0.0
            lot["qty"] = lot["qty"] - qty
            if lot["qty"] <= 1e-9:
                lots.pop(sym, None)
                state.get("opened", {}).pop(sym, None)
            else:
                lots[sym] = lot
            append_csv(TRADES_FILE, TRADES_HEADER,
                       [local(t), sym, "Verkauf", f"{qty:g}", f"{price:.2f}", f"{pnl:.2f}", f"{pct:.2f}"])
    state["seen_fill_ids"] = seen_list[-300:]


# ---------------------------------------------------------------- Aktionen
def cancel_open_orders(symbol=None):
    for o in call("GET", API, "/v2/orders", {"status": "open", "limit": 500}) or []:
        if symbol is None or o["symbol"] == symbol:
            try:
                call("DELETE", API, f"/v2/orders/{o['id']}")
            except urllib.error.HTTPError:
                pass


def sell(symbol, now, reason, price):
    cancel_open_orders(symbol)  # z.B. die Schlusskurs-Order
    for attempt in range(2):
        try:
            time.sleep(2)
            call("DELETE", API, f"/v2/positions/{urllib.parse.quote(symbol)}")
            log(now, symbol, "VERKAUF", reason, price)
            return True
        except urllib.error.HTTPError:
            time.sleep(3)
    log(now, symbol, "FEHLER", "Verkauf hat nicht geklappt", price)
    return False


def ensure_close_order(symbol, qty, now, open_orders, state):
    """Sicherheitsnetz: Verkaufsorder zum Schlusskurs (Market-on-Close).
    So wird die Aktie auf jeden Fall zum Börsenschluss verkauft – auch wenn Bert zu spät aufwacht."""
    if any(o["symbol"] == symbol and o["side"] == "sell" for o in open_orders):
        return
    if state.get("moc_fehler_tag") == us_day(now):
        return  # heute schon fehlgeschlagen -> nicht bei jedem Lauf erneut versuchen
    try:
        call("POST", API, "/v2/orders", body={"symbol": symbol, "qty": str(int(qty)), "side": "sell",
                                               "type": "market", "time_in_force": "cls"})
        log(now, symbol, "SICHERUNG", f"Verkaufsorder zum Börsenschluss für {int(qty)} Stück gesetzt")
    except urllib.error.HTTPError:
        state["moc_fehler_tag"] = us_day(now)
        log(now, symbol, "FEHLER", "Schlusskurs-Order hat nicht geklappt")


def buy(symbol, qty, now, reason, price):
    try:
        call("POST", API, "/v2/orders", body={"symbol": symbol, "qty": str(qty), "side": "buy",
                                               "type": "market", "time_in_force": "day"})
        log(now, symbol, "KAUF", f"{qty} Stück – {reason}", price)
        return True
    except urllib.error.HTTPError:
        log(now, symbol, "FEHLER", "Kauf hat nicht geklappt", price)
        return False


def write_equity(state, account, positions, now, market_open):
    pnl = float(account["equity"]) - state["baseline_equity"]
    equity = START_BUDGET + pnl
    row = [local(now), f"{equity:.2f}", f"{pnl:.2f}", f"{pnl / START_BUDGET * 100:.2f}", str(len(positions))]
    last = last_csv_row(EQUITY_FILE)
    if not market_open and last and last[1] == row[1] and last[4] == row[4]:
        return equity  # Börse zu und nichts geändert -> keine doppelte Zeile
    append_csv(EQUITY_FILE, EQUITY_HEADER, row)
    return equity


# ---------------------------------------------------------------- Hauptprogramm
def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    now = datetime.now(timezone.utc)
    state = load_state()
    account = call("GET", API, "/v2/account")
    if "baseline_equity" not in state:
        state["baseline_equity"] = float(account["equity"])
        state["start"] = iso_z(now)
        print(f"Erster Start! Bert startet mit {START_BUDGET:,.0f} $.")
    clock = call("GET", API, "/v2/clock")
    market_open = bool(clock["is_open"])

    log_fills(state, now)
    positions = {p["symbol"]: p for p in call("GET", API, "/v2/positions") or []}
    equity = write_equity(state, account, positions, now, market_open)
    print(f"Berts Kontostand: {equity:,.2f} $ | offene Positionen: {len(positions)}")

    if not market_open:
        print("Börse ist geschlossen – Bert macht Pause.")
        save_state(state)
        return

    minutes_left = (parse_ts(clock["next_close"]) - parse_ts(clock["timestamp"])).total_seconds() / 60
    print(f"Noch {minutes_left:.0f} Minuten bis Börsenschluss.")

    # 1) Kurz vor Schluss: alles verkaufen (Daytrading = nichts über Nacht halten)
    if minutes_left <= CLOSE_ALL_MIN:
        if positions:
            cancel_open_orders()
            call("DELETE", API, "/v2/positions", {"cancel_orders": "true"})
            for sym, p in positions.items():
                log(now, sym, "VERKAUF", "Börsenschluss naht – Daytrading heißt: alles raus",
                    float(p["current_price"]))
        save_state(state)
        return

    opened = state.setdefault("opened", {})
    today = us_day(now)
    closes = get_closes(SYMBOLS + [s for s in positions if s not in SYMBOLS], now)
    sold_now = set()

    # 2) Offene Positionen prüfen
    for sym, p in positions.items():
        price = float(p["current_price"])
        change = float(p["unrealized_plpc"])
        if opened.get(sym) and opened[sym] != today:
            reason = "Position vom Vortag übrig – wird geschlossen"
        elif change <= STOP_LOSS:
            reason = f"Stop-Loss bei {change * 100:.1f} %"
        elif change >= TAKE_PROFIT:
            reason = f"Gewinnmitnahme bei +{change * 100:.1f} %"
        else:
            sig, info = signal(closes.get(sym, []))
            reason = info.get("grund") if sig == "verkaufen" else None
        if reason and sell(sym, now, reason, price):
            sold_now.add(sym)

    # 2b) Sicherheitsnetz für alle offenen Positionen
    if minutes_left > MOC_CUTOFF_MIN:
        open_orders = call("GET", API, "/v2/orders", {"status": "open", "limit": 500}) or []
        for sym, p in positions.items():
            if sym not in sold_now and float(p["qty"]) >= 1:
                ensure_close_order(sym, float(p["qty"]), now, open_orders, state)

    # 3) Neue Käufe suchen
    if minutes_left <= NO_NEW_BUYS_MIN:
        print("Letzte 90 Minuten – keine neuen Käufe mehr.")
        save_state(state)
        return

    pending = {o["symbol"] for o in call("GET", API, "/v2/orders", {"status": "open", "limit": 500}) or []}
    held = set(positions) - sold_now
    invested = sum(float(p["market_value"]) for s, p in positions.items() if s not in sold_now)
    cash = equity - invested

    for sym in SYMBOLS:
        if sym in held or sym in pending or sym in sold_now:
            continue
        sig, info = signal(closes.get(sym, []))
        if sig != "kaufen":
            continue
        price = info["preis"]
        if len(held) >= MAX_POSITIONS:
            log(now, sym, "AUSGELASSEN", "Kaufsignal, aber schon 4 Aktien im Depot", price)
            continue
        qty = math.floor(min(POSITION_SIZE, cash) / price)
        if qty < 1:
            log(now, sym, "AUSGELASSEN", "Kaufsignal, aber nicht genug Geld übrig", price)
            continue
        if buy(sym, qty, now, info["grund"], price):
            held.add(sym)
            cash -= qty * price
            opened[sym] = today

    save_state(state)


if __name__ == "__main__":
    main()
