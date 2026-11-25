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
### 25.11. spät – Runde 3: Scanner „Stocks in Play“ (alle US-Aktien, 2,45 Mio. Kandidaten-Tage, 2018–2023)
| Strategie | Trades/Tag | netto/Trade | Sharpe | Urteil |
|---|---|---|---|---|
| ORB Stocks in Play (Zarattini/Barbon/Aziz 2024), Top 20, Stop 0,1 ATR, vorsichtige Kerzen-Annahme | 16 | −22 bp | −8 | ✗ |
| … gleiche Regel, günstigste Annahme (Stop in der Einstiegskerze zählt nicht) | 16 | +1,3 bp | 0,30 | ✗ (2 von 6 Jahren Minus) |
| … günstigste Annahme UND ohne Kosten | 16 | +12,9 bp | 3,28 | so sieht es in der Studie aus |
| ORB Stocks in Play, Top 5/10/20, Stop 0,05–1,0 ATR | 4–16 | −30 … +1,7 bp | ≤ 0 | ✗ |
| Trend auf Stocks in Play ab 10:00 mit VWAP-Stop | 10 | −9 bp | −1,2 | ✗ |
**Erkenntnis:** Die Scanner-Strategie lebt von winzigen Stops und fast null Kosten. Mit realistischen Kosten
(1 Cent/Aktie + 2 bp je Seite – bei 10–50-$-Aktien am Morgen eher noch zu wenig) bleibt nichts übrig.
Live-Problem zusätzlich: Mit den Gratis-Echtzeitdaten (IEX) wären im Schnitt nur 7,8 der Top 20 dieselben
Aktien wie mit allen Börsen (SIP) – geprüft für die letzten 120 Handelstage.
Bisher geprüfte Varianten: ca. 150.

### Festgelegte Kandidaten für den Endtest 2024–2026 (vor dem Endtest notiert)
- K1: Rauschzonen-Momentum SPY + QQQ, Parameter wie in der Studie (Rückblick 14 Tage, Prüfung alle 30 Min. ab
  10:00 New York, Stop = Rauschgrenze/VWAP, 2 % Ziel-Tagesschwankung, max. 4x Hebel, Schluss zum Börsenende).
- K2: dieselbe Regel auf Berts 8 Werten (SPY, QQQ, Apple, Microsoft, Nvidia, Amazon, Meta, Tesla).

### ENDTEST 2024-01-01 bis 2026-11-24 (einmalig, nichts danach angepasst)
| Kandidat | Trades/Tag | netto/Trade | Sharpe | 2024 | 2025 | 2026 | Summe auf 10.000 $ | Kosten x2 |
|---|---|---|---|---|---|---|---|---|
| K1 Rauschzone SPY+QQQ | 1,9 | +1,4 bp | 0,31 | +1.875 $ | −47 $ | −212 $ | **+1.616 $** | −1.798 $ |
| K2 Rauschzone Berts 8 | 8,0 | −2,6 bp | −0,81 | −363 $ | −1.306 $ | −416 $ | **−2.085 $** | −5.928 $ |
| Vergleich: SPY kaufen und halten | – | – | – | +23,3 % | +16,4 % | +5,4 % | +51,2 % | – |
Entwicklung 2018–2023 zum Vergleich: K1 +9.667 $ (Sharpe 1,00), K2 +5.311 $ (Sharpe 0,98).

**Ergebnis:** K2 (viele Trades) fällt im Endtest durch. K1 bleibt knapp im Plus (Kriterium 4 erfüllt), aber
deutlich schwächer als 2018–2023, 2025/2026 ungefähr null, mit doppelten Kosten im Minus. Die Studie wurde im
Mai 2024 veröffentlicht – typisch: Bekannte Effekte werden danach schwächer (McLean & Pontiff 2016).
**Keine getestete Strategie schafft viele Trades UND Gewinn.** Je mehr Trades, desto mehr fressen die Kosten.
Insgesamt geprüfte Varianten: ca. 150 (+ 2 Endtests).
