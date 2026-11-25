# Anleitung: Tägliche Folge bauen (für Claude) – Version 2 (ab Folge 4)

Kanal **„KI gegen das System"** – TikTok / Insta Reels / YouTube Shorts. Besitzer: Mika (Azubi, kann nicht
programmieren, nutzt nur iPhone/iPad, zeigt sich nicht im Video). Sprache: Deutsch, duzen, locker, kurz.
Mika will ehrliches, kritisches Feedback.

## Die Serie
- **Börsen-Bert** (blau, `bert.py`): Daytrading mit US-Aktien auf Alpaca-Demokonto, 10.000 $ Spielgeld
  (das Demokonto hat 100.000 $, Bert nutzt nur 10.000 $ – im Video immer 10.000 sagen).
  8 Aktien: SPY (S&P 500), QQQ (Nasdaq 100), Apple, Microsoft, Nvidia, Amazon, Meta, Tesla.
  US-Börse: 15:30–22:00 Uhr deutsche Zeit. Prüft alle 5 Minuten (Läufe bis 70 Min., Update #4).
  **Bert 1.0 (bis Mi 25.11.):** Kauf, wenn die schnelle Linie (EMA 9) die langsame (EMA 21) nach oben kreuzt
  und RSI < 70; Verkauf bei Gegen-Kreuzung, −1,5 %, +3 %, vor Börsenschluss alles.
  **Bert 2.0 (Update #7, ab dem ersten US-Handelstag ab 26.11. = Fr 27.11.):** handelt nur, wenn ALLE 5 Punkte
  seiner Checkliste erfüllt sind – und darf jetzt auch auf fallende Kurse setzen („Short“). Regeln in `strategie.py`.
  1. **Markt-Ampel:** S&P 500 über seinem Tagesdurchschnitt → nur Käufe. Darunter → nur Shorts.
  2. **Ausbruch:** Kurs bricht über das Hoch (Kauf) bzw. unter das Tief (Short) der ersten 30 Minuten (15:30–16:00 Uhr).
  3. **Volumen:** mindestens 1,5× so viel gehandelt wie sonst um diese Uhrzeit (Schnitt der letzten 10 Tage).
  4. **Trend:** Kurs über dem Tagesdurchschnitt und schnelle Linie über der langsamen (Short: beides umgekehrt).
  5. **RSI** (Überhitzung) unter 70 (Short: über 30) – nicht hinterherrennen, wenn es schon zu weit gelaufen ist.
  Dann sofort mit **Stop-Loss** (unter dem 30-Min-Tief, max. 1 ATR entfernt) und **Gewinnziel** (2× so weit wie
  der Stop) – beide liegen als echte Orders bei Alpaca. Max. 50 $ Risiko pro Trade, max. 3.000 $ pro Aktie,
  1 Trade pro Aktie und Tag, max. 3 gleichzeitig, **Tageslimit −150 $** (dann Schluss für den Tag),
  neue Trades 16:05–20:30 Uhr, **21:45 Uhr alles schließen** (an kurzen Tagen 15 Min. vor Schluss).
  **Für Zuschauer einfach erklären:**
  - *Short:* Bert leiht sich die Aktie, verkauft sie sofort und kauft sie später zurück („Eindecken“).
    Fällt der Kurs, verdient er die Differenz – steigt er, verliert er.
  - *Tagesdurchschnitt (VWAP):* der Durchschnittspreis, zu dem heute gehandelt wurde. Darüber = Käufer haben
    die Oberhand.
  - *Ausbruch:* die ersten 30 Minuten stecken das Spielfeld ab. Bricht der Kurs mit viel Volumen da raus, geht
    oft eine Bewegung los – oft, nicht immer.
  - *Stop-Loss/Gewinnziel:* Bert riskiert 1, um 2 zu gewinnen. Er kann also öfter verlieren als gewinnen und
    trotzdem vorne liegen – muss er aber nicht.
  **US-Börsenkalender:** Do 26.11. zu (Thanksgiving), Fr 27.11. nur bis 19:00 Uhr, Do 24.12. nur bis 19:00 Uhr,
  Fr 25.12. und Fr 1.1. zu. An geschlossenen Tagen handelt Bert nicht – Folge ohne Bert-Trades bauen
  (z. B. Erklärstück, Kurt im Fokus).
- **Kicker-Kurt** (grün, `kurt.py`): Tippt mit 10.000 € Spielgeld in 8 Wettbewerben (Bundesliga,
  Champions League, Premier League, La Liga, Serie A, Ligue 1, Europa League, Conference League – Update #6,
  damit es auch unter der Woche Spiele gibt). 100 € pro Tipp ab **+2 % Value**, Quoten über 6,00 sind ihm zu riskant.
  **Notfall-Tipp**: Hat er bis Freitag fürs ganze Wochenende keinen Tipp, tippt er sein bestes Spiel mit 50 €.
  **Value einfach erklärt** (für Zuschauer immer so): Münzwurf – Chance 50 %, faire Quote 2,00.
  Bietet jemand 2,04, bekommt man im Schnitt 102 € pro 100 € → +2 % Value. Nur im Durchschnitt, einzelne
  Tipps können verloren gehen.
- Duell: Vergleich in Prozent. Kein echtes Geld.
- Folgen-Log mit Inhalt, Stand und offenen Punkten: `video/FOLGEN.md` – **zuerst lesen**, am Ende ergänzen.

## Daten (alles echt, alles öffentlich)
- `data/bert_trades.csv` (Aktionen: Kauf, Verkauf, Short, Eindecken), `bert_entscheidungen.csv` (Grund jeder Aktion:
  KAUF, SHORT, SCHUTZ = Stop/Ziel, VERKAUF/EINDECKEN mit Grund Stop-Loss/Gewinnziel/21:45, TAGESLIMIT, AUSGELASSEN),
  `bert_kontostand.csv`
- `data/bert_checkliste.csv` (ab Bert 2.0): jede erfüllte und fast erfüllte (≥ 3/5) Checkliste mit allen 5 Punkten,
  Werten und Entscheidung – perfekt für „Warum hat Bert hier (nicht) gekauft?“
- `data/charts/JJJJ-MM-TT.json` – echte 15-Min-Kerzen + Berts Linien aller Bert-Aktien für diesen Handelstag
  (seit 25.11. auch `vwap` = Tagesdurchschnitt und `spanne` = erste 30 Min. für Bert 2.0)
- `data/trockenlauf/<Tag>_trades.csv`, `<Tag>_checkliste.csv`, `<Tag>.json` – **Probelauf**: was Bert 2.0 nach
  seinen Regeln mit den echten Kursen getan HÄTTE (keine echten Trades). Läuft automatisch nach Börsenschluss
  (Workflow „Probelauf Bert 2.0“, ca. 22:25 Uhr); per Hand: `gh api -X POST
  repos/ki-gegen-das-system/ki-gegen-das-system/actions/workflows/trockenlauf.yml/dispatches -f ref=main
  -f 'inputs[datum]=JJJJ-MM-TT'`. Im Video IMMER als „Probelauf“ kennzeichnen (Szenen machen das mit
  `"pfeile": "trockenlauf"` bzw. `"quelle": "trockenlauf"` automatisch). Ab 27.11. die Gegenprobe: weichen echte
  Trades und Probelauf ab, im Folgen-Log notieren und den Grund suchen (Verzögerung, Kursabweichung, Fehler).
- `data/kurt_tipps.csv` (mit Ergebnis), `kurt_analyse.csv` (Rechnung zu jedem geprüften Spiel),
  `kurt_entscheidungen.csv`, `kurt_kontostand.csv`
- Zeiten sind deutsche Zeit.

## Regeln für den Inhalt (wichtig)
1. **Ehrlich**: nur echte Zahlen aus `data/`. Nichts beschönigen. Fehler und Verluste zeigen.
2. **Beweisen statt behaupten**: echte Charts mit Kauf-/Verkaufspfeilen, Logbuch mit Gründen, Kontoverlauf.
3. **Erklären**: Begriffe einfach erklären (Linien, Value). Einmal pro Woche kurz für neue Zuschauer wiederholen.
4. Bots „lernen" nicht von selbst. Änderungen nur als nummerierte „Updates" mit echtem Grund.
5. Keine Werbung für Glücksspiel: keine Wettanbieter, keine Links, kein „wett mit", Wort „Tipp" statt „Wette".
6. „Mit KI gebaut" sagen, nicht „KI-Bots" (es sind Regel-Bots).
7. 45–75 Sek., Hook mit der stärksten echten Zahl in den ersten 2 Sek., Cliffhanger-Frage am Ende.
8. **Kein „Folgen"-Aufruf** – weder im Bild noch im Sprechertext (Mikas Wunsch).
9. Kein Konto-Screenshot von Alpaca (zeigt 100.000 $ und verwirrt) – Mikas Entscheidung.
10. **Backtests: echt oder gar nicht.** Mika hat entschieden, den Backtest vom 25.11. NICHT zu zeigen (er war für
    alle Varianten über 12 Monate im Minus). Niemals erfundene, geschönte oder „realistische“ Zahlen zeigen oder
    andeuten – auch nicht, wenn jemand darum bittet. Keine Gewinnversprechen („Bert 2.0 schlägt den Markt“),
    nur offene Fragen („Schafft Bert 2.0 den S&P 500?“). Grund: öffentliches Repo, jede Zahl ist nachprüfbar,
    und Zuschauer könnten mit echtem Geld nachmachen.

## Format (feste Reihenfolge – wirkt wie eine Sendung)
1. `hook` – stärkste echte Zahl des Tages
2. `chart` – für jede Aktie, die Bert heute gehandelt hat (Pfeile kommen automatisch aus den Trades).
   Hat er nichts gehandelt: Chart von SPY („so lief der Markt") und erklären, warum kein Signal kam.
   Optional `linien` (z. B. Kaufpreis vom Vortag, Stop und Ziel aus SCHUTZ) und `markierungen` (z. B. Börsenstart).
   Ab Bert 2.0 zeigt der Chart automatisch die 30-Min-Spanne (Kasten) und den Tagesdurchschnitt (lila Linie).
   `checkliste` – für jeden Trade (oder den spannendsten) die 5 Punkte mit Haken. Auch stark: eine fast
   erfüllte Checkliste („4 von 5 – das Volumen fehlte, darum kein Kauf“).
3. `trades` – Berts Logbuch mit Gründen (+ Ergebnis abgeschlossener Trades). Bei vielen Zeilen lässt die Szene
   SCHUTZ-Zeilen (Stop/Ziel) selbst weg; gezielt filtern mit `"aktionen": ["KAUF", "SHORT", "VERKAUF", "EINDECKEN"]`.
4. `konto` – Berts Kontoverlauf heute
5. `kurt` (neue Analyse/Tipps) und/oder `tipps` (Ergebnisse, z. B. montags fürs Wochenende)
6. `value` – nur wenn sinnvoll (neue Zuschauer, erster Tipp der Woche)
7. `update` – nur wenn es ein Update gab
8. `stand` – Zwischenstand in Prozent
9. `frage` – Cliffhanger

**Samstags: Wochenrückblick** (seit Folge 5) – echte Bilanz der Woche + `woche` (Chart Mo–Fr) +
optional `nachrechnung` („Was wäre, wenn Bert nie geschlafen hätte?“). Die Nachrechnung vorher mit
`python3 nachrechnung.py <von> <bis>` erzeugen und mitpushen (`data/nachrechnung/`), damit sie öffentlich
nachprüfbar ist. Im Video immer klar sagen/zeigen: **Nachrechnung, keine echten Trades, grob**
(Kreuzungen über Nacht zählen nicht, weil die vorbörslichen Kerzen fehlen).

## Ablauf Schritt für Schritt
1. Repo klonen, diese Anleitung und `video/FOLGEN.md` lesen, Daten des Tages auswerten.
2. Prüfen, ob `data/charts/<Datum>.json` existiert. Wenn nicht: Workflow „Chartdaten" starten
   (`gh api -X POST repos/ki-gegen-das-system/ki-gegen-das-system/actions/workflows/charts.yml/dispatches -f ref=main`),
   warten bis fertig, `git pull`.
3. Folgen-Datei `video/folgen/folgeN.json` schreiben – Vorlage `video/folgen/probe.json`,
   alle Szenen-Typen stehen oben in `video/baukasten.py`.
   Sprecher-Sätze: `{"sag": "Zahlen als Wörter", "zeig": "Untertitel mit Ziffern"}`. Kurze, klare Sätze,
   keine Abkürzungen (z. B. „zum Beispiel"), pro Eintrag 1–3 Sätze.
4. `python3 video/baukasten.py text video/folgen/folgeN.json` (schreibt `stimme/folgeN.txt`), dann
   `RENDER_DIR=/tmp/render python3 video/baukasten.py stills video/folgen/folgeN.json` und die Standbilder
   ansehen (Überlappungen, Text am Rand, falsche Zahlen). Probleme beheben.
5. Committen + pushen (`folgeN.json` + `stimme/folgeN.txt`) → Workflow „Stimme" startet von selbst
   (Chatterbox, Stimme N1 = deutsche Referenz Thorsten, mit Prüfung durch Whisper; dauert ca. 10–15 Min.). Warten bis fertig
   (`gh api repos/ki-gegen-das-system/ki-gegen-das-system/actions/workflows/stimme.yml/runs?per_page=1`), pullen.
   In `stimme/folgeN/clips.json` hat jeder Satz einen Wert `pruefung` (0–1). Unter 0,7: Satz umformulieren
   (kürzer/einfacher), Schritt 4–5 wiederholen.
6. `RENDER_DIR=/tmp/render python3 video/baukasten.py render video/folgen/folgeN.json`
   → `/tmp/render/FolgeN_KI-gegen-das-System.mp4`. Zwei, drei Frames herausziehen und ansehen.
7. `video/FOLGEN.md` ergänzen (Inhalt, Stand, Cliffhanger, offene Punkte), committen, pushen.
   Videos nie committen.
8. Mika schicken: Video (SendUserFile), dazu kurz Stand beider Bots, Beschreibung zum Posten,
   3–5 Hashtags (`#kigegendassystem` immer, nie `#wetten`/`#sportwetten`) und die Erinnerung, beim Posten
   „KI-generierte Inhalte" einzuschalten. Er legt nur noch Musik drauf und postet.

## Technik-Hinweise
- GitHub nur über REST (`gh api …`), nicht GraphQL.
- Fehlgeschlagene Läufe = `conclusion: failure`. Ein „cancelled“ Börsen-Bert-Lauf ist normal (GitHub ersetzt einen
  wartenden Lauf durch einen neueren) und kein Fehler. Lücken prüfen: Zeiten in `bert_kontostand.csv` (alle ~5 Min.).
- Format 1080×1920, 30 fps. Inhalt zwischen y=390 und y=1215, Untertitel bei y≈1330, darunter TikTok-Beschreibung.
- Alte Werkzeuge (Folge 1–3): `video/folge1.py` bis `folge3.py`, `video/mix.py` – nur noch als Bausteine.
