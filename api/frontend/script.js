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
 * Cambia entre tabs y sincroniza el menú lateral
 */
function switchTab(tabName) {
    // Ocultar todos los tabs
    const tabs = document.querySelectorAll('.tab-content');
    tabs.forEach(tab => tab.classList.remove('active'));

    // Desactivar todos los botones de tabs
    const buttons = document.querySelectorAll('.tab-btn');
    buttons.forEach(btn => btn.classList.remove('active'));

    // Desactivar todos los items del menú lateral
    const menuLinks = document.querySelectorAll('.menu-link');
    menuLinks.forEach(link => link.classList.remove('active'));

    // Mostrar tab seleccionado
    const selectedTab = document.getElementById(tabName + '-tab');
    if (selectedTab) {
        selectedTab.classList.add('active');
    }

    // Activar botón de tab seleccionado
    const selectedBtn = Array.from(buttons).find(btn => 
        btn.onclick && btn.onclick.toString().includes(`'${tabName}'`)
    );
    if (selectedBtn) {
        selectedBtn.classList.add('active');
    }

    // Activar item del menú lateral seleccionado
    const selectedMenuLink = Array.from(menuLinks).find(link => 
        link.onclick && link.onclick.toString().includes(`'${tabName}'`)
    );
    if (selectedMenuLink) {
        selectedMenuLink.classList.add('active');
    }
}

/**
 * Abre el modal de carga de archivo
 */
function openUploadModal() {
    const modal = document.getElementById('uploadModal');
    if (modal) {
        modal.classList.add('active');
    }
}

/**
 * Cierra el modal de carga de archivo
 */
function closeUploadModal() {
    const modal = document.getElementById('uploadModal');
    if (modal) {
        modal.classList.remove('active');
        // Limpiar campos
        document.getElementById('fileInput').value = '';
        document.getElementById('filePreview').style.display = 'none';
        document.getElementById('submitBtn').style.display = 'none';
    }
}

/**
 * Maneja la selección de archivo
 */
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        const fileInfo = document.getElementById('selectedFileInfo');
        const filePreview = document.getElementById('filePreview');
        const submitBtn = document.getElementById('submitBtn');

        // Mostrar información del archivo
        fileInfo.innerHTML = `
            <strong>📄 ${file.name}</strong><br>
            <span style="font-size: 0.85em;">Tamaño: ${(file.size / 1024 / 1024).toFixed(2)} MB</span><br>
            <span style="font-size: 0.85em;">Tipo: ${file.type}</span>
        `;

        filePreview.style.display = 'block';
        submitBtn.style.display = 'flex';
    }
}

/**
 * Inicia el análisis con el archivo seleccionado
 */
async function submitAnalysis() {
    const file = document.getElementById('fileInput').files[0];
    if (!file) {
        alert('Por favor selecciona un archivo');
        return;
    }

    try {
        // Crear FormData con el archivo
        const formData = new FormData();
        formData.append('file', file);
        
        // Mostrar estado de carga
        const submitBtn = document.getElementById('submitBtn');
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = '⏳ Enviando...';

        // Enviar archivo al servidor
        const response = await fetch(`${API_URL}/api/v1/analyze/image`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            console.log('✓ Análisis completado:', data);
            
            // Cerrar modal
            closeUploadModal();

            // Guardar los resultados en memoria para mostrar en Terreno
            window.analysisResults = data.data;

            // Navegar a la tab de Terreno
            switchTab('terreno');

            // Mostrar resultado exitoso
            displayAnalysisResults(data.data);
            
            // Restablecer botón
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        } else {
            throw new Error(data.message || 'Error al procesar el archivo');
        }
        
    } catch (error) {
        console.error('Error al enviar archivo:', error);
        
        const submitBtn = document.getElementById('submitBtn');
        submitBtn.disabled = false;
        submitBtn.textContent = '✓ Iniciar Análisis';
        
        alert(`Error al enviar el archivo:\n${error.message}`);
    }
}

/**
 * Muestra los resultados del análisis en todos los tabs correspondientes
 */
function displayAnalysisResults(analysisData) {
    try {
        // ==================== TERRENO ====================
        const terranoParams = analysisData.terrain_analysis;
        const terranoItems = document.querySelectorAll('#terreno-tab .param-item');
        
        if (terranoItems.length >= 4) {
            terranoItems[0].querySelector('.param-value').textContent = 
                terranoParams.slope_percentage + '%';
            
            terranoItems[1].querySelector('.param-value').textContent = 
                terranoParams.max_elevation + ' m';
            
            terranoItems[2].querySelector('.param-value').textContent = 
                terranoParams.min_elevation + ' m';
            
            terranoItems[3].querySelector('.param-value').textContent = 
                terranoParams.critical_zones_percentage + '%';
        }
        
        // ==================== HIDRÁULICA ====================
        const hidParams = analysisData.hydraulic_analysis;
        const hidItems = document.querySelectorAll('#hidraulica-tab .param-item');
        
        if (hidItems.length >= 4) {
            hidItems[0].querySelector('.param-value').textContent = 
                hidParams.source_pressure.toFixed(2) + ' kPa';
            
            hidItems[1].querySelector('.param-value').textContent = 
                hidParams.available_flow.toFixed(2) + ' L/min';
            
            hidItems[2].querySelector('.param-value').textContent = 
                hidParams.pressure_loss.toFixed(2) + ' kPa';
            
            hidItems[3].querySelector('.param-value').textContent = 
                hidParams.hydraulic_risk;
        }
        
        // ==================== AGUA Y MATERIALES ====================
        const waterParams = analysisData.water_analysis;
        const waterItems = document.querySelectorAll('#agua-tab .param-item');
        
        if (waterItems.length >= 4) {
            waterItems[0].querySelector('.param-value').textContent = 
                waterParams.ph.toFixed(2);
            
            waterItems[1].querySelector('.param-value').textContent = 
                waterParams.salinity_ppm.toFixed(0) + ' PPM';
            
            waterItems[2].querySelector('.param-value').textContent = 
                waterParams.hardness_mg_l.toFixed(0) + ' mg/L';
            
            waterItems[3].querySelector('.param-value').textContent = 
                waterParams.water_quality;
        }
        
        // Mostrar material recomendado
        const waterContent = document.getElementById('agua-tab')?.querySelector('.card-body');
        if (waterContent) {
            const materialDiv = document.createElement('div');
            materialDiv.style.marginTop = '20px';
            materialDiv.innerHTML = `
                <div style="background: rgba(0, 217, 255, 0.1); border: 1px solid rgba(0, 217, 255, 0.3); border-radius: 8px; padding: 15px;">
                    <h3 style="color: #00d9ff; margin: 0 0 10px 0; font-size: 1em;">Recomendación de Material</h3>
                    <p style="color: var(--text-secondary); margin: 0;"><strong>${waterParams.recommended_material}</strong></p>
                    <p style="color: var(--text-secondary); margin: 5px 0; font-size: 0.9em;">Compatibilidad: HDPE (${waterParams.material_compatibility.hdpe}) | PVC (${waterParams.material_compatibility.pvc})</p>
                </div>
            `;
            waterContent.appendChild(materialDiv);
        }
        
        // ==================== DISEÑO ====================
        const design = analysisData.design_recommendations;
        const disenoContent = document.getElementById('diseno-tab')?.querySelector('.card-body');
        
        if (disenoContent) {
            disenoContent.innerHTML = `
                <div style="margin-bottom: 20px;">
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px;">
                        <div style="background: rgba(0, 217, 255, 0.1); border: 1px solid rgba(0, 217, 255, 0.2); border-radius: 8px; padding: 15px;">
                            <p style="color: var(--text-secondary); margin: 0 0 5px 0; font-size: 0.85em;">Área Estimada</p>
                            <p style="color: #00d9ff; margin: 0; font-size: 1.3em; font-weight: bold;">${design.estimated_area} ha</p>
                        </div>
                        <div style="background: rgba(0, 217, 255, 0.1); border: 1px solid rgba(0, 217, 255, 0.2); border-radius: 8px; padding: 15px;">
                            <p style="color: var(--text-secondary); margin: 0 0 5px 0; font-size: 0.85em;">Manguera Estimada</p>
                            <p style="color: #00d9ff; margin: 0; font-size: 1.3em; font-weight: bold;">${design.estimated_drip_length.toLocaleString()} m</p>
                        </div>
                        <div style="background: rgba(0, 217, 255, 0.1); border: 1px solid rgba(0, 217, 255, 0.2); border-radius: 8px; padding: 15px;">
                            <p style="color: var(--text-secondary); margin: 0 0 5px 0; font-size: 0.85em;">Complejidad</p>
                            <p style="color: #00d9ff; margin: 0; font-size: 1.3em; font-weight: bold;">${design.complexity_level}</p>
                        </div>
                        <div style="background: rgba(0, 217, 255, 0.1); border: 1px solid rgba(0, 217, 255, 0.2); border-radius: 8px; padding: 15px;">
                            <p style="color: var(--text-secondary); margin: 0 0 5px 0; font-size: 0.85em;">Costo Estimado</p>
                            <p style="color: #00d9ff; margin: 0; font-size: 1.3em; font-weight: bold;">${design.estimated_cost_level}</p>
                        </div>
                    </div>
                    
                    <h3 style="color: #00d9ff; margin: 20px 0 15px 0;">📋 Recomendaciones</h3>
                    <div style="display: flex; flex-direction: column; gap: 10px;">
                        ${design.recommendations.map((rec, idx) => `
                            <div style="background: rgba(0, 217, 255, 0.05); border-left: 4px solid #00d9ff; padding: 12px; border-radius: 4px;">
                                <div style="display: flex; justify-content: space-between; align-items: start; gap: 10px;">
                                    <div>
                                        <p style="color: var(--text-secondary); margin: 0; font-size: 0.85em; font-weight: 600; text-transform: uppercase;">${rec.type}</p>
                                        <p style="color: var(--text-primary); margin: 5px 0 0 0;">${rec.message}</p>
                                        <p style="color: #00d9ff; margin: 5px 0 0 0; font-size: 0.9em;"><strong>Acción:</strong> ${rec.action}</p>
                                    </div>
                                    <span style="background: ${rec.priority === 'Alto' ? '#ff4757' : rec.priority === 'Medio' ? '#ffa502' : '#2ecc71'}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.75em; font-weight: bold; white-space: nowrap;">${rec.priority}</span>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        
        // ==================== MENSAJE DE ÉXITO ====================
        const terranoTab = document.getElementById('terreno-tab');
        const existingResult = terranoTab?.querySelector('[data-upload-result]');
        
        if (!existingResult) {
            const successDiv = document.createElement('div');
            successDiv.setAttribute('data-upload-result', '');
            successDiv.style.marginBottom = '20px';
            successDiv.innerHTML = `
                <div style="background: rgba(46, 204, 113, 0.1); border: 1px solid #2ecc71; border-radius: 8px; padding: 20px;">
                    <h3 style="color: #2ecc71; margin: 0 0 10px 0;">✓ Análisis completado</h3>
                    <p style="color: var(--text-secondary); margin: 0;"><strong>Archivo:</strong> ${analysisData.file_name}</p>
                    <p style="color: var(--text-secondary); margin: 5px 0;"><strong>Tamaño:</strong> ${(analysisData.file_size / 1024 / 1024).toFixed(2)} MB</p>
                    <p style="color: var(--text-secondary); margin: 5px 0;"><strong>Dimensiones:</strong> ${analysisData.image_dimensions.width}x${analysisData.image_dimensions.height} px</p>
                </div>
            `;
            
            const cardBody = terranoTab?.querySelector('.card-body');
            if (cardBody) {
                cardBody.insertBefore(successDiv, cardBody.firstChild);
            }
        }
        
    } catch (error) {
        console.error('Error mostrando resultados:', error);
    }
}

/**
 * Crea un elemento para mostrar resultados
 */
function createResultElement() {
    const terranoTab = document.getElementById('terreno-tab');
    const resultDiv = document.createElement('div');
    resultDiv.setAttribute('data-upload-result', '');
    if (terranoTab) {
        terranoTab.insertBefore(resultDiv, terranoTab.firstChild);
    }
    return resultDiv;
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
