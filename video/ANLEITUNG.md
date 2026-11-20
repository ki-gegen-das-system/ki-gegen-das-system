# Anleitung: Tägliche Folge bauen (für Claude) – Version 2 (ab Folge 4)

Kanal **„KI gegen das System"** – TikTok / Insta Reels / YouTube Shorts. Besitzer: Mika (Azubi, kann nicht
programmieren, nutzt nur iPhone/iPad, zeigt sich nicht im Video). Sprache: Deutsch, duzen, locker, kurz.
Mika will ehrliches, kritisches Feedback.

## Die Serie
- **Börsen-Bert** (blau, `bert.py`): Daytrading mit US-Aktien auf Alpaca-Demokonto, 10.000 $ Spielgeld
  (das Demokonto hat 100.000 $, Bert nutzt nur 10.000 $ – im Video immer 10.000 sagen).
  Regeln: Kauf, wenn die schnelle Linie (EMA 9, Ø ~2 Std.) die langsame (EMA 21, Ø ~5 Std.) nach oben kreuzt
  und RSI < 70. Verkauf bei Gegen-Kreuzung, −1,5 % (Stop-Loss), +3 % (Gewinnmitnahme), vor Börsenschluss alles.
  Prüft seit 20.11. alle 5 Minuten. US-Börse: 15:30–22:00 Uhr deutsche Zeit.
  Seit Update #4 (ab 23.11.): wartet vor Börsenbeginn auf den Start, jeder Lauf bis zu 70 Min., sicheres Speichern.
- **Kicker-Kurt** (grün, `kurt.py`): Tippt mit 10.000 € Spielgeld in 5 Ligen (Bundesliga, Premier League,
  La Liga, Serie A, Ligue 1). 100 € pro Tipp ab **+2 % Value**, Quoten über 6,00 sind ihm zu riskant.
  **Notfall-Tipp**: Hat er bis Freitag fürs ganze Wochenende keinen Tipp, tippt er sein bestes Spiel mit 50 €.
  **Value einfach erklärt** (für Zuschauer immer so): Münzwurf – Chance 50 %, faire Quote 2,00.
  Bietet jemand 2,04, bekommt man im Schnitt 102 € pro 100 € → +2 % Value. Nur im Durchschnitt, einzelne
  Tipps können verloren gehen.
- Duell: Vergleich in Prozent. Kein echtes Geld.
- Folgen-Log mit Inhalt, Stand und offenen Punkten: `video/FOLGEN.md` – **zuerst lesen**, am Ende ergänzen.

## Daten (alles echt, alles öffentlich)
- `data/bert_trades.csv`, `bert_entscheidungen.csv` (Grund jeder Aktion), `bert_kontostand.csv`
- `data/charts/JJJJ-MM-TT.json` – echte 15-Min-Kerzen + Berts Linien aller Bert-Aktien für diesen Handelstag
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

## Format (feste Reihenfolge – wirkt wie eine Sendung)
1. `hook` – stärkste echte Zahl des Tages
2. `chart` – für jede Aktie, die Bert heute gehandelt hat (Pfeile kommen automatisch aus den Trades).
   Hat er nichts gehandelt: Chart von SPY („so lief der Markt") und erklären, warum kein Signal kam.
   Optional `linien` (z. B. Kaufpreis vom Vortag) und `markierungen` (z. B. Börsenstart).
3. `trades` – Berts Logbuch mit Gründen (+ Ergebnis abgeschlossener Trades)
4. `konto` – Berts Kontoverlauf heute
5. `kurt` (neue Analyse/Tipps) und/oder `tipps` (Ergebnisse, z. B. montags fürs Wochenende)
6. `value` – nur wenn sinnvoll (neue Zuschauer, erster Tipp der Woche)
7. `update` – nur wenn es ein Update gab
8. `stand` – Zwischenstand in Prozent
9. `frage` – Cliffhanger

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
   (Chatterbox, Stimme X1, mit Prüfung durch Whisper; dauert ca. 10–15 Min.). Warten bis fertig
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
