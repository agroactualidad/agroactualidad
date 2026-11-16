#!/usr/bin/env python3
"""Actualización diaria del bloque «Almería hoy».

Qué hace:
  1. Lee los feeds RSS de scripts/sources.json.
  2. Se queda con las entradas recientes que hablan de Almería (palabras clave).
  3. Le pide a Claude un resumen breve con SOLO la información del titular y el
     extracto de cada entrada (no inventa datos que no estén en el texto).
  4. Añade las noticias nuevas a data/almeria.json (sin duplicar) y regenera index.html.

Solo usa la librería estándar de Python. Necesita la variable de entorno
ANTHROPIC_API_KEY (en GitHub: Settings > Secrets and variables > Actions).
"""
import json
import os
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "almeria.json"
MERCADOS = ROOT / "data" / "mercados.json"
INNOVACION = ROOT / "data" / "innovacion.json"
MUNDO = DATA.parent / "mundo.json"
IA = ROOT / "data" / "ia.json"
VISTAS = ROOT / "data" / "vistas.json"
SOURCES = ROOT / "scripts" / "sources.json"

MODEL = os.environ.get("CLAUDE_MODEL", "claude-haiku-5-5")  # modelo pequeño: barato
API_URL = "https://api.anthropic.com/v1/messages"
MAX_NUEVAS_POR_DIA = 20     # tope para controlar el gasto
DIAS_RECIENTES = 7          # solo entradas de los últimos días (las ya conocidas se ignoran por URL)
USER_AGENT = "AgroAlmeriaBot/1.0 (+proyecto personal; lee feeds RSS publicos)"
AREAS_IA_VALIDAS = ["ia", "sensores", "robots", "datos"]
CATEGORIAS_VALIDAS = ["variedades", "maquinaria", "bioinsumos", "envases"]
AMBITOS_VALIDOS = ["almeria", "espana", "europa", "mundo"]  # también vale para "origen_ia"
TAGS = ["mercados", "sanidad", "clima", "politica", "logistica", "campo", "innovacion"]


def log(msg):
    print(msg, flush=True)


# ---------- Lectura de feeds ----------

def limpiar(texto):
    texto = re.sub(r"<[^>]+>", " ", texto or "")
    return re.sub(r"\s+", " ", unescape(texto)).strip()


def parse_fecha(texto):
    if not texto:
        return None
    try:
        d = parsedate_to_datetime(texto)
    except (TypeError, ValueError):
        try:
            d = datetime.fromisoformat(texto.replace("Z", "+00:00"))
        except ValueError:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d


def parse_feed(xml_bytes, nombre):
    """Devuelve una lista de dicts {title, url, desc, date, source} de un RSS/Atom."""
    root = ET.fromstring(xml_bytes)
    entradas = []
    for it in root.iter():
        etiqueta = it.tag.split("}")[-1]
        if etiqueta not in ("item", "entry"):
            continue
        campos = {}
        for hijo in it:
            clave = hijo.tag.split("}")[-1]
            if clave == "link" and hijo.get("href"):
                campos.setdefault("link", hijo.get("href"))
            else:
                campos.setdefault(clave, hijo.text or "")
        fecha = parse_fecha(campos.get("pubDate") or campos.get("published") or campos.get("updated"))
        url = (campos.get("link") or "").strip()
        titulo = limpiar(campos.get("title"))
        if not (url and titulo and fecha):
            continue
        desc = limpiar(campos.get("description") or campos.get("summary") or "")[:700]
        entradas.append({"title": titulo, "url": url, "desc": desc, "date": fecha, "source": nombre})
    return entradas


def descargar(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def es_de_almeria(entrada, palabras):
    texto = f"{entrada['title']} {entrada['desc']}".lower()
    return any(p in texto for p in palabras)


# ---------- Resumen con Claude ----------

PROMPT = """Eres redactor de una web de noticias agrícolas con cinco bloques: «Almería», «Mercados» (Almería, España, Europa y mundo), «Innovación y productos», «IA y agricultura de precisión» y «Mundo» (solo noticias internacionales de política agraria, comercio, economía, empresas, clima y seguridad alimentaria).
Te paso UNA noticia (titular y extracto). Devuelve SOLO un JSON con estas claves:
- "relevante": (bloque Almería) true si la noticia trata de la agricultura de Almería o de algo que afecta directamente al sector almeriense (una plaga que sufre, un mercado donde vende, una norma que le aplica, una tecnología que usa); false si es una noticia general sin relación clara con Almería.
- "motivo": una frase corta explicando por qué es o no relevante.
- "titulo": titular claro en español, máximo 120 caracteres, con tus propias palabras.
- "resumen": 2 o 3 frases en español con tus propias palabras.
- "mercado": true si la noticia trata de mercados agrícolas (precios, cotizaciones, campañas, cosechas, exportaciones e importaciones, comercio, aranceles, costes de producción); false si no.
- "ambito": solo si "mercado" es true, el territorio principal de la noticia: "almeria" (mercado almeriense), "espana" (España en general o una región española que no sea Almería), "europa" (UE u otros países europeos) o "mundo" (el resto, o global).
- "innovacion": true si la noticia presenta una novedad de producto o tecnología para el campo (variedades y semillas nuevas, maquinaria y robots, mallas y plásticos, bioinsumos y control biológico, envases y poscosecha); false si no.
- "categoria": solo si "innovacion" es true: "variedades" (semillas, variedades, mejora genética), "maquinaria" (maquinaria, robots, tecnología e infraestructura de cultivo), "bioinsumos" (control biológico, bioestimulantes, protección de cultivos) o "envases" (envases, embalaje, poscosecha, conservación).
- "ia": true si la noticia trata de inteligencia artificial, sensores, riego de precisión, robots, drones, automatización, datos o plataformas digitales aplicados a la agricultura; false si no.
- "area_ia": solo si "ia" es true: "ia" (modelos de inteligencia artificial, visión por ordenador, predicción), "sensores" (sensores, riego y fertirrigación de precisión, teledetección), "robots" (robots, drones, maquinaria autónoma, automatización) o "datos" (plataformas digitales, cuadernos de campo, ciberseguridad, gestión de datos).
- "origen_ia": solo si "ia" es true: de dónde procede la noticia: "almeria" (ocurre en la provincia de Almería), "espana" (resto de España), "europa" (otro país europeo o ámbito de la UE) o "mundo" (fuera de Europa o alcance global).
- "pais_ia": solo si "ia" es true: país o región principal en español (ej. "Australia", "EE. UU.", "Murcia"); cadena vacía si es global o no consta.
- "mundo": true si la noticia es INTERNACIONAL (no trata de España ni de Almería) y habla de política agraria, comercio y aranceles, economía agraria, abonos y costes, empresas del sector, clima, sanidad animal o vegetal, o seguridad alimentaria; false si no. No pongas true si es solo un precio o cotización de campaña, una novedad de producto o una noticia de IA y robótica (eso son otros bloques).
- "seccion_mundo": solo si "mundo" es true: "politica" (leyes, subvenciones, acuerdos, aranceles, restricciones), "economia" (precios de insumos, inflación, renta agraria, finanzas), "empresas" (fusiones, resultados, inversión, maquinaria y agroindustria) o "clima" (clima, sequía, El Niño, plagas y enfermedades, hambre y seguridad alimentaria).
- "pais_mundo": solo si "mundo" es true: país o región principal en español (ej. "EE. UU.", "India", "UE y Mercosur"); "Mundial" si es global.
- "importancia": número entero de 1 a 5 (5 = afecta a muchos agricultores o decisiones/cifras clave de Almería; 3 = interesante; 1 = anecdótica).
- "tema": uno de {tags}. («innovacion» = tecnología, IA, robótica, digitalización, I+D; «campo» = estado de los cultivos y la cosecha).

Reglas estrictas:
- Usa SOLO la información del titular y del extracto. No añadas cifras, nombres ni hechos que no aparezcan ahí.
- No copies frases literales del texto original.
- Si el extracto es pobre pero el titular deja claro que va de Almería, resume solo lo que diga el titular.
- Si no hay información suficiente para resumir sin inventar, pon "relevante": false y explícalo en "motivo".
- Responde únicamente con el JSON, sin texto antes ni después.

Titular: {title}
Extracto: {desc}
Fuente: {source}
"""


def resumir(entrada, api_key):
    cuerpo = json.dumps({
        "model": MODEL,
        "max_tokens": 1000,
        "messages": [{"role": "user", "content": PROMPT.format(
            tags=", ".join(TAGS), title=entrada["title"], desc=entrada["desc"], source=entrada["source"])}],
    }).encode("utf-8")
    req = urllib.request.Request(API_URL, data=cuerpo, headers={
        "content-type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    })
    with urllib.request.urlopen(req, timeout=60) as r:
        resp = json.loads(r.read())
    texto = "".join(b.get("text", "") for b in resp.get("content", []) if b.get("type") == "text")
    m = re.search(r"\{.*\}", texto, re.S)
    if not m:
        raise ValueError("La respuesta de Claude no contiene JSON. Respuesta recibida: " + texto[:300].replace("\n", " "))
    datos = json.loads(m.group(0))
    try:
        datos["importancia"] = min(5, max(1, int(datos.get("importancia", 3))))
    except (TypeError, ValueError):
        datos["importancia"] = 3
    datos["ia"] = bool(datos.get("ia"))
    if datos.get("area_ia") not in AREAS_IA_VALIDAS:
        datos["area_ia"] = "ia"
    if datos.get("origen_ia") not in AMBITOS_VALIDOS:
        datos["origen_ia"] = "mundo"
    datos["pais_ia"] = str(datos.get("pais_ia") or "")[:40]
    datos["mundo"] = bool(datos.get("mundo"))
    if datos.get("seccion_mundo") not in ("politica", "economia", "empresas", "clima"):
        datos["seccion_mundo"] = "economia"
    datos["pais_mundo"] = str(datos.get("pais_mundo") or "Mundial")[:40]
    datos["innovacion"] = bool(datos.get("innovacion"))
    if datos.get("categoria") not in CATEGORIAS_VALIDAS:
        datos["categoria"] = "maquinaria"
    datos["mercado"] = bool(datos.get("mercado"))
    if datos.get("ambito") not in AMBITOS_VALIDOS:
        datos["ambito"] = "mundo"
    if datos.get("tema") not in TAGS:
        datos["tema"] = "campo"
    return datos


# ---------- Proceso principal ----------

def cargar(ruta, defecto):
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else defecto


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        log("Falta ANTHROPIC_API_KEY. Añádela como secreto en GitHub (Settings > Secrets > Actions).")
        return 1

    sys.path.insert(0, str(ROOT / "scripts"))
    import build_site
    hoy = datetime.now().astimezone().date()

    cfg = json.loads(SOURCES.read_text(encoding="utf-8"))
    palabras = [p.lower() for p in cfg["palabras_clave"]]
    palabras_mercado = [p.lower() for p in cfg.get("palabras_mercado", [])]
    palabras_innovacion = [p.lower() for p in cfg.get("palabras_innovacion", [])]
    palabras_ia = [p.lower() for p in cfg.get("palabras_ia", [])]
    almeria = cargar(DATA, {"items": [], "stats": []})
    mercados = cargar(MERCADOS, {"items": [], "charts": []})
    innov = cargar(INNOVACION, {"items": [], "charts": []})
    ia_data = cargar(IA, {"items": [], "charts": []})
    mundo = cargar(MUNDO, {"items": [], "charts": []})
    palabras_mundo = [p.lower() for p in cfg.get("palabras_mundo", [])]
    vistas = cargar(VISTAS, {})          # url -> fecha en que se revisó (para no gastar dos veces)
    conocidas = {i["url"] for i in almeria["items"]} | {i["url"] for i in mercados["items"]} | {i["url"] for i in innov["items"]} | {i["url"] for i in ia_data["items"]} | {i["url"] for i in mundo["items"]} | set(vistas)
    limite = datetime.now(timezone.utc) - timedelta(days=DIAS_RECIENTES)

    candidatas = []
    for feed in cfg["feeds"]:
        try:
            entradas = parse_feed(descargar(feed["url"]), feed["name"])
            log(f"{feed['name']}: {len(entradas)} entradas leídas")
        except (urllib.error.URLError, ET.ParseError, TimeoutError, OSError) as e:
            log(f"{feed['name']}: no se pudo leer ({e}). Se salta.")
            continue
        candidatas += [e for e in entradas
                       if e["date"] >= limite and e["url"] not in conocidas
                       and (es_de_almeria(e, palabras) or es_de_almeria(e, palabras_mercado)
                            or es_de_almeria(e, palabras_innovacion) or es_de_almeria(e, palabras_ia)
                            or es_de_almeria(e, palabras_mundo))]

    candidatas.sort(key=lambda e: e["date"], reverse=True)
    vistos = set()
    unicas = []
    for e in candidatas:  # evita duplicados si dos feeds repiten la misma noticia
        if e["url"] not in vistos:
            vistos.add(e["url"])
            unicas.append(e)
    candidatas = unicas[:MAX_NUEVAS_POR_DIA]
    log(f"{len(candidatas)} candidatas nuevas (cualquier bloque)")

    nuevas_alm, nuevas_mer, nuevas_inn, nuevas_ia, nuevas_mun = [], [], [], [], []
    for e in candidatas:
        try:
            r = resumir(e, api_key)
        except (urllib.error.URLError, ValueError, json.JSONDecodeError, OSError) as err:
            log(f"  Sin resumir «{e['title'][:60]}»: {err}")
            continue
        vistas[e["url"]] = hoy.isoformat()
        base = {
            "id": re.sub(r"[^a-z0-9]+", "-", e["title"].lower())[:50].strip("-") + "-" + e["date"].strftime("%Y-%m-%d"),
            "date": e["date"].astimezone().strftime("%Y-%m-%d"),
            "title": r["titulo"][:160],
            "summary": r["resumen"],
            "source": e["source"],
            "url": e["url"],
            "importancia": r["importancia"],
            "status": "auto",
        }
        # Cada noticia va a UN solo bloque, por prioridad: Almería, IA, Innovación, Mundo, Mercados.
        if r.get("relevante"):
            nuevas_alm.append({**base, "tag": r["tema"]})
            log(f"  Almería: {r['titulo'][:70]}")
        elif r.get("ia"):
            nuevas_ia.append({**base, "id": "a-" + base["id"], "tag": "innovacion", "ambito": r["area_ia"],
                              "origen": r["origen_ia"], **({"pais": r["pais_ia"]} if r["pais_ia"] else {})})
            log(f"  IA ({r['area_ia']}): {r['titulo'][:60]}")
        elif r.get("innovacion"):
            nuevas_inn.append({**base, "id": "i-" + base["id"], "tag": "innovacion", "ambito": r["categoria"]})
            log(f"  Innovación ({r['categoria']}): {r['titulo'][:60]}")
        elif r.get("mundo"):
            nuevas_mun.append({**base, "id": "w-" + base["id"], "tag": r["tema"], "ambito": r["seccion_mundo"],
                               "pais": r["pais_mundo"]})
            log(f"  Mundo ({r['seccion_mundo']}): {r['titulo'][:60]}")
        elif r.get("mercado"):
            nuevas_mer.append({**base, "id": "m-" + base["id"], "tag": "mercados", "ambito": r["ambito"]})
            log(f"  Mercados ({r['ambito']}): {r['titulo'][:60]}")
        else:
            log(f"  Descartada: {e['title'][:60]} | Motivo: {r.get('motivo', 'sin motivo')}")

    ahora = datetime.now().astimezone().isoformat(timespec="seconds")
    for datos, nuevas in ((almeria, nuevas_alm), (mercados, nuevas_mer), (innov, nuevas_inn), (ia_data, nuevas_ia), (mundo, nuevas_mun)):
        datos["items"] = build_site.vigentes(nuevas + datos["items"], hoy)   # caducan a los 30 días
        datos["items"].sort(key=lambda i: i["date"], reverse=True)
        for clave in ("stats", "charts"):
            if clave in datos:
                datos[clave] = [x for x in datos[clave]
                                if x.get("date") and build_site.antiguedad(x, hoy) <= build_site.DIAS_MAX]
        datos["checked"] = ahora          # última vez que se buscó (siempre)
        if nuevas:
            datos["updated"] = ahora      # última vez que entró una noticia nueva
        datos.setdefault("updated", ahora)
    log(f"Noticias nuevas hoy: Almería {len(nuevas_alm)}, Mercados {len(nuevas_mer)}, Innovación {len(nuevas_inn)}, IA {len(nuevas_ia)}, Mundo {len(nuevas_mun)}")

    vistas = {u: f for u, f in vistas.items()
              if (hoy - datetime.fromisoformat(f).date()).days <= 40}
    DATA.write_text(json.dumps(almeria, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    MERCADOS.write_text(json.dumps(mercados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    INNOVACION.write_text(json.dumps(innov, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    MUNDO.write_text(json.dumps(mundo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    IA.write_text(json.dumps(ia_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    VISTAS.write_text(json.dumps(vistas, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    build_site.build(hoy)
    return 0


if __name__ == "__main__":
    sys.exit(main())
