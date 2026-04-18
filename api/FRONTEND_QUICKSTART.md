# 🚀 INICIO RÁPIDO - Dashboard Frontend

## 1️⃣ **Asegúrate que el servidor esté corriendo**

```bash
cd c:\Users\luisg\Documents\Sistema-de-Recomendacion-tesis\api
python run.py
```

Deberías ver:
```
 * Running on http://0.0.0.0:5000
 * Debug mode: on
```

## 2️⃣ **Abre el Dashboard en tu Navegador**

Abre cualquiera de estas URLs:

- **http://localhost:5000/**
- **http://localhost:5000/dashboard**

## 3️⃣ **¿Qué ves?**

Un dashboard hermoso y moderno con:

✅ **Círculo de Estado** - Verde si la API está funcionando
✅ **Información en Tiempo Real** - Versión, estado, URL
✅ **Auto-verificación** - Se actualiza cada 30 segundos
✅ **Botones de Acción** - Verificar estado y ver docs
✅ **Lista de Endpoints** - Todos los disponibles
✅ **Estadísticas** - 4 tarjetas con capacidades

## 4️⃣ **Características**

### 🔄 Verificar Estado Manualmente
Click en botón azul "🔄 Verificar Estado"

### 📚 Ver Documentación
Click en botón "📚 Ver Documentación" (abre en ventana nueva)

### 📱 Responsivo
- Funciona en desktop, tablet y móvil
- Diseño oscuro profesional
- Animaciones suaves

---

## 📁 Archivos Creados

```
api/
└── frontend/                    ← NUEVO
    ├── index.html              (Página principal)
    ├── style.css              (Estilos modernos)
    ├── script.js              (Lógica JavaScript)
    └── README.md              (Documentación)
```

---

## 🛠️ Rutas Disponibles

| URL | Tipo | Descripción |
|-----|------|------------|
| `/` | GET | Dashboard principal |
| `/dashboard` | GET | Dashboard (alias) |
| `/frontend/style.css` | GET | Hoja de estilos |
| `/frontend/script.js` | GET | JavaScript |
| `/api/v1/health` | GET | API health check |
| `/api/v1/docs` | GET | Documentación JSON |

---

## 🎨 Diseño

✨ **Tema Oscuro Profesional**
- Gradientes azul-verde
- Efectos de sombra y luz
- Animaciones suaves
- Colores coherentes

✅ **Verde** = Éxito / Activo
🔵 **Azul** = Información
🔴 **Rojo** = Error
⚠️ **Naranja** = Alerta

---

## 🔍 Verificar que Todo Funciona

### En PowerShell:
```powershell
# 1. Verifica health check
curl http://localhost:5000/api/v1/health

# 2. Verifica que el dashboard se sirve
curl http://localhost:5000/

# 3. Verifica que el CSS se sirve
curl http://localhost:5000/frontend/style.css
```

### En el Navegador:
1. Abre http://localhost:5000/
2. Deberías ver el dashboard bonito
3. El círculo debería ser verde
4. Debería mostrar "API Funcionando Correctamente"

---

## 🐛 Si algo no funciona

### "No puedo acceder a http://localhost:5000"
- ¿Está corriendo `python run.py`?
- ¿Está el servidor en puerto 5000?
- Intenta con `http://127.0.0.1:5000`

### "La página se ve fea (sin estilos)"
- Verifica que `/frontend/style.css` se carga
- Abre Inspeccionar (F12) → Pestaña Red → busca `style.css`
- Si dice 404, hay problema con rutas

### "El JavaScript no funciona"
- Abre Consola (F12) → Pestaña Consola
- Busca errores rojos
- Verifica que `script.js` se carga

### "El botón 'Verificar Estado' no hace nada"
- Abre Consola (F12)
- Si hay rojo, copiar error
- Verifica que la API realmente está corriendo

---

## 📊 Próximo Paso

Ahora que tienes el dashboard funcionando, puedes:

1. **Agregar más endpoints** al frontend (formularios para análisis)
2. **Integrar gráficos** con Chart.js
3. **Agregar autenticación** de usuarios
4. **Conectar base de datos** para guardar proyectos
5. **Exportar reportes** en PDF

---

## 📸 Vista Previa (Descripción)

```
┌─────────────────────────────────────────┐
│  🌾 Sistema de Recomendación            │
│  Diseño de Redes de Riego Multiparámetros
├─────────────────────────────────────────┤
│                                         │
│     ✓ (círculo verde grande)            │
│  ✓ API Funcionando Correctamente        │
│                                         │
│  Estado:     Activo                     │
│  Versión:    1.0.0                      │
│  URL:        http://localhost:5000     │
│  Último:     12:34:56                   │
│                                         │
│  [🔄 Verificar] [📚 Documentación]      │
│                                         │
├─────────────────────────────────────────┤
│ 📊 Análisis | 💡 Recomendaciones       │
│ 🔧 Inteligente | ⚡ Rápido             │
├─────────────────────────────────────────┤
│ GET  /api/v1/health                    │
│ GET  /api/v1/docs                      │
│ POST /api/v1/analysis/elevation        │
│ POST /api/v1/analysis/hydraulic        │
│ POST /api/v1/recommendations           │
└─────────────────────────────────────────┘
```

---

¡Listo! Tu dashboard está funcionando. 🎉

**URL: http://localhost:5000/**
