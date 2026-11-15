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


ICONOS = {  # iconos sencillos (trazo) para cada tema
    "mercados": '<path d="M4 19V9M10 19V5M16 19v-7M22 19H2"/>',
    "sanidad": '<path d="M12 3c3 3 5 6 5 9a5 5 0 0 1-10 0c0-3 2-6 5-9z"/><path d="M12 12v5"/>',
    "clima": '<path d="M7 17a4 4 0 0 1 0-8 5 5 0 0 1 9.5-1A4.5 4.5 0 0 1 17 17z"/><path d="M9 20l1-2M13 20l1-2"/>',
    "politica": '<path d="M4 20h16M6 20V10M12 20V10M18 20V10M3 10l9-6 9 6z"/>',
    "logistica": '<path d="M2 7h12v9H2zM14 10h4l3 3v3h-7"/><circle cx="6" cy="17.5" r="1.6"/><circle cx="17" cy="17.5" r="1.6"/>',
    "campo": '<path d="M3 20V12a9 9 0 0 1 18 0v8M12 3v17M7.5 5.5v14.5M16.5 5.5v14.5"/>',
    "innovacion": '<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2V16h5v-.1c0-.8.4-1.5 1-2A6 6 0 0 0 12 3z"/>',
}


def icono(tag):
    return (f'<svg class="ico" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" '
            f'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONOS.get(tag, ICONOS["campo"])}</svg>')


def num_es(v, dec, signed=False):
    t = f"{abs(v):.{dec}f}".replace(".", ",")
    return ("−" if v < 0 else "+" if signed and v > 0 else "") + t


def render_chart(c):
    dec = c.get("decimals", 1)
    vals = [b["value"] for b in c["bars"]]
    lo, hi = min(0, min(vals)), max(0, max(vals))
    span = (hi - lo) or 1
    cero = -lo / span * 100
    filas = ""
    for b in c["bars"]:
        v = b["value"]
        ancho = abs(v) / span * 100
        izq = cero if v >= 0 else cero - ancho
        cls = "neg" if v < 0 else "pos"
        filas += f"""
          <li>
            <span class="lab">{escape(b['label'])}<small>{escape(b['src'])}</small></span>
            <span class="track"><i class="bar {cls}" style="left:{izq:.1f}%;width:{ancho:.1f}%"></i><i class="zero" style="left:{cero:.1f}%"></i></span>
            <span class="val">{num_es(v, dec, c.get('signed', False))} {escape(c['unit'])}</span>
          </li>"""
    return f"""
      <figure class="chart">
        <figcaption><h3>{escape(c['title'])}</h3><p>{escape(c.get('intro', ''))}</p></figcaption>
        <ul class="bars">{filas}
        </ul>
      </figure>"""


def render_story(item):
    tag = item.get("tag", "campo")
    status = item.get("status", "auto")
    mark = (
        '<span class="mark">Revisada</span>'
        if status == "revisada"
        else '<span class="mark auto">Resumen automático</span>'
    )
    return f"""
      <li class="story" id="{escape(item['id'])}" data-tag="{escape(tag)}">
        <div class="when"><span class="tico" data-tag="{escape(tag)}">{icono(tag)}</span><time datetime="{escape(item['date'])}">{fecha_corta(item['date'])}</time></div>
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
    charts = [c for c in data.get("charts", []) if c.get("date") and 0 <= antiguedad(c, hoy) <= DIAS_MAX]
    charts_html = "".join(render_chart(c) for c in charts)
    charts_section = f"""
  <section class="charts" id="graficos" aria-labelledby="charts-title">
    <div class="wrap">
      <h2 id="charts-title">Almería en gráficos</h2>
      <div class="chart-grid">{charts_html}
      </div>
    </div>
  </section>""" if charts else ""
    ultimas = "".join(
        f'<li><a href="#{"destacada" if i is lead else escape(i["id"])}">{escape(i["title"])}</a></li>' for i in items[:4])
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
  <title>Agro Actualidad: Almería hoy</title>
  <meta name="description" content="Lo que pasa hoy en la agricultura de Almería: mercados, plagas, clima, política agraria y logística, con enlace a cada fuente.">
  <meta name="theme-color" content="#0c1a2c">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,700&family=Instrument+Sans:wght@400;500;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="assets/styles.css">
</head>
<body>
  <header class="masthead">
    <div class="wrap bar">
      <a class="logo" href="./" aria-label="Agro Actualidad, inicio"><img src="assets/logo.png" width="790" height="216" alt="Agro Actualidad: del campo al mercado global"></a>
      <nav class="tabs" aria-label="Secciones">
        <div class="tab">
          <button type="button" aria-expanded="false" aria-controls="p-almeria" aria-current="page">Almería</button>
          <div class="panel" id="p-almeria" hidden>
            <p class="panel-intro">Agricultura almeriense, al día.</p>
            <ul class="panel-list">{ultimas}</ul>
            <a class="panel-go" href="#graficos">Ver gráficos</a>
          </div>
        </div>
        <div class="tab">
          <button type="button" aria-expanded="false" aria-controls="p-mercados">Mercados</button>
          <div class="panel" id="p-mercados" hidden>
            <p class="panel-intro"><strong>Próximamente.</strong> Precios en origen, cotizaciones, exportaciones y gráficos de evolución.</p>
          </div>
        </div>
        <div class="tab">
          <button type="button" aria-expanded="false" aria-controls="p-innovacion">Innovación y productos</button>
          <div class="panel" id="p-innovacion" hidden>
            <p class="panel-intro"><strong>Próximamente.</strong> Variedades nuevas, maquinaria, bioinsumos, envases y lanzamientos del sector.</p>
          </div>
        </div>
        <div class="tab">
          <button type="button" aria-expanded="false" aria-controls="p-ia">IA y agricultura de precisión</button>
          <div class="panel" id="p-ia" hidden>
            <p class="panel-intro"><strong>Próximamente.</strong> Sensores, robots, drones, riego inteligente e inteligencia artificial aplicada al campo.</p>
          </div>
        </div>
        <div class="tab">
          <button type="button" aria-expanded="false" aria-controls="p-mundo">Mundo</button>
          <div class="panel" id="p-mundo" hidden>
            <p class="panel-intro"><strong>Próximamente.</strong> Lo que mueve la agricultura en el resto del mundo: cosechas, comercio y política agraria.</p>
          </div>
        </div>
      </nav>
    </div>
  </header>

  <section class="hero" aria-labelledby="lead-title">
    <div class="wrap">
      <article class="lead" id="destacada">
        <p class="updated">Revisado el {fecha_larga(data.get('checked', data['updated']))}. Última noticia nueva: {fecha_larga(data['updated'])}.</p>
        <p class="lead-meta">{fecha_larga(lead['date'])} · {escape(lead['source'])}</p>
        <h1 id="lead-title">{escape(lead['title'])}</h1>
        <p>{escape(lead['summary'])}</p>
        <a class="go" href="{escape(lead['url'])}" rel="noopener" target="_blank">Leer la noticia original</a>
      </article>
{aside}
    </div>
  </section>

{charts_section}

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
