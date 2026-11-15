#!/usr/bin/env python3
"""Genera index.html a partir de data/almeria.json (solo librería estándar)."""
import json
from datetime import date, datetime, timedelta
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
    "innovacion": "Innovación e IA",
}
DIAS_MAX = 30          # una noticia desaparece de la web a los 30 días de su fecha
DIAS_FRESCAS = 7       # «noticias de los últimos días»
MAX_NOTICIAS_WEB = 8   # tope de noticias visibles (la web debe quedar corta)
HUECOS_FRESCOS = 3     # huecos reservados a las noticias más recientes
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def fecha_larga(iso):
    d = datetime.fromisoformat(iso[:10])
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


def fecha_corta(iso):
    d = datetime.fromisoformat(iso[:10])
    return f"{d.day} {MESES[d.month - 1][:3]}"


def antiguedad(item, hoy):
    return (hoy - datetime.fromisoformat(item["date"][:10]).date()).days


def vigentes(items, hoy):
    """Noticias de los últimos 30 días (y no futuras por error de fecha)."""
    return [i for i in items if -1 <= antiguedad(i, hoy) <= DIAS_MAX]


def seleccionar(items, hoy):
    """Elige las noticias visibles: vigentes, con tope, priorizando lo reciente y lo importante.

    1) Se reservan hasta HUECOS_FRESCOS huecos para las más recientes de los últimos 7 días.
    2) El resto se rellena por importancia (1-5) y, a igualdad, por fecha.
    """
    vivas = vigentes(items, hoy)
    if len(vivas) <= MAX_NOTICIAS_WEB:
        return sorted(vivas, key=lambda i: i["date"], reverse=True)
    por_fecha = sorted(vivas, key=lambda i: i["date"], reverse=True)
    frescas = [i for i in por_fecha if antiguedad(i, hoy) <= DIAS_FRESCAS][:HUECOS_FRESCOS]
    ids = {i["id"] for i in frescas}
    resto = sorted((i for i in vivas if i["id"] not in ids),
                   key=lambda i: (i.get("importancia", 3), i["date"]), reverse=True)
    elegidas = frescas + resto[:MAX_NOTICIAS_WEB - len(frescas)]
    return sorted(elegidas, key=lambda i: i["date"], reverse=True)


def elegir_destacada(items, hoy):
    """Destacada: la más importante de los últimos días; si no hay, la más reciente."""
    frescas = [i for i in items if antiguedad(i, hoy) <= DIAS_FRESCAS]
    if frescas:
        return max(frescas, key=lambda i: (i.get("importancia", 3), i["date"]))
    return items[0]


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


def build(hoy=None):
    hoy = hoy or date.today()
    data = json.loads(DATA.read_text(encoding="utf-8"))
    items = seleccionar(data["items"], hoy)
    if not items:
        raise SystemExit("No hay noticias de los últimos 30 días: no se regenera la web.")
    lead = elegir_destacada(items, hoy)
    rest = [i for i in items if i["id"] != lead["id"]]

    stats = [x for x in data.get("stats", [])
             if x.get("date") and 0 <= antiguedad(x, hoy) <= DIAS_MAX]
    figures = "".join(
        f"""
          <li>
            <span class="num">{escape(s['value'])}</span>
            <span class="what">{escape(s['label'])}</span>
            <span class="src"><a href="{escape(s['url'])}" rel="noopener" target="_blank">{escape(s['source'])}</a></span>
          </li>"""
        for s in stats
    )
    aside = f"""
      <aside aria-labelledby="figures-title">
        <h2 class="figures-title" id="figures-title">La provincia en cifras</h2>
        <ul class="figures">{figures}
        </ul>
      </aside>""" if len(stats) >= 2 else ""

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
      <p class="updated">Revisado el {fecha_larga(data.get('checked', data['updated']))}. Última noticia nueva: {fecha_larga(data['updated'])}.</p>
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
{aside}
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
