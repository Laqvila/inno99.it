#!/usr/bin/env python3
"""Genera il sito inno99.it.

Le pagine si scrivono in tools/pagine/*.html (contenuto della pagina, con un
blocco di metadati JSON in testa). Menu, piè di pagina, rassegna stampa, card
degli appuntamenti e domande frequenti vengono dai file in tools/dati/.

Uso, dalla radice del repository:
    python tools/build.py

Il token anti-cache di styles.css, main.js e del player video è calcolato in
automatico dal contenuto dei file, quindi non va più aggiornato a mano.
"""
import datetime
import hashlib
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
DATI = TOOLS / "dati"
PAGINE = TOOLS / "pagine"
SITE = "https://inno99.it"

EVENTI = json.loads((DATI / "eventi.json").read_text(encoding="utf-8"))
STAMPA = json.loads((DATI / "stampa.json").read_text(encoding="utf-8"))
FAQ = json.loads((DATI / "faq.json").read_text(encoding="utf-8"))
STAMPA.sort(key=lambda s: (s["data"], s["id"]), reverse=True)

MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
        "agosto", "settembre", "ottobre", "novembre", "dicembre"]
MESI_BREVI = ["gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott", "nov", "dic"]
TIPI = {"cartaceo": "Cartaceo", "online": "Online", "intervista": "Intervista", "anteprima": "Anteprima"}


def ver(rel):
    return hashlib.sha1((ROOT / rel).read_bytes()).hexdigest()[:10]


ASSETS = {p: f"/{p}?v={ver(p)}" for p in ["styles.css", "main.js", "video/player.css", "video/player.js"]}


def t(s):
    """Testo sicuro dentro un nodo HTML."""
    return html.escape(str(s), quote=False)


def a(s):
    """Testo sicuro dentro un attributo HTML."""
    return html.escape(str(s), quote=True)


def data_it(iso, breve=False):
    y, m, d = iso.split("-")
    mesi = MESI_BREVI if breve else MESI
    return f"{int(d)} {mesi[int(m) - 1]} {y}"


def evento(n):
    for e in EVENTI:
        if e["n"] == int(n):
            return e
    raise KeyError(f"evento {n} non trovato")


# --------------------------------------------------------------------------
# Icone (tratto arancione, stile coerente)
# --------------------------------------------------------------------------
ICONE = {
    "calendario": '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
    "luogo": '<path d="M12 21s7-5.7 7-11a7 7 0 1 0-14 0c0 5.3 7 11 7 11Z"/><circle cx="12" cy="10" r="2.5"/>',
    "persone": '<circle cx="9" cy="8" r="3.2"/><path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6"/><circle cx="17" cy="9" r="2.4"/><path d="M15.5 14.2c3 .2 5.5 2.6 5.5 5.8"/>',
    "play": '<circle cx="12" cy="12" r="9.5"/><path d="M10 8.5v7l6-3.5-6-3.5Z"/>',
    "documento": '<path d="M6 2h9l5 5v15H6z"/><path d="M14 2v6h6M9 13h8M9 17h8"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
    "telefono": '<path d="M5 3h4l2 5-2.5 1.5a11 11 0 0 0 6 6L16 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 5a2 2 0 0 1 2-2"/>',
    "freccia": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "giu": '<path d="m6 9 6 6 6-6"/>',
    "su": '<path d="m6 15 6-6 6 6"/>',
    "stella": '<path d="M12 3l2.6 5.6 6.1.7-4.5 4.2 1.2 6L12 16.6 6.6 19.5l1.2-6L3.3 9.3l6.1-.7z"/>',
    "micro": '<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3M9 21h6"/>',
    "rete": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>',
    "citta": '<path d="M3 21V9l6-4 6 4v12"/><path d="M15 21V11l6 3v7M7 12h4M7 16h4"/>',
    "idee": '<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3.6 10.8c.6.5 1 1.2 1 2V16h5.2v-.2c0-.8.4-1.5 1-2A6 6 0 0 0 12 3Z"/>',
    "calice": '<path d="M7 3h10l-1 7a4 4 0 0 1-8 0L7 3ZM12 14v6M8 21h8"/>',
    "esterno": '<path d="M14 4h6v6M20 4l-9 9M18 14v6H4V6h6"/>',
    "check": '<path d="m5 12 4.5 4.5L19 7"/>',
    "campana": '<path d="M6 16v-5a6 6 0 0 1 12 0v5l1.5 2h-15z"/><path d="M10 20.5a2 2 0 0 0 4 0"/>',
    "bus": '<rect x="4" y="3" width="16" height="15" rx="3"/><path d="M4 11h16M8 18v3M16 18v3M8 14.5h.01M16 14.5h.01"/>',
    "film": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M7 4v16M17 4v16M3 9h4M3 15h4M17 9h4M17 15h4"/>',
    "sconto": '<path d="M20.5 12.5 12.5 20.5 3.5 11.5V3.5h8z"/><circle cx="8" cy="8" r="1.6"/>',
    "telefonino": '<rect x="6" y="2" width="12" height="20" rx="2.5"/><path d="M11 18.5h2"/>',
    "piu": '<circle cx="12" cy="12" r="9.5"/><path d="M12 8v8M8 12h8"/>',
}


def icona(nome, cls="ico"):
    return f'<svg class="{cls}" viewBox="0 0 24 24" aria-hidden="true">{ICONE[nome]}</svg>'


# --------------------------------------------------------------------------
# L'AquiLive, l'app degli eventi dell'Aquila ideata da Mirko Rocci
# --------------------------------------------------------------------------
APP_IOS = "https://apps.apple.com/it/app/laquilive/id6796280318"
# su Google Play la provenienza arriva nei rapporti della Play Console
APP_ANDROID = "https://play.google.com/store/apps/details?id=it.aqlive99.app&referrer=utm_source%3Dinno99%26utm_medium%3Dsito"
MARCHI = {
    "apple": '<path d="M12.15 6.9c-.95 0-2.42-1.08-3.96-1.04-2.04.03-3.91 1.18-4.96 3.01-2.12 3.68-.55 9.1 1.52 12.09 1.01 1.45 2.21 3.09 3.79 3.04 1.52-.07 2.09-.99 3.94-.99 1.83 0 2.35.99 3.96.95 1.64-.03 2.68-1.48 3.68-2.95 1.16-1.69 1.64-3.33 1.66-3.42-.04-.01-3.18-1.22-3.22-4.86-.03-3.04 2.48-4.49 2.6-4.56-1.43-2.09-3.62-2.32-4.39-2.38-2-.16-3.68 1.09-4.62 1.09zm3.38-3.07c.84-1.01 1.4-2.43 1.25-3.83-1.21.05-2.66.81-3.53 1.82-.78.9-1.45 2.34-1.27 3.71 1.34.1 2.71-.69 3.55-1.7z"/>',
    "play": '<path fill="#00D7FE" d="M3.6 1.8c-.3.3-.4.7-.4 1.3v17.8c0 .6.1 1 .4 1.3l10-10.2z"/>'
            '<path fill="#FFCE00" d="m17 15.6-3.4-3.4L17 8.8l4 2.3c1.2.7 1.2 1.7 0 2.4z"/>'
            '<path fill="#FF3A44" d="M17 15.6 13.6 12.2 3.6 22.2c.4.4 1 .4 1.7 0z"/>'
            '<path fill="#00F076" d="M17 8.8 5.3 2.1c-.7-.4-1.3-.4-1.7 0l10 10.1z"/>',
}


def marchio(nome):
    fill = ' fill="currentColor"' if nome == "apple" else ""
    return f'<svg class="store-mark" viewBox="0 0 24 24" aria-hidden="true"{fill}>{MARCHI[nome]}</svg>'


def store_btns(cls=""):
    return (f'<div class="stores{" " + cls if cls else ""}">'
            f'<a class="store-btn" href="{a(APP_IOS)}" target="_blank" rel="noopener" aria-label="Scarica L&#39;AquiLive da App Store per iPhone">'
            f'{marchio("apple")}<span><small>Scarica su</small><b>App Store</b></span></a>'
            f'<a class="store-btn" href="{a(APP_ANDROID)}" target="_blank" rel="noopener" aria-label="Scarica L&#39;AquiLive da Google Play per Android">'
            f'{marchio("play")}<span><small>Disponibile su</small><b>Google Play</b></span></a></div>')


TELEFONI = {
    "servizi": ("servizi-inno99.jpg", 600, 1132, "La sezione Servizi esclusivi di L'AquiLive con Inno99 in evidenza"),
    "oggi": ("oggi-in-citta.jpg", 600, 1298, "La schermata Oggi in città di L'AquiLive con gli eventi del giorno e i Servizi esclusivi"),
    "mappa": ("mappa.jpg", 600, 1298, "La mappa di L'AquiLive con gli eventi geolocalizzati nel centro dell'Aquila"),
    "evento": ("scheda-evento.jpg", 600, 1132, "La scheda di un evento su L'AquiLive con data, ora, luogo e foto"),
    "notizie": ("notizie.jpg", 600, 1132, "Le notizie locali delle testate aquilane raccolte in L'AquiLive"),
}


def telefono(nome, cls=""):
    f, w, h, alt = TELEFONI[nome]
    return (f'<figure class="phone{" " + cls if cls else ""}"><img src="/img/laquilive/{f}" alt="{a(alt)}" '
            f'width="{w}" height="{h}" loading="lazy" /></figure>')


def comp_store(meta, args):
    return store_btns(args.get("cls", ""))


def comp_telefono(meta, args):
    return telefono(args["n"], args.get("cls", ""))


def comp_app(meta, args):
    if args.get("mini"):
        return f"""<aside class="app-mini reveal" aria-label="L'AquiLive">
  <img class="am-ico" src="/img/laquilive/icona.png" alt="" width="64" height="64" loading="lazy" />
  <div class="am-text"><b>Segui le prossime serate su <span class="aql">L'Aqui<i>Live</i></span></b><span>L'app gratuita degli eventi dell'Aquila, con una sezione dedicata a Inno99. <a class="link-inline" href="/laquilive/">Scopri l'app</a></span></div>
  {store_btns("sm")}
</aside>"""
    return f"""<div class="app-band reveal">
  <div class="ab-text">
    <span class="ab-kicker"><img src="/img/laquilive/icona.png" alt="" width="44" height="44" loading="lazy" /> Gli appuntamenti in tasca</span>
    <h2>Tutti gli Inno Talks su <span class="aql">L'Aqui<i>Live</i></span></h2>
    <p>L'app gratuita con tutti gli eventi dell'Aquila e provincia ha una sezione dedicata a Inno99. Salvi la serata, scegli quando ricevere il promemoria e il prossimo appuntamento non ti sfugge.</p>
    {store_btns()}
    <a class="link-arrow" href="/laquilive/">Scopri L'AquiLive <span>→</span></a>
  </div>
  <div class="ab-phones">
    {telefono("oggi", "back")}
    {telefono("servizi", "front")}
    <span class="ab-chip" aria-hidden="true">{icona("stella")} Inno99 in evidenza</span>
  </div>
</div>"""


COLORI_BURST = ["#F08020", "#D42A70", "#F0B400"]
RAGGI = "".join(
    '<use href="#{}" fill="{}" transform="rotate({:g})"/>'.format("rayL" if i % 2 == 0 else "rayS", COLORI_BURST[i % 3], i * 22.5)
    for i in range(16)
)
BURST_DEFS = """<svg class="sprite" aria-hidden="true" focusable="false"><defs>
<g id="rayL"><path d="M0,-18 L5.5,-36 L2.4,-56 L0,-61 L-2.4,-56 L-5.5,-36 Z"/><circle cx="0" cy="-68" r="6"/><circle cx="-6.6" cy="-61.5" r="4.4"/><circle cx="6.6" cy="-61.5" r="4.4"/></g>
<g id="rayS"><rect x="-2" y="-42" width="4" height="24" rx="2"/><circle cx="0" cy="-49" r="6"/><circle cx="-6.4" cy="-43" r="4.6"/><circle cx="6.4" cy="-43" r="4.6"/></g>
<symbol id="burst" viewBox="-84 -84 168 168">""" + RAGGI + """<circle cx="0" cy="0" r="12.5" fill="#F08020"/></symbol>
</defs></svg>"""


def burst(cls="burst-svg"):
    return f'<svg class="{cls}" viewBox="0 0 168 168" aria-hidden="true" focusable="false"><use href="#burst" width="168" height="168"/></svg>'


# --------------------------------------------------------------------------
# Intestazione, menu, drawer mobile, piè di pagina
# --------------------------------------------------------------------------
def voce_menu_evento(e, attivo):
    n = e["n"]
    cur = ' aria-current="page"' if attivo == n else ""
    if e["stato"] == "svolto":
        media = f'<img src="{a(e["img"])}" alt="" width="{e["img_w"]}" height="{e["img_h"]}" loading="lazy" />'
        tag = '<span class="mev-tag">Com\'è andata</span>'
        cls = "mev"
    elif e["stato"] == "prossimo":
        media = f'<img src="{a(e["img"])}" alt="" width="{e["img_w"]}" height="{e["img_h"]}" loading="lazy" />'
        tag = '<span class="mev-tag next">Prossima serata</span>'
        cls = "mev is-next"
    else:
        media = f'<span class="mev-soon">{burst()}</span>'
        tag = '<span class="mev-tag next">In preparazione</span>'
        cls = "mev is-next"
    return (f'<li><a class="{cls}" href="/inno-talks/{n}/"{cur}>'
            f'<span class="mev-media">{media}<span class="mev-n">#{n}</span></span>'
            f'<span class="mev-body"><b>{t(e["titolo"])}</b><span>{t(e["data_txt"])}'
            f'{" · " + t(e["luogo"]) if e.get("luogo") else ""}</span>{tag}</span></a></li>')


def header(meta):
    nav = meta.get("nav", "")
    ev_att = meta.get("evento")

    def cur(k):
        return ' aria-current="page"' if nav == k else ""

    eventi = "".join(voce_menu_evento(e, ev_att) for e in EVENTI)
    talks_cur = ' aria-current="page"' if nav == "talks" and not ev_att else (' data-section="on"' if nav == "talks" else "")
    return f"""<a class="skip" href="#main">Vai al contenuto</a>
<header class="site-head" id="site-head">
  <div class="head-in">
    <a class="brand" href="/" aria-label="Inno99, vai alla home">
      <span class="brand-mark">{burst("brand-burst")}</span>
      <span class="brand-word">Inn<span class="o">o</span>99</span>
    </a>
    <nav class="menu" aria-label="Menu principale">
      <ul class="menu-list">
        <li><a class="menu-link" href="/chi-siamo/"{cur("chi")}>Chi siamo</a></li>
        <li class="has-mega">
          <a class="menu-link" href="/inno-talks/"{talks_cur}>Inno Talks</a>
          <button class="mega-toggle" type="button" aria-expanded="false" aria-controls="mega-talks" aria-label="Mostra gli appuntamenti degli Inno Talks">{icona("giu")}</button>
          <div class="mega" id="mega-talks">
            <div class="mega-in">
              <div class="mega-intro">
                <span class="mega-kicker">Gli appuntamenti</span>
                <b class="mega-title">Gli Aperitivi dell'Innovazione</b>
                <p>Serate a formula aperitivo nei locali del centro storico dell'Aquila, con ospiti d'eccellenza e dialogo con il pubblico.</p>
                <a class="link-arrow" href="/inno-talks/">Scopri il format <span>→</span></a>
              </div>
              <ul class="mega-events">{eventi}</ul>
            </div>
          </div>
        </li>
        <li><a class="menu-link" href="/inno-podcast/"{cur("podcast")}>Inno Podcast <span class="soon-pill">In arrivo</span></a></li>
        <li><a class="menu-link" href="/rassegna-stampa/"{cur("stampa")}>Rassegna stampa</a></li>
        <li><a class="menu-link menu-app" href="/laquilive/"{cur("app")}><img src="/img/laquilive/icona.png" alt="" width="22" height="22" />L'AquiLive <span class="soon-pill app-pill">App</span></a></li>
      </ul>
    </nav>
    <a class="iv-chip" href="https://www.inno-valley.it" target="_blank" rel="noopener" aria-label="Innovalley Open Innovation Hub, sito ufficiale">
      <img src="/img/logo-innovalley.png" width="2048" height="1067" alt="Innovalley" />
    </a>
    <a class="btn btn-sm btn-glow head-cta" href="/contatti/"{cur("contatti")}>Contatti</a>
    <button class="burger" type="button" aria-expanded="false" aria-controls="drawer" aria-label="Apri il menu"><span></span><span></span><span></span></button>
  </div>
  <div class="progress" aria-hidden="true"><span></span></div>
</header>
{drawer(meta)}"""


def drawer(meta):
    nav = meta.get("nav", "")
    ev_att = meta.get("evento")

    def cur(k):
        return ' aria-current="page"' if nav == k else ""

    righe = []
    for e in EVENTI:
        c = ' aria-current="page"' if ev_att == e["n"] else ""
        cls = ' class="is-next"' if e["stato"] != "svolto" else ""
        righe.append(f'<li><a href="/inno-talks/{e["n"]}/"{c}{cls}><span class="dr-n">#{e["n"]}</span>'
                     f'<span class="dr-t"><b>{t(e["titolo"])}</b><small>{t(e["data_txt"])}</small></span></a></li>')
    return f"""<div class="drawer" id="drawer">
  <nav class="drawer-nav" aria-label="Menu">
    <a class="dr-link" href="/"{cur("home")}>Home</a>
    <a class="dr-link" href="/chi-siamo/"{cur("chi")}>Chi siamo</a>
    <div class="dr-group">
      <a class="dr-link" href="/inno-talks/"{cur("talks") if not ev_att else ""}>Inno Talks</a>
      <ul class="dr-events">{"".join(righe)}</ul>
    </div>
    <a class="dr-link" href="/inno-podcast/"{cur("podcast")}>Inno Podcast <span class="soon-pill">In arrivo</span></a>
    <a class="dr-link" href="/rassegna-stampa/"{cur("stampa")}>Rassegna stampa</a>
    <a class="dr-link" href="/laquilive/"{cur("app")}>L'AquiLive <span class="soon-pill app-pill">App</span></a>
    <a class="dr-link" href="/contatti/"{cur("contatti")}>Contatti</a>
  </nav>
  <div class="dr-foot">
    <a href="tel:+393288295361">{icona("telefono")} 328 82 95 361</a>
    <a href="mailto:eventi@inno-valley.it">{icona("mail")} eventi@inno-valley.it</a>
    <a class="iv-chip" href="https://www.inno-valley.it" target="_blank" rel="noopener"><img src="/img/logo-innovalley.png" width="2048" height="1067" alt="Innovalley" loading="lazy" /></a>
  </div>
</div>"""


def footer():
    eventi = "".join(
        f'<a href="/inno-talks/{e["n"]}/">#{e["n"]} · {t(e["titolo"])}</a>' for e in EVENTI)
    return f"""<footer class="footer">
  <div class="container footer-grid">
    <div class="footer-brand">
      <a class="brand" href="/" aria-label="Inno99, vai alla home"><span class="brand-mark">{burst("brand-burst")}</span><span class="brand-word">Inn<span class="o">o</span>99</span></a>
      <p>L'ecosistema dell'innovazione all'Aquila. Un programma di Innovalley nel quadro di L'Aquila Capitale Italiana della Cultura 2026.</p>
      <a class="p-logo-iv" href="https://www.inno-valley.it" target="_blank" rel="noopener" aria-label="Innovalley Open Innovation Hub"><img src="/img/logo-innovalley.png" width="2048" height="1067" alt="Innovalley" loading="lazy" /></a>
    </div>
    <div class="footer-col">
      <h4>Inno99</h4>
      <a href="/chi-siamo/">Chi siamo</a>
      <a href="/inno-talks/">Inno Talks</a>
      <a href="/inno-podcast/">Inno Podcast</a>
      <a href="/rassegna-stampa/">Rassegna stampa</a>
      <a href="/laquilive/">L'app L'AquiLive</a>
      <a href="/contatti/">Contatti</a>
    </div>
    <div class="footer-col">
      <h4>Appuntamenti</h4>
      {eventi}
    </div>
    <div class="footer-col">
      <h4>Contatti</h4>
      <a href="tel:+393288295361">328 82 95 361</a>
      <a href="mailto:eventi@inno-valley.it">eventi@inno-valley.it</a>
      <a href="https://www.inno-valley.it" target="_blank" rel="noopener">inno-valley.it</a>
    </div>
  </div>
  <div class="container footer-bottom">
    <span>© 2026 Inno99 · Innovalley Cube Srl e Associazione Innovalley Promotori di Innovazione · P.IVA 02176300693</span>
    <span>Sponsor unico 2026 · Synergie Italia</span>
  </div>
</footer>
<button class="to-top" type="button" aria-label="Torna all'inizio della pagina">{icona("su")}</button>"""


# --------------------------------------------------------------------------
# Componenti richiamabili dalle pagine con {{nome argomenti}}
# --------------------------------------------------------------------------
def comp_crumbs(meta, args):
    voci = meta.get("crumbs") or []
    parti = ['<a href="/">Home</a>']
    for nome, url in voci:
        parti.append('<span aria-hidden="true">›</span>')
        parti.append(f'<a href="{a(url)}">{t(nome)}</a>' if url else f'<span aria-current="page">{t(nome)}</span>')
    return f'<nav class="crumbs" aria-label="Percorso">{"".join(parti)}</nav>'


def talk_card(e):
    n = e["n"]
    if e["stato"] == "svolto":
        media = f'<img src="{a(e["img"])}" alt="{a(e["img_alt"])}" width="{e["img_w"]}" height="{e["img_h"]}" loading="lazy" />'
        stato = f'<span class="tc-state">{t(e["badge"])}</span>'
        go = "Com'è andata"
        cls = "talk-card tilt"
    elif e["stato"] == "prossimo":
        media = f'<img src="{a(e["img"])}" alt="{a(e["img_alt"])}" width="{e["img_w"]}" height="{e["img_h"]}" loading="lazy" />'
        stato = f'<span class="tc-state next"><span class="pulse-dot"></span> {t(e["badge"])}</span>'
        go = "Scopri la serata"
        cls = "talk-card tilt is-next"
    else:
        media = f'<span class="tc-soon">{burst()}</span>'
        stato = '<span class="tc-state next"><span class="pulse-dot"></span> In preparazione</span>'
        go = "Scopri le novità"
        cls = "talk-card tilt is-next"
    luogo = f' · {t(e["luogo"])}' if e.get("luogo") else ""
    if e.get("ora"):
        luogo = f' · ore {t(e["ora"])}{luogo}'
    return f"""<div class="reveal"><a class="{cls}" href="/inno-talks/{n}/">
  <span class="tc-media">{media}<span class="tc-num">#{n}</span>{stato}</span>
  <span class="tc-body">
    <span class="tc-date">{t(e["data_txt"])}{luogo}</span>
    <span class="tc-title">{t(e["titolo"])}</span>
    <span class="tc-text">{t(e["sintesi"])}</span>
    <span class="tc-go">{go} <span aria-hidden="true">→</span></span>
  </span>
</a></div>"""


def comp_appuntamenti(meta, args):
    cards = "\n".join(talk_card(e) for e in EVENTI)
    return f"""<div class="talks reveal-line">
  <div class="talks-line" aria-hidden="true"><span></span></div>
  <div class="talks-grid" data-stagger>
{cards}
  </div>
</div>"""


def press_card(s, mostra_evento=True, evidenza=True):
    est = s["url"].startswith("http")
    tgt = ' target="_blank" rel="noopener"' if est else ' target="_blank"'
    cta = s.get("cta") or ("Leggi l'articolo" if est else "Apri")
    feat = evidenza and s.get("evidenza")
    cls = ["press-card"]
    if feat:
        cls.append("featured")
    if s.get("img"):
        media = (f'<span class="press-media{" paper" if s["tipo"] == "cartaceo" else ""}">'
                 f'<img src="{a(s["img"])}" alt="" width="{s["img_w"]}" height="{s["img_h"]}" loading="lazy" /></span>')
    else:
        cls.append("no-photo")
        media = f'<span class="press-media mast"><span>{t(s["testata"])}</span></span>'
    quando = []
    if s.get("data_nota", True):
        quando.append(data_it(s["data"]))
    if s.get("nota"):
        quando.append(t(s["nota"]))
    if mostra_evento:
        quando.append(f'Inno Talks #{s["evento"]}')
    return f"""<article class="{' '.join(cls)} reveal" data-evento="{s['evento']}" data-tipo="{s['tipo']}">
  {media}
  <div class="press-body">
    <div class="press-head"><span class="press-src">{t(s["testata"])}</span><span class="press-badge {s['tipo']}">{TIPI[s["tipo"]]}</span></div>
    <h3 class="press-title"><a href="{a(s["url"])}"{tgt}>{t(s["titolo"])}</a></h3>
    <p>{t(s["estratto"])}</p>
    <div class="press-foot"><span class="press-date">{" · ".join(quando)}</span><span class="press-go">{t(cta)} <span aria-hidden="true">→</span></span></div>
  </div>
</article>"""


def in_evidenza_prima(voci):
    """Le pagine di giornale in evidenza occupano una riga intera: vanno in testa al gruppo
    così la griglia delle altre uscite resta compatta, sempre in ordine di data."""
    return [s for s in voci if s.get("evidenza")] + [s for s in voci if not s.get("evidenza")]


def comp_stampa(meta, args):
    if "evento" in args:
        voci = in_evidenza_prima([s for s in STAMPA if s["evento"] == int(args["evento"])])
        return '<div class="press-grid">\n' + "\n".join(press_card(s, mostra_evento=False) for s in voci) + "\n</div>"
    if "ultime" in args:
        voci = STAMPA[: int(args["ultime"])]
        return '<div class="press-grid" data-stagger>\n' + "\n".join(press_card(s, evidenza=False) for s in voci) + "\n</div>"
    # rassegna completa con filtri, raggruppata per serata
    blocchi = []
    for e in sorted([e for e in EVENTI if e["stato"] == "svolto"], key=lambda e: -e["n"]):
        voci = in_evidenza_prima([s for s in STAMPA if s["evento"] == e["n"]])
        if not voci:
            continue
        mese = MESI[int(e["data"][5:7]) - 1]
        blocchi.append(f"""<section class="press-block" data-group="{e['n']}" aria-labelledby="stampa-{e['n']}">
  <h2 class="press-group" id="stampa-{e['n']}"><a href="/inno-talks/{e['n']}/">Inno Talks #{e['n']} · {t(e['titolo'])}</a><span>{mese} {e['data'][:4]} · {len(voci)} uscite</span></h2>
  <div class="press-grid">
{chr(10).join(press_card(s, mostra_evento=False) for s in voci)}
  </div>
</section>""")
    eventi_chip = "".join(
        f'<button type="button" class="chip" data-f-evento="{e["n"]}" aria-pressed="false">Inno Talks #{e["n"]}</button>'
        for e in sorted([e for e in EVENTI if e["stato"] == "svolto"], key=lambda e: -e["n"]))
    tipi_presenti = [k for k in TIPI if any(s["tipo"] == k for s in STAMPA)]
    tipi_chip = "".join(
        f'<button type="button" class="chip" data-f-tipo="{k}" aria-pressed="false">{TIPI[k] if k != "intervista" else "Interviste"}</button>'
        for k in tipi_presenti)
    filtri = f"""<div class="press-filters" data-filters>
  <div class="pf-group" role="group" aria-label="Filtra per serata"><button type="button" class="chip" data-f-evento="*" aria-pressed="true">Tutte le serate</button>{eventi_chip}</div>
  <div class="pf-group" role="group" aria-label="Filtra per tipo"><button type="button" class="chip" data-f-tipo="*" aria-pressed="true">Tutti i formati</button>{tipi_chip}</div>
  <p class="pf-count" aria-live="polite"><b>{len(STAMPA)}</b> uscite</p>
</div>"""
    return filtri + "\n" + "\n".join(blocchi) + '\n<p class="pf-empty" hidden>Nessuna uscita con questi filtri.</p>'


def comp_testate(meta, args):
    nomi = []
    for s in STAMPA:
        if s["testata"] not in nomi:
            nomi.append(s["testata"])
    giro = "".join(f"<span>{t(n)}</span>" for n in nomi)
    eco = "".join(f'<span aria-hidden="true">{t(n)}</span>' for n in nomi)
    return f'<div class="outlets" aria-label="Le testate che hanno raccontato Inno99"><div class="outlets-track">{giro}{eco}</div></div>'


def numeri():
    svolti = [e for e in EVENTI if e["stato"] == "svolto"]
    ospiti = set()
    for e in svolti:
        ospiti.update(e.get("ospiti", []))
    testate = {s["testata"] for s in STAMPA}
    ultima = svolti[-1]
    return {"serate": len(svolti), "ospiti": len(ospiti), "uscite": len(STAMPA),
            "testate": len(testate), "partecipanti": ultima.get("partecipanti", 0)}


def comp_numeri(meta, args):
    n = numeri()
    return f"""<div class="stats reveal">
  <div class="stat"><span class="num" data-to="{n['serate']}">{n['serate']}</span><span class="lbl">serate realizzate</span></div>
  <div class="stat"><span class="num" data-to="{n['ospiti']}">{n['ospiti']}</span><span class="lbl">ospiti intervenuti</span></div>
  <div class="stat"><span class="num" data-to="{n['uscite']}">{n['uscite']}</span><span class="lbl">uscite sulla stampa</span></div>
  <div class="stat"><span class="num" data-to="{n['partecipanti']}" data-suffix="+">{n['partecipanti']}+</span><span class="lbl">persone all'ultima serata</span></div>
</div>"""


def comp_conta(meta, args):
    return str(numeri()[args.get("cosa", "uscite")])


def comp_faq(meta, args):
    meta.setdefault("_graph", []).append({
        "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": f["q"],
                        "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in FAQ],
    })
    voci = "".join(
        f'<details class="faq reveal"{" open" if i == 0 else ""}><summary><h3>{t(f["q"])}</h3></summary><p>{t(f["a"])}</p></details>'
        for i, f in enumerate(FAQ))
    return f'<div class="faq-list">{voci}</div>'


def comp_pager(meta, args):
    n = int(args["n"])
    prec = [e for e in EVENTI if e["n"] == n - 1]
    succ = [e for e in EVENTI if e["n"] == n + 1]
    parti = []
    if prec:
        e = prec[0]
        parti.append(f'<a class="pg prev" href="/inno-talks/{e["n"]}/"><small>← Serata precedente</small><b>#{e["n"]} · {t(e["titolo"])}</b><span>{t(e["data_txt"])}</span></a>')
    if succ:
        e = succ[0]
        parti.append(f'<a class="pg next" href="/inno-talks/{e["n"]}/"><small>Serata successiva →</small><b>#{e["n"]} · {t(e["titolo"])}</b><span>{t(e["data_txt"])}</span></a>')
    return f'<nav class="pager" aria-label="Altre serate">{"".join(parti)}</nav>'


def prossimo():
    return next((e for e in EVENTI if e["stato"] == "prossimo"), None)


def countdown(e):
    return (f'<div class="countdown" data-countdown="{a(e["inizio"])}" role="timer" '
            f'aria-label="Tempo che manca a Inno Talks #{e["n"]}" hidden>'
            '<div><b data-u="g">0</b><small>giorni</small></div>'
            '<div><b data-u="h">00</b><small>ore</small></div>'
            '<div><b data-u="m">00</b><small>minuti</small></div>'
            '<div><b data-u="s">00</b><small>secondi</small></div></div>'
            '<p class="cd-live" hidden><span class="pulse-dot"></span> La serata è iniziata, ti aspettiamo</p>')


def comp_countdown(meta, args):
    e = evento(args["n"]) if "n" in args else prossimo()
    return countdown(e) if e and e.get("inizio") else ""


def comp_prossimo(meta, args):
    """Il riquadro della prossima serata in home. Sparisce da solo se nessuna serata è annunciata."""
    e = prossimo()
    if not e:
        return ""
    g, m = int(e["data"][8:10]), MESI_BREVI[int(e["data"][5:7]) - 1]
    oggetto = f"Inno Talks #{e['n']} · prenotazione"
    extra = f'<li>{icona("calice")}{t(e["extra"])}</li>' if e.get("extra") else ""
    return f"""<div class="next-ev reveal">
  <a class="ne-media" href="/inno-talks/{e['n']}/" tabindex="-1" aria-hidden="true">
    <img src="{a(e['img'])}" alt="" width="{e['img_w']}" height="{e['img_h']}" loading="lazy" />
    <span class="ne-date"><b>{g}</b><small>{m}</small></span>
  </a>
  <div class="ne-body">
    <span class="kicker"><span class="pulse-dot"></span> Prossima serata · Inno Talks #{e['n']}</span>
    <h2><a href="/inno-talks/{e['n']}/">{t(e['titolo'])}</a></h2>
    <p class="ne-sub">{t(e['sottotitolo'])}</p>
    <ul class="ne-facts">
      <li>{icona("calendario")}{t(e['giorno'])} · ore {t(e['ora'])}</li>
      <li>{icona("luogo")}{t(e['luogo_esteso'])}, L'Aquila</li>
      {extra}
    </ul>
    <p class="ne-text">{t(e['sintesi'])}</p>
    {countdown(e)}
    <div class="ph-cta">
      <a class="btn btn-glow" href="mailto:eventi@inno-valley.it?subject={quote(oggetto)}">{icona("mail")} Prenota il posto</a>
      <a class="btn btn-ghost" href="/inno-talks/{e['n']}/">Scopri la serata <span class="btn-arrow">→</span></a>
    </div>
  </div>
</div>"""


def comp_icona(meta, args):
    return icona(args.get("n", "freccia"), args.get("cls", "ico"))


def comp_burst(meta, args):
    return burst(args.get("cls", "burst-svg"))


def comp_evento(meta, args):
    e = evento(args["n"])
    return t(e[args.get("campo", "titolo")])


COMPONENTI = {
    "crumbs": comp_crumbs,
    "appuntamenti": comp_appuntamenti,
    "stampa": comp_stampa,
    "testate": comp_testate,
    "numeri": comp_numeri,
    "conta": comp_conta,
    "faq": comp_faq,
    "pager": comp_pager,
    "icona": comp_icona,
    "burst": comp_burst,
    "evento": comp_evento,
    "app": comp_app,
    "countdown": comp_countdown,
    "prossimo": comp_prossimo,
    "store": comp_store,
    "telefono": comp_telefono,
}


def espandi(corpo, meta):
    def sost(m):
        nome = m.group(1)
        args = dict(re.findall(r'(\w+)=("[^"]*"|\S+)', m.group(2) or ""))
        args = {k: v.strip('"') for k, v in args.items()}
        if nome not in COMPONENTI:
            raise KeyError(f"componente sconosciuto: {nome}")
        return COMPONENTI[nome](meta, args)
    return re.sub(r"\{\{(\w+)((?:\s+\w+=(?:\"[^\"]*\"|\S+?))*)\s*\}\}", sost, corpo)


# --------------------------------------------------------------------------
# Pagina completa
# --------------------------------------------------------------------------
ORG = {
    "@type": "Organization",
    "@id": f"{SITE}/#innovalley",
    "name": "Innovalley Open Innovation Hub",
    "url": "https://www.inno-valley.it",
    "logo": f"{SITE}/img/logo-innovalley.png",
    "email": "eventi@inno-valley.it",
    "telephone": "+39 328 829 5361",
}
FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E"
           "%3Ccircle cx='50' cy='50' r='42' fill='%2322252C'/%3E%3Ccircle cx='50' cy='44' r='14' fill='%23E97B26'/%3E%3C/svg%3E")


def head(meta):
    path = meta["path"]
    url = SITE + path
    og = meta.get("og_image", "/img/inno-talks-2/sala.jpg")
    og_w, og_h = meta.get("og_w", 1600), meta.get("og_h", 900)
    og_alt = meta.get("og_alt", "La sala dell'Irish Pub Via Verdi piena di pubblico durante Inno Talks #2")
    graph = [ORG]
    if meta.get("crumbs"):
        voci = [{"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"}]
        for i, (nome, u) in enumerate(meta["crumbs"], start=2):
            voci.append({"@type": "ListItem", "position": i, "name": nome, "item": SITE + (u or path)})
        graph.append({"@type": "BreadcrumbList", "itemListElement": voci})
    graph += meta.get("jsonld", [])
    graph += meta.get("_graph", [])
    ld = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, indent=1)
    player_css = f'\n<link rel="stylesheet" href="{ASSETS["video/player.css"]}" />' if meta.get("player") else ""
    robots = meta.get("robots", "index, follow, max-image-preview:large")
    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self'; style-src 'self' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self' data:; media-src 'self' blob:; connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; upgrade-insecure-requests" />
<meta name="referrer" content="strict-origin-when-cross-origin" />
<title>{t(meta["title"])}</title>
<meta name="description" content="{a(meta["description"])}" />
<meta name="robots" content="{robots}" />
<link rel="canonical" href="{url}" />
<meta name="theme-color" content="#0A0D13" />
<meta property="og:type" content="{meta.get("og_type", "website")}" />
<meta property="og:site_name" content="Inno99" />
<meta property="og:locale" content="it_IT" />
<meta property="og:title" content="{a(meta.get("og_title", meta["title"]))}" />
<meta property="og:description" content="{a(meta.get("og_description", meta["description"]))}" />
<meta property="og:url" content="{url}" />
<meta property="og:image" content="{SITE}{og}" />
<meta property="og:image:width" content="{og_w}" />
<meta property="og:image:height" content="{og_h}" />
<meta property="og:image:alt" content="{a(og_alt)}" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{a(meta.get("og_title", meta["title"]))}" />
<meta name="twitter:description" content="{a(meta.get("og_description", meta["description"]))}" />
<meta name="twitter:image" content="{SITE}{og}" />
<link rel="icon" href="{FAVICON}" />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&amp;family=Inter:wght@300;400;500;600;700&amp;display=swap" rel="stylesheet" />
<link rel="stylesheet" href="{ASSETS["styles.css"]}" />{player_css}
<noscript><link rel="stylesheet" href="/noscript.css" /></noscript>
<script type="application/ld+json">
{ld}
</script>
</head>"""


def pagina(src):
    raw = src.read_text(encoding="utf-8")
    m = re.match(r"\s*<!--(.*?)-->\s*", raw, re.S)
    if not m:
        raise ValueError(f"{src.name}: manca il blocco di metadati iniziale")
    meta = json.loads(m.group(1))
    corpo = espandi(raw[m.end():], meta)
    player_js = f'\n<script src="{ASSETS["video/player.js"]}"></script>' if meta.get("player") else ""
    body_cls = f' class="{a(meta["body_class"])}"' if meta.get("body_class") else ""
    doc = f"""{head(meta)}
<body{body_cls}>
{BURST_DEFS}
<div class="bg-grid" aria-hidden="true"></div>
<div class="bg-glow glow-a" aria-hidden="true"></div>
<div class="bg-glow glow-b" aria-hidden="true"></div>
{header(meta)}
<main id="main">
{corpo.strip()}
</main>
{footer()}
<script src="{ASSETS["main.js"]}"></script>{player_js}
</body>
</html>
"""
    out = ROOT / meta["out"]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc, encoding="utf-8", newline="\n")
    return meta


def sitemap(metas):
    oggi = datetime.date.today().isoformat()
    righe = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
             '        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">']
    for m in sorted(metas, key=lambda m: m.get("priorita", 0.5), reverse=True):
        if m.get("sitemap") is False:
            continue
        righe.append("  <url>")
        righe.append(f"    <loc>{SITE}{m['path']}</loc>")
        righe.append(f"    <lastmod>{oggi}</lastmod>")
        righe.append(f"    <priority>{m.get('priorita', 0.5)}</priority>")
        if m.get("og_image"):
            righe.append(f"    <image:image><image:loc>{SITE}{m['og_image']}</image:loc></image:image>")
        righe.append("  </url>")
    righe.append("</urlset>")
    (ROOT / "sitemap.xml").write_text("\n".join(righe) + "\n", encoding="utf-8", newline="\n")


def llms(metas):
    """llms.txt, la scheda del sito per i motori di ricerca basati su IA, rigenerata dai dati."""
    r = ["# Inno99", "",
         "> Inno99 è il programma di Innovalley che porta la cultura dell'innovazione nei locali del centro storico "
         "dell'Aquila, nel quadro di L'Aquila Capitale Italiana della Cultura 2026. Si articola in due verticali, "
         "gli Inno Talks e Inno Podcast.", "",
         "Inno99 è nato da un'idea di Mirko Rocci e Federico Fioriti per Innovalley Open Innovation Hub. Mirko Rocci, "
         "fisico, è ideatore e curatore del programma e conduce ogni serata. Sponsor unico del ciclo 2026 è Synergie Italia.",
         "", "## Pagine", ""]
    for m in metas:
        if m.get("sitemap") is False:
            continue
        r.append(f"- [{m['title'].split(' | ')[0]}]({SITE}{m['path']}): {m['description']}")
    r += ["", "## Appuntamenti", ""]
    for e in sorted(EVENTI, key=lambda e: -e["n"]):
        if e["stato"] == "svolto":
            r.append(f"### Inno Talks #{e['n']} · {e['titolo']}")
            r.append(f"{e['giorno']} · {e['luogo_esteso']}, L'Aquila. {e['sottotitolo']}.")
            r.append("")
            r.append(e["sintesi"])
            r.append("")
            r += [f"- {x}" for x in e.get("llms", [])]
            r.append(f"- Pagina della serata: {SITE}/inno-talks/{e['n']}/")
        elif e["stato"] == "prossimo":
            r.append(f"### Inno Talks #{e['n']} · {e['titolo']} (prossima serata)")
            r.append(f"{e['giorno']}, ore {e['ora']} · {e['luogo_esteso']}, L'Aquila. {e['sottotitolo']}.")
            r.append("")
            r += [f"- {x}" for x in e.get("llms", [])]
            r.append(f"- Pagina della serata: {SITE}/inno-talks/{e['n']}/")
        else:
            r.append(f"### Inno Talks #{e['n']} · in preparazione")
            r.append(f"{e['giorno']}. {e['sintesi']} Aggiornamenti su {SITE}/inno-talks/{e['n']}/ "
                     "oppure a eventi@inno-valley.it e al 328 82 95 361.")
        r.append("")
    r += ["## Inno Podcast", "",
          "La seconda verticale di Inno99. Gli ospiti degli Inno Talks intervistati da Mirko Rocci in formato podcast "
          "professionale. I primi episodi arrivano a ottobre 2026. " + f"{SITE}/inno-podcast/", "",
          "## L'AquiLive, l'app con tutti gli eventi di Inno99", "",
          "L'AquiLive è l'app gratuita e senza pubblicità con tutti gli eventi dell'Aquila e provincia, ideata e costruita "
          "da Mirko Rocci. Dentro c'è una sezione dedicata a Inno99, tra i Servizi esclusivi, con gli appuntamenti degli "
          "Inno Talks. Ogni evento si può salvare con un promemoria. Disponibile in sei lingue.", "",
          f"- App Store (iPhone): {APP_IOS}",
          "- Google Play (Android): https://play.google.com/store/apps/details?id=it.aqlive99.app",
          f"- Pagina dedicata: {SITE}/laquilive/", "",
          "## Rassegna stampa", "",
          f"{len(STAMPA)} uscite su {len({s['testata'] for s in STAMPA})} testate. Elenco completo con filtri su {SITE}/rassegna-stampa/", ""]
    for e in sorted([e for e in EVENTI if e["stato"] == "svolto"], key=lambda e: -e["n"]):
        voci = [s for s in STAMPA if s["evento"] == e["n"]]
        if not voci:
            continue
        r.append(f"### Inno Talks #{e['n']} · {e['titolo']}")
        for s in voci:
            url = s["url"] if s["url"].startswith("http") else SITE + s["url"]
            quando = f", {data_it(s['data'])}" if s.get("data_nota", True) else ""
            r.append(f"- {s['testata']} ({TIPI[s['tipo']].lower()}{quando}), *{s['titolo']}*. {url}")
        r.append("")
    r += ["## Domande frequenti", ""]
    for f in FAQ:
        r.append(f"**{f['q']}**  ")
        r.append(f["a"])
        r.append("")
    r += ["## Organizzazione e contatti", "",
          "Inno99 è promosso da Innovalley Cube Srl e dall'Associazione Innovalley Promotori di Innovazione "
          "(Innovalley Open Innovation Hub, https://www.inno-valley.it). Sponsor unico 2026 Synergie Italia.",
          "", "Telefono 328 82 95 361 · eventi@inno-valley.it", ""]
    (ROOT / "llms.txt").write_text("\n".join(r), encoding="utf-8", newline="\n")


def main():
    metas = [pagina(p) for p in sorted(PAGINE.glob("*.html"))]
    sitemap(metas)
    llms(metas)
    print(f"{len(metas)} pagine generate:")
    for m in metas:
        print(f"  {m['out']:<34} {m['path']}")
    print("token anti-cache:", ", ".join(f"{k}={v.split('=')[1]}" for k, v in ASSETS.items()))


if __name__ == "__main__":
    sys.exit(main())
