# Google Trends Scraper México - Clase Magistral de Web Scraping

Una guía completa sobre cómo construir un scraper robusto de Google Trends usando Playwright, con análisis profundo del proceso de debugging y resolución de errores.

## 📋 Tabla de Contenidos

1. [Introducción](#introducción)
2. [¿Por qué Playwright?](#por-qué-playwright)
3. [El Viaje del Debugging](#el-viaje-del-debugging)
4. [Arquitectura de la Solución](#arquitectura-de-la-solución)
5. [Guía de Instalación](#guía-de-instalación)
6. [Ejecutar el Scraper](#ejecutar-el-scraper)
7. [Supabase vs Playwright](#supabase-vs-playwright)
8. [GitHub Actions: Automatización Recurrente](#github-actions-automatización-recurrente)
9. [Troubleshooting](#troubleshooting)

---

## Introducción

Google Trends es una herramienta poderosa que muestra qué está buscando la gente en tiempo real. Sin embargo, no ofrece una API pública directa para obtener datos programáticamente. Este proyecto demuestra cómo extraer datos de Google Trends México usando técnicas modernas de web scraping.

**Objetivo:** Obtener las 20-25 tendencias en vivo de México con sus volúmenes de búsqueda cada 24 horas, almacenarlas y visualizarlas.

---

## ¿Por qué Playwright?

### Las Opciones Evaluadas

| Librería | Pros | Contras | Uso Ideal |
|----------|------|---------|-----------|
| **requests + BeautifulSoup** | Rápido, simple, bajo overhead | No renderiza JavaScript, GET básicos | Sitios estáticos HTML puro |
| **Selenium** | Maduro, múltiples navegadores | Lento, complejo de configurar, mantenimiento pesado | Testing de QA, navegadores antiguos |
| **Scrapy** | Potente, framework completo | Overkill para sitios simples, curva de aprendizaje | Crawling de múltiples páginas a escala |
| **Playwright** ✅ | Rápido, async, moderno, menos detectable | Requiere más recursos que requests | **Sitios con JavaScript pesado como Google Trends** |
| **Puppeteer** | Excelente para Node.js | No es ideal para Python | JavaScript/Node.js |

### Por Qué Elegimos Playwright

\`\`\`
Google Trends = JavaScript + Single Page Application (SPA)
\`\`\`

**La realidad:** Google Trends es una SPA (Single Page Application) construida con Angular/TypeScript. El HTML inicial NO contiene los datos de tendencias. Los datos se cargan dinámicamente después de que JavaScript ejecuta.

**Por ejemplo, con `requests`:**
\`\`\`python
import requests
response = requests.get('https://trends.google.com/trending?geo=MX&hours=24')
# El HTML contiene solo: <div id="root"></div>
# Los datos están en JavaScript ejecutado DESPUÉS de cargar
\`\`\`

**Con Playwright:**
\`\`\`python
async with async_playwright() as p:
    page = await context.new_page()
    await page.goto(url)
    # Aquí JavaScript ha ejecutado y el DOM está completo
    await page.evaluate('...')  # Ejecutamos código dentro del navegador
\`\`\`

### Ventajas Específicas de Playwright

1. **Renderizado Completo de JavaScript**
   - Espera a que Angular renderice los componentes
   - Ejecuta código dentro del contexto del navegador

2. **API Async/Await Moderna**
   \`\`\`python
   # Async permite múltiples scrapers en paralelo
   tasks = [scrape_country(country) for country in countries]
   results = await asyncio.gather(*tasks)
   \`\`\`

3. **Menos Detectable que Selenium**
   - Playwright usa headless browsers moderno
   - Google no lo detecta tan fácilmente como a Selenium

4. **Mejor Manejo de Timeouts**
   \`\`\`python
   await page.goto(url, wait_until='domcontentloaded', timeout=30000)
   await page.wait_for_timeout(5000)  # Esperar a JavaScript renderizar
   \`\`\`

5. **Ejecución de JavaScript**
   \`\`\`python
   result = await page.evaluate('''() => {
       // Código JavaScript ejecutado EN el navegador
       return document.querySelectorAll('div.mZ3RIc').length
   }''')
   \`\`\`

---

## El Viaje del Debugging

### Fase 1: El Primer Intento (Falló)

\`\`\`python
# ❌ INTENTO 1: Requests + BeautifulSoup
import requests
from bs4 import BeautifulSoup

response = requests.get('https://trends.google.com/trending?geo=MX&hours=24')
soup = BeautifulSoup(response.text, 'html.parser')
trends = soup.find_all('div', class_='trend-item')  # ❌ No encuentra nada
\`\`\`

**Resultado:** 0 elementos encontrados

**Por qué falló:** Google Trends carga los datos con JavaScript después de que `requests` recibe el HTML. Lo que recibimos es solo el contenedor vacío.

### Fase 2: Entender el Problema (Investigación)

Ejecuté el script `test_scrape.py` que exploró selectores CSS:

\`\`\`
[v0] Selector 'div.mdl-card': 0 elementos encontrados
[v0] Selector 'div[data-cid]': 0 elementos encontrados
[v0] Selector 'a[href*="/trends/explore"]': 34 elementos encontrados
    → Pero están OCULTOS (hidden)
\`\`\`

**Descubrimiento clave:** Los elementos existen pero están con `display: none`. Esto significa que el HTML tiene estructura, pero los datos visibles se generan dinámicamente.

### Fase 3: Cambiar a Playwright (Solución)

\`\`\`python
# ✅ INTENTO 2: Playwright con renderizado completo
async with async_playwright() as p:
    browser = await p.chromium.launch()
    page = await context.new_page()
    await page.goto(url, wait_until='domcontentloaded')
    await page.wait_for_timeout(5000)  # Esperar a JS
    
    elements = await page.query_selector_all('a[href*="/trends/explore"]')
    # Ahora tenemos 34 elementos VISIBLES
\`\`\`

**Resultado:** Elementos encontrados pero con contenido incorrecto (navegación UI, no datos)

### Fase 4: Inspeccionar la Estructura Real

Creé `debug_trends_structure.py` que:
1. Capturó todo el texto visible
2. Buscó palabras conocidas ("león", "monterrey", etc.)
3. Analizó la estructura HTML alrededor de esos elementos

**Salida del debug:**
\`\`\`json
{
  "trend_name": "américa - león",
  "classes": ["mZ3RIc"],
  "parent_tag": "div",
  "siblings": {
    "volume": "200 mil+",
    "volume_class": "qNpYPd"
  }
}
\`\`\`

**Descubrimiento:** Los nombres están en `div.mZ3RIc` y los volúmenes en `div.qNpYPd`

### Fase 5: Implementar los Selectores Correctos

\`\`\`python
trends_data = await page.evaluate('''
    () => {
        let trends = [];
        
        // Los selectores correctos que encontramos
        const trendNames = document.querySelectorAll('div.mZ3RIc');
        const volumeElements = document.querySelectorAll('div.qNpYPd');
        
        for (let i = 0; i < Math.min(trendNames.length, volumeElements.length); i++) {
            trends.push({
                term: trendNames[i].textContent.trim(),
                volume: volumeElements[i].textContent.trim()
            });
        }
        return trends;
    }
''')
\`\`\`

**Resultado:** ✅ Extrae correctamente: "américa - león", "carlos manzo", "monterrey - tigres", etc.

### Lecciones Aprendidas

1. **Inspecciona siempre el DOM renderizado**, no solo el HTML inicial
2. **Los selectores cambian con frecuencia** - mantén múltiples fallbacks
3. **JavaScript es tu aliado** - ejecuta código dentro del navegador
4. **Debugging progresivo** - confirma cada paso antes de avanzar

---

## Arquitectura de la Solución

\`\`\`
┌─────────────────────────────────────────┐
│  scrape_trends.py (Script Principal)    │
│  - Inicia Playwright                    │
│  - Navega a Google Trends México        │
│  - Espera renderizado de JavaScript     │
│  - Extrae datos con selectores CSS      │
└──────────────────┬──────────────────────┘
                   │
                   ▼
        ┌─────────────────────┐
        │  trends_data.json   │
        │ (Datos extraídos)   │
        └──────────┬──────────┘
                   │
                   ▼
    ┌──────────────────────────────────┐
    │  trends.html (Frontend)          │
    │  - Carga JSON                    │
    │  - Renderiza tabla de tendencias │
    │  - Muestra gráficos              │
    └──────────────────────────────────┘
\`\`\`

### Flujo de Ejecución

\`\`\`python
1. async def scrape_google_trends_mexico()
   ↓
2. async_playwright() # Iniciar navegador
   ↓
3. page.goto() # Navegar a URL
   ↓
4. page.wait_until='domcontentloaded' # Esperar DOM básico
   ↓
5. await page.wait_for_timeout(5000) # Esperar JavaScript
   ↓
6. page.evaluate() # Ejecutar código en el navegador
   ↓
7. Retornar JSON con datos
   ↓
8. Guardar en trends_data.json
\`\`\`

---

## Guía de Instalación

### Requisitos Previos

- Python 3.7+
- pip (gestor de paquetes)

### Pasos de Instalación

\`\`\`bash
# 1. Clonar o descargar el proyecto
cd Scraping_pytrends

# 2. Instalar dependencias Python
pip install playwright

# 3. Instalar navegadores Playwright
playwright install chromium

# 4. Verificar instalación
python -c "import playwright; print('✅ Playwright instalado')"
\`\`\`

### Estructura de Carpetas

\`\`\`
Scraping_pytrends/
├── scripts/
│   ├── scrape_trends.py          # Script principal
│   ├── debug_trends_structure.py # Script de debugging
│   └── test_scrape.py            # Script de pruebas
├── public/
│   └── trends.html               # Frontend
├── trends_data.json              # Datos generados
├── README.md                     # Este archivo
└── .github/
    └── workflows/
        └── scrape.yml            # GitHub Actions
\`\`\`

---

## Ejecutar el Scraper

### Ejecución Manual

\`\`\`bash
# Ejecutar el scraper
python scripts/scrape_trends.py

# Resultado esperado:
# [v0] Navegando a Google Trends México...
# [v0] DOM cargado. Esperando a que JavaScript renderice...
# [v0] Extrayendo tendencias del DOM...
# [v0] Tendencias extraídas: 20
# [v0] Top 5 tendencias:
#   1. américa - león (volumen: 200 mil+)
#   2. carlos manzo (volumen: 200 mil+)
# ...
# [v0] Datos guardados en trends_data.json
\`\`\`

### Ver el Frontend

\`\`\`bash
# Abrir el archivo HTML en navegador
# Windows:
start public/trends.html

# Mac:
open public/trends.html

# Linux:
xdg-open public/trends.html
\`\`\`

### Salida (trends_data.json)

\`\`\`json
{
  "timestamp": "2025-11-02T10:30:45.123456",
  "country": "México",
  "geo_code": "MX",
  "timeframe": "Últimas 24 horas",
  "total_trends": 20,
  "trends": [
    {
      "rank": 1,
      "term": "américa - león",
      "volume": 100,
      "volume_text": "200 mil+"
    },
    {
      "rank": 2,
      "term": "carlos manzo",
      "volume": 100,
      "volume_text": "200 mil+"
    }
  ],
  "source": "Google Trends (Scraping Real)",
  "status": "success"
}
\`\`\`

---

## Supabase vs Playwright

### ¿Qué es Supabase?

**Supabase** es una **base de datos en la nube** (Backend-as-a-Service) basada en PostgreSQL.

\`\`\`
Supabase ≈ Firebase (Google) pero open-source + PostgreSQL
\`\`\`

### Diferencias Fundamentales

| Aspecto | Playwright | Supabase |
|--------|-----------|----------|
| **Tipo** | Web Scraping Tool | Base de Datos |
| **Función** | Renderizar navegadores y extraer datos | Almacenar datos persistentemente |
| **Ejecución** | En la máquina del cliente/servidor | En servidor remoto (nube) |
| **Usa para** | Obtener datos de sitios web | Guardar datos extraídos |
| **Lenguaje** | Python (con API en JS/Python) | SQL (acceso via REST API) |

### Analogía: Pizza

\`\`\`
Playwright = El repartidor que va y RECOGE la pizza del restaurante
Supabase = El refrigerador de tu casa donde ALMACENAS la pizza
\`\`\`

### ¿Cómo Funcionan Juntos?

\`\`\`python
# Paso 1: Playwright EXTRAE datos
trends = await scrape_google_trends_mexico()
# Resultado: {"trends": [...]}

# Paso 2: Supabase ALMACENA datos
supabase_client.table('trends').insert({
    'timestamp': trends['timestamp'],
    'data': trends['trends'],
    'country': 'MX'
})
\`\`\`

### Por Qué Necesitas Ambos

**Playwright solo:** Extraes datos, pero se pierden si apagas la computadora
\`\`\`python
data = scrape_trends()  # Obtengo datos
# Si cierro la app, ¿dónde están los datos?
\`\`\`

**Playwright + Supabase:** Extraes datos y los almacenas permanentemente
\`\`\`python
data = scrape_trends()           # Obtengo datos (Playwright)
store_to_database(data)          # Los almaceno (Supabase)
# Puedo acceder a ellos meses después
\`\`\`

### Ejemplo Práctico

**Caso de Uso:** Queremos ver cómo han cambiado las tendencias en los últimos 30 días.

1. **Con solo Playwright:**
   \`\`\`python
   data_hoy = scrape_trends()  # Obtengo hoy
   # ¿Y los datos de ayer, hace una semana, hace un mes?
   # Se perdieron porque no hay almacenamiento
   \`\`\`

2. **Con Playwright + Supabase:**
   \`\`\`python
   data_hoy = scrape_trends()
   db.insert(data_hoy)           # Guardar en Supabase
   
   # Luego puedo hacer queries:
   db.table('trends')
     .select('*')
     .where('date', '>=', '2025-10-02')
     .execute()
   # Resultado: tendencias de los últimos 30 días
   \`\`\`

---

## GitHub Actions: Automatización Recurrente

GitHub Actions te permite ejecutar scripts automáticamente en servidores de GitHub sin tener que dejar tu computadora prendida.

### Plan Completo de Implementación

#### Paso 1: Crear Archivo de Workflow

Crea: `.github/workflows/scrape.yml`

\`\`\`yaml
name: Google Trends Scraper

on:
  # Ejecutar cada 24 horas
  schedule:
    - cron: '0 0 * * *'  # 00:00 UTC (18:00 CDMX)
  
  # También permitir ejecución manual
  workflow_dispatch:

jobs:
  scrape:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install playwright
          playwright install chromium
      
      - name: Run scraper
        run: python scripts/scrape_trends.py
      
      - name: Upload data to repository
        run: |
          git config --local user.email "bot@github.com"
          git config --local user.name "GitHub Bot"
          git add trends_data.json
          git commit -m "Update trends data - $(date)" || echo "No changes"
          git push
      
      - name: Upload to Supabase
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
        run: python scripts/upload_to_supabase.py

\`\`\`

#### Paso 2: Agregar Secretos en GitHub

En tu repositorio:
1. Ve a **Settings** → **Secrets and variables** → **Actions**
2. Agrega:
   - `SUPABASE_URL`: Tu URL de Supabase
   - `SUPABASE_KEY`: Tu API key de Supabase

#### Paso 3: Script para Supabase (Opcional)

Crea: `scripts/upload_to_supabase.py`

\`\`\`python
import json
import os
from datetime import datetime
from supabase import create_client, Client

# Leer datos generados
with open('trends_data.json', 'r') as f:
    trends_data = json.load(f)

# Conectar a Supabase
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(url, key)

# Insertar datos
response = supabase.table('trends').insert({
    'timestamp': trends_data['timestamp'],
    'country': 'MX',
    'total_trends': trends_data['total_trends'],
    'data': json.dumps(trends_data['trends']),
}).execute()

print(f"Datos guardados en Supabase: {response}")
\`\`\`

#### Paso 4: Crear Tabla en Supabase

En la consola de Supabase, ejecuta:

\`\`\`sql
CREATE TABLE trends (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  timestamp TIMESTAMP DEFAULT NOW(),
  country VARCHAR(10),
  total_trends INT,
  data JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Índice para queries rápidas
CREATE INDEX idx_trends_timestamp ON trends(timestamp);
\`\`\`

#### Paso 5: Flujo Completo Automatizado

\`\`\`
┌─────────────────────────────────────────┐
│  GitHub Actions Timer (Cron)            │
│  Ejecuta cada 24 horas automáticamente  │
└────────────────┬────────────────────────┘
                 │
                 ▼
    ┌────────────────────────┐
    │  Servidor de GitHub    │
    │  Ejecuta scraper       │
    │  python scrape_trends  │
    └─────────┬──────────────┘
              │
              ▼
    ┌──────────────────────────┐
    │ trends_data.json         │
    │ (Datos generados)        │
    └────────┬─────────────────┘
             │
      ┌──────┴──────┐
      ▼             ▼
  GitHub Repo  Supabase (DB)
  (Historial)  (Almacenamiento)
\`\`\`

### Ventajas de Este Setup

1. ✅ **Automatizado**: Se ejecuta solo cada 24 horas
2. ✅ **Sin dependencia de tu computadora**: Corre en servidores de GitHub
3. ✅ **Historial**: Todos los datos guardados en Supabase
4. ✅ **Gratuito**: GitHub Actions te da 2000 minutos/mes gratis
5. ✅ **Escalable**: Puedes agregar más países/fuentes fácilmente

### Monitoreo

Ve a **Actions** en tu repositorio para ver:
- ✅ Ejecuciones exitosas
- ❌ Errores
- ⏱️ Duración de ejecución
- 📊 Historial de runs

---

## Troubleshooting

### Problema: "TimeoutError: Page.wait_for_selector exceeded"

**Causa:** Google Trends tardó más de 15 segundos en cargar

**Solución:**
\`\`\`python
# Aumentar timeout en scrape_trends.py
await page.goto(url, wait_until='domcontentloaded', timeout=60000)  # 60 segundos
await page.wait_for_timeout(10000)  # 10 segundos extra
\`\`\`

### Problema: "The request failed: Google returned a response with code 404"

**Causa:** Google detectó el bot y bloqueó la IP

**Solución:**
\`\`\`python
# Agregar user-agent realista (ya está en el código)
user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

# O usar proxy si continúa siendo bloqueado
\`\`\`

### Problema: Cero tendencias extraídas

**Causa:** Google cambió las clases CSS de su HTML

**Solución:**
1. Ejecuta `python scripts/debug_trends_structure.py`
2. Busca las nuevas clases en `debug_structure.json`
3. Actualiza los selectores en `scrape_trends.py`

\`\`\`python
# Ejemplo: si encontraste nueva clase "ng-TrendItem"
trendNames = document.querySelectorAll('div.ng-TrendItem');  # Nueva clase
\`\`\`

### Problema: GitHub Actions dice "No such file or directory"

**Causa:** Las rutas del archivo son incorrectas

**Solución:** Usa rutas relativas correctas
\`\`\`yaml
run: python scripts/scrape_trends.py  # ✅ Correcto
# NO: run: python ./scrape_trends.py  # ❌ Incorrecto
\`\`\`

---

## Referencias y Recursos

### Documentación
- [Playwright Python Docs](https://playwright.dev/python/)
- [Google Trends](https://trends.google.com)
- [GitHub Actions Workflows](https://docs.github.com/en/actions)
- [Supabase Documentation](https://supabase.com/docs)

### Conceptos Relacionados
- **Web Scraping Ético**: Siempre revisa `robots.txt` y `Terms of Service`
- **JavaScript Rendering**: Entender SPAs es fundamental en scraping moderno
- **Async/Await**: Clave para scrapers de alto rendimiento

---

## Conclusión

Este proyecto demuestra:

1. **Análisis profundo del problema** antes de empezar a codificar
2. **Debugging sistemático** para entender la estructura del sitio
3. **Selección correcta de herramientas** (Playwright para JavaScript)
4. **Automatización robusta** con GitHub Actions
5. **Persistencia de datos** con Supabase

El scraping moderno no es solo hacer requests HTTP. Requiere entender JavaScript, DOM, async/await, y arquitecturas de SPAs. Playwright es la herramienta perfecta para este trabajo.

¡Feliz scraping! 🚀
