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
SOURCES = ROOT / "scripts" / "sources.json"

MODEL = os.environ.get("CLAUDE_MODEL", "claude-haiku-5-5")  # modelo pequeño: barato
API_URL = "https://api.anthropic.com/v1/messages"
MAX_NUEVAS_POR_DIA = 8      # tope para controlar el gasto
DIAS_RECIENTES = 3          # solo entradas de los últimos días
MAX_NOTICIAS_WEB = 60       # histórico máximo que se conserva
USER_AGENT = "AgroAlmeriaBot/1.0 (+proyecto personal; lee feeds RSS publicos)"
TAGS = ["mercados", "sanidad", "clima", "politica", "logistica", "campo"]


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

PROMPT = """Eres redactor de una web de noticias agrícolas sobre Almería.
Te paso UNA noticia (titular y extracto). Devuelve SOLO un JSON con estas claves:
- "relevante": true si trata de la agricultura de Almería o afecta directamente a ella; si no, false.
- "titulo": titular claro en español, máximo 120 caracteres, con tus propias palabras.
- "resumen": 2 o 3 frases en español con tus propias palabras.
- "tema": uno de {tags}.

Reglas estrictas:
- Usa SOLO la información del titular y del extracto. No añadas cifras, nombres ni hechos que no aparezcan ahí.
- No copies frases literales del texto original.
- Si el extracto es demasiado pobre para resumir con fiabilidad, pon "relevante": false.

Titular: {title}
Extracto: {desc}
Fuente: {source}
"""


def resumir(entrada, api_key):
    cuerpo = json.dumps({
        "model": MODEL,
        "max_tokens": 500,
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
        raise ValueError("La respuesta de Claude no contiene JSON")
    datos = json.loads(m.group(0))
    if datos.get("tema") not in TAGS:
        datos["tema"] = "campo"
    return datos


# ---------- Proceso principal ----------

def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        log("Falta ANTHROPIC_API_KEY. Añádela como secreto en GitHub (Settings > Secrets > Actions).")
        return 1

    cfg = json.loads(SOURCES.read_text(encoding="utf-8"))
    palabras = [p.lower() for p in cfg["palabras_clave"]]
    datos = json.loads(DATA.read_text(encoding="utf-8"))
    conocidas = {i["url"] for i in datos["items"]}
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
                       if e["date"] >= limite and e["url"] not in conocidas and es_de_almeria(e, palabras)]

    candidatas.sort(key=lambda e: e["date"], reverse=True)
    vistas = set()
    unicas = []
    for e in candidatas:  # evita duplicados si dos feeds repiten la misma noticia
        if e["url"] not in vistas:
            vistas.add(e["url"])
            unicas.append(e)
    candidatas = unicas[:MAX_NUEVAS_POR_DIA]
    log(f"{len(candidatas)} candidatas nuevas sobre Almería")

    nuevas = []
    for e in candidatas:
        try:
            r = resumir(e, api_key)
        except (urllib.error.URLError, ValueError, json.JSONDecodeError, OSError) as err:
            log(f"  Sin resumir «{e['title'][:60]}»: {err}")
            continue
        if not r.get("relevante"):
            log(f"  Descartada por irrelevante: {e['title'][:60]}")
            continue
        nuevas.append({
            "id": re.sub(r"[^a-z0-9]+", "-", e["title"].lower())[:50].strip("-") + "-" + e["date"].strftime("%Y-%m-%d"),
            "date": e["date"].astimezone().strftime("%Y-%m-%d"),
            "tag": r["tema"],
            "title": r["titulo"][:160],
            "summary": r["resumen"],
            "source": e["source"],
            "url": e["url"],
            "status": "auto",
        })
        log(f"  Añadida: {r['titulo'][:70]}")

    datos["items"] = (nuevas + datos["items"])
    datos["items"].sort(key=lambda i: i["date"], reverse=True)
    datos["items"] = datos["items"][:MAX_NOTICIAS_WEB]
    datos["updated"] = datetime.now().astimezone().isoformat(timespec="seconds")
    DATA.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    sys.path.insert(0, str(ROOT / "scripts"))
    import build_site
    build_site.build()
    return 0


if __name__ == "__main__":
    sys.exit(main())
