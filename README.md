# Agro Almería

Web de noticias de la agricultura almeriense. Este primer bloque es **«Almería hoy»**.
Se actualiza sola cada día: lee fuentes del sector, Claude resume lo nuevo y la web se vuelve a generar.

## Qué hay en la carpeta

| Archivo | Para qué sirve |
|---|---|
| `index.html` | La web (se genera sola, no hace falta tocarla) |
| `assets/styles.css` | El diseño (azul oscuro) |
| `assets/app.js` | Los botones de filtro por tema |
| `data/almeria.json` | Las noticias. Aquí se guardan todas |
| `scripts/build_site.py` | Convierte `almeria.json` en `index.html` |
| `scripts/update_news.py` | Busca noticias nuevas y las resume con Claude |
| `scripts/sources.json` | Lista de fuentes (feeds RSS) y palabras clave de Almería |
| `.github/workflows/actualizar.yml` | El «reloj» que lo ejecuta cada día a las 7:00 |

## Puesta en marcha (una sola vez)

### 1. Crear el repositorio en GitHub
1. Entra en github.com con tu sesión y pulsa **New** (nuevo repositorio).
2. Nombre: `agro-almeria`. Déjalo en **Public** (GitHub Pages gratis lo necesita).
3. Pulsa **Create repository**.

### 2. Subir los archivos
1. En la página del repositorio vacío, pulsa **uploading an existing file**.
2. Arrastra **todo el contenido** de esta carpeta (incluida la carpeta oculta `.github`; si no la ves, activa «mostrar archivos ocultos» en tu sistema).
3. Abajo, pulsa **Commit changes**.

> Si `.github` no se sube con arrastrar, crea el archivo a mano: **Add file → Create new file**, escribe como nombre `.github/workflows/actualizar.yml`, pega el contenido y pulsa Commit.

### 3. Guardar la clave de la API de Claude
1. Crea una clave en console.anthropic.com (API Keys) y **ponle un límite de gasto mensual bajo** en los ajustes de facturación.
2. En tu repositorio: **Settings → Secrets and variables → Actions → New repository secret**.
3. Nombre: `ANTHROPIC_API_KEY`. Valor: tu clave. Pulsa **Add secret**.

### 4. Activar la web (GitHub Pages)
1. **Settings → Pages**.
2. En *Source* elige **Deploy from a branch**, rama `main`, carpeta `/ (root)`. Pulsa **Save**.
3. En uno o dos minutos tu web estará en `https://TU-USUARIO.github.io/agro-almeria/`.

### 5. Probar la actualización a mano
1. Pestaña **Actions → Actualizar noticias cada día → Run workflow**.
2. Cuando termine (círculo verde), abre el registro y copia lo que dice el paso «Buscar noticias, resumir y regenerar la web». Si algo falla, pégamelo y lo arreglamos.

## Cómo funciona la actualización
- Lee los feeds de `scripts/sources.json`.
- Se queda con las entradas de los últimos 3 días que mencionan Almería, sus comarcas u organizaciones del sector.
- Claude resume cada una usando **solo** el titular y el extracto (no inventa datos) y descarta lo irrelevante.
- Las noticias automáticas salen marcadas como **«Resumen automático»**; las que se han contrastado a mano, como **«Revisada»**.
- Máximo 8 noticias nuevas al día: el gasto con un modelo pequeño es de céntimos.

## Qué conviene saber
- Los feeds de HortiDaily y Agronews están confirmados; el de Hortoinfo hay que comprobarlo en la primera ejecución. Si uno falla, el script lo salta y sigue.
- Los resúmenes automáticos se basan en el extracto del feed, no en el artículo completo. Por eso son breves y prudentes.
- Cada noticia enlaza siempre a la fuente original. No se copian artículos.
