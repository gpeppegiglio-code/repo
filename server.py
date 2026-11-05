import base64
import hmac
import json
import os
import secrets
import sqlite3
import time

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA = Path(os.environ.get("DATA_DIR", str(ROOT / ".data")))
DATA.mkdir(parents=True, exist_ok=True)

DB = DATA / "board.sqlite3"

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
if not ADMIN_PASSWORD:
    raise RuntimeError(
        "Configura ADMIN_PASSWORD nelle variabili di Render."
    )

PEOPLE = [
    "LORENZO",
    "GIUSEPPE GIGLIO",
    "GIUSEPPE CEFALINO",
    "FEDERICA",
    "ROBERTO",
    "CARLO",
    "ANDREA",
    "SAMUELE",
    "SALVATORINO",
]


def connect():
    db = sqlite3.connect(DB, timeout=15)
    db.row_factory = sqlite3.Row
    return db


with connect() as db:
    db.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id TEXT PRIMARY KEY,
            kind TEXT NOT NULL,
            person TEXT NOT NULL,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            image TEXT NOT NULL,
            created INTEGER NOT NULL
        )
    """)


HTML = r"""<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#092b43">
<meta name="description"
      content="Portale per le segnalazioni e le comunicazioni del gruppo.">
<meta property="og:title" content="Ministero della Verità">
<meta property="og:description"
      content="Segnalazioni, comunicazioni e aggiornamenti del gruppo.">
<title>Ministero della Verità</title>
<link rel="stylesheet" href="/style.css">
<script src="/app.js" defer></script>
</head>

<body>
<div class="notice">
  Portale privato · Non affiliato a enti governativi
</div>

<header>
  <a class="brand" href="/">
    <img src="/logo.png" alt="Logo del gruppo">
    <span>
      MINISTERO DELLA VERITÀ
      <small>DIPARTIMENTO DELLE QUESTIONI TRA AMICI</small>
    </span>
  </a>
  <button id="share" class="outline">Condividi ↗</button>
</header>

<nav aria-label="Navigazione principale">
  <a href="#segnalazioni">Segnalazioni</a>
  <a href="#sala-stampa" id="open-news" aria-haspopup="dialog">Sala stampa</a>
  <a href="#informazioni">Il progetto</a>
  <button id="open-admin">Accesso redazione</button>
</nav>

<main>
  <section class="hero">
    <div>
      <div class="eyebrow">IL PORTALE DEL GRUPPO</div>
      <h1>Segnalazioni.<br>Ascolto.<br><em>Responsabilità.</em></h1>
      <p>
        Uno spazio dedicato alla raccolta delle segnalazioni
        e alle comunicazioni del gruppo, con serietà e rispetto.
      </p>
      <a href="#scrivi" class="gold">Invia una segnalazione →</a>
      <small>Nessun nome autore richiesto · Nessuna registrazione</small>
    </div>
    <img class="hero-logo" src="/logo.png" alt="Logo del Ministero della Verità">
  </section>

  <div class="ticker">
    <strong>ULTIM’ORA</strong>
    <span id="headline">La sala stampa è aperta.</span>
    <small>● AGGIORNAMENTO LIVE</small>
  </div>

  <section id="segnalazioni" class="section">
    <div class="heading">
      <div>
        <div class="eyebrow">OSSERVATORIO DEL GRUPPO</div>
        <h2>Le segnalazioni</h2>
      </div>
      <span id="count"></span>
    </div>

    <p class="muted">
      Consulta le segnalazioni e seleziona una persona per filtrare i risultati.
    </p>

    <div id="filters" class="filters"
         role="group" aria-label="Filtra per persona"></div>

    <div class="columns">
      <div>
        <div id="reports" aria-live="polite"></div>
        <p class="privacy">
          I contributi sono visibili a chi accede al sito.
          Non pubblicare informazioni private, insulti o accuse gravi.
          La redazione può rimuovere contenuti inappropriati.
        </p>
      </div>

      <aside id="scrivi">
        <div class="eyebrow">SPORTELLO DIGITALE</div>
        <h3>Invia una segnalazione</h3>
        <p class="muted">
          Racconta un episodio. Il nome dell’autore non viene richiesto.
        </p>

        <form id="report-form">
          <label for="person">A chi si riferisce?</label>
          <select id="person" required>
            <option value="">Seleziona una persona</option>
          </select>

          <label for="body">La tua segnalazione</label>
          <textarea id="body" rows="5" minlength="5" maxlength="2000"
                    placeholder="È successo che…" required></textarea>

          <label class="check">
            <input type="checkbox" required>
            Scrivo con rispetto e senza informazioni private.
          </label>

          <button class="primary" type="submit">
            Invia senza nome autore →
          </button>
          <p class="message" role="status"></p>
        </form>

        <p class="privacy">
          L’app non registra indirizzi IP nei propri log.
          Il servizio di hosting può conservare log tecnici:
          non è garantito anonimato assoluto.
        </p>
      </aside>
    </div>
  </section>

  <section id="informazioni" class="section about">
    <div>
      <div class="eyebrow">TRASPARENZA PRIMA DI TUTTO</div>
      <h2>Finalità del portale</h2>
    </div>
    <div>
      <p>
        Il portale raccoglie segnalazioni e comunicazioni del gruppo.
        È un servizio privato, non affiliato a enti pubblici.
      </p>
      <p>
        Le nuove segnalazioni e le notizie compaiono automaticamente
        entro pochi secondi. Usa questo spazio per confrontarti,
        senza insulti o molestie.
      </p>
    </div>
  </section>
</main>

<footer>
  MINISTERO DELLA VERITÀ
  <small>Portale privato per le segnalazioni e le comunicazioni del gruppo.</small>
</footer>

<dialog id="news-dialog" aria-labelledby="news-title">
  <button id="close-news" class="close" aria-label="Chiudi Sala stampa">×</button>
<section id="notizie" class="news-section">
    <div class="section">
      <div class="eyebrow">COMUNICAZIONI DAL GRUPPO</div>
      <h2 id="news-title">Sala stampa</h2>
      <p class="muted">
        Notizie, comunicati e aggiornamenti con testo e immagini.
      </p>
      <div id="news" class="news-grid" aria-live="polite"></div>
    </div>
  </section>
</dialog>

<dialog id="admin-dialog">
  <button id="close-admin" class="close" aria-label="Chiudi">×</button>

  <form id="login-form">
    <div class="eyebrow">AREA RISERVATA</div>
    <h2>Accesso redazione</h2>

    <label for="password">Password amministratore</label>
    <input id="password" type="password"
           autocomplete="current-password" required>

    <button class="primary">Accedi</button>
    <p class="message" role="status"></p>
  </form>

  <form id="news-form" hidden>
    <div class="eyebrow">REDAZIONE</div>
    <h2>Pubblica una notizia</h2>

    <label for="title">Titolo</label>
    <input id="title" minlength="3" maxlength="120" required>

    <label for="news-body">Testo</label>
    <textarea id="news-body" rows="4"
              minlength="5" maxlength="2000" required></textarea>

    <label for="image">Immagine · JPG, PNG, WebP · massimo 2 MB</label>
    <input id="image" type="file"
           accept="image/jpeg,image/png,image/webp" required>

    <button class="primary">Pubblica notizia →</button>
    <button id="logout" class="outline" type="button">
      Esci dalla redazione
    </button>
    <p class="message" role="status"></p>
  </form>
</dialog>

<div id="toast" role="status"></div>
</body>
</html>
"""


CSS = r"""
:root {
  --navy: #092b43;
  --deep: #061e30;
  --gold: #d5ad60;
  --paper: #f7f6f1;
  --ink: #183043;
  --muted: #65747e;
  --line: #dce0df;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  color: var(--ink);
  background: white;
  font: 15px/1.65 Arial, sans-serif;
}
button, input, select, textarea { font: inherit; }
button { cursor: pointer; }
a { color: inherit; }
button:focus-visible, a:focus-visible,
input:focus-visible, select:focus-visible, textarea:focus-visible {
  outline: 3px solid #ae7b25;
  outline-offset: 3px;
}
.notice {
  padding: 8px 6%;
  background: var(--deep);
  color: #e2e6e9;
  font-size: 11px;
}
header {
  padding: 24px 6%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
}
.brand {
  display: flex;
  align-items: center;
  gap: 16px;
  text-decoration: none;
  font: bold 23px Georgia, serif;
  letter-spacing: 1px;
}
.brand img {
  width: 78px;
  height: 78px;
  object-fit: contain;
  border-radius: 50%;
}
.brand small {
  display: block;
  margin-top: 9px;
  font: 9px Arial, sans-serif;
  letter-spacing: 2px;
}
.outline {
  background: transparent;
  border: 1px solid #b9c2c8;
  padding: 10px 15px;
  color: var(--navy);
  font-size: 12px;
}
nav {
  padding: 15px 6%;
  background: var(--navy);
  display: flex;
  align-items: center;
  gap: 30px;
  color: white;
  border-bottom: 1px solid #ffffff20;
}
nav a { text-decoration: none; font-size: 13px; }
nav button {
  margin-left: auto;
  border: 0;
  background: transparent;
  color: #d5dde2;
  font-size: 12px;
}
.hero {
  background: var(--navy);
  color: white;
  padding: 65px 9%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 60px;
}
.eyebrow {
  font-size: 10px;
  font-weight: bold;
  letter-spacing: 2px;
  color: #806030;
}
.hero .eyebrow { color: var(--gold); }
h1 {
  font: normal clamp(45px, 5vw, 72px)/1.08 Georgia, serif;
  margin: 24px 0;
}
h1 em { color: #e2bf79; }
.hero p { max-width: 440px; color: #c6d0d8; font-size: 14px; }
.hero small {
  display: block;
  margin-top: 18px;
  color: #b9c7d0;
  font-size: 10px;
}
.hero-logo {
  width: min(33vw, 360px);
  height: auto;
  border-radius: 50%;
  box-shadow: 0 15px 40px #0004;
}
.gold {
  display: inline-block;
  margin-top: 18px;
  padding: 14px 23px;
  background: var(--gold);
  color: var(--deep);
  font-size: 13px;
  font-weight: bold;
  text-decoration: none;
}
.ticker {
  display: flex;
  align-items: center;
  gap: 24px;
  background: #f0ece2;
  border-bottom: 1px solid #e4dece;
  padding: 15px 6%;
  font-size: 12px;
}
.ticker strong {
  font-size: 10px;
  color: #875b22;
  white-space: nowrap;
}
.ticker > span {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.ticker small { font-size: 9px; color: #40775f; white-space: nowrap; }
.section { max-width: 1300px; margin: auto; padding: 55px 6%; }
.heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 15px;
}
h2 { font: normal 36px/1.2 Georgia, serif; margin: 12px 0; }
h3 { font: normal 27px/1.25 Georgia, serif; margin: 15px 0; }
#count { font-size: 12px; color: var(--muted); }
.muted { color: var(--muted); font-size: 13px; }
.filters { display: flex; flex-wrap: wrap; gap: 8px; margin: 25px 0; }
.filters button {
  padding: 8px 11px;
  background: white;
  border: 1px solid var(--line);
  color: var(--ink);
  font-size: 10px;
}
.filters button.active {
  background: var(--navy);
  color: white;
  border-color: var(--navy);
}
.columns { display: grid; grid-template-columns: 1.6fr 1fr; gap: 32px; }
.card {
  border: 1px solid var(--line);
  border-top: 3px solid var(--gold);
  padding: 23px;
  margin-bottom: 16px;
  background: white;
}
.person {
  display: inline-block;
  padding: 4px 9px;
  background: #f5efdf;
  color: #795a27;
  font-size: 10px;
  font-weight: bold;
  letter-spacing: 1px;
}
.card p, .news-card p { white-space: pre-wrap; overflow-wrap: anywhere; }
.meta {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 10px;
  padding-top: 12px;
  border-top: 1px solid var(--line);
  color: var(--muted);
  font-size: 10px;
}
.privacy { font-size: 11px; color: var(--muted); line-height: 1.8; }
aside {
  align-self: start;
  padding: 27px;
  background: var(--paper);
  border: 1px solid #e8e4da;
}
label { display: block; font-size: 12px; font-weight: bold; margin: 17px 0 7px; }
input:not([type=checkbox]), select, textarea {
  width: 100%;
  padding: 11px;
  background: white;
  color: var(--ink);
  border: 1px solid #c8cfce;
}
textarea { resize: vertical; }
.check {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 11px;
  font-weight: normal;
}
.check input { margin-top: 5px; accent-color: var(--navy); }
.primary {
  width: 100%;
  border: 0;
  background: var(--navy);
  color: white;
  padding: 14px;
  margin-top: 16px;
  font-size: 12px;
}
.primary:disabled { opacity: .6; cursor: wait; }
.message { min-height: 20px; font-size: 12px; color: #7d4332; }
.news-section { background: var(--paper); border-block: 1px solid #e8e4da; }
.news-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 23px;
  margin-top: 25px;
}
.news-card { background: white; border: 1px solid var(--line); }
.news-card img { width: 100%; height: 200px; object-fit: cover; display: block; }
.news-card > div { padding: 20px; }
.news-card h3 { font-size: 24px; }
.news-card p { font-size: 13px; }
.news-card time { font-size: 10px; color: var(--muted); }
.empty {
  padding: 35px 25px;
  border: 1px dashed #cbd1ce;
  text-align: center;
  color: var(--muted);
  font-size: 13px;
}
.empty strong {
  display: block;
  font: 25px Georgia, serif;
  color: var(--navy);
  margin-bottom: 10px;
}
.news-grid .empty { grid-column: 1 / -1; }
.about { display: grid; grid-template-columns: 1fr 1fr; gap: 50px; }
.about p { color: var(--muted); font-size: 13px; }
footer {
  background: var(--deep);
  color: white;
  padding: 35px 6%;
  font: 18px Georgia, serif;
  letter-spacing: 1px;
}
footer small {
  display: block;
  margin-top: 9px;
  color: #a4b3bf;
  font: 11px Arial, sans-serif;
  letter-spacing: 0;
}
dialog {
  width: min(94vw, 500px);
  max-height: 90vh;
  overflow: auto;
  border: 1px solid var(--line);
  padding: 30px;
  color: var(--ink);
}
dialog::backdrop { background: #061e30bb; }
#news-dialog { width: min(94vw, 1100px); padding: 0; }
#news-dialog > .close { position: sticky; top: 10px; margin: 10px 16px 0 0; z-index: 1; }
#news-dialog .news-section { border: 0; }
#news-dialog .section { padding-top: 20px; }
body.modal-open { overflow: hidden; }
@media (min-width: 761px) and (max-width: 1000px) {
  #news-dialog .news-grid { grid-template-columns: repeat(2, 1fr); }
}
.close { float: right; background: transparent; border: 0; font-size: 28px; }
#news-form .outline { width: 100%; margin-top: 12px; }
.remove {
  background: none;
  border: 0;
  color: #974333;
  font-size: 11px;
  text-decoration: underline;
  margin-top: 12px;
}
#toast {
  display: none;
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  max-width: 90vw;
  background: var(--navy);
  color: white;
  padding: 12px 20px;
  z-index: 10;
  box-shadow: 0 4px 20px #0003;
  font-size: 13px;
}
#toast.show { display: block; }
@media (max-width: 760px) {
  header { padding: 18px 5%; }
  .brand { font-size: 15px; gap: 10px; letter-spacing: .3px; }
  .brand img { width: 55px; height: 55px; }
  .brand small { font-size: 7px; letter-spacing: .5px; }
  header .outline { font-size: 10px; padding: 8px; }
  nav { flex-wrap: wrap; gap: 17px; padding: 14px 5%; }
  nav a, nav button { font-size: 11px; }
  nav button { margin-left: 0; }
  .hero { padding: 40px 6%; }
  .hero-logo { display: none; }
  h1 { font-size: 51px; }
  h2 { font-size: 30px; }
  .ticker { gap: 13px; }
  .ticker small { display: none; }
  .section { padding: 38px 6%; }
  .columns, .about, .news-grid { grid-template-columns: 1fr; }
  .about { gap: 15px; }
  .filters { gap: 6px; }
  .filters button { font-size: 9px; }
}
@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto; }
}
"""


JS = r"""
const people = [
  "LORENZO", "GIUSEPPE GIGLIO", "GIUSEPPE CEFALINO",
  "FEDERICA", "ROBERTO", "CARLO", "ANDREA",
  "SAMUELE", "SALVATORINO"
];

const $ = selector => document.querySelector(selector);
let entries = [];
let selected = "";
let token = "";
let lastData = "";
let tickerIndex = 0;

function element(tag, text = "", className = "") {
  const node = document.createElement(tag);
  node.textContent = text;
  node.className = className;
  return node;
}

function formattedDate(timestamp) {
  return new Date(timestamp * 1000).toLocaleString("it-IT", {
    day: "numeric", month: "short",
    hour: "2-digit", minute: "2-digit"
  });
}

function toast(text) {
  $("#toast").textContent = text;
  $("#toast").className = "show";
  setTimeout(() => $("#toast").className = "", 4000);
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: "Bearer " + token } : {})
    }
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Operazione non riuscita");
  }
  return data;
}

function showEmpty(container, title, description) {
  const box = element("div", "", "empty");
  box.append(element("strong", title), element("span", description));
  container.append(box);
}

function renderFilters() {
  $("#filters").replaceChildren();
  ["", ...people].forEach(person => {
    const button = element(
      "button",
      person || "TUTTI",
      selected === person ? "active" : ""
    );
    button.type = "button";
    button.setAttribute("aria-pressed", selected === person);
    button.onclick = () => {
      selected = person;
      renderFilters();
      render();
    };
    $("#filters").append(button);
  });
}

function removeButton(id) {
  const button = element("button", "Rimuovi", "remove");
  button.type = "button";
  button.onclick = async () => {
    if (!confirm("Vuoi rimuovere questo contenuto?")) return;
    try {
      await api("/api/entries/" + id, { method: "DELETE" });
      await refresh(true);
    } catch (error) {
      toast(error.message);
    }
  };
  return button;
}

function updateTicker() {
  const news = entries.filter(item => item.kind === "news");
  $("#headline").textContent = news.length
    ? news[tickerIndex % news.length].title
    : "La sala stampa è aperta. Le notizie appariranno qui.";
}

function render() {
  const reports = entries.filter(
    item => item.kind === "report" &&
      (!selected || item.person === selected)
  );

  $("#count").textContent = reports.length +
    (reports.length === 1 ? " contributo" : " contributi");
  $("#reports").replaceChildren();

  if (!reports.length) {
    showEmpty(
      $("#reports"),
      "Il registro è aperto.",
      "Nessuna segnalazione" +
        (selected ? " per " + selected : "") + "."
    );
  }

  reports.forEach(item => {
    const card = element("article", "", "card");
    card.append(
      element("span", item.person, "person"),
      element("p", item.body)
    );

    const meta = element("div", "", "meta");
    meta.append(
      element("span", "AUTORE NON MOSTRATO"),
      element("time", formattedDate(item.created))
    );
    card.append(meta);

    if (token) card.append(removeButton(item.id));
    $("#reports").append(card);
  });

  $("#news").replaceChildren();
  const news = entries.filter(item => item.kind === "news");

  if (!news.length) {
    showEmpty(
      $("#news"),
      "Nessun comunicato, per ora.",
      "La redazione può pubblicare notizie con testo e immagini."
    );
  }

  news.forEach(item => {
    const card = element("article", "", "news-card");
    const image = element("img");
    image.src = item.image;
    image.alt = item.title;
    image.loading = "lazy";

    const content = element("div");
    content.append(
      element("time", formattedDate(item.created)),
      element("h3", item.title),
      element("p", item.body)
    );

    if (token) content.append(removeButton(item.id));
    card.append(image, content);
    $("#news").append(card);
  });

  updateTicker();
}

async function refresh(force = false) {
  try {
    const data = await api("/api/entries");
    const serialized = JSON.stringify(data);
    if (force || serialized !== lastData) {
      lastData = serialized;
      entries = data;
      render();
    }
  } catch (error) {
    if (!lastData) {
      $("#reports").replaceChildren();
      showEmpty(
        $("#reports"),
        "Connessione non disponibile.",
        "Riprovo automaticamente tra pochi secondi."
      );
    }
  }
}

people.forEach(person => {
  const option = element("option", person);
  option.value = person;
  $("#person").append(option);
});

$("#report-form").onsubmit = async event => {
  event.preventDefault();
  const form = event.currentTarget;
  const button = form.querySelector("button");
  const message = form.querySelector(".message");

  button.disabled = true;
  message.textContent = "";

  try {
    await api("/api/entries", {
      method: "POST",
      body: JSON.stringify({
        kind: "report",
        person: $("#person").value,
        body: $("#body").value
      })
    });
    form.reset();
    message.textContent = "Segnalazione pubblicata.";
    await refresh(true);
  } catch (error) {
    message.textContent = error.message;
  } finally {
    button.disabled = false;
  }
};

$("#open-admin").onclick = () => $("#admin-dialog").showModal();
$("#close-admin").onclick = () => $("#admin-dialog").close();

$("#login-form").onsubmit = async event => {
  event.preventDefault();
  token = $("#password").value;

  try {
    await api("/api/admin", { method: "POST" });
    $("#password").value = "";
    $("#login-form").hidden = true;
    $("#news-form").hidden = false;
    render();
  } catch (error) {
    token = "";
    $("#login-form .message").textContent = error.message;
  }
};

$("#logout").onclick = () => {
  token = "";
  $("#login-form").hidden = false;
  $("#news-form").hidden = true;
  $("#admin-dialog").close();
  render();
};

$("#news-form").onsubmit = async event => {
  event.preventDefault();
  const form = event.currentTarget;
  const button = form.querySelector(".primary");
  const message = form.querySelector(".message");

  button.disabled = true;
  message.textContent = "";

  try {
    const file = $("#image").files[0];
    if (!file || file.size > 2000000) {
      throw new Error("Scegli un’immagine fino a 2 MB.");
    }

    const image = await new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result);
      reader.onerror = () => reject(new Error("Immagine non leggibile."));
      reader.readAsDataURL(file);
    });

    await api("/api/entries", {
      method: "POST",
      body: JSON.stringify({
        kind: "news",
        title: $("#title").value,
        body: $("#news-body").value,
        image
      })
    });

    form.reset();
    message.textContent = "Notizia pubblicata.";
    await refresh(true);
  } catch (error) {
    message.textContent = error.message;
  } finally {
    button.disabled = false;
  }
};

$("#share").onclick = async () => {
  const url = location.origin;
  try {
    if (navigator.share) {
      await navigator.share({
        title: "Ministero della Verità",
        text: "Il portale degli amici",
        url
      });
    } else if (navigator.clipboard) {
      await navigator.clipboard.writeText(url);
      toast("Link copiato: incollalo su WhatsApp.");
    } else {
      toast("Copia il link dalla barra del browser.");
    }
  } catch (error) {
    if (error.name !== "AbortError") {
      toast("Copia il link dalla barra del browser.");
    }
  }
};

const newsDialog = $("#news-dialog");
$("#open-news").onclick = event => {
  event.preventDefault();
  newsDialog.showModal();
  document.body.classList.add("modal-open");
  refresh();
};
$("#close-news").onclick = () => newsDialog.close();
newsDialog.addEventListener("close", () => {
  document.body.classList.remove("modal-open");
});
newsDialog.addEventListener("click", event => {
  if (event.target !== newsDialog) return;
  const rect = newsDialog.getBoundingClientRect();
  if (event.clientX < rect.left || event.clientX > rect.right ||
      event.clientY < rect.top || event.clientY > rect.bottom) {
    newsDialog.close();
  }
});
renderFilters();
refresh();

setInterval(() => {
  if (!document.hidden) refresh();
}, 4000);

setInterval(() => {
  tickerIndex++;
  updateTicker();
}, 6000);
"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        # L'app non scrive log delle richieste o degli indirizzi IP.
        pass

    def send_content(self, status, content, content_type, cache=False):
        if isinstance(content, str):
            content = content.encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header(
            "Cache-Control",
            "public, max-age=300" if cache else "no-store",
        )
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self'; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'none'; "
            "form-action 'self'",
        )
        self.end_headers()
        self.wfile.write(content)

    def reply(self, status, data):
        self.send_content(
            status,
            json.dumps(data),
            "application/json; charset=utf-8",
        )

    def is_admin(self):
        supplied = self.headers.get("Authorization", "")
        supplied = supplied.removeprefix("Bearer ")
        return hmac.compare_digest(
            supplied.encode("utf-8"),
            ADMIN_PASSWORD.encode("utf-8"),
        )

    def allowed_origin(self):
        origin = self.headers.get("Origin")
        if not origin:
            return True
        return origin.split("://", 1)[-1] == self.headers.get("Host")

    def do_GET(self):
        path = self.path.split("?", 1)[0]

        if path == "/":
            return self.send_content(
                200, HTML, "text/html; charset=utf-8"
            )

        if path == "/style.css":
            return self.send_content(
                200, CSS, "text/css; charset=utf-8"
            )

        if path == "/app.js":
            return self.send_content(
                200, JS, "application/javascript; charset=utf-8"
            )

        if path == "/logo.png":
            logo = ROOT / "logo.png"
            if logo.is_file():
                return self.send_content(
                    200, logo.read_bytes(), "image/png", cache=True
                )
            return self.reply(404, {"error": "Logo non caricato"})

        if path == "/api/entries":
            with connect() as db:
                rows = db.execute("""
                    SELECT * FROM entries
                    ORDER BY created DESC, rowid DESC
                    LIMIT 200
                """)
                return self.reply(200, [dict(row) for row in rows])

        return self.reply(404, {"error": "Pagina non trovata"})

    def do_POST(self):
        if not self.allowed_origin():
            return self.reply(403, {"error": "Origine non consentita"})

        if self.path == "/api/admin":
            if self.is_admin():
                return self.reply(200, {"ok": True})
            return self.reply(401, {"error": "Password non corretta"})

        if self.path != "/api/entries":
            return self.reply(404, {"error": "Risorsa non trovata"})

        try:
            length = int(self.headers.get("Content-Length", "0"))

            if not 1 <= length <= 3_000_000:
                return self.reply(
                    413, {"error": "Richiesta troppo grande"}
                )

            item = json.loads(self.rfile.read(length))
            if not isinstance(item, dict):
                raise ValueError("Dati non validi")

            kind = item.get("kind")
            if kind not in ("report", "news"):
                raise ValueError("Tipo di contenuto non valido")

            if kind == "news" and not self.is_admin():
                return self.reply(
                    401,
                    {"error": "Accedi alla redazione per pubblicare"},
                )

            body = item.get("body", "")
            if not isinstance(body, str):
                raise ValueError("Testo non valido")
            body = body.strip()

            if not 5 <= len(body) <= 2000:
                raise ValueError(
                    "Il testo deve contenere da 5 a 2000 caratteri"
                )

            person = ""
            title = ""
            image = ""

            if kind == "report":
                person = item.get("person")
                if person not in PEOPLE:
                    raise ValueError("Seleziona una persona")

            if kind == "news":
                title = item.get("title", "")
                if not isinstance(title, str):
                    raise ValueError("Titolo non valido")
                title = title.strip()

                if not 3 <= len(title) <= 120:
                    raise ValueError(
                        "Il titolo deve contenere da 3 a 120 caratteri"
                    )

                image = item.get("image", "")
                allowed_prefixes = (
                    "data:image/png;base64,",
                    "data:image/jpeg;base64,",
                    "data:image/webp;base64,",
                )

                if (
                    not isinstance(image, str)
                    or not image.startswith(allowed_prefixes)
                ):
                    raise ValueError(
                        "Carica un’immagine PNG, JPG o WebP"
                    )

                raw = base64.b64decode(
                    image.split(",", 1)[1], validate=True
                )

                is_png = raw.startswith(b"\x89PNG\r\n\x1a\n")
                is_jpeg = raw.startswith(b"\xff\xd8\xff")
                is_webp = (
                    raw.startswith(b"RIFF")
                    and raw[8:12] == b"WEBP"
                )

                if not (is_png or is_jpeg or is_webp):
                    raise ValueError("File immagine non valido")

                if len(raw) > 2_000_000:
                    raise ValueError(
                        "L’immagine deve essere inferiore a 2 MB"
                    )

            with connect() as db:
                db.execute(
                    "INSERT INTO entries VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        secrets.token_hex(12),
                        kind,
                        person,
                        title,
                        body,
                        image,
                        int(time.time()),
                    ),
                )

            return self.reply(201, {"ok": True})

        except (ValueError, TypeError, UnicodeError):
            return self.reply(
                400,
                {"error": "Dati non validi: controlla testo e immagine"},
            )

    def do_DELETE(self):
        if not self.allowed_origin():
            return self.reply(403, {"error": "Origine non consentita"})

        if not self.is_admin():
            return self.reply(
                401, {"error": "Accesso amministratore richiesto"}
            )

        if not self.path.startswith("/api/entries/"):
            return self.reply(404, {"error": "Risorsa non trovata"})

        entry_id = self.path.rsplit("/", 1)[-1]
        with connect() as db:
            db.execute("DELETE FROM entries WHERE id = ?", (entry_id,))

        return self.reply(200, {"ok": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    print("Ministero della Verità: avvio server", flush=True)
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()
