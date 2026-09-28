# Inno99.it — istruzioni per Claude

## Progetto
Sito statico per **Inno99** (Innovalley, L'Aquila).  
Repository GitHub: `https://github.com/Laqvila/inno99.it`  
Branch principale: `main`

## Struttura del sito (multipagina, da settembre 2026)
| URL | Contenuto |
|---|---|
| `/` | Home: appuntamenti, ultima diretta, numeri, verticali, stampa in breve |
| `/chi-siamo/` | Missione, finalità, persone, Innovalley, sponsor Synergie Italia, FAQ |
| `/inno-talks/` | Il format e il calendario delle serate |
| `/inno-talks/N/` | Una pagina per ogni serata (racconto, ospiti, foto, stampa) |
| `/inno-podcast/` | Inno Podcast, in arrivo a ottobre 2026 |
| `/rassegna-stampa/` | Rassegna unica con filtri per serata e formato |
| `/contatti/` | Come partecipare, stampa, collaborazioni |

Nel menu "Inno Talks" apre un pannello con tutte le serate: le passate portano
alla loro pagina, la prossima è segnata "In preparazione".

## Come si modifica: generatore `tools/build.py`
**Le pagine HTML pubblicate sono generate. Non modificare a mano** `index.html`,
`*/index.html`, `404.html`, `sitemap.xml` e `llms.txt`: vengono riscritti a ogni build.

- `tools/pagine/NN-nome.html` — il corpo di ogni pagina. In testa c'è un commento
  JSON con i metadati (percorso, titolo, description, immagine social, briciole,
  JSON-LD). Nel corpo si usano componenti come `{{appuntamenti}}`,
  `{{stampa evento=2}}`, `{{stampa tutte=1}}`, `{{faq}}`, `{{pager n=2}}`,
  `{{icona n=mail}}`, `{{crumbs}}`, `{{burst}}`, `{{conta cosa=uscite}}`.
- `tools/dati/eventi.json` — le serate (numero, stato `svolto` o `in-preparazione`,
  data, titolo, luogo, immagine, sintesi, ospiti). Menu, card, footer e llms.txt
  si aggiornano da qui.
- `tools/dati/stampa.json` — la rassegna stampa (testata, tipo `cartaceo`/`online`/
  `intervista`/`anteprima`, data, titolo, estratto, url, immagine, `evidenza`).
- `tools/dati/faq.json` — le domande frequenti (anche in JSON-LD).
- `styles.css`, `main.js` — stili e interazioni, condivisi da tutte le pagine.

Dopo ogni modifica:

```bash
python tools/build.py
```

Il build rigenera tutte le pagine, `sitemap.xml` e `llms.txt`, e aggiunge da solo
a `styles.css` e `main.js` il token anti-cache `?v=<hash del contenuto>`.
GitHub Pages serve gli asset con cache di 4 ore: senza token gli utenti, soprattutto
da mobile, vedrebbero HTML nuovo con CSS/JS vecchi. Non serve più aggiornarlo a mano.

### Operazioni frequenti
- **Nuovo articolo di stampa**: aggiungi una voce in `stampa.json` (immagine in
  `img/stampa/`), poi build. Compare nella pagina della serata, nella rassegna e,
  se è tra le ultime tre, in home.
- **Annunciare la prossima serata**: in `eventi.json` compila la voce `in-preparazione`
  (data, titolo, luogo, ospiti) e aggiorna `tools/pagine/06-inno-talks-3.html`.
- **Dopo una serata**: metti la voce a `svolto`, crea la pagina della serata
  successiva (`inno-talks/N+1`) come `in-preparazione` copiando `06-inno-talks-3.html`,
  aggiorna i testi della home che citano "ottobre".
- **Immagini**: in `img/` (sottocartelle per serata o per la stampa), nomi kebab-case.
- **Anteprima**: server `inno99` in `.claude/launch.json` (porta 4319).

## Regola principale: deploy automatico
**Dopo ogni modifica ai file, esegui SEMPRE e in sequenza:**

```bash
python tools/build.py
git add -A
git commit -m "<descrizione sintetica della modifica>"
git push origin main
```

Non chiedere conferma per il push: è il comportamento atteso.  
Il messaggio di commit deve descrivere chiaramente la modifica (es. "Aggiunge sezione sponsor", "Aggiorna testo evento luglio", "Corregge data").

## Vincoli tecnici
- CSP senza script e stili inline: niente `<script>` o `style="..."` nelle pagine,
  tutto in `main.js` e `styles.css`.
- Percorsi sempre assoluti dalla radice (`/img/...`, `/inno-talks/2/`), perché le
  pagine stanno in sottocartelle.
- `_config.yml` esclude `tools/` e `CLAUDE.md` dalla pubblicazione.
- I vecchi link con ancora (`/#prossimo`, `/#stampa`, `/#faq`...) vengono
  reindirizzati alle nuove pagine da `main.js`.

## Brand
- Colori: navy `#22252C`, arancione `#ED7D2B → #E0691F`, magenta `#C2418F`, blu `#3B7DE0`, teal `#2BB6A8`
- Font: Space Grotesk (titoli), Inter (corpo testo)
- Logo Inno99: burst multicolore (arancione, giallo, magenta) — NON usare il calice (è solo Inno Talks)
- Logo Innovalley: solo il file ufficiale `img/logo-innovalley.png`, mai ridisegnato

## Contatti evento
- Prenotazioni: https://luma.com/5i7p2k1g
- Tel: 328 82 95 361
- Email: eventi@inno-valley.it
