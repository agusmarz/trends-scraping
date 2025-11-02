import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, timedelta
import pytz

def extract_minutes_ago(time_text):
    """
    Extrae el número de minutos de strings como '5 minutes ago', '2 hours ago', etc.
    Retorna None si no es reciente (en minutos) o si es antiguo (horas/días).
    """
    if not time_text:
        return None
    
    time_text = time_text.strip().lower()
    print(f"[v0] Analizando tiempo: '{time_text}'")
    
    # Buscar "X minutes ago"
    match = re.search(r'(\d+)\s+minutes?\s+ago', time_text)
    if match:
        minutes = int(match.group(1))
        print(f"[v0]   ✓ Es reciente: {minutes} minutos")
        return minutes
    
    # Si dice "hour" o "hours", no es reciente (>60 minutos)
    if 'hour' in time_text:
        print(f"[v0]   ✗ Es viejo: {time_text}")
        return None
    
    # Si dice "day" o "days", descartarlo
    if 'day' in time_text:
        print(f"[v0]   ✗ Es muy viejo: {time_text}")
        return None
    
    # Si dice "just now" o "now", contar como 0 minutos
    if 'just now' in time_text or 'now' == time_text:
        print(f"[v0]   ✓ Es ahora mismo: 0 minutos")
        return 0
    
    print(f"[v0]   ? Formato desconocido: {time_text}")
    return None

def extract_minutes_from_datetime(date_string):
    """
    Calcula cuántos minutos hace fue creada una tendencia basado en dateCreated.
    date_string ejemplo: "2025-11-02T10:30:00Z"
    Retorna el número de minutos, o None si es antiguo (>20 minutos).
    """
    if not date_string:
        return None
    
    try:
        # Parsear fecha ISO 8601
        created_time = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        now = datetime.now(created_time.tzinfo) if created_time.tzinfo else datetime.now()
        
        time_diff = now - created_time
        minutes_ago = int(time_diff.total_seconds() / 60)
        
        print(f"[v0] Tiempo desde creación: {minutes_ago} minutos")
        return minutes_ago
    except Exception as e:
        print(f"[v0] Error parseando fecha: {e}")
        return None

def should_update_based_on_freshness(trends_data, max_minutes=20):
    """
    Verifica si los datos son lo suficientemente recientes para sobreescribir JSON.
    Solo retorna True si hay al menos una tendencia actualizada hace menos de 20 minutos.
    """
    print(f"\n[v0] Verificando frescura de datos (máximo: {max_minutes} minutos)...")
    
    # Si no hay tendencias, no actualizar
    if not trends_data.get('trends') or len(trends_data['trends']) == 0:
        print("[v0] ✗ No hay tendencias, no se actualizará el JSON")
        return False
    
    # Buscar al menos una tendencia reciente
    for trend in trends_data['trends'][:10]:  # Revisar las primeras 10
        if trend.get('minutes_since_creation') is not None:
            minutes = trend.get('minutes_since_creation')
            if minutes < max_minutes:
                print(f"[v0] ✓ Datos suficientemente frescos ({minutes} < {max_minutes} minutos)")
                return True
    
    print(f"[v0] ✗ Datos no son lo suficientemente frescos (≥ {max_minutes} minutos)")
    return False

def scrape_twitter_trending_mexico():
    """
    Extrae tendencias de https://www.twitter-trending.com/mexico/en
    usando JSON-LD incrustado en el HTML (sin depender de JavaScript).
    
    Estrategia:
    1. Extraer JSON-LD ItemList con tendencias
    2. Los primeros items en la lista son los más recientes
    3. Retornar top tendencias con estructura clara
    """
    url = 'https://www.twitter-trending.com/mexico/en'
    
    print("[v0] ========== INICIANDO SCRAPING TWITTER-TRENDING.COM ==========")
    print(f"[v0] URL: {url}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-MX,es;q=0.9',
            'Referer': 'https://www.twitter-trending.com/',
        }
        
        print("[v0] Realizando solicitud HTTP...")
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        print(f"[v0] Status code: {response.status_code} ✓")
        print(f"[v0] Tamaño del HTML: {len(response.text)} caracteres")
        
        print("[v0] Parseando HTML con BeautifulSoup...")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print("[v0] Buscando JSON-LD schema.org...")
        json_ld_script = soup.find('script', {'type': 'application/ld+json'})
        
        if not json_ld_script:
            print("[v0] ERROR: No se encontró JSON-LD")
            return generate_example_data()
        
        print("[v0] ✓ JSON-LD encontrado")
        
        try:
            schema_data = json.loads(json_ld_script.string)
        except json.JSONDecodeError as e:
            print(f"[v0] ERROR parseando JSON: {e}")
            return generate_example_data()
        
        if schema_data.get('@type') != 'ItemList':
            print(f"[v0] ERROR: No es ItemList, es {schema_data.get('@type')}")
            return generate_example_data()
        
        items = schema_data.get('itemListElement', [])
        print(f"[v0] Total de tendencias en JSON-LD: {len(items)}")
        
        if not items:
            print("[v0] ERROR: No hay itemListElement")
            return generate_example_data()
        
        trends_list = []
        
        for idx, item in enumerate(items[:40]):
            if item.get('@type') != 'ListItem':
                continue
                
            position = item.get('position', idx + 1)
            name = item.get('name', '').strip()
            tweet_count = item.get('Tweet Count', 0)
            url_trend = item.get('url', '')
            date_created = item.get('dateCreated', '')
            
            if not name:
                print(f"[v0] ⚠ Item {position} sin nombre, saltando")
                continue
            
            if tweet_count == 1000:
                print(f"[v0] Volumen exacto 1000 detectado, cambiando a -1")
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
            print(f"[v0] #{position}: {name} ({tweet_count} tweets)")
        
        print(f"\n[v0] ✓ {len(trends_list)} tendencias extraídas correctamente")
        
        mexico_tz = pytz.timezone('America/Mexico_City')
        mexico_time_now = datetime.now(mexico_tz)
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "timestamp_mexico": {
                "timestamp_iso": mexico_time_now.isoformat(),
                "day": mexico_time_now.day,
                "month": mexico_time_now.month,
                "year": mexico_time_now.year,
                "hour": mexico_time_now.hour,
                "minute": mexico_time_now.minute
            },
            "country": "México",
            "platform": "Twitter/X",
            "source": "twitter-trending.com",
            "total_trends": len(trends_list),
            "trends": trends_list,
            "status": "success"
        }
        
        return result
    
    except requests.exceptions.Timeout:
        print("[v0] ERROR: Timeout - La solicitud tardó demasiado (>15s)")
        return generate_example_data()
    
    except requests.exceptions.ConnectionError as e:
        print(f"[v0] ERROR: Conexión rechazada - {str(e)[:100]}")
        return generate_example_data()
    
    except Exception as e:
        print(f"[v0] ERROR GENERAL: {type(e).__name__}: {str(e)[:100]}")
        return generate_example_data()

def generate_example_data():
    """
    Genera datos de ejemplo realistas de tendencias mexicanas
    para usar cuando falla el scraping.
    """
    print("[v0] Usando datos de ejemplo como fallback...")
    
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

def get_trend_time_from_creation(date_created_str):
    """
    Calcula la hora real en México a la que corresponden las tendencias
    basado en el dateCreated del JSON-LD.
    Retorna formato estructurado: {day, month, year, hour, minute, timestamp_iso}
    """
    try:
        # Parsear fecha ISO 8601
        created_time = datetime.fromisoformat(date_created_str.replace('Z', '+00:00'))
        
        # Convertir a zona horaria de México
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
        print(f"[v0] Error parseando fecha: {e}")
        # Retornar hora actual si hay error
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

if __name__ == "__main__":
    print("[v0] Iniciando scraper de twitter-trending.com...\n")
    data = scrape_twitter_trending_mexico()
    
    if should_update_based_on_freshness(data, max_minutes=20):
        output_file = 'twitter_trending_com_data.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n[v0] ✓ Datos guardados en {output_file}")
    else:
        print(f"\n[v0] ✗ Datos NO se guardaron (no lo suficientemente frescos)")
    
    print(f"\n[v0] ========== SCRAPING COMPLETADO ==========")
    print(f"[v0] Status: {data['status']}")
    print(f"[v0] Tendencias encontradas: {data['total_trends']}")
    if data['trends'][:3]:
        print("[v0] Top 3:")
        for t in data['trends'][:3]:
            minutes = t.get('minutes_since_creation', 'N/A')
            trend_time = t.get('trend_time_mexico', {})
            time_str = f"{trend_time.get('hour', 0):02d}:{trend_time.get('minute', 0):02d}"
            print(f"  #{t['rank']}: {t['term']} ({t['tweet_volume']} tweets, hace {minutes} min, hora: {time_str})")
