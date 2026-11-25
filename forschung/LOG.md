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
