import requests
from bs4 import BeautifulSoup
import json

def debug_twitter_structure():
    """
    Script de debug para explorar la estructura del sitio de Twitter Trends
    """
    url = 'https://xtrends.iamrohit.in/mexico'
    
    print("[v0] ========== DEBUG TWITTER TRENDS STRUCTURE ==========")
    print(f"[v0] URL: {url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        print(f"[v0] Status: {response.status_code}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Debug 1: Buscar tabla
        print("\n[v0] === BUSCANDO TABLA ===")
        table = soup.find('table', {'id': 'twitter-trends'})
        if table:
            print(f"[v0] ✓ Tabla encontrada")
        else:
            print(f"[v0] ✗ Tabla NO encontrada")
        
        # Debug 2: Buscar tbody
        print("\n[v0] === BUSCANDO TBODY ===")
        tbody = table.find('tbody', {'id': 'copyData'}) if table else None
        if tbody:
            rows = tbody.find_all('tr')
            print(f"[v0] ✓ tbody encontrado con {len(rows)} filas")
        else:
            print(f"[v0] ✗ tbody NO encontrado")
        
        # Debug 3: Analizar primeras 5 filas
        print("\n[v0] === ANALIZANDO PRIMERAS 5 FILAS ===")
        if tbody:
            for idx, row in enumerate(rows[:5]):
                print(f"\n[v0] Fila {idx}:")
                
                # Buscar link
                link = row.find('a', {'class': 'tweet'})
                if link:
                    print(f"  Rank: {link.get('rank', 'N/A')}")
                    print(f"  Texto: {link.text.strip()}")
                    print(f"  tweetCount: {link.get('tweetCount', 'N/A')}")
                    print(f"  href: {link.get('href', 'N/A')}")
                else:
                    print(f"  ✗ No link encontrado")
        
        # Debug 4: Guardar estructura de primeras 5 trends
        print("\n[v0] === GUARDANDO ESTRUCTURA DETALLADA ===")
        debug_data = []
        if tbody:
            for idx, row in enumerate(rows[:5]):
                row_data = {
                    "fila": idx,
                    "html": str(row)[:500],  # Primeros 500 chars
                    "link": None
                }
                
                link = row.find('a', {'class': 'tweet'})
                if link:
                    row_data["link"] = {
                        "rank": link.get('rank'),
                        "text": link.text.strip(),
                        "tweetCount": link.get('tweetCount'),
                        "tweetC": link.get('tweetC'),
                        "href": link.get('href')
                    }
                
                debug_data.append(row_data)
        
        with open('debug_twitter_structure.json', 'w', encoding='utf-8') as f:
            json.dump(debug_data, f, ensure_ascii=False, indent=2)
        
        print(f"[v0] Estructura guardada en debug_twitter_structure.json")
        
    except Exception as e:
        print(f"[v0] ERROR: {type(e).__name__}: {e}")

if __name__ == "__main__":
    debug_twitter_structure()
