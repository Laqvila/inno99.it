# Inno99.it — istruzioni per Claude

## Progetto
Sito statico per **Inno99** (Innovalley, L'Aquila).  
Repository GitHub: `https://github.com/Laqvila/inno99.it`  
Branch principale: `main`

## Stack
- `index.html` — struttura e contenuti
- `styles.css` — stili
- `main.js` — animazioni e interazioni (countdown, constellation, scroll reveal, ecc.)

## Regola principale: deploy automatico
**Dopo ogni modifica ai file, esegui SEMPRE e in sequenza:**

```bash
git add -A
git commit -m "<descrizione sintetica della modifica>"
git push origin main
```

Non chiedere conferma per il push: è il comportamento atteso.  
Il messaggio di commit deve descrivere chiaramente la modifica (es. "Aggiunge sezione sponsor", "Aggiorna testo evento luglio", "Corregge data").

### OBBLIGATORIO: cache busting quando tocchi styles.css o main.js
GitHub Pages serve gli asset con `Cache-Control: max-age=14400` (4 ore): senza
questo accorgimento gli utenti — soprattutto da mobile — vedono l'HTML nuovo con
CSS/JS vecchi, e la pagina appare rotta.

In `index.html` i due asset sono referenziati con un token di versione:

```html
<link rel="stylesheet" href="styles.css?v=AAAAMMGG" />
<script src="main.js?v=AAAAMMGG"></script>
```

**Ogni volta che modifichi `styles.css` o `main.js`, aggiorna il token in
entrambe le righe** con la data odierna (aggiungi una lettera se fai più deploy
nello stesso giorno: `20260909b`). Se modifichi solo testo in `index.html` non serve.

## Tipi di aggiornamento attesi
- **Testo**: modifica diretta in `index.html` (sezioni evento, speaker, descrizioni)
- **Stili**: modifica `styles.css`
- **Nuovi articoli / contenuti**: inserire nella sezione appropriata di `index.html`
- **Immagini/asset**: aggiungere i file nella cartella radice e referenziarli in `index.html`

## Brand
- Colori: navy `#22252C`, arancione `#ED7D2B → #E0691F`, magenta `#C2418F`, blu `#3B7DE0`, teal `#2BB6A8`
- Font: Space Grotesk (titoli), Inter (corpo testo)
- Logo Inno99: burst multicolore (arancione, giallo, magenta) — NON usare il calice (è solo Inno Talks)
- Logo Innovalley: catena di anelli molecolari

## Contatti evento
- Prenotazioni: https://luma.com/5i7p2k1g
- Tel: 328 82 95 361
- Email: eventi@inno-valley.it
