#!/usr/bin/env python3
"""Genera index.html a partir de data/almeria.json (solo librería estándar)."""
import json
from datetime import datetime
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "almeria.json"
OUT = ROOT / "index.html"

TAGS = {
    "mercados": "Mercados",
    "sanidad": "Sanidad vegetal",
    "clima": "Clima y agua",
    "politica": "Política agraria",
    "logistica": "Logística",
    "campo": "Campo",
}
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def fecha_larga(iso):
    d = datetime.fromisoformat(iso[:10])
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


def fecha_corta(iso):
    d = datetime.fromisoformat(iso[:10])
    return f"{d.day} {MESES[d.month - 1][:3]}"


def render_story(item):
    tag = item.get("tag", "campo")
    status = item.get("status", "auto")
    mark = (
        '<span class="mark">Revisada</span>'
        if status == "revisada"
        else '<span class="mark auto">Resumen automático</span>'
    )
    return f"""
      <li class="story" data-tag="{escape(tag)}">
        <time datetime="{escape(item['date'])}">{fecha_corta(item['date'])}</time>
        <div>
          <h3><a href="{escape(item['url'])}" rel="noopener" target="_blank">{escape(item['title'])}</a></h3>
          <p>{escape(item['summary'])}</p>
          <div class="byline">
            <span class="chip" data-tag="{escape(tag)}">{escape(TAGS.get(tag, tag))}</span>
            <span>{escape(item['source'])}</span>
            {mark}
          </div>
        </div>
      </li>"""


def build():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    items = sorted(data["items"], key=lambda i: i["date"], reverse=True)
    lead = next((i for i in items if i.get("lead")), items[0])
    rest = [i for i in items if i["id"] != lead["id"]]

    figures = "".join(
        f"""
          <li>
            <span class="num">{escape(s['value'])}</span>
            <span class="what">{escape(s['label'])}</span>
            <span class="src"><a href="{escape(s['url'])}" rel="noopener" target="_blank">{escape(s['source'])}</a></span>
          </li>"""
        for s in data.get("stats", [])
    )

    used_tags = [t for t in TAGS if any(i.get("tag") == t for i in rest)]
    buttons = '<button type="button" data-filter="todo" aria-pressed="true">Todo</button>' + "".join(
        f'<button type="button" data-filter="{t}" aria-pressed="false">{TAGS[t]}</button>'
        for t in used_tags
    )

    stories = "".join(render_story(i) for i in rest)
    sources = sorted({i["source"].split(" (")[0] for i in items})
    sources_html = "".join(f"<li>{escape(s)}</li>" for s in sources)

    html = f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Agro Almería: noticias del campo almeriense</title>
  <meta name="description" content="Lo que pasa hoy en la agricultura de Almería: mercados, plagas, clima, política agraria y logística, con enlace a cada fuente.">
  <meta name="theme-color" content="#0c1a2c">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,700&family=Instrument+Sans:wght@400;500;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="assets/styles.css">
</head>
<body>
  <header class="masthead">
    <div class="wrap">
      <a class="brand" href="./">Agro <span>Almería</span></a>
      <p class="updated">Actualizado el {fecha_larga(data['updated'])}</p>
    </div>
  </header>

  <section class="hero" aria-labelledby="lead-title">
    <div class="wrap">
      <article class="lead">
        <p class="lead-meta">{fecha_larga(lead['date'])} · {escape(lead['source'])}</p>
        <h1 id="lead-title">{escape(lead['title'])}</h1>
        <p>{escape(lead['summary'])}</p>
        <a class="go" href="{escape(lead['url'])}" rel="noopener" target="_blank">Leer la noticia original</a>
      </article>
      <aside aria-labelledby="figures-title">
        <h2 class="figures-title" id="figures-title">La provincia en cifras</h2>
        <ul class="figures">{figures}
        </ul>
      </aside>
    </div>
  </section>

  <div class="filters-bar">
    <div class="wrap">
      <div class="filters" role="group" aria-label="Filtrar noticias por tema">{buttons}</div>
    </div>
  </div>

  <main class="wrap">
    <ul class="feed">{stories}
    </ul>
    <p class="empty" id="empty" hidden>No hay noticias de este tema por ahora.</p>
  </main>

  <footer class="foot">
    <div class="wrap cols">
      <section>
        <h2>Cómo se hace esta página</h2>
        <p>Cada noticia es un resumen redactado con ayuda de inteligencia artificial y enlaza a la fuente original. Las marcadas como «Revisada» se han contrastado a mano con el medio; las de «Resumen automático» no. Ante cualquier cifra importante, consulta la fuente.</p>
      </section>
      <section>
        <h2>Fuentes consultadas</h2>
        <ul>{sources_html}</ul>
      </section>
    </div>
  </footer>
  <script src="assets/app.js" defer></script>
</body>
</html>
"""
    OUT.write_text(html, encoding="utf-8")
    print(f"index.html generado con {len(items)} noticias.")


if __name__ == "__main__":
    build()
