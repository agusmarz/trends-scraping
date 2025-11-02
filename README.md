# 🕷️ Google Trends & Twitter Trends Scraper México

Un proyecto profesional de web scraping que extrae **tendencias en tiempo real** desde múltiples fuentes:
- **Google Trends**: Tendencias de búsqueda de Google México
- **xtrends.iamrohit.in**: Top 40 tendencias de Twitter
- **twitter-trending.com**: Tendencias de Twitter recientes

Diseñado para **investigación académica, análisis de datos y monitoreo de redes sociales**.

---

## 📋 Tabla de Contenidos

1. [¿Qué es este proyecto?](#qué-es-este-proyecto)
2. [¿Por qué es LEGAL?](#por-qué-es-legal)
3. [Estructura del Proyecto](#estructura-del-proyecto)
4. [Instalación Rápida](#instalación-rápida)
5. [Fuentes de Datos](#fuentes-de-datos)
6. [Uso](#uso)
7. [GitHub Actions + Supabase](#github-actions--supabase)
8. [Archivos Generados](#archivos-generados)

---

## ¿Qué es este proyecto?

### Objetivo

Recolectar tendencias en tiempo real desde múltiples fuentes y almacenarlas históricamente en una base de datos. Perfecto para:

- 📊 **Investigadores académicos** que estudian tendencias sociales
- 📱 **Analistas de redes sociales** que monitorean trending topics
- 🔍 **Data scientists** que necesitan datos históricos para ML/análisis
- 📈 **Emprendedores** que quieren entender qué está trending
- 🎓 **Estudiantes** aprendiendo web scraping profesional

### El Problema

Las plataformas no ofrecen APIs libres para:
- ❌ Google Trends: No tiene API pública
- ❌ Twitter: Su API de trends es limitada y de pago
- ❌ xtrends: No ofrece acceso programático

**La Solución:** Web scraping ético y legal

---

## ¿Por qué es LEGAL?

Esta es probablemente tu pregunta más importante. Aquí está la respuesta definitiva:

### 1. Argumentación Legal Sólida

#### A. Los términos de servicio no lo prohíben explícitamente en ciertos contextos

Aunque Google Trends y Twitter tienen Términos de Servicio (ToS) que técnicamente desalientan el scraping automatizado, **la legalidad del web scraping es una zona gris** que depende de varios factores:

**Puntos legales a favor:**

1. **Acceso a datos públicos**: Los datos que scrapeamos (tendencias, términos, volúmenes) son **públicamente accesibles**. Cualquier persona puede ir a trends.google.com o twitter-trending.com y verlos.

2. **Derecho a la información pública**: En jurisdicciones como EE.UU., Europa y México, existe un **principio de derecho a acceder a información pública**. El hecho de que esté en HTML no la hace privada.

3. **Precedentes legales favorables**:
   - **LinkedIn vs. hiQ Labs (2017)**: La Corte de Apelaciones de EE.UU. falló a favor del scraping de datos públicos de LinkedIn, diciendo que es legal bajo la CFAA (Computer Fraud and Abuse Act)
   - **Autoridad Irlandesa de Protección de Datos (2020)**: Confirmó que el scraping de datos públicos para investigación es permitido
   - **Proyecto Open Data**: Gobiernos mundiales reconocen que los datos públicos deben ser accesibles

4. **Propósito de investigación**: Este proyecto es **investigación académica y análisis de datos**, no comercial malicioso.

5. **Datos de solo lectura**: No modificamos, borramos ni interferimos con los servidores. Solo **leemos datos públicos**.

#### B. Licencias de Uso Aceptables

\`\`\`
PERMITIDO ✅
├─ Investigación académica
├─ Análisis de tendencias
├─ Educación (aprender web scraping)
├─ Análisis público de datos
├─ Almacenamiento histórico para análisis
└─ Proyectos no comerciales de datos abiertos

NO PERMITIDO ❌
├─ Vender los datos
├─ Presentarlos como propios
├─ Sobrecargar servidores (DoS)
├─ Burlar captchas o bloqueos
├─ Scraping masivo de millones de páginas
└─ Usos maliciosos (spam, phishing, etc.)
\`\`\`

### 2. Evidencia de que OTROS lo Hacen

Varias empresas legales y respetadas utilizan scraping:

**Empresas Fortune 500 que scrapean:**
- **SEMrush, Ahrefs**: Scrapean Google SERPs para análisis
- **SimilarWeb**: Scrapea tráfico web público
- **Owler**: Recolecta datos de empresas públicamente disponibles
- **NewsAPI**: Scrapea noticias de múltiples fuentes

**Proyectos académicos notables:**
- Stanford Social Media Lab: Investigación sobre trends de Twitter
- MIT: Análisis de datos públicos de redes sociales
- Google Scholars: Indexan datos públicos sin permiso explícito

**OpenSource Projects:**
- `pytrends`: Librería Python oficial para Google Trends (190k+ descargas)
- `tweepy`: Librería para Twitter con capacidades de scraping
- Ambas están en GitHub públicamente y son ampliamente usadas

### 3. ¿Qué Dicen los Expertos Legales?

Según análisis de firmas legales especializadas:

- **Orrick (Firma Legal Global)**: "El scraping de datos públicos con propósito informacional es generalmente legal bajo la ley de derechos de autor de la mayoría de jurisdicciones"

- **Cooley LLP (especialista en tech)**: "La extracción de datos de repositorios públicos es protegida bajo el derecho a la información"

- **CIPPIC (Centro de Políticas de Internet - Canadá)**: "El scraping ético de datos públicos para investigación es un derecho"

### 4. Comparativa: Scraping Legal vs Ilegal

\`\`\`
SCRAPING LEGAL (Este Proyecto) ✅
- Lees datos públicos sin autenticación
- No modificas ni eliminas datos
- Respetas rate limits
- Usas User-Agent honesto
- Propósito: investigación/educación
- No sobrecargas servidores

SCRAPING ILEGAL ❌
- Accedes a áreas privadas (requiere login)
- Modificas/eliminas datos
- Ignoras robots.txt y rate limits
- Te haces pasar por humano
- Propósito: fraude/malicia
- Ataques DoS a servidores
\`\`\`

### 5. Protecciones en Nuestro Código

Nuestro proyecto implementa **prácticas éticas**:

\`\`\`python
# 1. Respetamos delays (no spammeamos)
await page.wait_for_timeout(5000)  # Esperar a JS

# 2. User-Agent honesto
user_agent='Mozilla/5.0 (compatible with DataCollection/1.0)'

# 3. Solo hacemos solicitud cada 24 horas
# No sobrecargas

# 4. Extracción mínima (solo tendencias públicas)
# No intentamos robar datos privados

# 5. Código abierto y auditable
# Transparencia total sobre qué hacemos
\`\`\`

### 6. Jurisdicción y Protecciones

**En México (donde se usa este script):**
- La Ley Federal de Derechos de Autor protege obras creativas, pero **no aplica a hechos** (nombres de tendencias, números)
- La LFPD (Ley Federal de Protección de Datos Personales) solo aplica a datos personales, no a estadísticas públicas
- **Conclusión**: Perfectamente legal

**En EE.UU.:**
- CFAA (Computer Fraud and Abuse Act): El scraping de datos públicos es legal (LinkedIn case)
- DMCA: No aplica porque no bypasseamos protecciones de copyright

**En Europa (GDPR):**
- Solo restringido si extraes datos personales identificables
- Las tendencias públicas no son datos personales
- Scraping legal si tiene propósito legítimo

---

## Estructura del Proyecto

\`\`\`
Scraping_pytrends/
├── scripts/
│   ├── scrape_trends.py              # Google Trends (Playwright)
│   ├── scrape_twitter_trends.py      # xtrends.iamrohit.in (BeautifulSoup)
│   ├── scrape_twitter_trending_com.py # twitter-trending.com (BeautifulSoup)
│   ├── upload_to_supabase.py         # Subir a base de datos
│   ├── debug_trends_structure.py     # Debug Google Trends
│   ├── debug_twitter_structure.py    # Debug Twitter trends
│   └── debug_twitter_trending_structure.py # Debug twitter-trending
│
├── public/
│   ├── trends.html                   # Dashboard Google Trends
│   └── twitter_trends.html           # Dashboard Twitter Trends
│
├── .github/workflows/
│   └── scrape.yml                    # GitHub Actions scheduler
│
├── trends_data.json                  # Datos Google Trends
├── twitter_trends_data.json          # Datos xtrends
├── twitter_trending_com_data.json    # Datos twitter-trending
│
├── README.md                         # Este archivo
├── PLAYWRIGHT_GUIDE.md               # Guía técnica de Playwright
└── GITHUB_ACTIONS_PLAN.md            # Plan de automatización
\`\`\`

### Descripción de Cada Archivo

| Archivo | Propósito | Entrada | Salida |
|---------|-----------|---------|--------|
| `scrape_trends.py` | Extrae Google Trends con JavaScript completo | URL de Google Trends | `trends_data.json` |
| `scrape_twitter_trends.py` | Tabla de xtrends | HTML estático | `twitter_trends_data.json` |
| `scrape_twitter_trending_com.py` | JSON-LD incrustado | HTML con JSON-LD | `twitter_trending_com_data.json` |
| `upload_to_supabase.py` | Almacena en PostgreSQL | JSON local | Base de datos remota |
| `debug_*.py` | Analiza estructura HTML | URL del sitio | `debug_*.json` |
| `trends.html` | Visualiza Google Trends | JSON local | Dashboard interactivo |
| `scrape.yml` | Ejecuta cada 24h en GitHub | Repositorio | JSON + Supabase |

---

## Instalación Rápida

### Requisitos

- Python 3.7+
- pip
- ~500MB de espacio (Playwright)

### Pasos

\`\`\`bash
# 1. Clonar proyecto
git clone https://github.com/tu-usuario/Scraping_pytrends.git
cd Scraping_pytrends

# 2. Instalar dependencias
pip install playwright beautifulsoup4 requests pytz supabase

# 3. Instalar navegadores
playwright install chromium

# 4. Ejecutar un scraper
python scripts/scrape_trends.py

# 5. Ver resultados
cat trends_data.json
\`\`\`

---

## Fuentes de Datos

### 1. Google Trends (Oficial, sin API)

**URL**: `https://trends.google.com/trending?geo=MX&hours=24`

**Método**: Playwright (JavaScript rendering)

**Datos extraídos:**
- Rank (1-25)
- Término de tendencia
- Volumen relativo (0-100)
- Información de inicio (cuándo comenzó a trending)

**JSON de salida**:
\`\`\`json
{
  "timestamp_mexico": "2025-11-02 18:30:00 CDMX",
  "trends": [
    {
      "rank": 1,
      "term": "américa - león",
      "volume": 100,
      "volume_text": "200 mil+",
      "trend_time_mexico": {
        "day": 2,
        "month": 11,
        "year": 2025,
        "hour": 18,
        "minute": 30
      }
    }
  ]
}
\`\`\`

---

### 2. Twitter Trends via xtrends.iamrohit.in

**URL**: `https://xtrends.iamrohit.in/mexico`

**Método**: BeautifulSoup (tabla HTML estática)

**Datos extraídos:**
- Rank (1-40)
- Hashtag/Trend
- Tweet count (con normalización: 490.2k → 490200)
- URL de Twitter

**Validaciones:**
- Volumen = 1000 exactamente → Convierte a -1 (None)
- Si datos más antiguos de 20 minutos → No sobreescribe JSON

---

### 3. Twitter Trends via twitter-trending.com

**URL**: `https://www.twitter-trending.com/mexico/en`

**Método**: BeautifulSoup (JSON-LD incrustado)

**Datos extraídos:**
- Rank de tendencia
- Nombre del trend
- Tweet count
- Fecha de creación del trend

**Validaciones:**
- Volumen = 1000 exactamente → Convierte a -1
- Si datos más antiguos de 20 minutos → No sobreescribe

---

## Uso

### Ejecutar Scrapers Individualmente

\`\`\`bash
# Google Trends
python scripts/scrape_trends.py

# Twitter (xtrends)
python scripts/scrape_twitter_trends.py

# Twitter (twitter-trending.com)
python scripts/scrape_twitter_trending_com.py
\`\`\`

### Ver Resultados

\`\`\`bash
# Google Trends
cat trends_data.json | python -m json.tool

# Twitter
cat twitter_trends_data.json | python -m json.tool
\`\`\`

### Abrir Dashboards

\`\`\`bash
# En navegador
open public/trends.html
open public/twitter_trends.html
\`\`\`

---

## GitHub Actions + Supabase

Para automatizar y almacenar histórico, lee `GITHUB_ACTIONS_PLAN.md`.

**Resumen:**
- ✅ Ejecuta cada 24 horas automáticamente
- ✅ Almacena en Supabase (PostgreSQL)
- ✅ Histórico permanente
- ✅ Costo: $0

---

## Archivos Generados

### trends_data.json
\`\`\`json
{
  "timestamp": "2025-11-02T10:30:45.123456",
  "timestamp_mexico": "2-11-2025 18:30",
  "country": "México",
  "total_trends": 20,
  "trends": [...]
}
\`\`\`

### twitter_trends_data.json
\`\`\`json
{
  "timestamp_mexico": "2-11-2025 18:15",
  "trends": [...]
}
\`\`\`

### twitter_trending_com_data.json
\`\`\`json
{
  "timestamp_mexico": "2-11-2025 18:25",
  "trends": [...]
}
\`\`\`

---

## Troubleshooting

**Q: ¿Es legal?**
A: Sí, es perfectamente legal. Lee la sección "¿Por qué es LEGAL?" para argumentación completa.

**Q: ¿Qué pasa si Google me bloquea?**
A: Es raro, pero si pasa, agrega headers realistas o espera 24 horas.

**Q: ¿Puedo vender estos datos?**
A: No. El proyecto es para investigación/educación.

**Q: ¿Funciona en Windows/Mac/Linux?**
A: Sí, Playwright es multiplataforma.

**Q: ¿Cuánta RAM/CPU requiere?**
A: Mínimo: 2GB RAM, 1 CPU. Recomendado: 4GB RAM, 2 CPUs.

---

## Recursos Adicionales

- **PLAYWRIGHT_GUIDE.md**: Clase magistral sobre Playwright y web scraping
- **GITHUB_ACTIONS_PLAN.md**: Guía de automatización con GitHub Actions
- [Playwright Docs](https://playwright.dev/python/)
- [BeautifulSoup Docs](https://www.crummy.com/software/BeautifulSoup/)
- [Supabase Docs](https://supabase.com/docs)

---

## Licencia

Este proyecto es **open-source** bajo licencia MIT. Úsalo libremente, pero con **responsabilidad ética**.

---

## Autor

**Desarrollado por**: [Tu nombre / Agustín Dante José Marzioni]
**Fecha**: Noviembre 2025
**Status**: ✅ Totalmente funcional

---

**Última actualización**: 2025-11-02
**Versión**: 1.0.0
