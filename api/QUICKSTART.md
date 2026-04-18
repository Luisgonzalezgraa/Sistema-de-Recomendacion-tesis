# Quick Start - API de Riego

## Pasos Iniciales Rápidos (5 minutos)

### 1. Setup Inicial

```bash
# Navegar a la carpeta de la API
cd c:\Users\luisg\Documents\Sistema-de-Recomendacion-tesis\api

# Crear ambiente virtual
python -m venv venv

# Activar ambiente
venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configurar API Key (Opcional)

Si no tienes Google API key, la API usará datos de prueba (Mock Service):

```bash
# Copiar archivo de configuración
copy .env.example .env

# (Opcional) Editar .env con tu Google API key
# GOOGLE_ELEVATION_API_KEY=tu_key_aqui
```

### 3. Ejecutar la API

```bash
python run.py
```

Deberías ver:
```
 * Running on http://0.0.0.0:5000
 * Debug mode: on
```

### 4. Probar la API

En otra terminal:

```bash
# Test simple (healthcheck)
curl http://localhost:5000/api/v1/health

# Ver documentación
curl http://localhost:5000/api/v1/docs
```

## Ejemplo Completo: Generar Recomendaciones

### Con PowerShell:

```powershell
# Crear archivo JSON con la solicitud
$body = @{
    location = @{
        latitude = -33.5731
        longitude = -70.6673
    }
    endpoint = @{
        latitude = -33.5745
        longitude = -70.6690
    }
    water_composition = @{
        density = 1000
        temperature = 20
        ph = 7.0
        salinity = 200
        hardness = 150
    }
    pipe_length = 450
    pipe_diameter = 0.016
    flow_rate = 0.00012
} | ConvertTo-Json

# Hacer la solicitud
$response = Invoke-WebRequest -Uri "http://localhost:5000/api/v1/recommendations" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

# Ver resultados
$response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

### Con cURL (Git Bash o Terminal):

```bash
curl -X POST http://localhost:5000/api/v1/recommendations \
  -H "Content-Type: application/json" \
  -d "{
    \"location\": {\"latitude\": -33.5731, \"longitude\": -70.6673},
    \"endpoint\": {\"latitude\": -33.5745, \"longitude\": -70.6690},
    \"water_composition\": {
      \"density\": 1000,
      \"temperature\": 20,
      \"ph\": 7.0,
      \"salinity\": 200,
      \"hardness\": 150
    },
    \"pipe_length\": 450,
    \"pipe_diameter\": 0.016,
    \"flow_rate\": 0.00012
  }"
```

## Estructura de Directorios

```
api/
├── app/                    # Código principal
├── tests/                  # Tests (próximamente)
├── data/                   # Datos
├── config.py              # Configuración
├── run.py                 # Ejecutable
├── requirements.txt       # Dependencias
├── .env.example          # Configuración de ejemplo
├── API_README.md         # Documentación completa
└── QUICKSTART.md         # Este archivo
```

## Endpoints Principales

| Endpoint | Método | Descripción |
|----------|--------|------------|
| `/api/v1/health` | GET | Verificar estado |
| `/api/v1/analysis/elevation` | POST | Análisis topográfico |
| `/api/v1/analysis/hydraulic` | POST | Análisis hidráulico |
| `/api/v1/recommendations` | POST | Recomendaciones completas |
| `/api/v1/docs` | GET | Documentación |

## Troubleshooting

### "ModuleNotFoundError: No module named 'flask'"

**Solución**: Asegurate de haber activado el ambiente virtual
```bash
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

### "Port 5000 is already in use"

**Solución**: Cambiar puerto o terminar proceso
```bash
# Con variable de entorno
set FLASK_PORT=5001
python run.py

# O terminar el proceso existente
taskkill /PID <pid> /F  # Windows
kill -9 <pid>  # Linux
```

### "Cannot connect to server"

**Solución**: Verificar que el servidor esté corriendo
```bash
# En otra terminal, verificar
curl http://localhost:5000/api/v1/health
```

### "Google API Error"

**Solución**: La API usa Mock Service automáticamente. Para usar Google API:
1. Obtener API key en https://console.cloud.google.com/
2. Habilitar "Elevation API"
3. Añadir key a `.env` y reiniciar servidor

## Próximos Pasos

1. **Leer documentación completa**: Ver `API_README.md`
2. **Ver ejemplos**: Carpeta `data/samples/`
3. **Ejecutar tests**: `pytest tests/` (próximos)
4. **Integrar con tu aplicación**: Usar los endpoints REST

## Información Útil

- **Documentación de Flask**: https://flask.palletsprojects.com/
- **API Google Elevation**: https://developers.google.com/maps/documentation/elevation
- **Ecuaciones utilizadas**: Ver `API_README.md` sección "Ecuaciones Implementadas"

¡Listo! Tu API está corriendo. Ahora puedes:
- Hacer llamadas a los endpoints
- Integrar con una aplicación frontend
- Crear scripts de automatización
- Expandir con más funcionalidades
