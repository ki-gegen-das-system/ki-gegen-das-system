# KI gegen das System 🤖

Zwei Bots, je 10.000 Spielgeld – wer macht mehr draus? Alles nur Demo, kein echtes Geld.

| Bot | Was er macht | Wann |
|---|---|---|
| **Börsen-Bert** | Daytrading mit US-Aktien auf einem Alpaca-Demokonto (10.000 $) | Mo–Fr, alle 15 Min. während die US-Börse offen ist (15:30–22:00 Uhr) |
| **Kicker-Kurt** | Tippt Fußballspiele mit Spielgeld (10.000 €), 100 € pro Tipp | Jeden Tag um 10:00 Uhr |

Verglichen wird in Prozent.

## Wo stehen die Ergebnisse?
Im Ordner `data/`:
- `bert_kontostand.csv` / `kurt_kontostand.csv` – Kontostand über die Zeit
- `bert_trades.csv` / `kurt_tipps.csv` – alle Käufe, Verkäufe und Tipps
- `bert_entscheidungen.csv` / `kurt_entscheidungen.csv` – warum der Bot was gemacht hat

## Per Hand starten
Reiter **Actions** → links Bot auswählen → **Run workflow**.

## Benötigte Secrets
`ALPACA_API_KEY`, `ALPACA_SECRET_KEY`, `ODDS_API_KEY`

## Stimme
KI-Stimme: Chatterbox Multilingual (Resemble AI, MIT-Lizenz) mit der Stimme von Thorsten Müller als Vorlage
(Thorsten-Voice-Datensatz, CC0 – danke!). Einstellung in `stimme/einstellungen.json`.
