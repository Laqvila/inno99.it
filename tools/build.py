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
}


def icona(nome, cls="ico"):
    return f'<svg class="{cls}" viewBox="0 0 24 24" aria-hidden="true">{ICONE[nome]}</svg>'


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
    else:
        media = f'<span class="tc-soon">{burst()}</span>'
        stato = '<span class="tc-state next"><span class="pulse-dot"></span> In preparazione</span>'
        go = "Scopri le novità"
        cls = "talk-card tilt is-next"
    luogo = f' · {t(e["luogo"])}' if e.get("luogo") else ""
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
        else:
            r.append(f"### Inno Talks #{e['n']} · in preparazione")
            r.append(f"{e['giorno']}. {e['sintesi']} Aggiornamenti su {SITE}/inno-talks/{e['n']}/ "
                     "oppure a eventi@inno-valley.it e al 328 82 95 361.")
        r.append("")
    r += ["## Inno Podcast", "",
          "La seconda verticale di Inno99. Gli ospiti degli Inno Talks intervistati da Mirko Rocci in formato podcast "
          "professionale. I primi episodi arrivano a ottobre 2026. " + f"{SITE}/inno-podcast/", "",
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
