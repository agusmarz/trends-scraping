import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import pytz
import random
import time
import sys

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

def scrape_twitter_trending_mexico():
    """
    Extrae tendencias de https://www.twitter-trending.com/mexico/en
    """
    url = 'https://www.twitter-trending.com/mexico/en'
    
    print("[v0] ========== INICIANDO SCRAPING TWITTER-TRENDING.COM ==========", file=sys.stderr)
    print(f"[v0] URL: {url}", file=sys.stderr)
    
    # Aumentar delay inicial
    delay_before_request = random.uniform(2, 5)
    print(f"[v0] Esperando {delay_before_request:.1f}s antes de solicitar...", file=sys.stderr)
    time.sleep(delay_before_request)
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'es-MX,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
            'Referer': 'https://www.google.com/',
        }
        
        print("[v0] Realizando solicitud HTTP...", file=sys.stderr)
        
        # Aumentar timeout a 30 segundos
        response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
        
        print(f"[v0] Status code: {response.status_code} ✓", file=sys.stderr)
        print(f"[v0] Tamaño del HTML: {len(response.text)} caracteres", file=sys.stderr)
        print(f"[v0] Encoding: {response.encoding}", file=sys.stderr)
        
        # Verificar si recibimos HTML válido
        if response.status_code != 200:
            print(f"[v0] ERROR: Status code {response.status_code}", file=sys.stderr)
            print(f"[v0] Response headers: {dict(response.headers)}", file=sys.stderr)
            return generate_example_data()
        
        if len(response.text) < 1000:
            print(f"[v0] ERROR: HTML demasiado corto (posible bloqueo)", file=sys.stderr)
            print(f"[v0] Primeros 500 chars: {response.text[:500]}", file=sys.stderr)
            return generate_example_data()
        
        response.raise_for_status()
        
        delay_after_response = random.uniform(1, 3)
        time.sleep(delay_after_response)
        
        print("[v0] Parseando HTML con BeautifulSoup...", file=sys.stderr)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print("[v0] Buscando JSON-LD schema.org...", file=sys.stderr)
        json_ld_script = soup.find('script', {'type': 'application/ld+json'})
        
        if not json_ld_script:
            print("[v0] ERROR: No se encontró JSON-LD", file=sys.stderr)
            print(f"[v0] Scripts encontrados: {len(soup.find_all('script'))}", file=sys.stderr)
            
            # Guardar HTML para debug
            with open('/tmp/debug_html.html', 'w', encoding='utf-8') as f:
                f.write(response.text[:5000])
            print("[v0] HTML guardado en /tmp/debug_html.html para debug", file=sys.stderr)
            
            return generate_example_data()
        
        print("[v0] ✓ JSON-LD encontrado", file=sys.stderr)
        
        delay_before_parse = random.uniform(0.5, 2)
        time.sleep(delay_before_parse)
        
        try:
            schema_data = json.loads(json_ld_script.string)
            print(f"[v0] JSON-LD parseado exitosamente. Tipo: {schema_data.get('@type')}", file=sys.stderr)
        except json.JSONDecodeError as e:
            print(f"[v0] ERROR parseando JSON: {e}", file=sys.stderr)
            return generate_example_data()
        
        if schema_data.get('@type') != 'ItemList':
            print(f"[v0] ERROR: No es ItemList, es {schema_data.get('@type')}", file=sys.stderr)
            return generate_example_data()
        
        items = schema_data.get('itemListElement', [])
        print(f"[v0] Total de tendencias en JSON-LD: {len(items)}", file=sys.stderr)
        
        if not items or len(items) == 0:
            print("[v0] ERROR: No hay itemListElement o está vacío", file=sys.stderr)
            print(f"[v0] Keys en schema_data: {list(schema_data.keys())}", file=sys.stderr)
            return generate_example_data()
        
        trends_list = []
        
        for idx, item in enumerate(items[:40]):
            if idx % 10 == 0 and idx > 0:
                delay_between_items = random.uniform(0.1, 0.3)
                time.sleep(delay_between_items)
            
            if item.get('@type') != 'ListItem':
                continue
                
            position = item.get('position', idx + 1)
            name = item.get('name', '').strip()
            tweet_count = item.get('Tweet Count', 0)
            url_trend = item.get('url', '')
            date_created = item.get('dateCreated', '')
            
            if not name:
                print(f"[v0] ⚠ Item {position} sin nombre, saltando", file=sys.stderr)
                continue
            
            # Convertir volumen exacto de 1000 a -1
            if tweet_count == 1000:
                print(f"[v0] Volumen exacto 1000 detectado para '{name}', cambiando a -1", file=sys.stderr)
                tweet_count = -1
            
            minutes_since_creation = extract_minutes_from_datetime(date_created)
            
            trend_time = get_trend_time_from_creation(date_created) if date_created else {
                "timestamp_iso": datetime.now(pytz.timezone('America/Mexico_City')).isoformat(),
                "day": datetime.now(pytz.timezone('America/Mexico_City')).day,
                "month": datetime.now(pytz.timezone('America/Mexico_City')).month,
                "year": datetime.now(pytz.timezone('America/Mexico_City')).year,
                "hour": datetime.now(pytz.timezone('America/Mexico_City')).hour,
                "minute": datetime.now(pytz.timezone('America/Mexico_City')).minute,
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
            
            if idx < 5:  # Solo loggear primeras 5
                print(f"[v0] #{position}: {name} ({tweet_count} tweets)", file=sys.stderr)
        
        print(f"\n[v0] ✓ {len(trends_list)} tendencias extraídas correctamente", file=sys.stderr)
        
        if len(trends_list) == 0:
            print("[v0] ERROR: No se extrajo ninguna tendencia válida", file=sys.stderr)
            return generate_example_data()
        
        first_trend_minutes = trends_list[0]['minutes_since_creation'] if trends_list and trends_list[0].get('minutes_since_creation') is not None else None
        
        mexico_tz = pytz.timezone('America/Mexico_City')
        mexico_time_now = datetime.now(mexico_tz)
        
        if first_trend_minutes is not None:
            mexico_time_data = (mexico_time_now - timedelta(minutes=first_trend_minutes))
        else:
            mexico_time_data = mexico_time_now
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "timestamp_mexico": {
                "timestamp_iso": mexico_time_data.isoformat(),
                "day": mexico_time_data.day,
                "month": mexico_time_data.month,
                "year": mexico_time_data.year,
                "hour": mexico_time_data.hour,
                "minute": mexico_time_data.minute
            },
            "country": "México",
            "platform": "Twitter/X",
            "source": "twitter-trending.com",
            "total_trends": len(trends_list),
            "trends": trends_list,
            "status": "success"
        }
        
        print(f"[v0] ✓✓✓ SCRAPING EXITOSO - {len(trends_list)} tendencias", file=sys.stderr)
        return result
    
    except requests.exceptions.Timeout:
        print("[v0] ERROR: Timeout - La solicitud tardó más de 30s", file=sys.stderr)
        return generate_example_data()
    
    except requests.exceptions.ConnectionError as e:
        print(f"[v0] ERROR: Conexión rechazada - {str(e)[:200]}", file=sys.stderr)
        return generate_example_data()
    
    except Exception as e:
        print(f"[v0] ERROR GENERAL: {type(e).__name__}: {str(e)[:200]}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return generate_example_data()

def generate_example_data():
    """
    Genera datos de ejemplo cuando falla el scraping.
    """
    print("[v0] ⚠⚠⚠ Usando datos de ejemplo como fallback...", file=sys.stderr)
    
    mexico_tz = pytz.timezone('America/Mexico_City')
    now = datetime.now(mexico_tz)
    
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
        "timestamp": datetime.now().isoformat(),
        "timestamp_mexico": {
            "timestamp_iso": now.isoformat(),
            "day": now.day,
            "month": now.month,
            "year": now.year,
            "hour": now.hour,
            "minute": now.minute
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
    data = scrape_twitter_trending_mexico()
    
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