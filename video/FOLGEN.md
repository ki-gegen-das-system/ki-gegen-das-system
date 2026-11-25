# Folgen-Log

| Folge | Datum (Daten von) | Inhalt | Stand am Ende | Cliffhanger |
|---|---|---|---|---|
| 1 | 17.11. | Intro: „Ich kann nicht programmieren" → 2 Bots, je 10.000. Kurt lässt Bayern–Köln aus (Quote 27, zu riskant). Bert startet 48 Min. vor Schluss, kauft nichts. | Bert 10.000 $ · Kurt 10.000 € | Folge 2: Berts erster Trading-Tag |
| 2 | 18.11. | Erklärung: Blau (Ø ~2 Std.) kreuzt Gelb (Ø ~5 Std.) = Kauf, 3 Notbremsen (−1,5 %, +3 %, Börsenschluss). Bert kauft 6 Tesla à 384,71 $. Fehler: Schluss verschlafen (GitHub weckte nur stündlich). **Update #1**: Verkaufsorder zum Börsenschluss. Kurt: 0 Tipps. | Bert 9.987,52 $ (−0,12 %) · Kurt 10.000 € | Verkauft Bert Tesla mit Gewinn? |
| 3 | 19.11. | 15:24 Konto +41,81 $, aber Bert schläft. 16:35 Verkauf 6 Tesla à 379,52 $ (gekauft 384,71 $) → −31,14 $ (−1,35 %). Danach kein Kaufsignal. Problem: wacht nur ~1×/Std. **Update #2**: Projekt öffentlich → alles live nachprüfbar, Bert prüft ab 20.11. alle 5 Min. Kurt: 6 Samstagsspiele geprüft, 0 Tipps (5× Value unter 3 %, Paderborn Quote 10,50 zu riskant). Neue Stimme C. | Bert 9.968,85 $ (−0,31 %) · Kurt 10.000 € | Bert zum ersten Mal den ganzen Tag wach – holt er die 31 $ zurück? |
| 4 | 20.11. | Neuer Look, neue Stimme N1, echte Charts. Crash-Tag: Nvidia −12 %, US-Markt (SPY) −3,2 %. Bert: blaue Linie den ganzen Tag unter gelb → 0 Trades, Konto −0,06 $ (schon vor Börsenstart). Ehrliche Fehler: erste Stunde verpasst (GitHub weckte erst 16:29), letzte halbe Stunde (21:32–22:00) nicht gespeichert (Speicher-Konflikt zweier Läufe). Kurt: 36 Spiele, 1 Tipp Man United bei Liverpool (Quote 4,70, faire Chance 23 %, +6,2 % Value, 100 €). Value per Münzwurf erklärt, **Update #3** gezeigt. | Bert 9.968,79 $ (−0,31 %) · Kurt 10.000 € (±0 %, 100 € offen) | Trifft Kurts erster Tipp (So 17:30)? |
| 5 | 21.11. (Wochenrückblick, Daten 16.–21.11.) | Erster Wochenrückblick (Sa). Hook −31 $. Berts einziger Trade: Mi 18:28 Kauf 6 Tesla à 384,71 $ → Börsenschluss verschlafen → Do 16:35 Verkauf à 379,52 $ = −31,14 $ (−1,35 %). Nachrechnung „Was, wenn Bert nie schläft?“ (`nachrechnung.py`, Mi–Fr, KEINE echten Trades, Kreuzungen über Nacht nicht gezählt): 4 Käufe (QQQ, TSLA, MSFT, SPY, alle Mi), alle im Minus, −37,51 $. Grund: SPY Mo–Fr −7,87 %, Bert verdient nur bei steigenden Kursen (Wochen-Chart SPY). Wochenanalyse: keine Regeländerung (Mikas Entscheidung), ab Mo Update #4. Kurt: 48 Spiele in 5 Ligen, 15× Value – jedes Mal beim Außenseiter (14× Quote über 6 = zu riskant), 1 Tipp Man United bei Liverpool (4,70). Neue Szenen `woche` + `nachrechnung`. 71,9 Sek. | Bert 9.968,79 $ (−0,31 %) · Kurt 10.000 € (±0 %, 100 € offen) | So 17:30 trifft Kurt? Mo: Bert endlich den ganzen Tag wach? Wer gewinnt Woche 2? |
| 6 | 23.11. | Hook +20,53 $ (Berts erster Gewinn) vs. Kurts erster Tipp −100 €. Bert 15:31 Kaufsignal Apple (frische Kreuzung, RSI 57), gekauft 6 à 348,13 $ + 1 à 346,30 $ (Order in 2 Teilen). Andere 7 Aktien: Blau lag schon vorbörslich über Gelb → keine frische Kreuzung. Blau den ganzen Tag über Gelb → gehalten, 21:34 Verkauf 7 à 350,80 $ (Börsenschluss-Regel) = +20,53 $ (+0,84 %). Ehrlicher Fehler: Schlusskurs-Sicherung (Update #1) von Alpaca abgelehnt („potential wash trade“, weil der Kauf noch nicht ganz ausgeführt war) – kein Schaden, Bert war wach. 16:40 kurz über 10.000 $ (10.001,42). **Update #4 geprüft**: 15:31 wach („wartet auf den Start“ im Log) ✓, nichts verloren ✓, aber 1 Lücke 17:45–18:03 (18 Min., GitHub-Start zu spät; nichts verpasst). Kurt: Liverpool – Man United 4:0 → Tipp verloren −100 €; Value nur im Schnitt (faire Chance war 23 %). Satz „andere 7 Aktien: Kreuzung schon vorbörslich“ wegen Länge gestrichen. 72,2 Sek. | Bert 9.989,32 $ (−0,11 %) · Kurt 9.900 € (−1,00 %) → Bert führt | Bert fehlen 10,68 $ bis zur Null – schafft er das morgen? |
| 7 | 24.11. | Hook −118,88 $ = Berts schlechtester Tag: 9 Trades (Kauf→Verkauf), 8 im Minus, nur Apple +0,95 $. Linien kurz für neue Zuschauer erklärt (Blau Ø ~2 Std., Gelb Ø ~5 Std.; Kreuzung hoch = Kauf, runter = Verkauf). Meta-Chart: Linien kreuzen ständig → 3× Kauf, 3× Verkauf (einmal nur 5 Min. dazwischen: 15:51 Kauf, 15:56 Verkauf), zusammen −43,66 $. Tesla: größter Verlust, Kauf 15:36 à 389,40 $, Notbremse −1,5 %, aber Bert prüft nur alle 5 Min. → Verkauf 16:11 bei −1,70 % = −39,74 $. Neue Szene `bilanz` (alle 9 Trades). Grund: Markt seitwärts (SPY +0,5 %) → viele Fehlsignale. Technik: keine Lücke, kein fehlgeschlagener Lauf, alle 7 Sicherungen gesetzt (2 Käufe waren vor der Sicherung schon wieder verkauft). Kurt: bis Freitag kein Spiel in seinen 5 Ligen → kein Tipp. 74,7 Sek. | Bert 9.870,37 $ (−1,30 %) · Kurt 9.900 € (−1,00 %) → Kurt führt | Nur Pech an einem ruhigen Tag – oder sind Berts Regeln das Problem? |

## Updates (Übersicht)
- **Update #1** (18.11.): Bert stellt nach jedem Kauf eine Verkaufsorder zum Börsenschluss.
- **Update #2** (19.11.): Repository öffentlich, Bert prüft alle 5 Minuten.
- **Update #3** (20.11., Kurt): 5 Ligen statt nur Bundesliga, Value-Grenze 2 % statt 3 %, Notfall-Tipp (50 €),
  wenn er bis Freitag fürs Wochenende nichts findet. Mit Mika abgesprochen – in der Wochenanalyse am 21.11.
  nicht erneut vorschlagen, erst nach einer Woche Daten bewerten.
- **Neues Video-Format** (ab Folge 4, mit Mika abgesprochen): echte Charts, Untertitel, Terminal-Look,
  Transparenz-Zeile, neue Stimme N1 (Chatterbox mit echter deutscher Stimme von Thorsten Müller als Vorlage, CC0 – von Mika am 20.11. ausgewählt; X1 klang zu englisch). Kein Alpaca-Screenshot.
- **Update #4** (20.11. abends, Bert, mit Mikas OK): Grund = die zwei Fehler aus Folge 4.
  (1) Startet ein Lauf vor Börsenbeginn, wartet Bert auf den Start statt Pause zu machen.
  (2) Jeder Lauf bleibt bis zu 70 statt 58 Minuten wach → die nur ungefähr stündlichen GitHub-Starts reihen sich lückenlos aneinander.
  (3) Sicheres Speichern: immer vom neuesten Stand starten, 5 Versuche, Logbücher werden zusammengeführt statt abzubrechen.
  Getestet: nachgestellter Konflikt vom 20.11. löst sich jetzt, Testlauf auf GitHub grün. Erster echter Einsatz: Mo 23.11.

- **Update #5** (24.11. abends, Bert, mit Mikas OK): Grund = abgelehnte Schlusskurs-Sicherung in Folge 6 (23.11.).
  (1) Ist Berts Kauf noch nicht ganz ausgeführt, wartet er mit der Sicherung bis zum nächsten Check (sonst lehnt Alpaca sie als „Wash Trade“ ab).
  (2) Klappt die Sicherung trotzdem nicht, versucht er es bei jedem Check erneut (vorher: den ganzen Tag keine Sicherung mehr). „FEHLER“ steht dann nur einmal pro Tag im Logbuch.
  Getestet: 23.11. mit nachgestelltem Alpaca durchgespielt (Kauf in zwei Teilen → Sicherung erst beim nächsten Check; 2× abgelehnt → 3. Versuch klappt). Erster echter Einsatz: Mi 25.11.
- **Update #6** (25.11. abends, Kurt, Mikas Wunsch „Content unter der Woche"): Champions League, Europa League und
  Conference League dazu (8 Wettbewerbe). Erster Lauf 25.11. ~20 Uhr: 43 Europapokal-Spiele geprüft (7× CL heute 21:00,
  18× EL + 18× ECL am Do 26.11.), **kein Tipp** (bester Value +1,7 %). Neuer Tipp am Wochenende: Rayo Vallecano bei
  Real Betis (La Liga), Quote 6,00, Value +9,1 % – wieder ein Außenseiter. API-Abfragen: 458 von 500 übrig.
- **Backtest 25.11.** (`backtest.py`, Ergebnisse in `data/backtest/<Zeitraum>/`): Bert 1.0 gegen 4 Varianten von
  „Bert 2.0" (Checkliste: Markt-Ampel SPY über VWAP, Ausbruch über das 30-Min-Hoch, relatives Volumen ≥ 1,5,
  Kurs über VWAP + Blau über Gelb, RSI < 70; Stop als echte Order, Ziel 2× Risiko, 50 $ Risiko/Trade,
  1 Trade/Aktie/Tag, Tageslimit −150 $). 12 Monate echte 5-Min-Kerzen, Einstellungen vorher festgelegt.
  Ergebnis: **alle Varianten im Minus**. Bert 1.0: −378,78 $ (max. Rückgang bis −847 $). Bert 2.0 nur Kauf, 8 Aktien:
  −85,63 $ (max. Rückgang ~−107 $). Kauf+Short 8: Hälfte 1 +83,76 $, Hälfte 2 −167,27 $ (= Zufall). 20 Aktien: schlechter.
  SPY einfach halten: ca. +8 %. **Mikas Entscheidung steht noch aus – im Video nicht als beschlossen darstellen.**
- **Wochenanalyse 21.11.** (mit Mika): bei beiden Bots **nichts geändert**. Bert: erst 1 echter Trade, Update #4 läuft erst ab 23.11. – erst eine Woche ohne Pannen abwarten. Kurt: Update #3 erst seit 20.11. – nach einer Woche Daten bewerten.

## Für die nächsten Folgen merken
- Ab Folge 4: kein „FOLGEN →"-Button und kein „Folgen!" im Sprechertext mehr.
- Woche 2: Value-Szene (Münzwurf) noch nicht gezeigt – beim ersten neuen Kurt-Tipp der Woche einbauen.
- Folge 8 (Mi 25.11.): Cliffhanger aus Folge 7 beantworten (Pech oder Regeln?). Ehrlich bleiben: Bert „lernt“ nicht – an Seitwärts-Tagen wird er wieder hin und her handeln. Ob man das ändert (z. B. Mindestabstand zwischen Kauf und Verkauf), ist eine Regeländerung → nur mit Mikas OK, frühestens in der Wochenanalyse am Sa 28.11. vorschlagen.
- Wochenrückblick 28.11.: Zahl der „Hin-und-her“-Trades (Kauf und Verkauf innerhalb von ≤ 15 Min.) zählen – am 24.11.: Meta 15:51–15:56 (−6,10 $), Microsoft 17:32–17:37 (−1,83 $), Meta 19:05–19:20 (−12,72 $).
- **Update #5** in der nächsten Folge nach dem 24.11. (Daten 25.11.) mit Szene `update` zeigen (Grund: abgelehnte Sicherung aus Folge 6). Vorher prüfen: Steht nach jedem Kauf eine „SICHERUNG“ im Logbuch? Kein „FEHLER“ oder nur einer mit späterer SICHERUNG?
- Nächster Wochenrückblick (Sa 28.11.): `python3 nachrechnung.py 2026-11-23 2026-11-27` und mit Berts echten Trades vergleichen. Ist Bert dank Update #4 durchgehend wach, sollten echte und nachgerechnete Käufe fast gleich sein – guter Beweis, ob das Update wirkt.
- Kurt: bisher kam Value **nur** bei Außenseitern (15 von 15). Erster Tipp (Außenseiter Man United, 4,70) verloren 0:4. Beobachten, ob das so bleibt – dann ist sein Value wahrscheinlich oft eine Täuschung (bei Außenseitern ist die faire Chance am schwersten zu schätzen). In der nächsten Wochenanalyse prüfen.

## Offene Punkte (Stand 24.11.)
- ~~**23.11. – Schlusskurs-Sicherung abgelehnt**~~ (Kauf war noch nicht ganz ausgeführt → Alpaca: „potential wash trade“, danach den ganzen Tag keine Sicherung) → mit **Update #5** behoben (ab 25.11. prüfen). Am 24.11. (noch alter Code) keine Ablehnung: 9 Käufe, 7 Sicherungen gesetzt, die 2 anderen Käufe waren beim nächsten Check schon wieder verkauft.
- **24.11.**: Konto-Szene zeigt „heute −118,95 $“, Hook/Bilanz −118,88 $ (Summe der Trades). Differenz 0,07 $ = Konto über Nacht 23.→24.11. ohne Trade (wie am 19.→20.11., Ursache unklar). Im Video nicht erklärt.
- **24.11.**: Tesla-Stop-Loss bei −1,70 % statt −1,5 % (Bert prüft nur alle 5 Min.). Kein Fehler im Code, aber die Notbremse ist dadurch nicht exakt. Möglicher Fix (nur mit Mikas OK!): echte Stop-Order bei Alpaca direkt nach dem Kauf.
- Update #4 am 23.11. geprüft: Start pünktlich 15:31, nichts verloren (doppelte Zeilen 19:08/21:19 durch überlappende Läufe, harmlos). Aber 1 Lücke 17:45–18:03 (Lauf endete 17:45, nächster GitHub-Start erst 18:03). Beobachten – wenn das öfter passiert, evtl. Läufe noch länger wach lassen (nur mit Mikas OK).
- ~~Bert verpasst die erste Börsenstunde~~ und ~~Speicher-Konflikt (Log 21:32–22:00 am 20.11. verloren)~~ → mit Update #4 behoben (am 23.11. geprüft, siehe oben).
  Die verlorenen Zeilen vom 20.11. wurden nicht nachgetragen (nichts passiert: 9.968,79 $, 0 Positionen – steht im Actions-Log), damit Video und Daten zusammenpassen.
- Chartdaten speichert Bert um 22:02 zu früh (erst ab 22:05 erlaubt) → „Chartdaten" täglich per Hand starten (macht die tägliche Routine, kein Problem).
- Kurt prüft jedes Spiel nur einmal: Bundesliga-Spiele vom Wochenende waren schon am 19.11. (alte 3-%-Regel) geprüft, daher steht am 20.11. „4 Ligen". Alle lagen unter 2 %, also kein Tipp verpasst.
- Konto über Nacht 19.→20.11. −0,06 $ ohne Trade (Ursache unklar, evtl. Gebühr/Rundung bei Alpaca).
- Nachrechnung 21.11.: Meine erste schnelle Version (17 Trades, −240 $, an Mika geschickt) war zu grob – sie hat Kreuzungen über Nacht gezählt. Saubere Version (im Video): Mi–Fr 4 Käufe, alle im Minus, −37,51 $; Mo–Fr wären es 8 Käufe, alle im Minus, −93,22 $. Mit Kreuzungen über Nacht (unsicher) wären es Mi–Fr bis zu 11 Käufe / −171 $.
- Hinweis zu Folge 4 („bei allen 8 Aktien nicht kaufen“): stimmt für die Zeit, in der Bert wach war. Apple lag zum Börsenstart am 20.11. kurz über Gelb (Kreuzung vorbörslich) – ob das ein Kauf gewesen wäre, lässt sich nicht sicher sagen. Nicht nachträglich korrigiert.
