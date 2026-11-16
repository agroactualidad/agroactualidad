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

/* Origen de la noticia (filtro sin JavaScript) */
.origen-filtro { display: flex; flex-wrap: wrap; gap: 8px; margin: 22px 0 4px; align-items: center; }
.origen-filtro input { position: absolute; opacity: 0; pointer-events: none; }
.origen-filtro label { cursor: pointer; padding: 7px 14px; border-radius: 999px; border: 1px solid rgba(255,255,255,.18); color: #cfdcf0; font-size: .92rem; }
.origen-filtro input:checked + label { background: #2f6fd0; border-color: #2f6fd0; color: #fff; }
.origen-filtro input:focus-visible + label { outline: 2px solid #9fc4ff; outline-offset: 2px; }
.chip.origen { --dot: #8fb8ff; font-weight: 600; }
.chip.origen[data-origen="almeria"] { --dot: #9fdc8e; }
.chip.origen[data-origen="espana"] { --dot: #f0b45a; }
.chip.origen[data-origen="europa"] { --dot: #c9b6ff; }

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


def origen_chip(item):
    o = item.get("origen")
    if o not in ORIGENES:
        return ""
    texto = ORIGENES[o] + (f" · {item['pais']}" if item.get("pais") else "")
    return f'<span class="chip origen" data-origen="{o}">{escape(texto)}</span>'


ORIGENES = {"mundo": "Mundo", "europa": "Europa", "espana": "España", "almeria": "Almería"}


def render_story(item, con_origen=False):
    tag = item.get("tag", "campo")
    status = item.get("status", "auto")
    mark = (
        '<span class="mark">Revisada</span>'
        if status == "revisada"
        else '<span class="mark auto">Resumen automático</span>'
    )
    return f"""
      <li class="story" id="{escape(item['id'])}" data-tag="{escape(tag)}"{f' data-origen="{escape(item["origen"])}"' if con_origen and item.get("origen") else ''}>
        <div class="when"><span class="tico" data-tag="{escape(tag)}">{icono(tag)}</span><time datetime="{escape(item['date'])}">{fecha_corta(item['date'])}</time></div>
        <div>
          <h3><a href="{escape(item['url'])}" rel="noopener" target="_blank">{escape(item['title'])}</a></h3>
          <p>{escape(item['summary'])}</p>
          <div class="byline">
            <span class="chip" data-tag="{escape(tag)}">{escape(TAGS.get(tag, tag))}</span>
            {origen_chip(item) if con_origen else ''}
            {f'<span class="chip ajeno">Desde: {escape(item["prestada"])}</span>' if item.get("prestada") else ''}
            <span>{escape(item['source'])}</span>
            {mark}
          </div>
        </div>
      </li>"""


AMBITOS = {  # (se mantiene el nombre por compatibilidad con update_news.py)
    "almeria": "El mercado en Almería",
    "espana": "El mercado en España",
    "europa": "El mercado en Europa",
    "mundo": "El mercado en el mundo",
}
MAX_SECCION = 6        # tope de noticias por sección
MIN_SECCION = 3        # por debajo de esto, la sección se completa con otras

# Cada bloque con varias secciones: Mercados e Innovación y productos.
BLOQUES = {
    "mercados": {
        "pestana": "Mercados", "archivo": "mercados.html", "datos": ROOT / "data" / "mercados.json",
        "prefijo": "m", "clase": "mercado",
        "intro": "Precios, campañas y comercio, de Almería al mundo.",
        "secciones": AMBITOS,
        "corto": lambda t: t.replace("El mercado en el ", "").replace("El mercado en ", "").capitalize(),
        "resumen": "Cuatro mercados", "graficos": "Los mercados en gráficos",
        "titulo": "Agro Actualidad: mercados agrícolas",
        "descripcion": "Precios, campañas y comercio agrícola en Almería, España, Europa y el resto del mundo, con enlace a cada fuente.",
        "otros": "Otros mercados",
    },
    "innovacion": {
        "pestana": "Innovación y productos", "archivo": "innovacion.html", "datos": ROOT / "data" / "innovacion.json",
        "prefijo": "n", "clase": "mercado",
        "intro": "Variedades, maquinaria, bioinsumos y envases que llegan al campo.",
        "secciones": {"variedades": "Variedades y semillas", "maquinaria": "Maquinaria y tecnología de cultivo",
                      "bioinsumos": "Bioinsumos y protección de cultivos", "envases": "Envases y poscosecha"},
        "corto": lambda t: t, "resumen": "Cuatro áreas", "graficos": "La innovación en gráficos",
        "titulo": "Agro Actualidad: innovación y productos",
        "descripcion": "Novedades en variedades, maquinaria, bioinsumos y envases para el campo, con enlace a cada fuente.",
        "otros": "Otras áreas",
    },
    "ia": {
        "pestana": "IA y agricultura de precisión", "archivo": "ia.html", "datos": ROOT / "data" / "ia.json",
        "prefijo": "a", "clase": "mercado",
        "intro": "Última hora mundial en IA, sensores, robots y datos para el cultivo.",
        "secciones": {"ia": "Inteligencia artificial", "sensores": "Sensores y riego de precisión",
                      "robots": "Robots, drones y automatización", "datos": "Datos y plataformas digitales"},
        "corto": lambda t: t, "resumen": "Cuatro áreas", "graficos": "La tecnología en gráficos",
        "origen": True,
        "titulo": "Agro Actualidad: IA y agricultura de precisión",
        "descripcion": "Inteligencia artificial, sensores, robots y plataformas de datos aplicados a la agricultura, con enlace a cada fuente.",
        "otros": "Otras áreas",
    },
}
PROXIMAMENTE = {
    "mundo": ("Mundo", "Lo que mueve la agricultura en el resto del mundo: cosechas, comercio y política agraria."),
}


def secciones_bloque(items, nombres, otros, hoy):
    """Reparte las noticias por sección (máx. 6 cada una).

    Si una sección se queda con menos de 3, se completa con noticias de secciones
    que tienen de sobra. La noticia se MUEVE (no se duplica) y queda marcada
    «Desde: ...»; ninguna sección cede si se queda con menos de 3.
    """
    vivas = vigentes(items, hoy)
    sel = {k: seleccionar([i for i in vivas if i.get("ambito") == k], hoy)[:MAX_SECCION] for k in nombres}
    for k in nombres:
        while len(sel[k]) < MIN_SECCION:
            pool = [(k2, i) for k2 in nombres if k2 != k and len(sel[k2]) > MIN_SECCION for i in sel[k2]]
            if not pool:
                break
            k2, extra = max(pool, key=lambda p: (p[1].get("importancia", 3), p[1]["date"]))
            sel[k2] = [i for i in sel[k2] if i["id"] != extra["id"]]
            copia = dict(extra)
            copia["prestada"] = nombres.get(k2, otros)
            sel[k].append(copia)
        sel[k].sort(key=lambda i: i["date"], reverse=True)
    return sel


def cabecera(activa, menus):
    """Barra superior con el logo y las cinco pestañas desplegables."""
    pestanas = ""
    for clave, titulo, destino, panel in menus:
        actual = ' aria-current="page"' if clave == activa else ""
        enlace = f'<a class="panel-go" href="{destino}">Abrir {titulo}</a>' if destino and clave != activa else ""
        pestanas += f'''
        <div class="tab">
          <button type="button" aria-expanded="false" aria-controls="p-{clave}"{actual}>{titulo}</button>
          <div class="panel" id="p-{clave}" hidden>{panel}
            {enlace}
          </div>
        </div>'''
    return f'''  <header class="masthead">
    <div class="wrap bar">
      <a class="logo" href="./" aria-label="Agro Actualidad, inicio"><img src="assets/logo.png" width="790" height="216" alt="Agro Actualidad: del campo al mercado global"></a>
      <nav class="tabs" aria-label="Secciones">{pestanas}
      </nav>
    </div>
  </header>'''


def menus_pestanas(lista_almeria):
    menus = [("almeria", "Almería", "index.html",
              f'<p class="panel-intro">Agricultura almeriense, al día.</p><ul class="panel-list">{lista_almeria}</ul>')]
    for clave, cfg in BLOQUES.items():
        enlaces = "".join(
            f'<li><a href="{cfg["archivo"]}#{cfg["prefijo"]}-{k}">{escape(t)}</a></li>' for k, t in cfg["secciones"].items())
        menus.append((clave, cfg["pestana"], cfg["archivo"],
                      f'<p class="panel-intro">{escape(cfg["intro"])}</p><ul class="panel-list">{enlaces}</ul>'))
    for clave, (titulo, texto) in PROXIMAMENTE.items():
        menus.append((clave, titulo, "", f'<p class="panel-intro"><strong>Próximamente.</strong> {texto}</p>'))
    orden = ["almeria", "mercados", "innovacion", "ia", "mundo"]
    return sorted(menus, key=lambda m: orden.index(m[0]))


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


def render_bloque(clave, cfg, hoy, menus):
    """Genera la página de un bloque con secciones (Mercados, Innovación...)."""
    if not cfg["datos"].exists():
        print(f"{cfg['archivo']}: falta {cfg['datos'].name}, no se genera.")
        return
    data = json.loads(cfg["datos"].read_text(encoding="utf-8"))
    secciones = secciones_bloque(data.get("items", []), cfg["secciones"], cfg["otros"], hoy)
    todas = list({i["id"]: i for lista in secciones.values() for i in lista}.values())
    if not todas:
        print(f"{cfg['archivo']}: sin noticias vigentes, no se genera.")
        return
    lead = elegir_destacada(sorted(todas, key=lambda i: i["date"], reverse=True), hoy)
    p = cfg["prefijo"]
    bloques = ""
    for k, titulo in cfg["secciones"].items():
        lista = secciones[k]
        if not lista:
            bloques += f"""
    <section class="{cfg['clase']}" id="{p}-{k}">
      <h2>{escape(titulo)}</h2>
      <p class="empty-sec">Sin noticias nuevas en los últimos 30 días.</p>
    </section>"""
            continue
        bloques += f"""
    <section class="{cfg['clase']}" id="{p}-{k}">
      <h2>{escape(titulo)} <span class="cuenta">{len(lista)}</span></h2>
      <ul class="feed">{"".join(render_story(i, cfg.get("origen", False)) for i in lista)}
      </ul>
    </section>"""
    filtro_origen = ""
    if cfg.get("origen"):
        usados = [o for o in ORIGENES if any(i.get("origen") == o for i in todas)]
        radios = '<input type="radio" name="origen" id="or-todo" checked><label for="or-todo">Todo el mundo</label>'
        css = ""
        for o in usados:
            radios += f'<input type="radio" name="origen" id="or-{o}"><label for="or-{o}">{ORIGENES[o]}</label>'
            css += (f'body:has(#or-{o}:checked) .story:not([data-origen="{o}"]){{display:none}}'
                    f'body:has(#or-{o}:checked) .mercados section:not(:has(.story[data-origen="{o}"])){{display:none}}')
        filtro_origen = f'<div class="origen-filtro" role="radiogroup" aria-label="Filtrar por origen de la noticia">{radios}</div><style>{css}</style>'
    navegacion = "".join(f'<a href="#{p}-{k}">{escape(cfg["corto"](t))}</a>' for k, t in cfg["secciones"].items())
    cuerpo = f"""
  <section class="hero" aria-labelledby="lead-title">
    <div class="wrap">
      <article class="lead" id="destacada">
        <p class="updated">Revisado el {fecha_larga(data.get('checked', data['updated']))}. Última noticia nueva: {fecha_larga(data['updated'])}.</p>
        <p class="lead-meta">{fecha_larga(lead['date'])} · {escape(lead['source'])}</p>
        <h1 id="lead-title">{escape(lead['title'])}</h1>
        <p>{escape(lead['summary'])}</p>
        <a class="go" href="{escape(lead['url'])}" rel="noopener" target="_blank">Leer la noticia original</a>
      </article>
      <aside aria-labelledby="salto-title">
        <h2 class="figures-title" id="salto-title">{escape(cfg['resumen'])}</h2>
        <nav class="saltos">{navegacion}</nav>
        <p class="nota">Cada apartado muestra hasta {MAX_SECCION} noticias de los últimos 30 días. Si uno se queda corto, se completa con noticias destacadas de los demás.</p>
      </aside>
    </div>
  </section>
{bloque_graficos(data, hoy, cfg['graficos'])}

  <div class="wrap">{filtro_origen}</div>
  <main class="wrap mercados">{bloques}
  </main>"""
    (ROOT / cfg["archivo"]).write_text(pagina(
        cfg["titulo"], cfg["descripcion"], cabecera(clave, menus), cuerpo,
        sorted({i["source"].split(" (")[0] for i in todas})), encoding="utf-8")
    print(f"{cfg['archivo']} generado con {len(todas)} noticias en {len(cfg['secciones'])} apartados.")


def build(hoy=None):
    """Genera todas las páginas: Almería (index.html) y los bloques con secciones."""
    hoy = hoy or date.today()
    almeria = json.loads(DATA.read_text(encoding="utf-8"))
    items = seleccionar(almeria["items"], hoy)
    if not items:
        raise SystemExit("No hay noticias de los últimos 30 días: no se regenera la web.")
    lead = elegir_destacada(items, hoy)
    rest = [i for i in items if i["id"] != lead["id"]]
    menus = menus_pestanas(indice(items, lead))

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
        cabecera("almeria", menus),
        cuerpo,
        sorted({i["source"].split(" (")[0] for i in items})), encoding="utf-8")
    print(f"index.html generado con {len(items)} noticias.")

    for clave, cfg in BLOQUES.items():
        render_bloque(clave, cfg, hoy, menus)


if __name__ == "__main__":
    build()
