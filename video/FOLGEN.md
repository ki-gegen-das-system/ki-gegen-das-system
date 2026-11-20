# Folgen-Log

| Folge | Datum (Daten von) | Inhalt | Stand am Ende | Cliffhanger |
|---|---|---|---|---|
| 1 | 17.11. | Intro: „Ich kann nicht programmieren" → 2 Bots, je 10.000. Kurt lässt Bayern–Köln aus (Quote 27, zu riskant). Bert startet 48 Min. vor Schluss, kauft nichts. | Bert 10.000 $ · Kurt 10.000 € | Folge 2: Berts erster Trading-Tag |
| 2 | 18.11. | Erklärung: Blau (Ø ~2 Std.) kreuzt Gelb (Ø ~5 Std.) = Kauf, 3 Notbremsen (−1,5 %, +3 %, Börsenschluss). Bert kauft 6 Tesla à 384,71 $. Fehler: Schluss verschlafen (GitHub weckte nur stündlich). **Update #1**: Verkaufsorder zum Börsenschluss. Kurt: 0 Tipps. | Bert 9.987,52 $ (−0,12 %) · Kurt 10.000 € | Verkauft Bert Tesla mit Gewinn? |
| 3 | 19.11. | 15:24 Konto +41,81 $, aber Bert schläft. 16:35 Verkauf 6 Tesla à 379,52 $ (gekauft 384,71 $) → −31,14 $ (−1,35 %). Danach kein Kaufsignal. Problem: wacht nur ~1×/Std. **Update #2**: Projekt öffentlich → alles live nachprüfbar, Bert prüft ab 20.11. alle 5 Min. Kurt: 6 Samstagsspiele geprüft, 0 Tipps (5× Value unter 3 %, Paderborn Quote 10,50 zu riskant). Neue Stimme C. | Bert 9.968,85 $ (−0,31 %) · Kurt 10.000 € | Bert zum ersten Mal den ganzen Tag wach – holt er die 31 $ zurück? |
| 4 | 20.11. | Neuer Look, neue Stimme N1, echte Charts. Crash-Tag: Nvidia −12 %, US-Markt (SPY) −3,2 %. Bert: blaue Linie den ganzen Tag unter gelb → 0 Trades, Konto −0,06 $ (schon vor Börsenstart). Ehrliche Fehler: erste Stunde verpasst (GitHub weckte erst 16:29), letzte halbe Stunde (21:36–22:00) nicht gespeichert (Speicher-Konflikt zweier Läufe). Kurt: 36 Spiele, 1 Tipp Man United bei Liverpool (Quote 4,70, faire Chance 23 %, +6,2 % Value, 100 €). Value per Münzwurf erklärt, **Update #3** gezeigt. | Bert 9.968,79 $ (−0,31 %) · Kurt 10.000 € (±0 %, 100 € offen) | Trifft Kurts erster Tipp (So 17:30)? |

## Updates (Übersicht)
- **Update #1** (18.11.): Bert stellt nach jedem Kauf eine Verkaufsorder zum Börsenschluss.
- **Update #2** (19.11.): Repository öffentlich, Bert prüft alle 5 Minuten.
- **Update #3** (20.11., Kurt): 5 Ligen statt nur Bundesliga, Value-Grenze 2 % statt 3 %, Notfall-Tipp (50 €),
  wenn er bis Freitag fürs Wochenende nichts findet. Mit Mika abgesprochen – in der Wochenanalyse am 21.11.
  nicht erneut vorschlagen, erst nach einer Woche Daten bewerten.
- **Neues Video-Format** (ab Folge 4, mit Mika abgesprochen): echte Charts, Untertitel, Terminal-Look,
  Transparenz-Zeile, neue Stimme N1 (Chatterbox mit echter deutscher Stimme von Thorsten Müller als Vorlage, CC0 – von Mika am 20.11. ausgewählt; X1 klang zu englisch). Kein Alpaca-Screenshot.

## Für die nächsten Folgen merken
- Ab Folge 4: kein „FOLGEN →"-Button und kein „Folgen!" im Sprechertext mehr.
- Folge 5 (Montag, Daten 23.11.): Ergebnis Liverpool – Man United mit Szene `tipps` zeigen.
- Folge 5: Bert-Fehler offen ansprechen, falls Mika sie beheben lässt (siehe offene Punkte).

## Offene Punkte (Stand 20.11.)
- **Bert verpasst die erste Börsenstunde**: GitHub startet die geplanten Läufe unzuverlässig (20.11.: Lauf 15:20 Uhr endete sofort, weil Börse noch zu; nächster erst 16:29). Braucht Mikas OK für eine Änderung an `bert.yml`/`bert.py`.
- **Speicher-Konflikt**: Lauf um 21:26 Uhr wartete auf den Vorgänger, arbeitete aber mit altem Stand → `git pull --rebase` scheiterte an `bert_kontostand.csv`, Log 21:36–22:00 fehlt (keine Trades betroffen). Braucht Mikas OK für eine Änderung am Workflow.
- Chartdaten speichert Bert um 22:02 zu früh (erst ab 22:05 erlaubt) → „Chartdaten" muss täglich per Hand laufen.
- Kurt prüft jedes Spiel nur einmal: Bundesliga-Spiele vom Wochenende waren schon am 19.11. (alte 3-%-Regel) geprüft, daher steht am 20.11. „4 Ligen". Alle lagen unter 2 %, also kein Tipp verpasst.
- Konto über Nacht 19.→20.11. −0,06 $ ohne Trade (Ursache unklar, evtl. Gebühr/Rundung bei Alpaca).
