# Anleitung: Tägliche Folge bauen (für Claude)

Kanal **„KI gegen das System"** – TikTok / Insta Reels / YouTube Shorts. Besitzer: Mika (Azubi, kann nicht
programmieren, nutzt nur iPhone/iPad, zeigt sich nicht im Video). Sprache: Deutsch, duzen, locker, kurz.

## Die Serie
- **Börsen-Bert** (blau, `bert.py`): Daytrading mit US-Aktien auf Alpaca-Demokonto, 10.000 $ Spielgeld.
- **Kicker-Kurt** (grün, `kurt.py`): Tippt Bundesliga mit 10.000 € Spielgeld, 100 € pro Tipp, nur bei „Value" ≥ 3 %.
- Duell: Vergleich in Prozent. Kein echtes Geld.
- Folgen-Log mit Inhalt und Stand: `video/FOLGEN.md` – **zuerst lesen** (Nummer, Story, Cliffhanger),
  am Ende um die neue Folge ergänzen.

## Daten
- `data/bert_trades.csv`, `bert_entscheidungen.csv` (Grund jeder Aktion), `bert_kontostand.csv`
- `data/kurt_tipps.csv`, `kurt_entscheidungen.csv`, `kurt_kontostand.csv`
- Zeiten sind deutsche Zeit. US-Börse: 15:30–22:00 Uhr.

## Regeln für den Inhalt (wichtig)
1. **Ehrlich**: nur echte Zahlen aus `data/`. Nichts beschönigen. Fehler zeigen (Fehler = guter Content).
2. **Erklären, warum**: bei jedem Trade/Tipp Uhrzeit, Preis/Quote und Grund nennen. Glaubwürdigkeit > Hype.
3. Bots „lernen" nicht von selbst. Nicht so tun. Änderungen nur als nummerierte „Updates" mit echtem Grund.
4. Keine Werbung für Glücksspiel: keine Wettanbieter, keine Links, kein „wett mit", Wort „Tipp" statt „Wette".
5. „Mit KI gebaut" sagen, nicht „KI-Bots" (es sind Regel-Bots).
6. Repo ist öffentlich: „Alle Trades live nachprüfbar" ist ein Beweis-Argument.
7. Länge 50–70 Sek., Hook in den ersten 2 Sek., Cliffhanger-Frage am Ende.
8. **Kein „Folgen"-Aufruf** – weder als Button/Text im Bild noch als „Folgen!" im Sprechertext (Mikas Wunsch).

## Technik
- Bausteine: `video/folge1.py` (Hintergrund, Text-Pop, Roboter, Render), Beispiel-Folge: `video/folge2.py`.
  Neue Folge = Kopie von `folge2.py` als `folgeN.py`, Header-Text und Szenen anpassen.
- Format 1080×1920, 30 fps. Wichtiges zwischen y=300 und y=1650 (unten liegt die TikTok-Beschreibung).
- Zahlen deutsch formatieren (`money()` in folge2.py). Umlaute in Teamnamen korrigieren (Monchengladbach → Mönchengladbach).
- Vor dem Rendern: `python3 folgeN.py stills` und die Standbilder ansehen (Überlappungen, Text am Rand).
- Rendern: `RENDER_DIR=/tmp/render python3 folgeN.py`, dann Szenen mit concat zusammenfügen:
  `printf "file '%s.mp4'\n" s1 s2 … > list.txt; ffmpeg -f concat -safe 0 -i list.txt -c copy joined.mp4`
- **Stimme**: Sprechertext als `stimme/folgeN.txt` (eine Zeile pro Szene: `M:SS.s|Text`, Startzeit = Szenenstart,
  Zahlen als Wörter ausschreiben). Pushen → GitHub-Workflow „Stimme" erzeugt `stimme/folgeN/*.wav` (Stimme C,
  Thorsten). Warten, bis der Lauf fertig ist (`gh api repos/ki-gegen-das-system/ki-gegen-das-system/actions/runs`),
  pullen, dann mischen: `python3 video/mix.py joined.mp4 stimme/folgeN FolgeN_KI-gegen-das-System.mp4`
- Videos nie ins Repo committen (stehen in `.gitignore`).
- GitHub nur über REST (`gh api …`), nicht GraphQL. Workflows per Hand: `gh api -X POST …/actions/workflows/<datei>/dispatches -f ref=main`.

## Was Mika bekommt
Das fertige Video (SendUserFile), dazu kurz: Stand beider Bots in 2–3 Sätzen, Beschreibung + 3–5 Hashtags
(`#kigegendassystem` immer, nie `#wetten`/`#sportwetten`). Er legt nur noch Musik drauf und postet.
