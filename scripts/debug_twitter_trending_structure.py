import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

def debug_twitter_trending_structure():
    """
    Script de debug para explorar la estructura de twitter-trending.com
    y entender cómo extraer información de tiempos.
    """
    url = 'https://www.twitter-trending.com/mexico/en'
    
    print("[v0] ========== DEBUG TWITTER-TRENDING.COM ==========")
    print(f"[v0] URL: {url}\n")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        print(f"[v0] Status: {response.status_code}")
        print(f"[v0] HTML size: {len(response.text)} caracteres\n")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Buscar JSON-LD
        print("[v0] ========== JSON-LD ENCONTRADO ==========")
        json_ld_scripts = soup.find_all('script', {'type': 'application/ld+json'})
        print(f"[v0] Scripts JSON-LD: {len(json_ld_scripts)}\n")
        
        for idx, script in enumerate(json_ld_scripts):
            try:
                schema_data = json.loads(script.string)
                print(f"[v0] Script {idx}:")
                print(f"  Type: {schema_data.get('@type')}")
                print(f"  Items: {len(schema_data.get('itemListElement', []))}")
                
                if schema_data.get('@type') == 'ItemList':
                    print("[v0] Primeros 3 items:")
                    for item in schema_data.get('itemListElement', [])[:3]:
                        print(f"  - {item.get('position')}: {item.get('name')} ({item.get('Tweet Count')} tweets)")
                print()
            except json.JSONDecodeError as e:
                print(f"[v0] Error parseando JSON-LD {idx}: {e}\n")
        
        # 2. Buscar elementos de tendencias en el HTML
        print("[v0] ========== BUSCANDO ELEMENTOS DE TENDENCIAS ==========")
        
        # Intentar diferentes selectores
        selectors = [
            ('div', {'class': 'trend-item'}),
            ('li', {'class': 'trend'}),
            ('div', {'class': 'trend'}),
            ('article', {'class': 'trend'}),
            ('tr', {}),  # Si es una tabla
        ]
        
        for tag, attrs in selectors:
            elements = soup.find_all(tag, attrs) if attrs else soup.find_all(tag)
            if elements:
                print(f"[v0] Encontrados {len(elements)} elementos <{tag}> con attrs {attrs}")
                print(f"[v0] Primeros 2 elementos:")
                for elem in elements[:2]:
                    print(f"  HTML: {str(elem)[:200]}...")
                print()
        
        # 3. Buscar información de tiempos
        print("[v0] ========== BUSCANDO INFORMACIÓN DE TIEMPOS ==========")
        
        time_elements = soup.find_all(string=lambda text: text and ('ago' in text.lower() or 'now' in text.lower()))
        print(f"[v0] Elementos con 'ago' o 'now': {len(time_elements)}")
        for elem in time_elements[:10]:
            print(f"  - {elem.strip()}")
        
        # Guardar primeras 10k caracteres del HTML para análisis manual
        debug_file = 'debug_twitter_trending_html.html'
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(response.text[:10000])
        print(f"\n[v0] Primeros 10k caracteres guardados en {debug_file}")
        
    except Exception as e:
        print(f"[v0] ERROR: {type(e).__name__}: {e}")

if __name__ == "__main__":
    debug_twitter_trending_structure()
