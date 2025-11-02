import asyncio
from playwright.async_api import async_playwright

async def debug_google_trends():
    """
    Script de depuración para inspeccionar la estructura de la página de Google Trends
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        url = 'https://trends.google.com/trending?geo=MX&hours=24'
        
        print("[v0] Navegando...")
        await page.goto(url, wait_until='domcontentloaded', timeout=30000)
        await page.wait_for_timeout(6000)
        
        print("[v0] Extrayendo estructura...")
        
        # Extraer texto visible de la página
        all_text = await page.evaluate('''
            () => {
                // Buscar todos los textos visibles que se vean en la página
                let allElements = document.body.innerText;
                return allElements;
            }
        ''')
        
        # Guardar primeros 10000 caracteres
        with open('debug_visible_text.txt', 'w', encoding='utf-8') as f:
            f.write(all_text[:10000])
        
        print("[v0] Texto visible guardado en debug_visible_text.txt")
        
        # Ahora obtener estructura HTML de elementos con texto
        structure = await page.evaluate('''
            () => {
                let elements = [];
                
                // Buscar elementos que contengan nombres de tendencias conocidas
                const allDivs = document.querySelectorAll('div, span, p, a');
                
                allDivs.forEach(el => {
                    const text = el.innerText?.trim() || el.textContent?.trim();
                    
                    // Buscar términos conocidos de las tendencias
                    if (text && (
                        text.includes('león') || 
                        text.includes('manzo') || 
                        text.includes('monterrey') ||
                        text.includes('atlas') ||
                        text.includes('madrid') ||
                        text.includes('200') ||
                        text.includes('mil+')
                    )) {
                        const parent = el.parentElement;
                        elements.push({
                            tag: el.tagName,
                            text: text.substring(0, 100),
                            class: el.className,
                            parentTag: parent?.tagName,
                            parentClass: parent?.className,
                            role: el.getAttribute('role'),
                            parentRole: parent?.getAttribute('role'),
                            dataAttr: el.getAttribute('data-tooltip'),
                            ariaLabel: el.getAttribute('aria-label')
                        });
                    }
                });
                
                return elements;
            }
        ''')
        
        with open('debug_structure.json', 'w', encoding='utf-8') as f:
            import json
            json.dump(structure, f, indent=2, ensure_ascii=False)
        
        print(f"[v0] Encontrados {len(structure)} elementos con términos de trends")
        print("[v0] Estructura guardada en debug_structure.json")
        
        # Mostrar primeros 5 elementos
        if structure:
            print("\n[v0] Primeros elementos encontrados:")
            for i, el in enumerate(structure[:5]):
                print(f"  {i+1}. Tag: {el['tag']}, Texto: {el['text'][:50]}")
                print(f"     Class: {el['class'][:100] if el['class'] else 'N/A'}")
                print(f"     Parent: {el['parentTag']} ({el['parentClass'][:100] if el['parentClass'] else 'N/A'})")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_google_trends())
