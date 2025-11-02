import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import re

def normalize_tweet_count(count_str):
    """
    Convierte strings de volumen a números normalizados.
    Ejemplos: "443.6k" -> 443600, "Under 10k" -> 5000
    """
    if not count_str:
        return 0
    
    count_str = count_str.strip().lower()
    print(f"[v0] Normalizando: '{count_str}'")
    
    # Si dice "Under 10k"
    if "under 10k" in count_str:
        return 5000
    
    # Si tiene "k" (miles)
    if "k" in count_str:
        try:
            # Extraer número: "443.6k" -> 443.6
            match = re.search(r'([\d.]+)\s*k', count_str)
            if match:
                number = float(match.group(1))
                return int(number * 1000)
        except:
            pass
    
    # Si tiene números sin letra
    try:
        match = re.search(r'([\d.]+)', count_str)
        if match:
            return int(float(match.group(1)))
    except:
        pass
    
    return 0

def scrape_twitter_trends_mexico():
    """
    Extrae top 40 tendencias de Twitter para México desde xtrends.iamrohit.in
    """
    url = 'https://xtrends.iamrohit.in/mexico'
    
    print("[v0] ========== INICIANDO SCRAPING TWITTER TRENDS ==========")
    print(f"[v0] URL: {url}")
    
    try:
        # Headers realistas
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-MX,es;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache',
        }
        
        print("[v0] Realizando solicitud HTTP...")
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        print(f"[v0] Status code: {response.status_code}")
        print(f"[v0] Tamaño del HTML: {len(response.text)} caracteres")
        
        print("[v0] Parseando HTML...")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Buscar la tabla con id="twitter-trends"
        print("[v0] Buscando tabla con id='twitter-trends'...")
        trends_table = soup.find('table', {'id': 'twitter-trends'})
        
        if not trends_table:
            print("[v0] ERROR: Tabla no encontrada")
            return {
                "timestamp": datetime.now().isoformat(),
                "country": "México",
                "platform": "Twitter/X",
                "total_trends": 0,
                "trends": [],
                "source": "Twitter Trends Scraper",
                "status": "error",
                "error": "Tabla de tendencias no encontrada"
            }
        
        print("[v0] Tabla encontrada. Extrayendo filas...")
        
        # Buscar todas las filas de la tabla (excluyendo header)
        tbody = trends_table.find('tbody', {'id': 'copyData'})
        if not tbody:
            print("[v0] ERROR: tbody no encontrado")
            return {
                "timestamp": datetime.now().isoformat(),
                "country": "México",
                "platform": "Twitter/X",
                "total_trends": 0,
                "trends": [],
                "source": "Twitter Trends Scraper",
                "status": "error",
                "error": "tbody no encontrado"
            }
        
        rows = tbody.find_all('tr')
        print(f"[v0] Total de filas encontradas: {len(rows)}")
        
        trends = []
        valid_count = 0
        ad_count = 0
        
        for idx, row in enumerate(rows):
            # Ignorar filas de anuncios (que tienen ads)
            if row.find('ins', {'class': 'adsbygoogle'}):
                ad_count += 1
                print(f"[v0] Fila {idx}: Saltando anuncio")
                continue
            
            try:
                # Buscar el link con clase 'tweet'
                tweet_link = row.find('a', {'class': 'tweet'})
                
                if not tweet_link:
                    print(f"[v0] Fila {idx}: No contiene link .tweet")
                    continue
                
                # Extraer datos del link
                rank = tweet_link.get('rank', str(valid_count + 1))
                trend_name = tweet_link.text.strip()
                tweet_count_str = tweet_link.get('tweetcount', tweet_link.get('tweetc', '0'))
                
                # Validar datos
                if not trend_name or len(trend_name) < 1:
                    print(f"[v0] Fila {idx}: Nombre vacío")
                    continue
                
                # Normalizar volumen
                tweet_volume = normalize_tweet_count(tweet_count_str)
                
                trend_obj = {
                    "rank": int(rank),
                    "term": trend_name,
                    "tweet_volume": tweet_volume,
                    "tweet_volume_text": tweet_count_str,
                    "url": tweet_link.get('href', '')
                }
                
                trends.append(trend_obj)
                valid_count += 1
                
                print(f"[v0] ✓ Trend {valid_count}: '{trend_name}' - {tweet_count_str}")
                
                # Limitar a 40 tendencias
                if valid_count >= 40:
                    break
            
            except Exception as e:
                print(f"[v0] ERROR en fila {idx}: {type(e).__name__}: {e}")
                continue
        
        print(f"[v0] Tendencias extraídas: {valid_count}")
        print(f"[v0] Filas de anuncios saltadas: {ad_count}")
        
        if valid_count > 0:
            print(f"[v0] Top 5 tendencias:")
            for t in trends[:5]:
                print(f"  {t['rank']}. {t['term']} ({t['tweet_volume_text']})")
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "country": "México",
            "platform": "Twitter/X",
            "total_trends": valid_count,
            "trends": trends,
            "source": "xtrends.iamrohit.in",
            "status": "success" if valid_count > 0 else "error",
            "debug": {
                "rows_processed": len(rows),
                "ads_skipped": ad_count
            }
        }
        
        return result
    
    except requests.exceptions.Timeout:
        print("[v0] ERROR: Timeout - La solicitud tardó demasiado")
        return {
            "timestamp": datetime.now().isoformat(),
            "country": "México",
            "platform": "Twitter/X",
            "total_trends": 0,
            "trends": [],
            "source": "Twitter Trends Scraper",
            "status": "error",
            "error": "Timeout en la solicitud HTTP"
        }
    
    except requests.exceptions.ConnectionError as e:
        print(f"[v0] ERROR: Conexión rechazada - {e}")
        return {
            "timestamp": datetime.now().isoformat(),
            "country": "México",
            "platform": "Twitter/X",
            "total_trends": 0,
            "trends": [],
            "source": "Twitter Trends Scraper",
            "status": "error",
            "error": f"Error de conexión: {str(e)}"
        }
    
    except Exception as e:
        print(f"[v0] ERROR GENERAL: {type(e).__name__}: {e}")
        return {
            "timestamp": datetime.now().isoformat(),
            "country": "México",
            "platform": "Twitter/X",
            "total_trends": 0,
            "trends": [],
            "source": "Twitter Trends Scraper",
            "status": "error",
            "error": str(e)
        }

if __name__ == "__main__":
    print("[v0] Iniciando scraper de Twitter Trends...")
    data = scrape_twitter_trends_mexico()
    
    # Guardar en JSON
    output_file = 'twitter_trends_data.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n[v0] ========== SCRAPING COMPLETADO ==========")
    print(f"[v0] Datos guardados en {output_file}")
    print(f"[v0] Status: {data['status']}")
    print(f"[v0] Tendencias extraídas: {data['total_trends']}")
    print("\n" + json.dumps(data, ensure_ascii=False, indent=2))
