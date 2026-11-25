# Forschung Bert 3.0 – Protokoll

Auftrag (Mika, 25.11.2026): gründlich nach einer Daytrading-Strategie suchen, die in den Backtests Gewinn macht,
mit möglichst vielen Trades pro Tag (ideal ~15), gern mehr Aktien (20+), gern „den ganzen Tag“.

## Vorab festgelegte Regeln (vor dem Blick auf die Ergebnisse)
- Daten: echte 5-Min-Kerzen (SIP, alle US-Börsen) 2018–2026, 48 Aktien/ETFs; dazu Scanner über alle US-Aktien.
- **Entwicklung nur 2018–2023.** Der Zeitraum **2024-01-01 bis 2026-11-25 bleibt gesperrt** und wird erst ganz am
  Ende EINMAL mit den wenigen Kandidaten getestet (sonst passt man die Strategie unbemerkt an die Vergangenheit an).
- Kosten je Kauf/Verkauf: ETFs 1 bp, große Aktien 2 bp, wilde Aktien 3 bp; Scanner-Aktien 1 Cent/Aktie + 2 bp;
  Krypto 0,25 % Alpaca-Gebühr + 2 bp. (1 bp = 0,01 %)
- **Bestanden** heißt: (1) 2018–2023 nach Kosten im Plus, Sharpe ≥ 0,7, in mindestens 5 von 6 Jahren im Plus;
  (2) auch mit doppelten Kosten im Plus; (3) Nachbar-Einstellungen ebenfalls im Plus; (4) 2024–2026 im Plus;
  (5) live machbar (Alpaca-Gratisdaten IEX, GitHub alle 5 Min.). Ziel: möglichst ≥ 5 Trades/Tag.
- Jede getestete Variante wird hier mitgezählt (je mehr Versuche, desto größer die Glücks-Gefahr).

## Verlauf
### 25.11. abends – Runde 1 (48 Aktien/ETFs, 5-Min-Kerzen, nur 2018–2023)
Netto = pro Trade nach Kosten. Summe = Gewinn/Verlust auf 10.000 $ über 6 Jahre (ohne Zinseszins).
| Strategie | Trades/Tag | netto/Trade | Sharpe | Jahre im Plus | Urteil |
|---|---|---|---|---|---|
| Nur über Nacht / nur tagsüber halten (SPY, QQQ) | 1 | −0,1 … +1,9 bp | 0,0–0,3 | – | nur Vergleich |
| Letzte halbe Stunde (Gao 2018), 48 Werte | 46 | −4,3 bp | −2,4 | 0/6 | ✗ |
| ORB-Regel QQQ (Zarattini & Aziz 2023) | 1 | +1,2 bp | 0,38 | 4/6 | ✗ (SPY/ETFs/Aktien negativ) |
| ORB fester Korb, Stop 0,1–0,5 ATR, Top 5/20 | 5–12 | −14 … +1,6 bp | −6 … +0,5 | ≤ 4/6 | ✗ |
| RSI(2)-Rückkehr zum Mittelwert (ETFs/Aktien) | 20–135 | −1 … −4 bp | negativ | ≤ 1/6 | ✗ (Kosten fressen alles) |
| Gap schließen / Gap folgen | 4–12 | −16 … +12 bp | −1 … +0,4 | ≤ 3/6 | ✗ (nur 2020 gut) |
| Querschnitt Gewinner/Verlierer seit Eröffnung | 6–10 | −9 … −1 bp | negativ | ≤ 2/6 | ✗ |
| Krypto 24/7 Rauschzone (0,25 % Gebühr) | 10–16 | −52 bp | −15 | 0/3 | ✗ (Gebühr; auch ohne Gebühr ~0) |
| Maschinelles Lernen (Gradient Boosting, 30 Min.), Test 2020–23 | 31–165 | −2,4 … +0,6 bp | ≤ 0,23 | ≤ 2/4 | ✗ |
| **Rauschzonen-Momentum (Zarattini/Aziz/Barbon 2024), SPY+QQQ** | 1,9 | +3,1 bp | **1,00** | 5/6 | **Kandidat** (Kosten x2: Sharpe 0,36) |
| **Rauschzonen-Momentum, Berts 8 Werte** | 7,7 | +2,6 bp | **0,98** | 5/6 (2019 ±0) | **Kandidat**, aber Kosten x2 → negativ |
| Rauschzonen-Momentum, 20 / 48 Werte | 19–47 | −0,4 … −1,9 bp | ≤ 0 | – | ✗ (bei Value-/Bankaktien wirkt es nicht) |
Rauschzone je Wert (Diagnose, NICHT zur Auswahl genutzt): gut bei Tesla, QQQ, SPY, Amazon, XLK, SMH, AMD;
schlecht bei Banken, Öl, Konsum, Pharma (JPM, CVX, WMT, LLY …), IWM, DIA.
Robustheit Rauschzone (Nachbarn: Rückblick 10/20, Takt 20/60 Min., Start 10:30, ohne VWAP-Stop, Hebel 2):
SPY+QQQ Sharpe 0,70–1,07, Berts 8: 0,48–1,18 – alle Nachbarn im Plus → kein Einzeltreffer.
Vor-/nachbörslich (SPY/QQQ 2025–26): vorbörslich nur 2–4 % des Volumens, 5-Min-Schwankung 4–6 bp statt 9–12 bp
→ „den ganzen Tag handeln“ bringt bei Aktien kaum etwas.
Bisher geprüfte Varianten: ca. 130.
