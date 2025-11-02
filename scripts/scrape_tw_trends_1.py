import asyncio
from playwright.async_api import async_playwright
import json
import re
from datetime import datetime, timedelta
import pytz
import random
import sys

def extract_minutes_ago(time_text):
    """
    Extrae el número de minutos de strings como '5 minutes ago', '2 hours ago', etc.
    Retorna None si no es reciente (en minutos) o si es antiguo (horas/días).
    """
    if not time_text:
        return None
    
    time_text = time_text.strip().lower()
    print(f"[v0] Analizando tiempo: '{time_text}'", file=sys.stderr)
    
    # Buscar "X minutes ago"
    match = re.search(r'(\d+)\s+minutes?\s+ago', time_text)
    if match:
        minutes = int(match.group(1))
        print(f"[v0]   ✓ Es reciente: {minutes} minutos", file=sys.stderr)
        return minutes
    
    # Si dice "hour" o "hours", no es reciente (>60 minutos)
    if 'hour' in time_text:
        print(f"[v0]   ✗ Es viejo: {time_text}", file=sys.stderr)
        return None
    
    # Si dice "day" o "days", descartarlo
    if 'day' in time_text:
        print(f"[v0]   ✗ Es muy viejo: {time_text}", file=sys.stderr)
        return None
    
    # Si dice "just now" o "now", contar como 0 minutos
    if 'just now' in time_text or 'now' == time_text:
        print(f"[v0]   ✓ Es ahora mismo: 0 minutos", file=sys.stderr)
        return 0
    
    print(f"[v0]   ? Formato desconocido: {time_text}", file=sys.stderr)
    return None

def extract_minutes_from_datetime(date_string):
    """
    Calcula cuántos minutos hace fue creada una tendencia basado en dateCreated.
    """
    if not date_string:
        return None
    
    try:
        created_time = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        now = datetime.now(created_time.tzinfo) if created_time.tzinfo else datetime.now()
        
        time_diff = now - created_time
        minutes_ago = int(time_diff.total_seconds() / 60)
        
        print(f"[v0] Tiempo desde creación: {minutes_ago} minutos", file=sys.stderr)
        return minutes_ago
    except Exception as e:
        print(f"[v0] Error parseando fecha: {e}", file=sys.stderr)
        return None

def get_trend_time_from_creation(date_created_str):
    """
    Calcula la hora real en México a la que corresponden las tendencias.
    """
    try:
        created_time = datetime.fromisoformat(date_created_str.replace('Z', '+00:00'))
        mexico_tz = pytz.timezone('America/Mexico_City')
        created_time_mexico = created_time.astimezone(mexico_tz)
        
        return {
            "timestamp_iso": created_time_mexico.isoformat(),
            "day": created_time_mexico.day,
            "month": created_time_mexico.month,
            "year": created_time_mexico.year,
            "hour": created_time_mexico.hour,
            "minute": created_time_mexico.minute
        }
    except Exception as e:
        print(f"[v0] Error parseando fecha: {e}", file=sys.stderr)
        mexico_tz = pytz.timezone('America/Mexico_City')
        now = datetime.now(mexico_tz)
        return {
            "timestamp_iso": now.isoformat(),
            "day": now.day,
            "month": now.month,
            "year": now.year,
            "hour": now.hour,
            "minute": now.minute
        }

async def scrape_twitter_trending_mexico():
    """
    Extrae tendencias de https://www.twitter-trending.com/mexico/en
    Usa Playwright para bypassear protección Cloudflare.
    """
    url = 'https://www.twitter-trending.com/mexico/en'
    
    print("[v0] ========== INICIANDO SCRAPING TWITTER-TRENDING.COM ==========", file=sys.stderr)
    print(f"[v0] URL: {url}", file=sys.stderr)
    
    async with async_playwright() as p:
        try:
            print("[v0] Lanzando navegador Chromium...", file=sys.stderr)
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox'
                ]
            )
            
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                locale='es-MX',
                timezone_id='America/Mexico_City'
            )
            
            # Inyectar scripts para evadir detección
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.chrome = {runtime: {}};
            """)
            
            page = await context.new_page()
            
            print("[v0] Navegando a twitter-trending.com...", file=sys.stderr)
            
            delay_before_nav = random.uniform(2, 4)
            await asyncio.sleep(delay_before_nav)
            
            response = await page.goto(url, wait_until='domcontentloaded', timeout=40000)
            
            print(f"[v0] Status code: {response.status}", file=sys.stderr)
            
            if response.status == 403:
                print("[v0] ⚠ Status 403 - Esperando a que Cloudflare resuelva...", file=sys.stderr)
                await asyncio.sleep(5)
            
            # Esperar a que JavaScript renderice
            print("[v0] Esperando a que la página cargue completamente...", file=sys.stderr)
            await asyncio.sleep(random.uniform(3, 6))
            
            # Verificar si hay JSON-LD
            print("[v0] Buscando JSON-LD...", file=sys.stderr)
            html = await page.content()
            
            if len(html) < 2000:
                print(f"[v0] ERROR: HTML demasiado corto ({len(html)} chars)", file=sys.stderr)
                await browser.close()
                return generate_example_data()
            
            print(f"[v0] HTML recibido: {len(html)} caracteres", file=sys.stderr)
            
            # Extraer JSON-LD usando JavaScript
            json_ld_data = await page.evaluate("""
                () => {
                    const script = document.querySelector('script[type="application/ld+json"]');
                    if (!script) return null;
                    try {
                        return JSON.parse(script.textContent);
                    } catch (e) {
                        return null;
                    }
                }
            """)
            
            if not json_ld_data:
                print("[v0] ERROR: No se encontró JSON-LD", file=sys.stderr)
                
                # Guardar HTML para debug
                with open('/tmp/debug_html.html', 'w', encoding='utf-8') as f:
                    f.write(html[:5000])
                print("[v0] HTML guardado en /tmp/debug_html.html", file=sys.stderr)
                
                await browser.close()
                return generate_example_data()
            
            print(f"[v0] ✓ JSON-LD encontrado. Tipo: {json_ld_data.get('@type')}", file=sys.stderr)
            
            if json_ld_data.get('@type') != 'ItemList':
                print(f"[v0] ERROR: Tipo incorrecto: {json_ld_data.get('@type')}", file=sys.stderr)
                await browser.close()
                return generate_example_data()
            
            items = json_ld_data.get('itemListElement', [])
            print(f"[v0] Total de tendencias en JSON-LD: {len(items)}", file=sys.stderr)
            
            if not items:
                print("[v0] ERROR: itemListElement vacío", file=sys.stderr)
                await browser.close()
                return generate_example_data()
            
            # Ahora extraer información de tiempos desde el HTML visible
            print("[v0] Extrayendo información de tiempos...", file=sys.stderr)
            time_info = await page.evaluate("""
                () => {
                    const timeElements = Array.from(document.querySelectorAll('*'))
                        .filter(el => {
                            const text = el.textContent || '';
                            return text.includes('ago') || text.includes('minutes') || text.includes('hours');
                        })
                        .map(el => el.textContent.trim())
                        .filter(text => text.length < 50);
                    return timeElements;
                }
            """)
            
            print(f"[v0] Elementos de tiempo encontrados: {len(time_info)}", file=sys.stderr)
            if time_info:
                print(f"[v0] Ejemplos: {time_info[:3]}", file=sys.stderr)
            
            # Procesar tendencias
            trends_list = []
            scraping_time_mexico = datetime.now(pytz.timezone('America/Mexico_City'))
            oldest_trend_minutes = None
            
            for idx, item in enumerate(items[:40]):
                if item.get('@type') != 'ListItem':
                    continue
                    
                position = item.get('position', idx + 1)
                name = item.get('name', '').strip()
                tweet_count = item.get('Tweet Count', 0)
                url_trend = item.get('url', '')
                date_created = item.get('dateCreated', '')
                
                if not name:
                    continue
                
                # Convertir volumen exacto de 1000 a -1
                if tweet_count == 1000:
                    tweet_count = -1
                
                # Calcular minutos desde creación
                minutes_since_creation = extract_minutes_from_datetime(date_created)
                
                # También intentar extraer de time_info si disponible
                if idx < len(time_info):
                    minutes_from_html = extract_minutes_ago(time_info[idx])
                    if minutes_from_html is not None:
                        minutes_since_creation = minutes_from_html
                
                # Guardar el mayor número de minutos (tendencia más antigua)
                if minutes_since_creation is not None:
                    if oldest_trend_minutes is None or minutes_since_creation > oldest_trend_minutes:
                        oldest_trend_minutes = minutes_since_creation
                
                trend_time = get_trend_time_from_creation(date_created) if date_created else {
                    "timestamp_iso": scraping_time_mexico.isoformat(),
                    "day": scraping_time_mexico.day,
                    "month": scraping_time_mexico.month,
                    "year": scraping_time_mexico.year,
                    "hour": scraping_time_mexico.hour,
                    "minute": scraping_time_mexico.minute,
                }
                
                trend_data = {
                    "rank": position,
                    "term": name,
                    "tweet_volume": tweet_count,
                    "minutes_since_creation": minutes_since_creation,
                    "trend_time_mexico": trend_time,
                    "url": url_trend
                }
                
                trends_list.append(trend_data)
                
                if idx < 5:
                    print(f"[v0] #{position}: {name} ({tweet_count} tweets, {minutes_since_creation} min)", file=sys.stderr)
            
            await browser.close()
            
            print(f"\n[v0] ✓ {len(trends_list)} tendencias extraídas correctamente", file=sys.stderr)
            
            if len(trends_list) == 0:
                print("[v0] ERROR: No se extrajo ninguna tendencia", file=sys.stderr)
                return generate_example_data()
            
            # Calcular cuándo se actualizaron los datos por última vez
            first_trend_minutes = trends_list[0]['minutes_since_creation'] if trends_list and trends_list[0].get('minutes_since_creation') is not None else None
            
            if first_trend_minutes is not None:
                data_updated_time = scraping_time_mexico - timedelta(minutes=first_trend_minutes)
            else:
                data_updated_time = scraping_time_mexico
            
            result = {
                "scraping_time": {
                    "timestamp_iso": scraping_time_mexico.isoformat(),
                    "day": scraping_time_mexico.day,
                    "month": scraping_time_mexico.month,
                    "year": scraping_time_mexico.year,
                    "hour": scraping_time_mexico.hour,
                    "minute": scraping_time_mexico.minute,
                    "description": "Hora en la que se ejecutó el scraping"
                },
                "data_source_updated_time": {
                    "timestamp_iso": data_updated_time.isoformat(),
                    "day": data_updated_time.day,
                    "month": data_updated_time.month,
                    "year": data_updated_time.year,
                    "hour": data_updated_time.hour,
                    "minute": data_updated_time.minute,
                    "minutes_ago": first_trend_minutes,
                    "description": "Hora en la que la fuente actualizó los datos por última vez"
                },
                "country": "México",
                "platform": "Twitter/X",
                "source": "twitter-trending.com",
                "total_trends": len(trends_list),
                "trends": trends_list,
                "status": "success"
            }
            
            print(f"[v0] ✓✓✓ SCRAPING EXITOSO", file=sys.stderr)
            print(f"[v0] Scraping realizado: {scraping_time_mexico.strftime('%H:%M:%S')}", file=sys.stderr)
            print(f"[v0] Datos actualizados: {data_updated_time.strftime('%H:%M:%S')} ({first_trend_minutes} min atrás)", file=sys.stderr)
            return result
            
        except Exception as e:
            print(f"[v0] ERROR GENERAL: {type(e).__name__}: {str(e)[:200]}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            if 'browser' in locals():
                await browser.close()
            return generate_example_data()

def generate_example_data():
    """
    Genera datos de ejemplo cuando falla el scraping.
    """
    print("[v0] ⚠⚠⚠ Usando datos de ejemplo como fallback...", file=sys.stderr)
    
    mexico_tz = pytz.timezone('America/Mexico_City')
    now = datetime.now(mexico_tz)
    data_time = now - timedelta(minutes=5)
    
    example_trends = [
        {
            "rank": 1,
            "term": "Carlos Manzo",
            "tweet_volume": -1,
            "minutes_since_creation": 5,
            "trend_time_mexico": {
                "timestamp_iso": (now - timedelta(minutes=5)).isoformat(),
                "day": (now - timedelta(minutes=5)).day,
                "month": (now - timedelta(minutes=5)).month,
                "year": (now - timedelta(minutes=5)).year,
                "hour": (now - timedelta(minutes=5)).hour,
                "minute": (now - timedelta(minutes=5)).minute,
            }
        },
        {
            "rank": 2,
            "term": "#FueClaudia",
            "tweet_volume": 28000,
            "minutes_since_creation": 8,
            "trend_time_mexico": {
                "timestamp_iso": (now - timedelta(minutes=8)).isoformat(),
                "day": (now - timedelta(minutes=8)).day,
                "month": (now - timedelta(minutes=8)).month,
                "year": (now - timedelta(minutes=8)).year,
                "hour": (now - timedelta(minutes=8)).hour,
                "minute": (now - timedelta(minutes=8)).minute,
            }
        },
        {
            "rank": 3,
            "term": "Michoacán",
            "tweet_volume": 180000,
            "minutes_since_creation": 12,
            "trend_time_mexico": {
                "timestamp_iso": (now - timedelta(minutes=12)).isoformat(),
                "day": (now - timedelta(minutes=12)).day,
                "month": (now - timedelta(minutes=12)).month,
                "year": (now - timedelta(minutes=12)).year,
                "hour": (now - timedelta(minutes=12)).hour,
                "minute": (now - timedelta(minutes=12)).minute,
            }
        },
    ]
    
    return {
        "scraping_time": {
            "timestamp_iso": now.isoformat(),
            "day": now.day,
            "month": now.month,
            "year": now.year,
            "hour": now.hour,
            "minute": now.minute,
            "description": "Hora en la que se ejecutó el scraping"
        },
        "data_source_updated_time": {
            "timestamp_iso": data_time.isoformat(),
            "day": data_time.day,
            "month": data_time.month,
            "year": data_time.year,
            "hour": data_time.hour,
            "minute": data_time.minute,
            "minutes_ago": 5,
            "description": "Hora en la que la fuente actualizó los datos por última vez (estimado)"
        },
        "country": "México",
        "platform": "Twitter/X",
        "source": "twitter-trending.com",
        "total_trends": len(example_trends),
        "trends": example_trends,
        "status": "example_data"
    }

if __name__ == "__main__":
    print("[v0] Iniciando scraper de twitter-trending.com...\n", file=sys.stderr)
    data = asyncio.run(scrape_twitter_trending_mexico())
    
    output_file = 'twitter_trending_com_data.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n[v0] ✓ Datos guardados en {output_file}", file=sys.stderr)
    
    print(f"\n[v0] ========== SCRAPING COMPLETADO ==========", file=sys.stderr)
    print(f"[v0] Status: {data['status']}", file=sys.stderr)
    print(f"[v0] Tendencias encontradas: {data['total_trends']}", file=sys.stderr)
    if data['trends'][:3]:
        print("[v0] Top 3:", file=sys.stderr)
        for t in data['trends'][:3]:
            minutes = t.get('minutes_since_creation', 'N/A')
            print(f"  #{t['rank']}: {t['term']} ({t['tweet_volume']} tweets, {minutes} min)", file=sys.stderr)