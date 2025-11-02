# Plan de Implementación: GitHub Actions + Supabase

Guía paso a paso para automatizar el scraper de Google Trends con GitHub Actions y almacenar datos en Supabase.

## 📋 Resumen Ejecutivo

\`\`\`
Objetivo: Ejecutar el scraper automáticamente cada 24 horas 
          y almacenar datos históricos en Supabase
\`\`\`

### Arquitectura Final

\`\`\`
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Actions (Scheduler)               │
│              Ejecuta cada 24 horas automáticamente           │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼ (cada 24h)
          ┌────────────────────────────────┐
          │  Servidor Ubuntu de GitHub      │
          │  - Python 3.11                 │
          │  - Playwright instalado        │
          │  - Ejecuta scraper             │
          └────────────────┬───────────────┘
                           │
                    ┌──────┴───────┐
                    ▼              ▼
          ┌─────────────────┐  ┌──────────────────┐
          │ trends_data     │  │ Supabase         │
          │   .json         │  │ (PostgreSQL)     │
          │                 │  │                  │
          │ Repositorio     │  │ Histórico        │
          │ GitHub          │  │ Permanente       │
          └─────────────────┘  └──────────────────┘
\`\`\`

---

## Fase 1: Configurar Supabase (15 minutos)

### Paso 1.1: Crear Proyecto en Supabase

1. Ve a [supabase.com](https://supabase.com)
2. Haz clic en "Sign Up" (si no tienes cuenta)
3. Usa tu email de GitHub (recomendado)
4. Crea un nuevo proyecto:
   - **Nombre**: `google-trends-scraper`
   - **Contraseña**: Guárdala segura
   - **Región**: `us-east-1` (o la más cercana)
5. Espera 2-3 minutos a que se cree

### Paso 1.2: Crear la Tabla de Datos

En la consola de Supabase (o SQL Editor):

\`\`\`sql
-- Crear tabla para almacenar tendencias
CREATE TABLE trends (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
  country VARCHAR(10) NOT NULL,
  geo_code VARCHAR(5) NOT NULL,
  timeframe VARCHAR(50),
  total_trends INT,
  data JSONB NOT NULL,
  source VARCHAR(100),
  status VARCHAR(20),
  created_at TIMESTAMP DEFAULT NOW(),
  
  -- Índices para queries rápidas
  CONSTRAINT trends_timestamp_idx UNIQUE(timestamp, country)
);

-- Crear índices
CREATE INDEX idx_trends_timestamp ON trends(timestamp DESC);
CREATE INDEX idx_trends_country ON trends(country);
CREATE INDEX idx_trends_created_at ON trends(created_at DESC);

-- Habilitar Row Level Security (RLS)
ALTER TABLE trends ENABLE ROW LEVEL SECURITY;

-- Política pública de lectura (cualquiera puede leer)
CREATE POLICY "Trends are publicly readable" 
  ON trends FOR SELECT 
  USING (true);

-- Política de inserción con API Key
CREATE POLICY "API can insert trends" 
  ON trends FOR INSERT 
  WITH CHECK (true);

-- Crear vista para obtener tendencias recientes
CREATE VIEW recent_trends AS
SELECT 
  timestamp,
  country,
  total_trends,
  data,
  status
FROM trends
WHERE timestamp >= NOW() - INTERVAL '30 days'
ORDER BY timestamp DESC;
\`\`\`

### Paso 1.3: Obtener las Credenciales

1. Ve a **Settings** → **API**
2. Copia:
   - **Project URL**: `https://xxxxx.supabase.co`
   - **Project API Key (anon)**: `eyJhbGc...`
3. Guárdalas temporalmente (las vas a usar pronto)

---

## Fase 2: Configurar GitHub (10 minutos)

### Paso 2.1: Crear Carpeta de Workflows

En la raíz de tu repositorio, crea esta estructura:

\`\`\`
.github/
├── workflows/
│   ├── scrape.yml           (El workflow principal)
│   └── cleanup.yml          (Opcional: limpiar datos antiguos)
\`\`\`

### Paso 2.2: Crear el Archivo de Workflow Principal

Crea: `.github/workflows/scrape.yml`

\`\`\`yaml
name: 🕷️ Scrape Google Trends México

on:
  # Ejecutar cada día a las 00:00 UTC (18:00 CDMX)
  schedule:
    - cron: '0 0 * * *'
  
  # Ejecutar cada 6 horas (extra frequent)
  # - cron: '0 */6 * * *'
  
  # Ejecutar manualmente desde GitHub UI
  workflow_dispatch:
  
  # Ejecutar en cada push a main (para testing)
  push:
    branches:
      - main

jobs:
  scrape:
    runs-on: ubuntu-latest
    name: Scrape Trends
    
    steps:
      # Paso 1: Descargar el código
      - name: 📥 Checkout code
        uses: actions/checkout@v4
      
      # Paso 2: Configurar Python
      - name: 🐍 Setup Python 3.11
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'
      
      # Paso 3: Instalar dependencias
      - name: 📦 Install dependencies
        run: |
          pip install --upgrade pip
          pip install playwright
          pip install supabase
          playwright install chromium
      
      # Paso 4: Ejecutar el scraper
      - name: 🕷️ Run scraper
        run: python scripts/scrape_trends.py
      
      # Paso 5: Guardar datos en Supabase
      - name: 💾 Upload to Supabase
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
        run: python scripts/upload_to_supabase.py
      
      # Paso 6: Guardar en el repositorio (historial)
      - name: 📊 Commit trends data to repo
        run: |
          git config --local user.email "github-actions[bot]@users.noreply.github.com"
          git config --local user.name "GitHub Actions Bot"
          git add trends_data.json
          git commit -m "📈 Update trends - $(date -u +'%Y-%m-%d %H:%M:%S UTC')" \
            || echo "✓ No changes to commit"
          git push
      
      # Paso 7: Notificar en caso de error (opcional)
      - name: 📧 Send error notification
        if: failure()
        uses: actions/github-script@v6
        with:
          script: |
            github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: '❌ Scraper Error - ' + new Date().toISOString(),
              body: 'El scraper de Google Trends falló. Revisa los logs.'
            })
\`\`\`

### Paso 2.3: Crear Script para Subir a Supabase

Crea: `scripts/upload_to_supabase.py`

\`\`\`python
import json
import os
from datetime import datetime
from supabase import create_client, Client

def upload_to_supabase():
    """
    Leer trends_data.json y subirlo a Supabase
    """
    
    # Obtener credenciales de GitHub Secrets
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        print("[v0] ❌ Error: SUPABASE_URL o SUPABASE_KEY no configurados")
        return False
    
    # Conectar a Supabase
    print("[v0] 🔗 Conectando a Supabase...")
    supabase: Client = create_client(supabase_url, supabase_key)
    
    # Leer datos del scraper
    print("[v0] 📖 Leyendo trends_data.json...")
    try:
        with open('trends_data.json', 'r', encoding='utf-8') as f:
            trends_data = json.load(f)
    except FileNotFoundError:
        print("[v0] ❌ Error: trends_data.json no encontrado")
        return False
    
    # Preparar datos para insertar
    insert_data = {
        'timestamp': trends_data.get('timestamp'),
        'country': trends_data.get('country', 'México'),
        'geo_code': trends_data.get('geo_code', 'MX'),
        'timeframe': trends_data.get('timeframe'),
        'total_trends': trends_data.get('total_trends'),
        'data': json.dumps(trends_data.get('trends', [])),
        'source': trends_data.get('source', 'Google Trends Scraper'),
        'status': trends_data.get('status', 'unknown')
    }
    
    print(f"[v0] 📤 Insertando {insert_data['total_trends']} tendencias...")
    
    try:
        response = supabase.table('trends').insert(insert_data).execute()
        print(f"[v0] ✅ Datos insertados en Supabase: {response.data}")
        return True
    except Exception as e:
        print(f"[v0] ❌ Error al insertar: {str(e)}")
        return False

if __name__ == "__main__":
    success = upload_to_supabase()
    exit(0 if success else 1)
\`\`\`

### Paso 2.4: Agregar Secretos en GitHub

1. Ve a tu repositorio en GitHub
2. Ve a **Settings** → **Secrets and variables** → **Actions**
3. Haz clic en **"New repository secret"**
4. Crea dos secretos:

**Secreto 1: SUPABASE_URL**
- Name: `SUPABASE_URL`
- Secret: `https://xxxxx.supabase.co` (de Supabase)

**Secreto 2: SUPABASE_KEY**
- Name: `SUPABASE_KEY`
- Secret: `eyJhbGc...` (el API Key de Supabase)

---

## Fase 3: Validar y Probar (5 minutos)

### Prueba 1: Ejecutar Manualmente

1. Ve a tu repositorio → **Actions**
2. Selecciona el workflow "Scrape Google Trends México"
3. Haz clic en **"Run workflow"** → **"Run workflow"**
4. Espera 2-3 minutos

**Resultado esperado:**
\`\`\`
✅ All checks passed
- Checkout code: ✅
- Setup Python 3.11: ✅
- Install dependencies: ✅
- Run scraper: ✅ (20 tendencias extraídas)
- Upload to Supabase: ✅
- Commit trends data to repo: ✅
\`\`\`

### Prueba 2: Verificar en Supabase

1. Ve a tu proyecto Supabase
2. Ve a **SQL Editor**
3. Ejecuta:

\`\`\`sql
SELECT * FROM trends ORDER BY timestamp DESC LIMIT 5;
\`\`\`

**Resultado esperado:**
\`\`\`
id  | timestamp           | country | total_trends | data                    | status
1   | 2025-11-02 10:30:00 | México  | 20          | [{"rank":1,"term":...}] | success
\`\`\`

### Prueba 3: Verificar en GitHub

1. Ve a tu repositorio
2. Verifica que `trends_data.json` se actualizó

---

## Fase 4: Configurar Schedule Automático

El archivo `.github/workflows/scrape.yml` ya contiene:

\`\`\`yaml
on:
  schedule:
    - cron: '0 0 * * *'  # Cada día a las 00:00 UTC
\`\`\`

**Explicación del Cron:**
\`\`\`
'0 0 * * *'
 │ │ │ │ │
 │ │ │ │ └─ Día de la semana (0-6, 0=domingo)
 │ │ │ └─── Mes (1-12)
 │ │ └───── Día del mes (1-31)
 │ └─────── Hora (0-23)
 └───────── Minuto (0-59)

'0 0 * * *' = 00:00 UTC = 18:00 CDMX = Medianoche México
\`\`\`

**Otros horarios útiles:**

\`\`\`yaml
# Cada 6 horas
- cron: '0 */6 * * *'

# Cada 12 horas (6 AM y 6 PM UTC)
- cron: '0 0,12 * * *'

# Cada 4 horas
- cron: '0 */4 * * *'

# Lunes a Viernes a las 9 AM UTC
- cron: '0 9 * * 1-5'
\`\`\`

---

## Fase 5: Monitoreo y Mantenimiento

### Dashboard de GitHub Actions

1. Ve a **Actions** en tu repositorio
2. Verifica:
   - ✅ Últimas ejecuciones
   - ⏱️ Duración de cada ejecución
   - ❌ Errores (si los hay)

### Consultas Útiles en Supabase

**Obtener tendencias del último día:**
\`\`\`sql
SELECT * FROM trends 
WHERE timestamp >= NOW() - INTERVAL '24 hours'
ORDER BY timestamp DESC;
\`\`\`

**Tendencias que subieron más:**
\`\`\`sql
SELECT 
  data->0->>'term' as trend,
  COUNT(*) as appearances,
  MAX((data->0->>'volume')::int) as max_volume
FROM trends
WHERE timestamp >= NOW() - INTERVAL '7 days'
GROUP BY data->0->>'term'
ORDER BY appearances DESC
LIMIT 10;
\`\`\`

**Ver historial de un trend específico:**
\`\`\`sql
SELECT 
  timestamp,
  data
FROM trends
WHERE data::text LIKE '%américa%'
ORDER BY timestamp DESC;
\`\`\`

### Alertas de Error

Si quieres recibir notificaciones cuando falle el scraper, agrega un step al workflow:

\`\`\`yaml
- name: 📧 Notify on failure
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    text: 'Google Trends Scraper failed!'
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
\`\`\`

---

## Fase 6: Escalar (Opcional)

### Agregar Más Países

Modifica `scripts/scrape_trends.py`:

\`\`\`python
countries = [
    {'geo': 'MX', 'name': 'México'},
    {'geo': 'AR', 'name': 'Argentina'},
    {'geo': 'BR', 'name': 'Brasil'},
    {'geo': 'CO', 'name': 'Colombia'},
]

for country in countries:
    data = await scrape_google_trends(country['geo'])
    await upload_to_supabase(data)
\`\`\`

### Crear Dashboard con Datos

Con los datos en Supabase, puedes:
- Crear un dashboard con Grafana
- Usar Power BI para visualizar tendencias
- Construir un API REST para acceder a los datos
- Crear alertas automáticas cuando una tendencia explota

### Usar Webhooks para Notifications

\`\`\`yaml
- name: 📱 Webhook notification
  run: |
    curl -X POST ${{ secrets.WEBHOOK_URL }} \
      -H "Content-Type: application/json" \
      -d '{"message":"Trends updated: $(date)"}'
\`\`\`

---

## Troubleshooting

### Problema: "Secrets not found"

**Solución:** Verifica que los secretos estén en:
`Settings` → `Secrets and variables` → `Actions`

### Problema: "Timeout during scraping"

**Solución:** Aumenta el timeout en el workflow:

\`\`\`yaml
- name: Run scraper
  timeout-minutes: 10  # Incrementar a 10 minutos
  run: python scripts/scrape_trends.py
\`\`\`

### Problema: "supabase module not found"

**Solución:** Verifica que `pip install supabase` esté en el workflow

### Problema: "Permission denied" al hacer push

**Solución:** GitHub Actions necesita permisos. Ve a:
`Settings` → `Actions` → `General` → `Workflow permissions`
Selecciona: `Read and write permissions`

---

## Resultado Final

Después de completar todos los pasos:

✅ El scraper se ejecuta automáticamente cada 24 horas
✅ Los datos se guardan en Supabase
✅ Histórico completo de tendencias disponible
✅ Puedes consultar datos de los últimos meses
✅ Todo sin necesidad de dejar tu computadora prendida

**Costo mensual:** $0 (GitHub Actions gratuito + Supabase free tier)

¡Listo para tener un scraper profesional en producción! 🚀
