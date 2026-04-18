# 🎨 Frontend - Dashboard de la API de Riego

Interfaz web moderna y responsiva para interactuar con la API del Sistema de Recomendación de Riego.

## 📁 Estructura

```
frontend/
├── index.html      # Página principal
├── style.css       # Estilos (CSS3, gradientes, animaciones)
├── script.js       # Lógica (JavaScript vanilla)
└── README.md       # Este archivo
```

## 🌐 Acceso

Una vez que el servidor esté corriendo, accede a:

```
http://localhost:5000/
```

O directamente al dashboard:

```
http://localhost:5000/dashboard
```

## ✨ Características

### 🏠 Health Check
- Verifica automáticamente el estado de la API
- Muestra información en tiempo real:
  - Estado del servidor
  - Versión de la API
  - URL del servidor
  - Última verificación

### 🔄 Auto-Refresh
- Verifica el estado automáticamente cada 30 segundos
- Actualización manual con botón

### 📚 Documentación Integrada
- Acceso rápido a documentación de endpoints
- Abre en ventana emergente
- Lista todos los endpoints disponibles

### 📊 Estadísticas
- Muestra capacidades del sistema:
  - Análisis geoespacial e hidráulico
  - Motor de recomendaciones inteligente
  - Procesamiento rápido

### 🎨 Diseño Responsivo
- Funciona perfectamente en:
  - Desktop
  - Tablet
  - Dispositivos móviles
- Tema oscuro profesional
- Animaciones suaves

## 🎯 Componentes Principales

### Health Check Card
Panel principal que muestra el estado de la API:
- Círculo de estado animado
- Información detallada cuando está activo
- Mensaje de error cuando hay problemas
- Botones de acción

### Stats Grid
4 tarjetas que muestran las capacidades:
1. **Análisis** - Geoespacial e Hidráulico
2. **Recomendaciones** - Basadas en parámetros reales
3. **Inteligente** - Motor de decisión automático
4. **Rápido** - Resultados en segundos

### Endpoints Preview
Lista de todos los endpoints disponibles:
- Método HTTP (GET/POST)
- Ruta del endpoint
- Descripción breve

## 🔧 Tecnologías Utilizadas

- **HTML5**: Estructura semántica
- **CSS3**: 
  - Gradientes lineales y radiales
  - Animaciones personalizadas
  - Flexbox y Grid
  - Media queries responsivas
- **JavaScript ES6+**:
  - Fetch API para llamadas HTTP
  - Async/await
  - Manipulación del DOM
  - Event listeners

## 🎨 Paleta de Colores

| Color | Código | Uso |
|-------|--------|-----|
| Verde Primario | `#2ecc71` | Éxito, activo |
| Azul Secundario | `#3498db` | Información, secundario |
| Rojo Peligro | `#e74c3c` | Errores |
| Naranja Alerta | `#f39c12` | Advertencias |
| Fondo Oscuro | `#1a1a2e` | Fondo principal |
| Fondo Claro | `#0f3460` | Contenedores |
| Texto Primario | `#ecf0f1` | Texto principal |

## 📱 Diseño Responsivo

### Desktop (>768px)
- Layout completo
- 4 columnas en stats grid
- Botones lado a lado

### Tablet (480px - 768px)
- Layout optimizado
- 2 columnas en stats grid
- Botones adaptados

### Móvil (<480px)
- Layout vertical
- 1 columna en stats grid
- Botones a pantalla completa

## 🚀 Funcionalidades de JavaScript

### `checkHealth()`
Verifica el estado de la API y actualiza la interfaz.

```javascript
async function checkHealth() {
    // Llamada a GET /api/v1/health
    // Actualiza estado visual
    // Muestra información
}
```

### `displaySuccess(data)`
Muestra los datos exitosos en la interfaz.

### `displayError(error)`
Muestra mensajes de error cuando la API no está disponible.

### `openApiDocs()`
Abre la documentación en una ventana emergente.

### `formatTime(date)`
Formatea la hora actual (HH:MM:SS).

## 🎬 Animaciones

### Entrante
- **slideDown**: Título con movimiento suave hacia abajo
- **slideUp**: Subtítulo con movimiento hacia arriba
- **slideInUp**: Cards con entrada desde abajo
- **fadeIn**: Contenido con desvanecimiento suave

### Interactivas
- **pulse**: Badge de estado pulsante
- **spin**: Spinner de carga giratorio
- **hover**: Efectos al pasar mouse

## 🐛 Debugging

### Consola del Navegador
El script registra mensajes útiles:

```javascript
console.log('🌾 Dashboard de Riego cargado');
console.log('✓ API Health Check Exitoso');
console.error('✕ API Health Check Falló');
```

Abre la consola con `F12` en el navegador.

## 🔐 CORS

El dashboard hace llamadas CORS a la API. Asegúrate de que CORS está habilitado en Flask (ya lo está en la configuración).

## 📋 Estructura del JSON de Respuesta

```json
{
    "success": true,
    "message": "API is running",
    "data": {
        "version": "1.0.0"
    },
    "errors": null,
    "timestamp": "2026-04-18T00:15:27.355690"
}
```

## 🔗 URLs Disponibles

| Ruta | Descripción |
|------|-------------|
| `/` | Página principal (dashboard) |
| `/dashboard` | Dashboard explícito |
| `/frontend/style.css` | Archivo CSS |
| `/frontend/script.js` | Archivo JavaScript |
| `/api/v1/health` | API health check |
| `/api/v1/docs` | Documentación de API |

## 🎓 Ejemplos de Uso

### Verificar Estado
1. Abre `http://localhost:5000/`
2. El dashboard verifica automáticamente
3. Verás un círculo verde si está activo
4. Puedes hacer clic en "Verificar Estado" para actualizar

### Ver Documentación
1. Haz clic en "Ver Documentación"
2. Se abrirá una ventana con todos los endpoints
3. Lista el método HTTP y descripción

## 🔮 Futuras Mejoras

- [ ] Formularios interactivos para cada endpoint
- [ ] Visualización de respuestas en tiempo real
- [ ] Gráficos de datos (Chart.js)
- [ ] Historial de solicitudes
- [ ] Tema claro/oscuro togglable
- [ ] Exportación de datos
- [ ] Autenticación de usuarios

## 📝 Notas

- El dashboard se actualiza automáticamente cada 30 segundos
- Usa Fetch API (compatible con navegadores modernos)
- No requiere librerías externas (JavaScript vanilla)
- Diseño responsive sin frameworks CSS

## ✉️ Soporte

Si hay problemas:

1. Verifica que el servidor esté corriendo: `python run.py`
2. Abre la consola del navegador (F12)
3. Revisa los mensajes de error
4. Verifica la conectividad a `http://localhost:5000`

---

**Versión**: 1.0.0  
**Última actualización**: 2026-04-18  
**Autor**: Sistema de Recomendación de Riego - USACH 2026
