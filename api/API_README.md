# API de Recomendación para Diseño de Redes de Riego

## Descripción General

API REST para un **Sistema de Recomendación Multiparámetros para el Diseño de Redes de Riego**. Esta API integra análisis geoespacial, hidráulico y de composición del agua para generar recomendaciones técnicas precisas en el diseño de sistemas de riego por goteo.

### Características Principales

- **Análisis Geoespacial**: Procesamiento de imágenes aéreas y cálculo de pendientes del terreno
- **Análisis Hidráulico**: Cálculos de pérdidas de presión usando ecuación Hazen-Williams
- **Análisis de Composición del Agua**: Evaluación de compatibilidad de materiales según calidad del agua
- **Motor de Recomendaciones**: Genera sugerencias técnicas sobre materiales y potencia de motobomba
- **Integración con Google Elevation API**: Obtención de datos altimétricos precisos
- **API REST profesional**: Arquitectura modular y escalable

## Estructura del Proyecto

```
api/
├── app/
│   ├── __init__.py                  # Factory de la aplicación Flask
│   ├── routes.py                    # Definición de endpoints
│   ├── models/
│   │   ├── __init__.py
│   │   └── data_models.py          # Modelos de datos (dataclasses)
│   ├── modules/
│   │   ├── __init__.py
│   │   ├── geospatial_analyzer.py  # Análisis geoespacial
│   │   ├── hydraulic_calculator.py # Cálculos hidráulicos
│   │   └── recommendation_engine.py# Motor de recomendaciones
│   ├── services/
│   │   ├── __init__.py
│   │   └── elevation_service.py    # Servicios de elevación (Google API)
│   └── utils/
│       └── __init__.py
├── tests/                           # Suite de pruebas
├── data/
│   └── samples/                     # Datos de ejemplo
├── config.py                        # Configuración de la aplicación
├── run.py                          # Punto de entrada
├── requirements.txt                 # Dependencias de Python
├── .env.example                     # Ejemplo de variables de entorno
└── README.md                        # Este archivo
```

## Requisitos Previos

- Python 3.10 o superior
- pip (gestor de paquetes de Python)
- Conexión a Internet (para Google Elevation API)
- API key de Google Maps (obtener en https://console.cloud.google.com/)

## Instalación

### 1. Clonar o descargar el repositorio

```bash
cd c:\Users\luisg\Documents\Sistema-de-Recomendacion-tesis\api
```

### 2. Crear ambiente virtual (recomendado)

**En Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**En Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Copiar el archivo de ejemplo y editarlo:

```bash
copy .env.example .env
```

Editar `.env` y agregar tu Google Maps API key:
```
GOOGLE_ELEVATION_API_KEY=tu_api_key_aqui
```

## Uso

### Iniciar el servidor

```bash
python run.py
```

O con Flask CLI:
```bash
set FLASK_APP=run.py
flask run
```

El servidor estará disponible en `http://localhost:5000`

### Verificar que la API está funcionando

```bash
curl http://localhost:5000/api/v1/health
```

Respuesta esperada:
```json
{
  "success": true,
  "message": "API is running",
  "data": {
    "version": "1.0.0"
  },
  "timestamp": "2026-04-17T12:00:00.000000"
}
```

## Endpoints Disponibles

### 1. Health Check

**Endpoint**: `GET /api/v1/health`

Verifica el estado de la API.

**Respuesta**:
```json
{
  "success": true,
  "message": "API is running",
  "data": {"version": "1.0.0"},
  "timestamp": "2026-04-17T12:00:00"
}
```

---

### 2. Análisis de Elevación

**Endpoint**: `POST /api/v1/analysis/elevation`

Realiza análisis topográfico para puntos geográficos.

**Request Body**:
```json
{
  "points": [
    {
      "latitude": -33.5731,
      "longitude": -70.6673,
      "elevation": null
    },
    {
      "latitude": -33.5740,
      "longitude": -70.6680,
      "elevation": null
    }
  ]
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Topographic analysis completed",
  "data": {
    "point_start": {"latitude": -33.5731, "longitude": -70.6673, "elevation": 567.89},
    "point_end": {"latitude": -33.5740, "longitude": -70.6680, "elevation": 572.15},
    "elevation_difference": 4.26,
    "slope_percentage": 2.31,
    "slope_radians": 0.0404,
    "slope_degrees": 2.31,
    "distance": 184.45
  },
  "timestamp": "2026-04-17T12:00:00"
}
```

---

### 3. Análisis Hidráulico

**Endpoint**: `POST /api/v1/analysis/hydraulic`

Realiza análisis hidráulico del sistema de riego.

**Request Body**:
```json
{
  "topographic_analysis": {
    "point_start": {"latitude": -33.5731, "longitude": -70.6673, "elevation": 567.89},
    "point_end": {"latitude": -33.5740, "longitude": -70.6680, "elevation": 572.15},
    "elevation_difference": 4.26,
    "slope_percentage": 2.31,
    "slope_radians": 0.0404,
    "slope_degrees": 2.31,
    "distance": 184.45
  },
  "water_composition": {
    "density": 1000,
    "temperature": 20,
    "ph": 7.0,
    "salinity": 200,
    "hardness": 150,
    "fertilizer_content": null,
    "pesticide_content": null
  },
  "pipe_length": 500,
  "pipe_diameter": 0.016,
  "flow_rate": 0.0001,
  "emitter_coefficient": 0.95,
  "emitter_exponent": 0.55
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Hydraulic analysis completed",
  "data": {
    "flow_rate": 0.0001,
    "initial_pressure": 1.5,
    "final_pressure": 1.42,
    "pressure_loss": 0.08,
    "hazen_williams_loss": 0.042,
    "elevation_pressure_change": 0.042,
    "emitter_flow": 1.25,
    "required_pump_power": 0.0125,
    "design_warnings": []
  },
  "timestamp": "2026-04-17T12:00:00"
}
```

---

### 4. Recomendaciones Completas

**Endpoint**: `POST /api/v1/recommendations`

Genera recomendaciones completas de diseño.

**Request Body**:
```json
{
  "location": {
    "latitude": -33.5731,
    "longitude": -70.6673
  },
  "endpoint": {
    "latitude": -33.5740,
    "longitude": -70.6680
  },
  "water_composition": {
    "density": 1000,
    "temperature": 20,
    "ph": 7.0,
    "salinity": 200,
    "hardness": 150,
    "fertilizer_content": null,
    "pesticide_content": null
  },
  "pipe_length": 500,
  "pipe_diameter": 0.016,
  "flow_rate": 0.0001,
  "emitter_coefficient": 0.95,
  "emitter_exponent": 0.55
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Recommendations generated successfully",
  "data": {
    "project_id": "uuid-string",
    "timestamp": "2026-04-17T12:00:00",
    "topographic_analysis": {...},
    "water_composition": {...},
    "hydraulic_analysis": {...},
    "recommended_tubings": [
      {
        "name": "HDPE 16mm",
        "material_type": "HDPE",
        "internal_diameter": 16,
        "external_diameter": 20,
        "wall_thickness": 2,
        "hazen_williams_c": 150,
        "recommended_pressure": 2.5,
        "compatibility_notes": [...]
      }
    ],
    "recommended_pump_power": 0.015,
    "design_notes": [...],
    "confidence_score": 0.82
  },
  "timestamp": "2026-04-17T12:00:00"
}
```

---

### 5. Documentación de la API

**Endpoint**: `GET /api/v1/docs`

Obtiene documentación de todos los endpoints disponibles.

## Ecuaciones Implementadas

### 1. Pérdidas por Fricción (Hazen-Williams)

```
hf = 10.67 * L * (Q^1.852) / (C^1.852 * D^4.87)
```

Donde:
- `hf`: Pérdida de carga (m)
- `L`: Longitud de tuberías (m)
- `Q`: Caudal (m³/s)
- `C`: Coeficiente de rugosidad
- `D`: Diámetro interno (m)

### 2. Variación de Presión por Altura

```
ΔP = ρ * g * Δh
```

Donde:
- `ΔP`: Cambio de presión (Pa)
- `ρ`: Densidad del agua (kg/m³)
- `g`: Aceleración gravitatoria (m/s²)
- `Δh`: Diferencia de elevación (m)

### 3. Comportamiento de Emisores

```
q = k * P^x
```

Donde:
- `q`: Caudal del gotero (L/h)
- `P`: Presión de operación (bar)
- `k`: Coeficiente del diseño del emisor
- `x`: Exponente de descarga (típicamente 0.5-0.6)

### 4. Potencia de Bomba

```
Power (HP) = (Flow (L/min) * Pressure (bar)) / 600
```

## Formato de Respuestas

Todas las respuestas siguen este formato estándar:

```json
{
  "success": boolean,
  "message": string,
  "data": object|null,
  "errors": array|null,
  "timestamp": ISO8601 datetime
}
```

## Manejo de Errores

Los errores devuelven códigos HTTP apropiados:

- **400**: Bad Request (entrada inválida)
- **404**: Not Found (recurso no encontrado)
- **500**: Internal Server Error (error del servidor)

Ejemplo de error:
```json
{
  "success": false,
  "message": "Missing required fields: pipe_length, pipe_diameter",
  "errors": ["pipe_length", "pipe_diameter"],
  "timestamp": "2026-04-17T12:00:00"
}
```

## Variables de Entorno

| Variable | Descripción | Valor por Defecto |
|----------|-------------|------------------|
| `FLASK_ENV` | Entorno (development/testing/production) | development |
| `FLASK_HOST` | Host del servidor | 0.0.0.0 |
| `FLASK_PORT` | Puerto del servidor | 5000 |
| `GOOGLE_ELEVATION_API_KEY` | API key de Google Maps | (requerido) |
| `LOG_LEVEL` | Nivel de logging | INFO |

## Ejemplos de Uso

### Con cURL

```bash
# Health check
curl -X GET http://localhost:5000/api/v1/health

# Análisis de elevación
curl -X POST http://localhost:5000/api/v1/analysis/elevation \
  -H "Content-Type: application/json" \
  -d @elevation_request.json

# Recomendaciones
curl -X POST http://localhost:5000/api/v1/recommendations \
  -H "Content-Type: application/json" \
  -d @recommendation_request.json
```

### Con Python

```python
import requests

# Recomendaciones
url = "http://localhost:5000/api/v1/recommendations"
payload = {
    "location": {"latitude": -33.5731, "longitude": -70.6673},
    "endpoint": {"latitude": -33.5740, "longitude": -70.6680},
    "water_composition": {
        "density": 1000,
        "temperature": 20,
        "ph": 7.0,
        "salinity": 200,
        "hardness": 150
    },
    "pipe_length": 500,
    "pipe_diameter": 0.016,
    "flow_rate": 0.0001
}

response = requests.post(url, json=payload)
recommendations = response.json()
print(recommendations)
```

### Con JavaScript/Fetch

```javascript
const url = "http://localhost:5000/api/v1/recommendations";
const payload = {
  location: { latitude: -33.5731, longitude: -70.6673 },
  endpoint: { latitude: -33.5740, longitude: -70.6680 },
  water_composition: {
    density: 1000,
    temperature: 20,
    ph: 7.0,
    salinity: 200,
    hardness: 150
  },
  pipe_length: 500,
  pipe_diameter: 0.016,
  flow_rate: 0.0001
};

fetch(url, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(payload)
})
  .then(response => response.json())
  .then(data => console.log(data));
```

## Limitaciones Actuales

- El análisis hidráulico es simplificado (ecuaciones preliminares)
- No incluye simulaciones avanzadas de uniformidad
- Limitado a un solo sector de riego
- Datos de goteros genéricos (no específicos por marca)
- Dependencia de Google Elevation API para datos altimétricos

## Futuras Mejoras

- [ ] Integración con base de datos de características de goteros por marca
- [ ] Análisis de múltiples sectores de riego
- [ ] Simulaciones avanzadas de uniformidad
- [ ] Procesamiento de imágenes GeoTIFF
- [ ] Autenticación y autorización de usuarios
- [ ] Sistema de almacenamiento de proyectos
- [ ] Dashboard web de visualización
- [ ] Integración con QGIS
- [ ] Exportación de reportes en PDF
- [ ] API de cálculo DEM completo

## Autores

Luis González  
Seminario 2026  
Departamento de Ingeniería Informática  
Universidad de Santiago de Chile

## Licencia

Proyecto de tesis académica - Derechos reservados

## Referencias

- Hazen, A., & Williams, G. S. (1905). Hydraulic tables.
- Solomon, K. H. (1985). Global uniformity of trickle irrigation systems.
- Chen et al. (2022). An estimation of the discharge exponent of a drip irrigation emitter.
- FAO. (2007). Technical Handbook on Pressurized Irrigation Techniques.

## Soporte

Para reportar issues o solicitar features:
- Crear un issue en el repositorio
- Contactar al autor: luis.gonzalez@usach.cl
