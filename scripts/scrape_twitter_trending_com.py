import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime

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
            
            if not name:
                print(f"[v0] ⚠ Item {position} sin nombre, saltando")
                continue
            
            trend_data = {
                "rank": position,
                "term": name,
                "tweet_volume": tweet_count,
                "url": url_trend
            }
            
            trends_list.append(trend_data)
            print(f"[v0] #{position}: {name} ({tweet_count} tweets)")
        
        print(f"\n[v0] ✓ {len(trends_list)} tendencias extraídas correctamente")
        
        result = {
            "timestamp": datetime.now().isoformat(),
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
    
    example_trends = [
        {"rank": 1, "term": "Carlos Manzo", "tweet_volume": 1000},
        {"rank": 2, "term": "#FueClaudia", "tweet_volume": 28000},
        {"rank": 3, "term": "Michoacán", "tweet_volume": 180000},
        {"rank": 4, "term": "Calderón", "tweet_volume": 12000},
        {"rank": 5, "term": "#FueElEstado", "tweet_volume": 12399},
        {"rank": 6, "term": "Gabinete de Seguridad", "tweet_volume": 19000},
        {"rank": 7, "term": "Chinguen", "tweet_volume": 15399},
        {"rank": 8, "term": "Cállate", "tweet_volume": 8987},
        {"rank": 9, "term": "Colosio", "tweet_volume": 3859},
        {"rank": 10, "term": "#MexicoDeLuto", "tweet_volume": 5909},
    ]
    
    return {
        "timestamp": datetime.now().isoformat(),
        "country": "México",
        "platform": "Twitter/X",
        "source": "twitter-trending.com",
        "total_trends": len(example_trends),
        "trends": example_trends,
        "status": "example_data"
    }

if __name__ == "__main__":
    print("[v0] Iniciando scraper de twitter-trending.com...\n")
    data = scrape_twitter_trending_mexico()
    
    # Guardar en JSON
    output_file = 'twitter_trending_com_data.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n[v0] ========== SCRAPING COMPLETADO ==========")
    print(f"[v0] Datos guardados en {output_file}")
    print(f"[v0] Status: {data['status']}")
    print(f"[v0] Tendencias encontradas: {data['total_trends']}")
    if data['trends'][:3]:
        print("[v0] Top 3:")
        for t in data['trends'][:3]:
            print(f"  #{t['rank']}: {t['term']} ({t['tweet_volume']} tweets)")
