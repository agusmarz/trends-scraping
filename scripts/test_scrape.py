"""
Script de prueba para debuggear el scraping de Google Trends
Explora la estructura real del HTML y extrae datos correctamente
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime

async def test_scrape():
    """
    Prueba de scraping con mucho detalle para ver qué estructura tiene el sitio
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        url = 'https://trends.google.com/trending?geo=MX&hours=24'
        
        print("[v0] ========== INICIANDO PRUEBA DE SCRAPING ==========")
        print(f"[v0] URL: {url}")
        
        try:
            # Navegar
            response = await page.goto(url, wait_until='networkidle', timeout=40000)
            print(f"[v0] Status de respuesta: {response.status}")
            
            # Esperar un poco más para asegurar que todo cargue
            await page.wait_for_timeout(3000)
            
            # Obtener el HTML completo para inspeccionar
            html = await page.content()
            print(f"[v0] Tamaño del HTML: {len(html)} caracteres")
            
            # Intentar seleccionadores comunes en Google Trends
            print("\n[v0] ========== PROBANDO SELECCIONADORES ==========")
            
            selectors_to_try = [
                'div.mdl-card',
                'div[data-cid]',
                'a[href*="/trends/explore"]',
                'span.title',
                'div.trend-item',
                'div.feed-item',
                'article',
                'div.ng-scope'
            ]
            
            for selector in selectors_to_try:
                try:
                    count = await page.locator(selector).count()
                    print(f"[v0] Selector '{selector}': {count} elementos encontrados")
                    
                    if count > 0 and count < 50:
                        # Si hay pocos, mostrar el HTML
                        elem = await page.locator(selector).first.inner_html()
                        print(f"[v0]   → Primer elemento: {elem[:200]}...")
                except Exception as e:
                    print(f"[v0] Selector '{selector}': Error - {e}")
            
            # Intentar encontrar JSON incrustado
            print("\n[v0] ========== BUSCANDO DATOS JSON ==========")
            if 'window["_INITIAL_STATE"]' in html or '_INITIAL_STATE' in html:
                print("[v0] ✓ JSON de estado inicial encontrado en el HTML")
            else:
                print("[v0] JSON de estado inicial NO encontrado")
            
            # Buscar cualquier JSON
            import re
            json_patterns = re.findall(r'var\s+\w+\s*=\s*(\{.*?\});', html[:10000])
            print(f"[v0] Patrones JSON encontrados: {len(json_patterns)}")
            
            # Intentar ejecutar JavaScript para extraer datos
            print("\n[v0] ========== INTENTANDO EXTRACCIÓN VÍA JAVASCRIPT ==========")
            
            # Inyectar JavaScript para extraer tendencias
            trends_via_js = await page.evaluate("""
                () => {
                    // Buscar todos los elementos que se vean como tendencias
                    const trends = [];
                    
                    // Intento 1: por cards
                    const cards = document.querySelectorAll('[data-cid], .trend-item, .feed-item, .mdl-card');
                    console.log('Cards encontradas:', cards.length);
                    
                    // Intento 2: buscar todos los enlaces que conducen a /trends/explore
                    const links = document.querySelectorAll('a[href*="/trends/explore"]');
                    console.log('Enlaces encontrados:', links.length);
                    
                    links.forEach((link, idx) => {
                        const text = link.textContent.trim();
                        const href = link.getAttribute('href');
                        if (text && text.length > 0) {
                            trends.push({
                                rank: idx + 1,
                                term: text,
                                href: href
                            });
                        }
                    });
                    
                    return {
                        totalTrends: trends.length,
                        trends: trends.slice(0, 20)
                    };
                }
            """)
            
            print(f"[v0] Tendencias extraídas via JS: {trends_via_js}")
            
            # Guardar el HTML para inspección manual
            with open('debug_page.html', 'w', encoding='utf-8') as f:
                f.write(html[:5000])  # Primeros 5000 caracteres
            print("[v0] Primeros 5000 caracteres del HTML guardados en debug_page.html")
            
        except Exception as e:
            print(f"[v0] ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_scrape())
