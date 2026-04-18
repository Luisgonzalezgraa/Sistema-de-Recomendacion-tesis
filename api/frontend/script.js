/**
 * Script para consumir el endpoint /api/v1/health
 */

// Configuración
const API_URL = 'http://localhost:5000';
const HEALTH_ENDPOINT = '/api/v1/health';
const DOCS_ENDPOINT = '/api/v1/docs';

/**
 * Verifica el estado de la API
 */
async function checkHealth() {
    try {
        // Mostrar estado de carga
        setLoadingState(true);

        // Hacer la llamada a la API
        const response = await fetch(`${API_URL}${HEALTH_ENDPOINT}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        // Parsear respuesta
        const data = await response.json();

        // Mostrar datos exitosos
        displaySuccess(data);
        setLoadingState(false);

    } catch (error) {
        console.error('Error al verificar salud de la API:', error);
        displayError(error);
        setLoadingState(false);
    }
}

/**
 * Muestra los datos exitosos
 */
function displaySuccess(data) {
    const statusCircle = document.getElementById('statusCircle');
    const statusText = document.getElementById('statusText');
    const statusBadge = document.getElementById('statusBadge');
    const apiInfo = document.getElementById('apiInfo');

    // Actualizar círculo de estado
    statusCircle.classList.remove('loading');
    statusCircle.classList.add('success');

    // Actualizar texto
    statusText.textContent = '✓ API Funcionando Correctamente';
    statusBadge.textContent = 'En Línea';
    statusBadge.classList.remove('loading');
    statusBadge.classList.add('success');

    // Mostrar información
    apiInfo.style.display = 'block';
    document.getElementById('infoStatus').textContent = data.success ? 'Activo' : 'Inactivo';
    document.getElementById('infoVersion').textContent = data.data?.version || 'Desconocida';
    document.getElementById('infoUrl').textContent = API_URL;
    document.getElementById('infoTime').textContent = formatTime(new Date());

    // Ocultar mensaje de error
    document.getElementById('errorMessage').style.display = 'none';

    // Log
    console.log('✓ API Health Check Exitoso:', data);
}

/**
 * Muestra el mensaje de error
 */
function displayError(error) {
    const statusCircle = document.getElementById('statusCircle');
    const statusText = document.getElementById('statusText');
    const statusBadge = document.getElementById('statusBadge');
    const errorMessage = document.getElementById('errorMessage');
    const errorText = document.getElementById('errorText');

    // Actualizar círculo de estado
    statusCircle.classList.remove('success');
    statusCircle.classList.add('error');

    // Actualizar texto
    statusText.textContent = '✕ Error al conectar con la API';
    statusBadge.textContent = 'Desconectado';
    statusBadge.classList.remove('success');
    statusBadge.classList.add('error');

    // Mostrar error
    errorMessage.style.display = 'block';
    errorText.textContent = `⚠️ ${error.message}`;

    // Ocultar información
    document.getElementById('apiInfo').style.display = 'none';

    // Log
    console.error('✕ API Health Check Falló:', error);
}

/**
 * Actualiza el estado de carga
 */
function setLoadingState(isLoading) {
    const statusCircle = document.getElementById('statusCircle');

    if (isLoading) {
        statusCircle.classList.add('loading');
    } else {
        statusCircle.classList.remove('loading');
    }
}

/**
 * Abre la documentación de la API
 */
async function openApiDocs() {
    try {
        const response = await fetch(`${API_URL}${DOCS_ENDPOINT}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error('No se pudo obtener la documentación');
        }

        const docs = await response.json();

        // Abrir en una nueva ventana con los datos formateados
        const docWindow = window.open('', '_blank', 'width=1000,height=800');
        if (docWindow) {
            docWindow.document.write(`
                <!DOCTYPE html>
                <html lang="es">
                <head>
                    <meta charset="UTF-8">
                    <title>Documentación de la API</title>
                    <style>
                        * { margin: 0; padding: 0; box-sizing: border-box; }
                        body {
                            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                            background: linear-gradient(135deg, #1a1a2e 0%, #0f3460 100%);
                            color: #ecf0f1;
                            padding: 30px;
                            line-height: 1.6;
                        }
                        .container { max-width: 900px; margin: 0 auto; }
                        h1 { 
                            font-size: 2.5em;
                            margin-bottom: 10px;
                            background: linear-gradient(135deg, #2ecc71, #3498db);
                            -webkit-background-clip: text;
                            -webkit-text-fill-color: transparent;
                        }
                        .subtitle { color: #bdc3c7; margin-bottom: 30px; }
                        .endpoint { 
                            background: #16213e;
                            border-left: 4px solid #2ecc71;
                            padding: 20px;
                            margin: 20px 0;
                            border-radius: 8px;
                        }
                        .endpoint-method {
                            display: inline-block;
                            padding: 4px 8px;
                            border-radius: 4px;
                            font-weight: bold;
                            margin-right: 10px;
                        }
                        .method-get { background: rgba(52, 152, 219, 0.2); color: #3498db; }
                        .method-post { background: rgba(46, 204, 113, 0.2); color: #2ecc71; }
                        .endpoint-path { 
                            font-family: 'Courier New', monospace;
                            color: #ecf0f1;
                            font-weight: bold;
                        }
                        .endpoint-desc { color: #bdc3c7; margin-top: 8px; }
                        pre {
                            background: #0f3460;
                            padding: 15px;
                            border-radius: 8px;
                            overflow-x: auto;
                            margin-top: 10px;
                        }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>${docs.title}</h1>
                        <p class="subtitle">Versión ${docs.version}</p>
                        <h2 style="margin: 30px 0 20px; font-size: 1.5em;">Endpoints Disponibles</h2>
            `);

            // Agregar endpoints
            if (docs.endpoints) {
                Object.entries(docs.endpoints).forEach(([key, endpoint]) => {
                    const method = endpoint.url.includes('health') || endpoint.url.includes('docs') ? 'GET' : 'POST';
                    const methodClass = method === 'GET' ? 'method-get' : 'method-post';
                    docWindow.document.write(`
                        <div class="endpoint">
                            <span class="endpoint-method ${methodClass}">${method}</span>
                            <span class="endpoint-path">${endpoint.url}</span>
                            <div class="endpoint-desc">${endpoint.description}</div>
                        </div>
                    `);
                });
            }

            docWindow.document.write(`
                        <p style="margin-top: 40px; text-align: center; color: #7f8c8d; font-size: 0.9em;">
                            Documentación generada automáticamente desde la API
                        </p>
                    </div>
                </body>
                </html>
            `);
            docWindow.document.close();
        }

    } catch (error) {
        alert('Error al obtener documentación: ' + error.message);
        console.error('Error:', error);
    }
}

/**
 * Formatea la hora actual
 */
function formatTime(date) {
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
    return `${hours}:${minutes}:${seconds}`;
}

/**
 * Manejo de errores CORS (si ocurre)
 */
window.addEventListener('unhandledrejection', event => {
    if (event.reason.message && event.reason.message.includes('CORS')) {
        console.warn('CORS issue detected. Ensure API server has CORS enabled.');
    }
});

// Log de inicialización
console.log('🌾 Dashboard de Riego cargado');
console.log(`📡 API URL: ${API_URL}`);
console.log('✓ Listo para verificar estado de la API');
