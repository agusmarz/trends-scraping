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
    Extrae tendencias RECIENTES de https://www.twitter-trending.com/mexico/en
    Solo extrae tendencias con "X minutes ago" (últimas actualizaciones).
    """
    url = 'https://www.twitter-trending.com/mexico/en'
    
    print("[v0] ========== INICIANDO SCRAPING TWITTER-TRENDING.COM ==========")
    print(f"[v0] URL: {url}")
    print("[v0] Filtro: Solo tendencias 'X minutes ago'")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-MX,es;q=0.9,en;q=0.8',
            'Referer': 'https://www.twitter-trending.com/',
        }
        
        print("[v0] Realizando solicitud HTTP...")
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        print(f"[v0] Status code: {response.status_code}")
        print(f"[v0] Tamaño del HTML: {len(response.text)} caracteres")
        
        print("[v0] Parseando HTML...")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Buscar JSON-LD schema.org
        print("[v0] Buscando JSON-LD incrustado...")
        json_ld_scripts = soup.find_all('script', {'type': 'application/ld+json'})
        
        if not json_ld_scripts:
            print("[v0] ERROR: No se encontraron scripts JSON-LD")
            return create_error_response("No se encontraron scripts JSON-LD")
        
        print(f"[v0] Encontrados {len(json_ld_scripts)} scripts JSON-LD")
        
        trends_list = None
        
        # Buscar el ItemList con las tendencias
        for script in json_ld_scripts:
            try:
                schema_data = json.loads(script.string)
                if schema_data.get('@type') == 'ItemList' and 'itemListElement' in schema_data:
                    trends_list = schema_data
                    print("[v0] ✓ JSON-LD de tendencias encontrado")
                    break
            except json.JSONDecodeError:
                continue
        
        if not trends_list:
            print("[v0] ERROR: No se encontró ItemList en JSON-LD")
            return create_error_response("No se encontró ItemList en JSON-LD")
        
        total_items = trends_list.get('numberOfItems', 0)
        print(f"[v0] Total de tendencias en la página: {total_items}")
        
        # Ahora necesitamos los tiempos de actualización
        # Estos están en el HTML, no en el JSON-LD
        print("[v0] Buscando información de tiempos en el HTML...")
        
        # Buscar todos los elementos con información de tendencias
        trend_elements = soup.find_all('div', class_='trend-item')
        if not trend_elements:
            # Intentar otro selector
            trend_elements = soup.find_all('li', class_='trend')
        
        print(f"[v0] Elementos de tendencias encontrados en HTML: {len(trend_elements)}")
        
        # Mapear tiempos a índices
        time_map = {}
        for idx, element in enumerate(trend_elements):
            time_text = None
            
            # Buscar texto de tiempo en diferentes ubicaciones
            time_span = element.find('span', class_='time')
            if time_span:
                time_text = time_span.get_text()
            else:
                # Buscar en todo el elemento
                for span in element.find_all('span'):
                    text = span.get_text().strip()
                    if 'ago' in text or 'now' in text.lower():
                        time_text = text
                        break
            
            if time_text:
                time_map[idx] = time_text
                print(f"[v0] Elemento {idx}: {time_text}")
        
        # Extraer solo tendencias recientes (X minutes ago)
        recent_trends = []
        
        if trends_list.get('itemListElement'):
            for idx, item in enumerate(trends_list['itemListElement']):
                if item.get('@type') == 'ListItem':
                    position = item.get('position', idx + 1)
                    name = item.get('name', '').strip()
                    tweet_count = item.get('Tweet Count', 0)
                    url = item.get('url', '')
                    
                    # Obtener tiempo
                    time_text = time_map.get(idx, time_map.get(position - 1))
                    
                    # Verificar si es reciente
                    minutes = extract_minutes_ago(time_text) if time_text else None
                    
                    if minutes is not None:  # Solo incluir si es reciente
                        recent_trends.append({
                            "position": position,
                            "term": name,
                            "tweet_count": tweet_count,
                            "time_text": time_text,
                            "minutes_ago": minutes,
                            "url": url
                        })
                        print(f"[v0] ✓ RECIENTE #{position}: {name} ({time_text})")
                    else:
                        print(f"[v0] ✗ NO RECIENTE #{position}: {name} ({time_text})")
        
        print(f"\n[v0] Tendencias recientes encontradas: {len(recent_trends)}")
        
        if recent_trends:
            print("[v0] Top 5 tendencias recientes:")
            for t in recent_trends[:5]:
                print(f"  #{t['position']}: {t['term']} ({t['time_text']})")
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "country": "México",
            "platform": "Twitter/X",
            "source": "twitter-trending.com",
            "filter": "only_recent_minutes",
            "total_trends_on_page": total_items,
            "recent_trends_count": len(recent_trends),
            "trends": recent_trends,
            "status": "success" if recent_trends else "no_recent_trends"
        }
        
        return result
    
    except requests.exceptions.Timeout:
        print("[v0] ERROR: Timeout - La solicitud tardó demasiado")
        return create_error_response("Timeout en la solicitud HTTP")
    
    except requests.exceptions.ConnectionError as e:
        print(f"[v0] ERROR: Conexión rechazada - {e}")
        return create_error_response(f"Error de conexión: {str(e)}")
    
    except Exception as e:
        print(f"[v0] ERROR GENERAL: {type(e).__name__}: {e}")
        return create_error_response(str(e))

def create_error_response(error_msg):
    """Crea una respuesta de error estructurada"""
    return {
        "timestamp": datetime.now().isoformat(),
        "country": "México",
        "platform": "Twitter/X",
        "source": "twitter-trending.com",
        "filter": "only_recent_minutes",
        "total_trends_on_page": 0,
        "recent_trends_count": 0,
        "trends": [],
        "status": "error",
        "error": error_msg
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
    print(f"[v0] Tendencias recientes encontradas: {data['recent_trends_count']}")
    print("\n" + json.dumps(data, ensure_ascii=False, indent=2))
