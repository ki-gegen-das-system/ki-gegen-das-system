# Bert 3.0 – Ergebnis der Strategie-Forschung (25.11.2026)

**Frage (Mika):** Gibt es eine Daytrading-Strategie, die in den Backtests Gewinn macht – mit vielen Trades
(ideal ~15 am Tag), gern mit 20+ Aktien und „den ganzen Tag“?

**Kurzantwort: Nein – nicht beides zusammen.** Rund 150 Varianten mit echten Kursen 2018–2026 (48 Aktien/ETFs,
5-Min-Kerzen; dazu ein Scanner über alle US-Aktien) und realistischen Kosten. Viele Trades heißt viele Kosten,
und die fressen jeden kleinen Vorteil auf. Einzige Strategie mit Plus im ungesehenen Endtest:
**Rauschzonen-Momentum auf SPY + QQQ** – aber schwach (+1.616 $ auf 10.000 $ in fast 3 Jahren, SPY kaufen und
halten: +51 %) und nur ~2 Trades pro Tag.

## Vorgehen (ehrlich, damit wir uns nicht selbst reinlegen)
- Entwickelt nur mit 2018–2023. 2024–2026 war gesperrt und wurde ganz am Ende EINMAL für die Kandidaten getestet.
- Kosten je Kauf/Verkauf: ETFs 0,01 %, große Aktien 0,02 %, wilde Aktien 0,03 %, kleinere Aktien 1 Cent + 0,02 %,
  Krypto 0,25 % Gebühr. Eher vorsichtig gerechnet.
- Alle Regeln, Zahlen und der Code liegen in `forschung/` (LOG.md = vollständiges Protokoll).

## Was durchgefallen ist (2018–2023, nach Kosten)
Schlussstunde (Gao 2018), Opening Range Breakout (fester Korb und QQQ-Regel), Rückkehr zum Mittelwert (RSI 2),
Gaps, Gewinner/Verlierer-Querschnitt, Krypto 24/7 (Gebühr frisst alles), Machine Learning (Gradient Boosting),
**Scanner „Stocks in Play“** (berühmte Studie 2024: sieht nur mit winzigen Stops und ohne Kosten gut aus –
mit realistischen Kosten −22 bis +1 bp pro Trade; außerdem würden die Gratis-Echtzeitdaten nur 8 von 20
gleichen Aktien wählen).

## Was bestanden hat – und was davon übrig blieb
Rauschzonen-Momentum (Zarattini/Aziz/Barbon 2024): Kauf/Short, wenn der Kurs aus seiner üblichen
Tagesschwankung seit Eröffnung ausbricht; Prüfung alle 30 Min.; Stop zurück in der Zone bzw. am
Tagesdurchschnitt; zum Börsenschluss alles zu.
| | 2018–2023 | Endtest 2024–2026 | Trades/Tag | Tage ohne Trade |
|---|---|---|---|---|
| SPY + QQQ | +9.667 $, Sharpe 1,0 | **+1.616 $**, Sharpe 0,3 (2025/26 ≈ 0) | ~2 | 30 % |
| Berts 8 Werte | +5.311 $, Sharpe 1,0 | **−2.085 $**, Sharpe −0,8 | ~8 | 3 % |

## Ganzer Tag?
Bei Alpaca gibt es Aktien vor- und nachbörslich (ab 10 Uhr / bis 2 Uhr), aber dort laufen nur 2–4 % des
Volumens und die Kurse bewegen sich kaum (4–6 statt 9–12 bp pro 5 Min.). Krypto läuft 24/7, aber 0,25 %
Gebühr pro Trade macht jede getestete Krypto-Strategie kaputt.

## Entscheidung für Mika – gefallen am 25.11.: Variante A als ZWEITER Bot „Momentum-Max“, Bert 2.0 bleibt
- **A – Action:** Bert 3.0 = Rauschzone auf Berts 8 Werten. ~8 Trades/Tag, fast jeden Tag was los, gut im
  Video zu zeigen (Rauschband im Chart). Aber: im Endtest leicht im Minus (≈ −7 % pro Jahr). Ehrlich als
  Live-Test erzählen: „Funktioniert die Studie noch?“
- **B – Beste Chance:** Bert 3.0 = Rauschzone nur auf SPY + QQQ. Einzige Strategie mit Plus im Endtest,
  aber ~2 Trades/Tag und an 30 % der Tage nichts.
- **C:** Bert 2.0 so lassen (läuft ab 27.11.; Backtest ebenfalls leicht im Minus, ~1 Trade/Tag).
Umbau erst nach Mikas OK (Regel: Bot-Änderungen nur mit OK).
