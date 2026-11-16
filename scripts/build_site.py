#!/usr/bin/env python3
"""Genera index.html a partir de data/almeria.json (solo librería estándar)."""
import json
from datetime import date, datetime, timedelta
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "almeria.json"
OUT = ROOT / "index.html"
MERCADOS = ROOT / "data" / "mercados.json"
MERCADOS_OUT = ROOT / "mercados.html"

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
ESTILOS = r"""
/* Agro Almería · tema azul profundo, pensado para lectura larga */
:root {
  --bg: #0c1a2c;
  --bg-deep: #091424;
  --surface: #13284a;
  --line: #234266;
  --text: #e8eff8;
  --muted: #a3b7cd;
  --accent: #6fd3c7;
  --accent-ink: #062a2a;
  --max: 1120px;
  --gutter: clamp(18px, 4vw, 40px);
}

* { box-sizing: border-box; }
html { color-scheme: dark; }

body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: "Instrument Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
  font-size: 1.0625rem;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}

a { color: inherit; text-decoration-color: color-mix(in srgb, var(--accent) 55%, transparent); text-underline-offset: 3px; }
a:hover { color: var(--accent); }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; border-radius: 3px; }

.wrap { max-width: var(--max); margin: 0 auto; padding: 0 var(--gutter); }

h1, h2, h3 {
  font-family: "Bricolage Grotesque", "Instrument Sans", system-ui, sans-serif;
  font-weight: 700;
  line-height: 1.12;
  letter-spacing: -0.015em;
  margin: 0;
}

/* Cabecera: logo a la izquierda, pestañas desplegables a la derecha */
.masthead { position: relative; background: var(--bg-deep); border-bottom: 1px solid var(--line); z-index: 20; }
.masthead .bar { display: flex; align-items: center; justify-content: space-between; gap: 12px 28px; flex-wrap: wrap; padding-top: 12px; padding-bottom: 12px; }
.logo { display: block; background: #f6faf6; border-radius: 12px; padding: 6px 14px; line-height: 0; }
.logo img { height: 50px; width: auto; display: block; }
.updated { color: var(--muted); font-size: 0.9rem; margin: 0 0 18px; }

.tabs { display: flex; flex-wrap: wrap; gap: 2px 6px; }
.tab > button {
  font: inherit; font-size: 0.97rem; font-weight: 500; color: var(--text); background: none; border: 0;
  padding: 10px 14px; border-radius: 8px; cursor: pointer; display: inline-flex; align-items: center; gap: 8px;
}
.tab > button::after { content: ""; width: 7px; height: 7px; border-right: 1.6px solid currentColor; border-bottom: 1.6px solid currentColor; transform: rotate(45deg) translateY(-2px); opacity: .7; }
.tab > button[aria-expanded="true"] { background: var(--surface); }
.tab > button[aria-expanded="true"]::after { transform: rotate(225deg) translateY(-2px); }
.tab > button:hover { background: color-mix(in srgb, var(--surface) 70%, transparent); }
.tab > button[aria-current="page"] { box-shadow: inset 0 -2px 0 var(--accent); border-radius: 8px 8px 0 0; }
.panel {
  position: absolute; right: var(--gutter); top: 100%; width: min(380px, calc(100vw - 2 * var(--gutter)));
  background: var(--surface); border: 1px solid var(--line); border-radius: 0 0 14px 14px;
  padding: 18px 20px; box-shadow: 0 18px 40px rgba(0,0,0,.35);
}
.panel[hidden] { display: none; }
.panel-intro { margin: 0; color: #cbd9e8; font-size: .97rem; }
.panel-intro strong { color: var(--accent); font-weight: 600; }
.panel-list { list-style: none; margin: 14px 0 0; padding: 0; display: grid; gap: 10px; font-size: .93rem; }
.panel-list a { text-decoration: none; display: block; padding-left: 12px; border-left: 2px solid var(--line); }
.panel-list a:hover { border-left-color: var(--accent); }
.panel-go { display: inline-block; margin-top: 14px; font-weight: 600; color: var(--accent); }

/* Gráficos */
.charts { padding: clamp(28px, 5vw, 48px) 0; border-bottom: 1px solid var(--line); background: var(--bg); }
.charts h2 { font-size: 1.5rem; margin-bottom: 20px; }
.chart-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 420px), 1fr)); gap: 20px; }
.chart { margin: 0; background: var(--surface); border: 1px solid var(--line); border-radius: 14px; padding: 20px 22px 8px; }
.chart h3 { font-size: 1.1rem; }
.chart figcaption p { color: var(--muted); font-size: .86rem; margin: 6px 0 14px; max-width: 60ch; }
.bars { list-style: none; margin: 0; padding: 0; }
.bars li { display: grid; grid-template-columns: minmax(0, 1.1fr) minmax(0, 1.4fr) auto; gap: 12px; align-items: center; padding: 8px 0; border-top: 1px solid color-mix(in srgb, var(--line) 60%, transparent); }
.bars .lab { font-size: .93rem; line-height: 1.25; }
.bars .lab small { display: block; color: var(--muted); font-size: .76rem; margin-top: 2px; }
.bars .track { position: relative; height: 14px; border-radius: 4px; background: color-mix(in srgb, var(--bg) 55%, transparent); }
.bars .bar { position: absolute; top: 0; bottom: 0; border-radius: 4px; }
.bars .pos { background: var(--accent); }
.bars .neg { background: #f0b45a; }
.bars .zero { position: absolute; top: -3px; bottom: -3px; width: 1px; background: var(--muted); opacity: .6; }
.bars .val { font-variant-numeric: tabular-nums; font-weight: 600; font-size: .93rem; min-width: 5.5em; text-align: right; }
@media (max-width: 520px) { .bars li { grid-template-columns: 1fr auto; } .bars .track { grid-column: 1 / -1; order: 3; } }

/* Iconos de tema */
.when { display: flex; flex-direction: column; align-items: flex-start; gap: 8px; }
.tico { display: inline-grid; place-items: center; width: 38px; height: 38px; border-radius: 10px; background: var(--surface); color: var(--accent); border: 1px solid var(--line); }
.tico[data-tag="sanidad"] { color: #f0b45a; }
.tico[data-tag="clima"] { color: #8fb8ff; }
.tico[data-tag="politica"] { color: #c9b6ff; }
.tico[data-tag="logistica"] { color: #ffa98f; }

/* Portada: tejado de invernadero multicapilla como trama de fondo */
.hero {
  background-color: var(--bg-deep);
  background-image:
    url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='56' viewBox='0 0 160 56'%3E%3Cpath d='M0 56 L40 12 L80 56 L120 12 L160 56' fill='none' stroke='%236fd3c7' stroke-opacity='.10' stroke-width='1.2'/%3E%3C/svg%3E"),
    linear-gradient(180deg, rgba(9,20,36,0) 55%, var(--bg) 100%);
  background-repeat: repeat, no-repeat;
  border-bottom: 1px solid var(--line);
}
.hero .wrap {
  display: grid;
  grid-template-columns: minmax(0, 1.55fr) minmax(0, 1fr);
  gap: clamp(28px, 5vw, 72px);
  padding-top: clamp(36px, 6vw, 72px);
  padding-bottom: clamp(40px, 6vw, 72px);
  align-items: start;
}
.lead-meta { color: var(--muted); font-size: 0.95rem; margin: 0 0 14px; }
.lead h1 { font-size: clamp(2rem, 4.6vw, 3.4rem); max-width: 22ch; }
.lead p { color: #cbd9e8; max-width: 62ch; margin: 22px 0 0; }
.lead .go {
  display: inline-block; margin-top: 26px; padding: 11px 20px;
  background: var(--accent); color: var(--accent-ink); font-weight: 600;
  border-radius: 8px; text-decoration: none;
}
.lead .go:hover { background: #8fe0d6; color: var(--accent-ink); }

.figures { margin: 0; padding: 0; list-style: none; border-top: 1px solid var(--line); }
.figures-title { font-size: 1.05rem; color: var(--muted); font-weight: 500; margin: 0 0 14px; font-family: inherit; letter-spacing: 0; }
.figures li { padding: 16px 0; border-bottom: 1px solid var(--line); }
.figures .num { display: block; font-family: "Bricolage Grotesque", sans-serif; font-weight: 700; font-size: 2rem; line-height: 1.1; }
.figures .what { display: block; color: #cbd9e8; font-size: 0.95rem; margin-top: 4px; }
.figures .src { display: block; color: var(--muted); font-size: 0.85rem; margin-top: 6px; }

/* Barra de filtros */
.filters-bar { position: sticky; top: 0; z-index: 5; background: color-mix(in srgb, var(--bg) 92%, transparent); backdrop-filter: blur(8px); border-bottom: 1px solid var(--line); }
.filters { display: flex; gap: 8px; padding: 14px 0; overflow-x: auto; scrollbar-width: thin; }
.filters button {
  flex: 0 0 auto; font: inherit; font-size: 0.95rem; color: var(--text);
  background: transparent; border: 1px solid var(--line); border-radius: 999px;
  padding: 6px 15px; cursor: pointer;
}
.filters button:hover { border-color: var(--accent); }
.filters button[aria-pressed="true"] { background: var(--accent); border-color: var(--accent); color: var(--accent-ink); font-weight: 600; }

/* Lista de noticias */
.feed { list-style: none; margin: 0; padding: 12px 0 8px; }
.story {
  display: grid; grid-template-columns: 96px minmax(0, 1fr); gap: 8px 28px;
  padding: 28px 0; border-bottom: 1px solid var(--line);
}
.story[hidden] { display: none; }
.story time { color: var(--muted); font-size: 0.95rem; }
.story h3 { font-size: clamp(1.25rem, 2.4vw, 1.6rem); max-width: 34ch; }
.story h3 a { text-decoration: none; }
.story h3 a:hover { text-decoration: underline; text-decoration-color: var(--accent); }
.story p { color: #cbd9e8; margin: 12px 0 0; max-width: 68ch; }
.story .byline { color: var(--muted); font-size: 0.9rem; margin-top: 12px; display: flex; flex-wrap: wrap; gap: 6px 14px; align-items: center; }
.chip { display: inline-flex; align-items: center; gap: 6px; }
.chip::before { content: ""; width: 8px; height: 8px; border-radius: 50%; background: var(--dot, var(--accent)); }
.chip[data-tag="mercados"] { --dot: #6fd3c7; }
.chip[data-tag="sanidad"] { --dot: #f0a58a; }
.chip[data-tag="clima"] { --dot: #7fb2ff; }
.chip[data-tag="politica"] { --dot: #d6b8ff; }
.chip[data-tag="logistica"] { --dot: #e9cf99; }
.chip[data-tag="campo"] { --dot: #9fdc8e; }
.mark { border: 1px solid var(--line); border-radius: 6px; padding: 1px 8px; font-size: 0.82rem; }
.mark.auto { border-color: #8a7a4a; color: #e9cf99; }
.empty { padding: 40px 0; color: var(--muted); }

/* Pie */
.foot { background: var(--bg-deep); border-top: 1px solid var(--line); margin-top: 24px; padding: 40px 0 56px; color: var(--muted); font-size: 0.95rem; }
.foot .cols { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 32px; }
.foot h2 { font-size: 1.05rem; color: var(--text); margin-bottom: 8px; }
.foot p, .foot ul { margin: 0; max-width: 56ch; }
.foot ul { padding-left: 1.1em; }

@media (max-width: 860px) {
  .hero .wrap { grid-template-columns: 1fr; }
  .story { grid-template-columns: 1fr; gap: 4px; }
  .when { flex-direction: row; align-items: center; gap: 10px; }
  .foot .cols { grid-template-columns: 1fr; }
}

@media (prefers-reduced-motion: reduce) {
  * { scroll-behavior: auto !important; transition: none !important; }
}

/* Ajustes de cabecera: una sola fila en pantallas anchas */
.masthead .wrap { max-width: 1320px; }
.logo img { height: 46px; }
.tab > button { padding: 10px 11px; font-size: 0.94rem; }
.tabs { gap: 0 2px; }

/* Página de Mercados */
.saltos { display: grid; gap: 8px; }
.saltos a { display: block; padding: 12px 16px; border: 1px solid var(--line); border-radius: 10px; background: var(--surface); text-decoration: none; font-weight: 600; }
.saltos a:hover { border-color: var(--accent); color: var(--text); }
.nota { color: var(--muted); font-size: .88rem; margin: 14px 0 0; }
.mercado { padding-top: clamp(28px, 5vw, 48px); scroll-margin-top: 20px; }
.mercado + .mercado { border-top: 1px solid var(--line); margin-top: 20px; }
.mercado h2 { font-size: clamp(1.4rem, 3vw, 1.9rem); display: flex; align-items: center; gap: 12px; }
.mercado .cuenta { font-family: "Instrument Sans", sans-serif; font-size: .8rem; font-weight: 600; color: var(--accent); border: 1px solid var(--line); border-radius: 999px; padding: 2px 10px; }
.empty-sec { color: var(--muted); }
.chip.ajeno { font-style: italic; }

"""

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
            {f'<span class="chip ajeno">Desde: {escape(item["prestada"])}</span>' if item.get("prestada") else ''}
            <span>{escape(item['source'])}</span>
            {mark}
          </div>
        </div>
      </li>"""


AMBITOS = {
    "almeria": "El mercado en Almería",
    "espana": "El mercado en España",
    "europa": "El mercado en Europa",
    "mundo": "El mercado en el mundo",
}
MAX_SECCION = 6        # tope de noticias por cada uno de los cuatro mercados
MIN_SECCION = 3        # por debajo de esto, la sección se completa con otras


def seccion_mercado(items, ambito, hoy, usados):
    """Noticias de un ámbito; si hay pocas, completa con las de otros mercados."""
    propias = [i for i in vigentes(items, hoy) if i.get("ambito") == ambito and i["id"] not in usados]
    elegidas = seleccionar(propias, hoy)[:MAX_SECCION]
    if len(elegidas) < MIN_SECCION:
        ids = {i["id"] for i in elegidas} | usados
        otras = [i for i in vigentes(items, hoy) if i["id"] not in ids]
        otras.sort(key=lambda i: (i.get("importancia", 3), i["date"]), reverse=True)
        for extra in otras[:MIN_SECCION - len(elegidas)]:
            copia = dict(extra)
            copia["prestada"] = AMBITOS.get(extra.get("ambito", ""), "Otros mercados")
            elegidas.append(copia)
        elegidas.sort(key=lambda i: i["date"], reverse=True)
    usados.update(i["id"] for i in elegidas)
    return elegidas


def cabecera(activa, data, enlaces):
    """Barra superior con el logo y las cinco pestañas desplegables."""
    pestanas = ""
    for clave, titulo, destino, panel in enlaces:
        actual = ' aria-current="page"' if clave == activa else ""
        pestanas += f'''
        <div class="tab">
          <button type="button" aria-expanded="false" aria-controls="p-{clave}"{actual}>{titulo}</button>
          <div class="panel" id="p-{clave}" hidden>{panel}
            {f'<a class="panel-go" href="{destino}">Abrir {titulo}</a>' if destino else ''}
          </div>
        </div>'''
    return f'''  <header class="masthead">
    <div class="wrap bar">
      <a class="logo" href="./" aria-label="Agro Actualidad, inicio"><img src="assets/logo.png" width="790" height="216" alt="Agro Actualidad: del campo al mercado global"></a>
      <nav class="tabs" aria-label="Secciones">{pestanas}
      </nav>
    </div>
  </header>'''


PROXIMAMENTE = {
    "innovacion": ("Innovación y productos", "Variedades nuevas, maquinaria, bioinsumos, envases y lanzamientos del sector."),
    "ia": ("IA y agricultura de precisión", "Sensores, robots, drones, riego inteligente e inteligencia artificial aplicada al campo."),
    "mundo": ("Mundo", "Lo que mueve la agricultura en el resto del mundo: cosechas, comercio y política agraria."),
}


def pestanas(activa, lista_almeria, lista_mercados):
    base = "" if activa == "almeria" else ""
    enlaces = [
        ("almeria", "Almería", "index.html" if activa != "almeria" else "",
         f'<p class="panel-intro">Agricultura almeriense, al día.</p><ul class="panel-list">{lista_almeria}</ul>'),
        ("mercados", "Mercados", "mercados.html" if activa != "mercados" else "",
         f'<p class="panel-intro">Precios, campañas y comercio, de Almería al mundo.</p><ul class="panel-list">{lista_mercados}</ul>'),
    ]
    for clave, (titulo, texto) in PROXIMAMENTE.items():
        enlaces.append((clave, titulo, "",
                        f'<p class="panel-intro"><strong>Próximamente.</strong> {texto}</p>'))
    return enlaces


def pagina(titulo, descripcion, cabecera_html, cuerpo, fuentes):
    sources_html = "".join(f"<li>{escape(s)}</li>" for s in fuentes)
    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(titulo)}</title>
  <meta name="description" content="{escape(descripcion)}">
  <meta name="theme-color" content="#0c1a2c">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,700&family=Instrument+Sans:wght@400;500;600&display=swap" rel="stylesheet">
  <style>{ESTILOS}</style>
</head>
<body>
{cabecera_html}
{cuerpo}
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


def bloque_graficos(data, hoy, titulo):
    charts = [c for c in data.get("charts", []) if c.get("date") and 0 <= antiguedad(c, hoy) <= DIAS_MAX]
    if not charts:
        return ""
    cuerpo = "".join(render_chart(c) for c in charts)
    return f"""
  <section class="charts" id="graficos" aria-labelledby="charts-title">
    <div class="wrap">
      <h2 id="charts-title">{escape(titulo)}</h2>
      <div class="chart-grid">{cuerpo}
      </div>
    </div>
  </section>"""


def indice(items, lead=None):
    return "".join(
        f'<li><a href="#{"destacada" if lead is not None and i is lead else escape(i["id"])}">{escape(i["title"])}</a></li>'
        for i in items[:4])


def build(hoy=None):
    """Genera las dos páginas: Almería (index.html) y Mercados (mercados.html)."""
    hoy = hoy or date.today()
    almeria = json.loads(DATA.read_text(encoding="utf-8"))
    mercados = json.loads(MERCADOS.read_text(encoding="utf-8")) if MERCADOS.exists() else {"items": []}

    items = seleccionar(almeria["items"], hoy)
    if not items:
        raise SystemExit("No hay noticias de los últimos 30 días: no se regenera la web.")
    lead = elegir_destacada(items, hoy)
    rest = [i for i in items if i["id"] != lead["id"]]

    secciones = {}
    usados = set()
    for ambito in AMBITOS:
        secciones[ambito] = seccion_mercado(mercados.get("items", []), ambito, hoy, usados)
    todas_mercados = [i for lista in secciones.values() for i in lista]

    lista_almeria = indice(items, lead)
    lista_mercados = "".join(
        f'<li><a href="mercados.html#m-{clave}">{escape(AMBITOS[clave])}</a></li>' for clave in AMBITOS)

    # ---------- Página 1: Almería ----------
    stats = [x for x in almeria.get("stats", []) if x.get("date") and 0 <= antiguedad(x, hoy) <= DIAS_MAX]
    figures = "".join(
        f"""
          <li>
            <span class="num">{escape(s['value'])}</span>
            <span class="what">{escape(s['label'])}</span>
            <span class="src"><a href="{escape(s['url'])}" rel="noopener" target="_blank">{escape(s['source'])}</a></span>
          </li>"""
        for s in stats)
    aside = f"""
      <aside aria-labelledby="figures-title">
        <h2 class="figures-title" id="figures-title">La provincia en cifras</h2>
        <ul class="figures">{figures}
        </ul>
      </aside>""" if len(stats) >= 2 else ""

    used_tags = [t for t in TAGS if any(i.get("tag") == t for i in rest)]
    buttons = '<button type="button" data-filter="todo" aria-pressed="true">Todo</button>' + "".join(
        f'<button type="button" data-filter="{t}" aria-pressed="false">{TAGS[t]}</button>'
        for t in used_tags)

    cuerpo = f"""
  <section class="hero" aria-labelledby="lead-title">
    <div class="wrap">
      <article class="lead" id="destacada">
        <p class="updated">Revisado el {fecha_larga(almeria.get('checked', almeria['updated']))}. Última noticia nueva: {fecha_larga(almeria['updated'])}.</p>
        <p class="lead-meta">{fecha_larga(lead['date'])} · {escape(lead['source'])}</p>
        <h1 id="lead-title">{escape(lead['title'])}</h1>
        <p>{escape(lead['summary'])}</p>
        <a class="go" href="{escape(lead['url'])}" rel="noopener" target="_blank">Leer la noticia original</a>
      </article>
{aside}
    </div>
  </section>
{bloque_graficos(almeria, hoy, "Almería en gráficos")}

  <div class="filters-bar">
    <div class="wrap">
      <div class="filters" role="group" aria-label="Filtrar noticias por tema">{buttons}</div>
    </div>
  </div>

  <main class="wrap">
    <ul class="feed">{"".join(render_story(i) for i in rest)}
    </ul>
    <p class="empty" id="empty" hidden>No hay noticias de este tema por ahora.</p>
  </main>"""

    OUT.write_text(pagina(
        "Agro Actualidad: Almería hoy",
        "Lo que pasa hoy en la agricultura de Almería: mercados, plagas, clima, política agraria y logística, con enlace a cada fuente.",
        cabecera("almeria", almeria, pestanas("almeria", lista_almeria, lista_mercados)),
        cuerpo,
        sorted({i["source"].split(" (")[0] for i in items})), encoding="utf-8")
    print(f"index.html generado con {len(items)} noticias.")

    # ---------- Página 2: Mercados ----------
    if not todas_mercados:
        print("mercados.html: sin noticias vigentes, no se genera.")
        return
    lead_m = elegir_destacada(sorted(todas_mercados, key=lambda i: i["date"], reverse=True), hoy)
    bloques = ""
    for clave, titulo in AMBITOS.items():
        lista = secciones[clave]
        if not lista:
            bloques += f"""
    <section class="mercado" id="m-{clave}">
      <h2>{escape(titulo)}</h2>
      <p class="empty-sec">Sin noticias nuevas en los últimos 30 días.</p>
    </section>"""
            continue
        bloques += f"""
    <section class="mercado" id="m-{clave}">
      <h2>{escape(titulo)} <span class="cuenta">{len(lista)}</span></h2>
      <ul class="feed">{"".join(render_story(i) for i in lista)}
      </ul>
    </section>"""

    navegacion = "".join(
        f'<a href="#m-{clave}">{escape(titulo.replace("El mercado en el ", "").replace("El mercado en ", "").capitalize())}</a>' for clave, titulo in AMBITOS.items())

    cuerpo_m = f"""
  <section class="hero" aria-labelledby="lead-title">
    <div class="wrap">
      <article class="lead" id="destacada">
        <p class="updated">Revisado el {fecha_larga(mercados.get('checked', mercados['updated']))}. Última noticia nueva: {fecha_larga(mercados['updated'])}.</p>
        <p class="lead-meta">{fecha_larga(lead_m['date'])} · {escape(lead_m['source'])}</p>
        <h1 id="lead-title">{escape(lead_m['title'])}</h1>
        <p>{escape(lead_m['summary'])}</p>
        <a class="go" href="{escape(lead_m['url'])}" rel="noopener" target="_blank">Leer la noticia original</a>
      </article>
      <aside aria-labelledby="salto-title">
        <h2 class="figures-title" id="salto-title">Cuatro mercados</h2>
        <nav class="saltos">{navegacion}</nav>
        <p class="nota">Cada mercado muestra hasta {MAX_SECCION} noticias de los últimos 30 días. Si uno se queda corto, se completa con noticias destacadas de los demás.</p>
      </aside>
    </div>
  </section>
{bloque_graficos(mercados, hoy, "Los mercados en gráficos")}

  <main class="wrap mercados">{bloques}
  </main>"""

    MERCADOS_OUT.write_text(pagina(
        "Agro Actualidad: mercados agrícolas",
        "Precios, campañas y comercio agrícola en Almería, España, Europa y el resto del mundo, con enlace a cada fuente.",
        cabecera("mercados", mercados, pestanas("mercados", lista_almeria, lista_mercados)),
        cuerpo_m,
        sorted({i["source"].split(" (")[0] for i in todas_mercados})), encoding="utf-8")
    print(f"mercados.html generado con {len(todas_mercados)} noticias en 4 mercados.")


if __name__ == "__main__":
    build()
