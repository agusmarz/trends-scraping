# 🎓 Clase Magistral: Web Scraping Profesional con Playwright

Una guía técnica profunda sobre cómo construir un scraper robusto de aplicaciones complejas con JavaScript, análisis de debugging y arquitectura profesional.

## 📋 Tabla de Contenidos

1. [Introducción](#introducción)
2. [¿Por qué Playwright?](#por-qué-playwright)
3. [El Viaje del Debugging](#el-viaje-del-debugging)
4. [Arquitectura de la Solución](#arquitectura-de-la-solución)
5. [Técnicas Avanzadas](#técnicas-avanzadas)
6. [Optimización y Escalabilidad](#optimización-y-escalabilidad)
7. [Troubleshooting Experto](#troubleshooting-experto)

---

## Introducción

Google Trends es una herramienta poderosa que muestra qué está buscando la gente en tiempo real. Sin embargo, no ofrece una API pública directa para obtener datos programáticamente. Este documento es una **guía técnica profesional** sobre cómo extraer datos de aplicaciones complejas con JavaScript usando Playwright.

**¿Qué aprenderás?**
- Por qué Playwright es la herramienta correcta
- Cómo debuggear sitios con JavaScript complejo
- Extracción de datos desde aplicaciones Angular/React
- Optimización para producción
- Manejo de errores robusto

---

## ¿Por qué Playwright?

### Las Opciones Evaluadas

| Librería | Pros | Contras | Uso Ideal |
|----------|------|---------|-----------|
| **requests + BeautifulSoup** | Rápido, simple, bajo overhead | No renderiza JavaScript | Sitios estáticos HTML puro |
| **Selenium** | Maduro, múltiples navegadores | Lento, complejo, mantenimiento pesado | Testing de QA |
| **Scrapy** | Potente, framework completo | Overkill para sitios simples | Crawling masivo |
| **Playwright** ✅ | Rápido, async, moderno, poco detectable | Requiere más recursos | **SPAs con JavaScript pesado** |
| **Puppeteer** | Excelente para Node.js | No es ideal para Python | JavaScript/Node.js |

### Por Qué Elegimos Playwright

**La realidad:** Google Trends es una SPA (Single Page Application) construida con Angular. El HTML inicial NO contiene datos. Los datos se cargan dinámicamente con JavaScript.

\`\`\`python
# Con requests (NO FUNCIONA)
response = requests.get('https://trends.google.com/trending?geo=MX')
# HTML contiene solo: <div id="root"></div>

# Con Playwright (SÍ FUNCIONA)
async with async_playwright() as p:
    page = await context.new_page()
    await page.goto(url)
    # Aquí JavaScript ha ejecutado y el DOM está renderizado
\`\`\`

### Ventajas Específicas de Playwright

**1. Renderizado Completo de JavaScript**
\`\`\`python
# Playwright espera a que React/Angular renderice
await page.goto(url, wait_until='domcontentloaded')
await page.wait_for_timeout(5000)  # Esperar JavaScript
\`\`\`

**2. API Async/Await Moderna**
\`\`\`python
# Permite múltiples scrapers en paralelo
tasks = [scrape_country(c) for c in ['MX', 'AR', 'BR']]
results = await asyncio.gather(*tasks)  # 3x más rápido
\`\`\`

**3. Ejecución de JavaScript**
\`\`\`python
# Ejecutar código directamente en el navegador
result = await page.evaluate('''() => {
    return document.querySelectorAll('div.trend').length
}''')
\`\`\`

**4. Menos Detectable**
\`\`\`python
# Playwright es más sigiloso que Selenium
# Google no lo detecta tan fácilmente
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
trends = soup.find_all('div', class_='trend-item')  # 0 elementos
\`\`\`

**Resultado:** Sin datos

**Lección:** Necesitamos renderizado de JavaScript

### Fase 2: Investigar (Debugging)

Creamos `test_scrape.py`:

\`\`\`python
# Probar múltiples selectores
selectors = [
    'div.mdl-card',
    'div[data-cid]',
    'a[href*="/trends/explore"]',
    'span.title',
    'article'
]

for selector in selectors:
    elements = await page.query_selector_all(selector)
    print(f"[v0] Selector '{selector}': {len(elements)} elementos")
\`\`\`

**Descubrimiento:**
\`\`\`
[v0] Selector 'a[href*="/trends/explore"]': 34 elementos encontrados
    → Pero están OCULTOS (display: none)
\`\`\`

**Lección:** Los elementos existen pero están ocultos. El contenido visible se genera dinámicamente.

### Fase 3: Cambiar a Playwright

\`\`\`python
# ✅ INTENTO 2: Playwright
async with async_playwright() as p:
    browser = await p.chromium.launch()
    page = await context.new_page()
    await page.goto(url, wait_until='domcontentloaded')
    await page.wait_for_timeout(5000)  # Esperar JS
    
    elements = await page.query_selector_all('a[href*="/trends/explore"]')
    # Ahora: 34 elementos encontrados
\`\`\`

**Resultado:** Elementos encontrados pero contenido incorrecto

**Lección:** Necesitamos analizar la estructura correcta

### Fase 4: Inspeccionar Estructura HTML

Creamos `debug_trends_structure.py`:

\`\`\`python
# Capturar texto visible
visible_text = await page.evaluate('() => document.body.innerText')

# Buscar palabras conocidas
keywords = ['león', 'monterrey', 'carlos']
for keyword in keywords:
    if keyword in visible_text:
        print(f"[v0] Encontrado: {keyword}")
\`\`\`

**Salida del debug:**
\`\`\`
[v0] Encontrado: león
[v0] Encontrado: monterrey
[v0] Encontrado: carlos
\`\`\`

**Lección:** Los datos están allí, solo necesitamos los selectores CSS correctos

### Fase 5: Implementar Selectores Correctos

Analizando la estructura, descubrimos:
- Nombres están en: `div.mZ3RIc`
- Volúmenes están en: `div.qNpYPd`

\`\`\`python
# ✅ SOLUCIÓN FINAL
trends_data = await page.evaluate('''
    () => {
        let trends = [];
        const names = document.querySelectorAll('div.mZ3RIc');
        const volumes = document.querySelectorAll('div.qNpYPd');
        
        for (let i = 0; i < Math.min(names.length, volumes.length); i++) {
            trends.push({
                term: names[i].textContent.trim(),
                volume: volumes[i].textContent.trim()
            });
        }
        return trends;
    }
''')
\`\`\`

**Resultado:** ✅ Extrae correctamente todos los trends

---

## Arquitectura de la Solución

### Flujo de Ejecución Paso a Paso

\`\`\`
1. async def scrape_google_trends_mexico()
   ↓
2. async_playwright() → Iniciar navegador en modo headless
   ↓
3. browser.new_context() → Crear contexto aislado
   ↓
4. context.new_page() → Nueva página/pestaña
   ↓
5. page.goto(url) → Navegar a URL
   ↓
6. page.wait_until='domcontentloaded' → Esperar DOM básico
   ↓
7. await page.wait_for_timeout(5000) → Esperar JavaScript
   ↓
8. page.evaluate(javascript_code) → Ejecutar código EN el navegador
   ↓
9. Retornar datos extraídos
   ↓
10. Guardar en JSON
   ↓
11. browser.close() → Limpiar recursos
\`\`\`

### Código Estructurado

\`\`\`python
import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import pytz

async def scrape_google_trends_mexico():
    """
    Función principal de scraping
    """
    print("[v0] Iniciando scraper...")
    
    try:
        # Contexto asíncrono de Playwright
        async with async_playwright() as playwright:
            # Lanzar navegador
            browser = await playwright.chromium.launch(
                headless=True  # No mostrar navegador
            )
            
            # Contexto aislado (privacidad)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                viewport={'width': 1280, 'height': 720},
                ignore_https_errors=True
            )
            
            # Nueva página
            page = await context.new_page()
            
            # Navegar
            url = 'https://trends.google.com/trending?geo=MX&hours=24'
            print(f"[v0] Navegando a {url}...")
            
            await page.goto(
                url,
                wait_until='domcontentloaded',
                timeout=30000
            )
            
            # Esperar renderizado JavaScript
            print("[v0] Esperando JavaScript...")
            await page.wait_for_timeout(5000)
            
            # Extraer datos
            print("[v0] Extrayendo datos...")
            trends = await extract_trends(page)
            
            # Generar timestamp
            mexico_tz = pytz.timezone('America/Mexico_City')
            timestamp = datetime.now(mexico_tz)
            
            # Formatear respuesta
            result = {
                'timestamp': timestamp.isoformat(),
                'country': 'México',
                'trends': trends,
                'status': 'success'
            }
            
            # Guardar JSON
            with open('trends_data.json', 'w') as f:
                json.dump(result, f, indent=2)
            
            print(f"[v0] ✅ {len(trends)} tendencias extraídas")
            
            # Limpiar recursos
            await browser.close()
            
            return result
            
    except Exception as e:
        print(f"[v0] ❌ Error: {str(e)}")
        return {'status': 'error', 'error': str(e)}

async def extract_trends(page):
    """
    Extraer datos del DOM usando JavaScript
    """
    trends = await page.evaluate('''
        () => {
            let trends = [];
            const trendNames = document.querySelectorAll('div.mZ3RIc');
            const volumeElements = document.querySelectorAll('div.qNpYPd');
            
            for (let i = 0; i < Math.min(trendNames.length, volumeElements.length); i++) {
                trends.push({
                    rank: i + 1,
                    term: trendNames[i].textContent.trim(),
                    volume: volumeElements[i].textContent.trim()
                });
            }
            return trends;
        }
    ''')
    return trends

# Ejecutar
if __name__ == "__main__":
    asyncio.run(scrape_google_trends_mexico())
\`\`\`

---

## Técnicas Avanzadas

### 1. Inyección de JavaScript Personalizado

\`\`\`python
# Ejecutar funciones complejas
result = await page.evaluate('''
    () => {
        // Tu código JavaScript aquí
        let trends = [];
        
        // Iterar elementos
        document.querySelectorAll('div.trend').forEach((el, i) => {
            trends.push({
                rank: i + 1,
                name: el.querySelector('.name').textContent,
                volume: parseInt(el.getAttribute('data-volume')),
                change: parseFloat(el.querySelector('.change').textContent)
            });
        });
        
        return trends;
    }
''')
\`\`\`

### 2. Esperar Elementos Específicos

\`\`\`python
# Esperar a que aparezca un elemento
await page.wait_for_selector('div.trends-loaded', timeout=15000)

# Esperar con expresión personalizada
await page.wait_for_function('''
    () => document.querySelectorAll('div.trend').length > 10
''', timeout=30000)

# Esperar navegación
await page.wait_for_navigation(timeout=15000)
\`\`\`

### 3. Interactuar con Elementos

\`\`\`python
# Click
await page.click('button.load-more')

# Escribir en input
await page.fill('input#search', 'búsqueda')

# Presionar tecla
await page.press('input', 'Enter')

# Scroll
await page.evaluate('window.scrollBy(0, 1000)')
\`\`\`

### 4. Capturar Screenshots para Debugging

\`\`\`python
# Guardar screenshot
await page.screenshot(path='debug_screenshot.png')

# Guardar HTML
html = await page.content()
with open('debug_page.html', 'w') as f:
    f.write(html)

# Capturar console logs
page.on('console', lambda msg: print(f"[LOG] {msg.text}"))
\`\`\`

### 5. Manejo Robusto de Errores

\`\`\`python
try:
    async with async_playwright() as p:
        # ... código ...
except TimeoutError:
    print("[v0] Timeout: Página tardó mucho en cargar")
except Exception as e:
    print(f"[v0] Error desconocido: {e}")
finally:
    # Limpiar siempre
    await browser.close()
\`\`\`

---

## Optimización y Escalabilidad

### 1. Scrapear Múltiples Páginas en Paralelo

\`\`\`python
async def scrape_multiple_countries():
    """
    Extraer datos de múltiples países simultáneamente
    """
    countries = ['MX', 'AR', 'BR', 'CO', 'CL']
    
    tasks = [
        scrape_trends_for_country(country)
        for country in countries
    ]
    
    results = await asyncio.gather(*tasks)
    return results
\`\`\`

### 2. Reuso de Contextos

\`\`\`python
# ❌ INEFICIENTE: Crear navegador para cada página
async def bad_approach():
    for i in range(10):
        browser = await playwright.chromium.launch()
        # ... scraping ...
        await browser.close()

# ✅ EFICIENTE: Reuso contextos
async def good_approach():
    browser = await playwright.chromium.launch()
    
    for i in range(10):
        context = await browser.new_context()
        page = await context.new_page()
        # ... scraping ...
        await context.close()
    
    await browser.close()
\`\`\`

### 3. Memory Management

\`\`\`python
async def scrape_with_cleanup():
    """
    Limpiar memoria entre scrapes
    """
    browser = await playwright.chromium.launch()
    
    try:
        # Scrape 1
        data1 = await scrape(browser)
        
        # Limpiar memoria (importante para larga ejecución)
        import gc
        gc.collect()
        
        # Scrape 2
        data2 = await scrape(browser)
        
    finally:
        await browser.close()
\`\`\`

---

## Troubleshooting Experto

### Problema 1: "TimeoutError: Page.wait_for_selector exceeded"

\`\`\`
Causa: Sitio tardó más de lo esperado
Solución: Aumentar timeout
\`\`\`

\`\`\`python
# Aumentar timeout a 60 segundos
await page.wait_for_selector('div.content', timeout=60000)

# O usar wait_for_function más flexible
await page.wait_for_function('''
    () => {
        const trends = document.querySelectorAll('div.trend');
        return trends.length > 0;
    }
''', timeout=60000)
\`\`\`

### Problema 2: "Error: Browser has been closed"

\`\`\`
Causa: Referencia a página después de cerrar navegador
Solución: Verificar orden de cierre
\`\`\`

\`\`\`python
try:
    # ... scraping ...
    data = await extract(page)
finally:
    await context.close()  # Primero contexto
    await browser.close()  # Luego navegador
\`\`\`

### Problema 3: "The request failed: Google returned 404/429"

\`\`\`
Causa: Google detectó bot y bloqueó
Solución: Headers realistas + delays
\`\`\`

\`\`\`python
context = await browser.new_context(
    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    headers={
        'Accept-Language': 'es-MX,es;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
        'Referer': 'https://www.google.com'
    }
)

# Agregar delays
await page.wait_for_timeout(random.randint(3000, 8000))
\`\`\`

### Problema 4: "Elements are not visible"

\`\`\`
Causa: Elementos están display:none o overflow hidden
Solución: Usar evaluate para extraer aunque no sean visibles
\`\`\`

\`\`\`python
# En lugar de:
# elements = await page.query_selector_all('div.trend')
# for el in elements:
#     text = await el.text_content()  # Podría ser None si oculto

# Usar JavaScript que ignora visibilidad:
data = await page.evaluate('''
    () => {
        return Array.from(document.querySelectorAll('div.trend')).map(el => ({
            text: el.textContent,  // Obtiene texto sin importar visibilidad
            innerHTML: el.innerHTML
        }));
    }
''')
\`\`\`

### Problema 5: "Memory leak en ejecuciones largas"

\`\`\`
Causa: Página acumula datos en memoria
Solución: Destruir contexto entre scrapes
\`\`\`

\`\`\`python
async def long_running_scraper():
    """
    Scraping prolongado sin memory leak
    """
    browser = await playwright.chromium.launch()
    
    for iteration in range(100):
        # Nuevo contexto por cada iteración
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            await page.goto(url)
            data = await extract(page)
            save_data(data)
        finally:
            # Limpiar
            await context.close()
            
            # Force garbage collection
            import gc
            gc.collect()
    
    await browser.close()
\`\`\`

---

## Conclusión

Playwright es la herramienta correcta para scraping profesional de:
- ✅ Single Page Applications (SPAs)
- ✅ Aplicaciones Angular/React/Vue
- ✅ Sitios con JavaScript pesado
- ✅ Cuando necesitas interacción (clicks, typing)
- ✅ Scraping a escala con paralelismo

**Lecciones finales:**
1. Siempre analiza la estructura antes de codificar
2. Usa debugging sistemático (screenshots, console logs)
3. Implementa manejo robusto de errores
4. Optimiza para memoria en ejecuciones largas
5. Respeta rate limits y comportamiento ético

¡Ahora eres un experto en web scraping profesional! 🚀
