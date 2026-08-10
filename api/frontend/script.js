const API_URL = "http://localhost:5000";
const HEALTH_ENDPOINT = "/api/v1/health";
const DOCS_ENDPOINT = "/api/v1/docs";

const DEFAULT_HYDRAULIC_ASSUMPTIONS = {
    flow_per_hectare_l_min: 35,
    emitter_operating_pressure_kpa: 100,
    pressure_safety_factor: 1.2,
    pump_efficiency: 0.6,
    max_sector_area_ha: 3,
    minimum_flow_l_min: 20,
    hazen_williams_c: 150,
    pipe_diameter_large_m: 0.04,
    pipe_diameter_small_m: 0.032,
    minimum_pipe_length_m: 80,
    pipe_length_factor: 1.25
};

let hydraulicAssumptions = { ...DEFAULT_HYDRAULIC_ASSUMPTIONS };
let activeMetricInfo = null;
let currentPumpEvaluation = null;
let currentMaterials = null;
const PERCENT_ASSUMPTIONS = new Set(["pressure_safety_factor", "pipe_length_factor"]);

const MATERIAL_POPUPS = {
    main_pipe: {
        title: "Tuberia principal",
        imageUrl: "https://images.prom.ua/4676789559_w640_h640_truba-dlya-poliva.jpg",
        imageAlt: "Tuberia HDPE 32 mm real para riego",
        sourceUrl: "https://prom.ua/p2045721726-truba-dlya-poliva.html",
        copy: "Alternativas para conducir el caudal desde la fuente o motobomba hasta el sector de riego.",
        options: [
            { name: "HDPE para matriz principal", spec: "Recomendado para enterrado o trazados largos; flexible y resistente.", use: "Usar con la clase de presion calculada y diametro del sector." },
            { name: "PVC hidraulico presion", spec: "Alternativa rigida para tramos rectos y cabezales protegidos del sol.", use: "Cuidar proteccion UV y uniones correctamente cementadas." },
            { name: "PE agricola reforzado", spec: "Opcion flexible para conduccion secundaria de bajo a medio requerimiento.", use: "Validar presion nominal antes de comprar." }
        ]
    },
    laterals: {
        title: "Laterales de goteo",
        imageUrl: "https://cdn.salla.sa/NzYZr/c525c3e9-0b3e-4da3-bd3b-8fea8f06a203-1000x1000-EbXyeIqUoixgrxUVRXLDwbv0ftFhS3kUvorWvTcW.png",
        imageAlt: "Rollo real de tuberia lateral de riego 16 mm",
        sourceUrl: "https://mygarden.com.sa/ar/AzDwnpZ",
        copy: "Lineas que distribuyen el agua dentro del cultivo y contienen o alimentan los goteros.",
        options: [
            { name: "Tuberia PE 16 mm para goteo", spec: "Lateral reutilizable para goteros insertados o autocompensados.", use: "Buena opcion cuando se necesita mantenimiento y cambio de emisores." },
            { name: "Cinta de riego 16 mm", spec: "Solucion economica para cultivos en hileras y temporadas definidas.", use: "Elegir espesor y espaciamiento segun cultivo." },
            { name: "Manguera con gotero integrado", spec: "Lateral con emisores ya incorporados a distancia fija.", use: "Reduce errores de instalacion en marcos regulares." }
        ]
    },
    valves: {
        title: "Llaves de paso",
        imageUrl: "https://www.keyhole.com.tw/wp-content/uploads/2020/01/KHP-PBV06-2-inch-plastic-ball-valve-socket-connection-sch80_02.jpg",
        imageAlt: "Valvula bola PVC real para riego",
        sourceUrl: "https://storage.googleapis.com/dzxtzwuaybacve/irrigation-system-ball-valve.html",
        copy: "Elementos de corte para aislar sectores, limpiar lineas y operar el sistema con seguridad.",
        options: [
            { name: "Valvula bola PVC/HDPE", spec: "Corte manual rapido para matriz o sector.", use: "Debe coincidir con el diametro calculado de la tuberia principal." },
            { name: "Valvula de compuerta", spec: "Permite apertura gradual, util en cabezales o tramos de mayor diametro.", use: "Requiere mas espacio y mantenimiento que una bola." },
            { name: "Valvula sectorial", spec: "Corte por zona de riego para manejar turnos.", use: "Instalar una por sector o subunidad de riego." }
        ]
    },
    emitters: {
        title: "Goteros y conectores",
        imageUrl: "https://cfrouting.zoeysite.com/cdn-cgi/image/format%3Dauto%2Cquality%3D85%2Cfit%3Dscale-down/https%3A//s3.amazonaws.com/zcom-media/sites/a0i0L00000Scsq8QAB/media/catalog/product/d/0/d014-072519-1.jpg",
        imageAlt: "Gotero real para riego por goteo",
        sourceUrl: "https://www.dripirrigation.com/d014",
        copy: "Emisores y accesorios que entregan el agua al cultivo y conectan laterales, derivaciones y terminales.",
        options: [
            { name: "Gotero 2 L/h", spec: "Caudal referencial usado en el listado preliminar.", use: "Adecuado para riego localizado de baja descarga." },
            { name: "Gotero autocompensado", spec: "Mantiene caudal mas estable ante variaciones de presion.", use: "Conveniente en terrenos con pendiente o lineas largas." },
            { name: "Conectores, tees y terminales", spec: "Piezas para derivar, unir y cerrar laterales.", use: "Comprar segun numero de hileras y trazado final." }
        ]
    }
};

const modules = {
    inicio: "Inicio",
    terreno: "Terreno",
    hidraulica: "Hidraulica",
    materiales: "Materiales",
    diseno: "Recomendacion",
    resultados: "Reporte",
    api: "Sistema"
};

function $(id) {
    return document.getElementById(id);
}

function setText(id, value) {
    const element = $(id);
    if (element) {
        element.textContent = value;
    }
}

function formatNumber(value, decimals = 2) {
    if (value === null || value === undefined || value === "") {
        return "--";
    }
    const number = Number(value);
    if (!Number.isFinite(number)) {
        return "--";
    }
    return number.toLocaleString("es-CL", {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

function formatBytes(bytes) {
    const value = Number(bytes);
    if (!Number.isFinite(value)) {
        return "--";
    }
    if (value < 1024 * 1024) {
        return `${formatNumber(value / 1024, 1)} KB`;
    }
    return `${formatNumber(value / 1024 / 1024, 2)} MB`;
}

function formatUnit(value, unit, decimals = 2) {
    const formatted = formatNumber(value, decimals);
    return formatted === "--" ? "--" : `${formatted}${unit}`;
}

function factorToPercent(value) {
    const number = Number(value);
    if (!Number.isFinite(number)) {
        return "";
    }
    return Number(((number - 1) * 100).toFixed(2));
}

function percentToFactor(value) {
    const number = Number(value);
    if (!Number.isFinite(number)) {
        return null;
    }
    return 1 + (number / 100);
}

function formatFactorAsPercent(value, decimals = 0) {
    const percent = factorToPercent(value);
    return percent === "" ? "--" : formatUnit(percent, "%", decimals);
}

function clampPercent(value, max) {
    const number = Number(value);
    const limit = Number(max);
    if (!Number.isFinite(number) || !Number.isFinite(limit) || limit <= 0) {
        return 0;
    }
    return Math.max(0, Math.min(100, (number / limit) * 100));
}

function formatTime(date) {
    return date.toLocaleTimeString("es-CL", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit"
    });
}

async function checkHealth() {
    setText("statusBadge", "Verificando");
    setText("systemStatus", "Conectando");

    try {
        const response = await fetch(`${API_URL}${HEALTH_ENDPOINT}`, {
            method: "GET",
            headers: { "Content-Type": "application/json" }
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        displaySuccess(data);
    } catch (error) {
        displayError(error);
    }
}

function displaySuccess(data) {
    const apiState = $("apiState");
    const statusBadge = $("statusBadge");

    if (apiState) {
        apiState.textContent = "Activo";
        apiState.classList.remove("is-offline");
        apiState.classList.add("is-online");
    }

    if (statusBadge) {
        statusBadge.textContent = "En linea";
        statusBadge.classList.remove("error");
        statusBadge.classList.add("success");
    }

    setText("systemStatus", "Activo");
    setText("footerState", "OK");
    setText("infoVersion", data?.data?.version || "1.0");
    setText("infoTime", formatTime(new Date()));
    setText("errorText", "");
}

function displayError(error) {
    const apiState = $("apiState");
    const statusBadge = $("statusBadge");

    if (apiState) {
        apiState.textContent = "Offline";
        apiState.classList.remove("is-online");
        apiState.classList.add("is-offline");
    }

    if (statusBadge) {
        statusBadge.textContent = "Desconectado";
        statusBadge.classList.remove("success");
        statusBadge.classList.add("error");
    }

    setText("systemStatus", "Offline");
    setText("footerState", "Error API");
    setText("infoTime", formatTime(new Date()));
    setText("errorText", error.message);
}

function setLoadingState(isLoading) {
    const submitBtn = $("submitBtn");
    if (submitBtn) {
        submitBtn.disabled = isLoading;
        submitBtn.textContent = isLoading ? "Procesando..." : "Iniciar analisis";
    }
    setText("flowState", isLoading ? "Procesando" : "Listo");
}

async function openApiDocs() {
    const response = await fetch(`${API_URL}${DOCS_ENDPOINT}`);
    return response.json();
}

function switchTab(tabName) {
    document.querySelectorAll(".tab-content").forEach(tab => {
        tab.classList.remove("active");
    });
    document.querySelectorAll(".tab-btn").forEach(button => {
        button.classList.remove("active");
    });
    document.querySelectorAll(".menu-link").forEach(link => {
        link.classList.remove("active");
    });

    const selectedTab = $(`${tabName}-tab`);
    if (selectedTab) {
        selectedTab.classList.add("active");
    }

    document.querySelectorAll(".tab-btn").forEach(button => {
        const handler = button.getAttribute("onclick") || "";
        if (handler.includes(`'${tabName}'`) || handler.includes(`"${tabName}"`)) {
            button.classList.add("active");
        }
    });

    document.querySelectorAll(".menu-link").forEach(link => {
        const handler = link.getAttribute("onclick") || "";
        if (handler.includes(`'${tabName}'`) || handler.includes(`"${tabName}"`)) {
            link.classList.add("active");
        }
    });

    setText("footerModule", modules[tabName] || tabName);
}

function openUploadModal() {
    const modal = $("uploadModal");
    if (modal) {
        modal.classList.add("active");
        modal.setAttribute("aria-hidden", "false");
    }
}

function closeUploadModal() {
    const modal = $("uploadModal");
    if (modal) {
        modal.classList.remove("active");
        modal.setAttribute("aria-hidden", "true");
    }

    const fileInput = $("fileInput");
    const filePreview = $("filePreview");
    const submitBtn = $("submitBtn");

    if (fileInput) {
        fileInput.value = "";
    }
    if (filePreview) {
        filePreview.style.display = "none";
    }
    if (submitBtn) {
        submitBtn.style.display = "inline-flex";
        submitBtn.disabled = false;
        submitBtn.textContent = "Iniciar analisis";
    }
}

function handleFileSelect(event) {
    const file = event.target.files[0];
    if (!file) {
        return;
    }

    const filePreview = $("filePreview");
    const selectedFileInfo = $("selectedFileInfo");

    if (selectedFileInfo) {
        selectedFileInfo.textContent = `${file.name} | ${formatBytes(file.size)} | ${file.type || "tipo no declarado"}`;
    }
    if (filePreview) {
        filePreview.style.display = "block";
    }
}

async function submitAnalysis(targetTab = "terreno") {
    const file = $("fileInput")?.files[0] || window.selectedAnalysisFile;
    if (!file) {
        alert("Selecciona una imagen antes de iniciar el analisis.");
        return;
    }

    try {
        window.selectedAnalysisFile = file;
        const formData = new FormData();
        formData.append("file", file);
        Object.entries(hydraulicAssumptions).forEach(([key, value]) => {
            formData.append(key, value);
        });
        setLoadingState(true);
        setText("footerProgress", "en proceso");

        const response = await fetch(`${API_URL}/api/v1/analyze/image`, {
            method: "POST",
            body: formData
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.message || "Error al procesar el archivo");
        }

        window.analysisResults = data.data;
        displayAnalysisResults(data.data);
        closeUploadModal();
        switchTab(targetTab);
    } catch (error) {
        alert(`Error al enviar el archivo:\n${error.message}`);
        setText("footerState", "Error analisis");
    } finally {
        setLoadingState(false);
    }
}

const metricInfo = {
    pressure: {
        title: "Presion requerida",
        copy: "Presion minima estimada en la fuente. Se calcula con presion de operacion del gotero, perdida por desnivel, perdida por friccion y margen de seguridad.",
        fields: [
            ["emitter_operating_pressure_kpa", "Presion gotero", "kPa"],
            ["pressure_safety_factor", "Margen seguridad", "%"]
        ]
    },
    flow: {
        title: "Caudal requerido estimado",
        copy: "Demanda preliminar del sector. No es agua medida en la fuente: se estima multiplicando superficie del sector por caudal de diseno por hectarea, con un minimo configurable.",
        fields: [
            ["flow_per_hectare_l_min", "Caudal por hectarea", "L/min/ha"],
            ["minimum_flow_l_min", "Caudal minimo", "L/min"],
            ["max_sector_area_ha", "Sector maximo", "ha"]
        ]
    },
    loss: {
        title: "Perdida de carga",
        copy: "Suma de perdida por desnivel y friccion. La friccion usa Hazen-Williams con longitud critica, diametro y coeficiente C.",
        fields: [
            ["hazen_williams_c", "Coeficiente Hazen-Williams", "C"],
            ["minimum_pipe_length_m", "Longitud minima", "m"],
            ["pipe_length_factor", "Margen recorrido", "%"],
            ["pipe_diameter_large_m", "Diametro sector >= 1 ha", "m"],
            ["pipe_diameter_small_m", "Diametro sector < 1 ha", "m"]
        ]
    },
    pump: {
        title: "Potencia bomba",
        copy: "HP estimados para mover el caudal requerido hasta la altura/presion total del terreno analizado. Se ajusta por rendimiento estimado de la bomba.",
        fields: [
            ["pump_efficiency", "Rendimiento bomba", "0-1"]
        ]
    }
};

function openMetricInfo(metricKey) {
    const config = metricInfo[metricKey];
    const modal = $("metricInfoModal");
    const title = $("metricInfoTitle");
    const copy = $("metricInfoCopy");
    const settings = $("metricSettings");
    if (!config || !modal || !settings) {
        return;
    }

    activeMetricInfo = metricKey;
    if (title) {
        title.textContent = config.title;
    }
    if (copy) {
        copy.textContent = config.copy;
    }
    settings.innerHTML = config.fields.map(([key, label, unit]) => {
        const isPercent = PERCENT_ASSUMPTIONS.has(key);
        const value = isPercent ? factorToPercent(hydraulicAssumptions[key]) : hydraulicAssumptions[key];
        const step = isPercent ? "1" : "0.001";
        return `
        <label class="setting-field">
            <span>${label}</span>
            <div>
                <input type="number" step="${step}" data-assumption="${key}" data-input-kind="${isPercent ? "percent-factor" : "raw"}" value="${value}">
                <small>${unit}</small>
            </div>
        </label>
    `;
    }).join("");

    modal.classList.add("active");
    modal.setAttribute("aria-hidden", "false");
}

function closeMetricInfo() {
    const modal = $("metricInfoModal");
    if (modal) {
        modal.classList.remove("active");
        modal.setAttribute("aria-hidden", "true");
    }
    activeMetricInfo = null;
}

function saveMetricInfo() {
    document.querySelectorAll("[data-assumption]").forEach(input => {
        const key = input.dataset.assumption;
        const value = Number(input.value);
        if (Number.isFinite(value)) {
            hydraulicAssumptions[key] = input.dataset.inputKind === "percent-factor"
                ? percentToFactor(value)
                : value;
        }
    });
    closeMetricInfo();
    if (window.selectedAnalysisFile) {
        submitAnalysis("hidraulica");
    }
}

function resetHydraulicAssumptions() {
    hydraulicAssumptions = { ...DEFAULT_HYDRAULIC_ASSUMPTIONS };
    if (activeMetricInfo) {
        openMetricInfo(activeMetricInfo);
    }
}

function displayAnalysisResults(analysisData) {
    if (!analysisData) {
        return;
    }

    const terrain = analysisData.terrain_analysis || {};
    const hydraulic = analysisData.hydraulic_analysis || {};
    const materials = analysisData.materials_analysis || {};
    const design = analysisData.design_recommendations || {};
    if (hydraulic.assumptions) {
        hydraulicAssumptions = { ...hydraulicAssumptions, ...hydraulic.assumptions };
    }

    const fileName = analysisData.file_name || "--";
    const shortName = fileName.length > 28 ? `${fileName.slice(0, 25)}...` : fileName;
    const area = design.estimated_area;

    setText("currentZone", shortName);
    setText("topArea", Number.isFinite(Number(area)) ? `${formatNumber(area, 2)} ha` : "--");
    setText("metricFile", shortName);
    setText("metricSize", formatBytes(analysisData.file_size));
    setText("metricSlope", formatUnit(terrain.slope_degrees, "°", 2));
    setText("metricRisk", hydraulic.hydraulic_risk || "--");
    setText("metricRecommendation", design.complexity_level || "Generada");

    setText("terrainStatus", "Activo");
    setText("hydraulicStatus", "Activo");
    setText("materialsStatus", "Generado");
    setText("designStatus", "Generada");
    setText("footerProgress", "100%");
    setText("footerState", "OK");
    setText("flowState", "Completado");

    setText("terrainMax", formatUnit(terrain.max_elevation, " m", 2));
    setText("terrainMin", formatUnit(terrain.min_elevation, " m", 2));
    setText("terrainSlope", formatUnit(terrain.slope_degrees, "°", 2));
    setText("terrainCritical", formatUnit(terrain.critical_zones_percentage, "%", 0));
    renderTerrainCharts(terrain);

    setText("hydPressure", formatNumber(hydraulic.source_pressure, 2));
    setText("hydFlow", formatNumber(hydraulic.available_flow, 2));
    setText("hydLoss", formatNumber(hydraulic.pressure_loss, 2));
    setText("hydRisk", hydraulic.hydraulic_risk || "--");
    setText("hydPumpPower", formatUnit(hydraulic.required_pump_power, " HP", 2));

    setText("designArea", formatNumber(design.estimated_area, 2));
    setText("designLength", formatNumber(design.estimated_drip_length, 0));
    setText("designComplexity", design.complexity_level || "--");
    setText("designCost", design.estimated_cost_level || "--");

    renderHydraulicCharts(hydraulic);
    renderPumpCatalog(hydraulic);
    renderMaterials(materials);
    renderRecommendations(design.recommendations || []);
    renderReport(analysisData);
}

function renderTerrainCharts(terrain) {
    renderElevationProfile(terrain.elevation_profile || []);
    renderSlopeDistribution(terrain.slope_distribution || []);
}

function renderElevationProfile(profile) {
    const container = $("elevationProfileState");
    if (!container) {
        return;
    }

    if (!profile.length) {
        container.innerHTML = `
            <strong>Sin perfil disponible</strong>
            <span>El analisis no recibio una serie de elevaciones para graficar.</span>
        `;
        container.className = "chart-empty";
        return;
    }

    const width = 640;
    const height = 250;
    const padding = 26;
    const elevations = profile.map(point => Number(point.elevation_m));
    const distances = profile.map(point => Number(point.distance_m));
    const minElev = Math.min(...elevations);
    const maxElev = Math.max(...elevations);
    const maxDist = Math.max(...distances) || 1;
    const elevSpan = Math.max(maxElev - minElev, 0.01);
    const points = profile.map(point => {
        const x = padding + (Number(point.distance_m) / maxDist) * (width - padding * 2);
        const y = height - padding - ((Number(point.elevation_m) - minElev) / elevSpan) * (height - padding * 2);
        return `${x.toFixed(1)},${y.toFixed(1)}`;
    }).join(" ");
    const areaPoints = `${padding},${height - padding} ${points} ${width - padding},${height - padding}`;

    container.className = "terrain-chart";
    container.innerHTML = `
        <svg class="line-chart" viewBox="0 0 ${width} ${height}" role="img" aria-label="Perfil de elevacion">
            <polygon points="${areaPoints}" class="line-area"></polygon>
            <polyline points="${points}" class="line-path"></polyline>
            <line x1="${padding}" y1="${height - padding}" x2="${width - padding}" y2="${height - padding}" class="axis"></line>
            <line x1="${padding}" y1="${padding}" x2="${padding}" y2="${height - padding}" class="axis"></line>
        </svg>
        <div class="chart-caption">
            <span>${formatUnit(minElev, " m", 2)} min</span>
            <strong>${formatUnit(maxElev - minElev, " m", 2)} desnivel</strong>
            <span>${formatUnit(maxElev, " m", 2)} max</span>
        </div>
    `;
}

function renderSlopeDistribution(distribution) {
    const container = $("slopeDistributionState");
    if (!container) {
        return;
    }

    if (!distribution.length) {
        container.innerHTML = `
            <strong>Sin distribucion disponible</strong>
            <span>El analisis no genero frecuencias por rango.</span>
        `;
        container.className = "chart-empty";
        return;
    }

    const maxPct = Math.max(...distribution.map(item => Number(item.percentage) || 0), 1);
    container.className = "slope-bars";
    container.innerHTML = distribution.map(item => {
        const pct = Number(item.percentage) || 0;
        const height = Math.max(4, (pct / maxPct) * 100);
        const tone = pct >= 25 ? "red" : pct >= 12 ? "orange" : "green";
        return `
            <div class="slope-bar">
                <div class="slope-column">
                    <span class="${tone}" style="--bar-height:${height}%; --bar-width:${height}%"></span>
                </div>
                <strong>${formatNumber(pct, 1)}%</strong>
                <small>${item.range}%</small>
            </div>
        `;
    }).join("");
}

function renderHydraulicCharts(hydraulic) {
    const pressureChart = $("hydPressureChart");
    const sectorChart = $("hydSectorChart");
    if (!pressureChart || !sectorChart) {
        return;
    }

    const rows = [
        { label: "Presion requerida", value: hydraulic.source_pressure, max: 500, unit: " kPa", color: "var(--cyan)" },
        { label: "Antes de margen", value: hydraulic.pressure_before_safety, max: 500, unit: " kPa", color: "var(--green)" },
        { label: "Perdida total", value: hydraulic.pressure_loss, max: 250, unit: " kPa", color: "var(--orange)" },
        { label: "Desnivel", value: hydraulic.elevation_pressure_change, max: 120, unit: " kPa", color: "var(--purple)" },
        { label: "Friccion", value: hydraulic.friction_loss, max: 160, unit: " kPa", color: "var(--red)" },
        { label: "Presion total bomba", value: hydraulic.required_total_pressure, max: 500, unit: " kPa", color: "var(--green)" }
    ];

    pressureChart.innerHTML = rows.map(row => `
        <div class="chart-row">
            <span>${row.label}</span>
            <div class="chart-track">
                <span class="chart-fill" style="--value:${clampPercent(row.value, row.max)}%; --fill:${row.color};"></span>
            </div>
            <strong class="chart-value">${formatUnit(row.value, row.unit, 2)}</strong>
        </div>
    `).join("");

    sectorChart.innerHTML = `
        <div class="gauge-card"><span>Sector</span><strong>${formatUnit(hydraulic.design_sector_area, " ha", 2)}</strong><small>area analizada</small></div>
        <div class="gauge-card"><span>Gotero</span><strong>${formatUnit(hydraulic.emitter_operating_pressure, " kPa", 0)}</strong><small>presion base</small></div>
        <div class="gauge-card"><span>Margen</span><strong>${formatFactorAsPercent(hydraulic.pressure_safety_factor, 0)}</strong><small>seguridad</small></div>
        <div class="gauge-card"><span>Diametro</span><strong>${formatUnit(hydraulic.pipe_diameter, " mm", 0)}</strong><small>tuberia base</small></div>
        <div class="gauge-card"><span>Longitud</span><strong>${formatUnit(hydraulic.pipe_length, " m", 0)}</strong><small>tramo critico</small></div>
        <div class="gauge-card"><span>Presion final</span><strong>${formatUnit(hydraulic.final_pressure, " kPa", 2)}</strong><small>salida estimada</small></div>
        <div class="gauge-card"><span>Caudal requerido</span><strong>${formatUnit(hydraulic.available_flow, " L/min", 2)}</strong><small>${formatUnit(hydraulic.flow_per_hectare, " L/min/ha", 2)}</small></div>
        <div class="gauge-card"><span>Riesgo</span><strong>${hydraulic.hydraulic_risk || "--"}</strong><small>criterio hidraulico</small></div>
        <div class="gauge-card"><span>Altura total</span><strong>${formatUnit(hydraulic.required_total_head, " m", 2)}</strong><small>carga dinamica</small></div>
        <div class="gauge-card"><span>Potencia</span><strong>${formatUnit(hydraulic.required_pump_power, " HP", 2)}</strong><small>eficiencia ${formatUnit(hydraulic.assumptions?.pump_efficiency, "", 2)}</small></div>
        <div class="gauge-card"><span>Motobomba</span><strong>${hydraulic.recommended_pump?.model || "--"}</strong><small>${hydraulic.recommended_pump?.type || "catalogo"}</small></div>
    `;
}

function renderPumpCatalog(hydraulic) {
    const container = $("pumpCatalog");
    const status = $("pumpStatus");
    if (!container) {
        return;
    }

    const catalog = hydraulic.pump_catalog || [];
    const matching = catalog.filter(pump => pump.meets_requirements);
    const recommended = hydraulic.recommended_pump || null;
    const spec = hydraulic.required_pump_spec || {};
    currentPumpEvaluation = { catalog, matching, recommended, spec };

    if (!recommended) {
        container.innerHTML = '<p class="empty-state">Sin motobomba evaluada.</p>';
        if (status) {
            status.textContent = "Pendiente";
        }
        return;
    }

    if (status) {
        status.textContent = matching.length ? "Compatible" : "Sin coincidencia exacta";
    }

    container.innerHTML = `
        <button class="pump-requirement-card ${recommended.meets_requirements ? "suitable" : "limited"}" onclick="openPumpList()">
            <div>
                <span>Requerimiento calculado</span>
                <strong>Bomba de ${formatUnit(spec.minimum_power_hp, " HP", 2)} para ${formatUnit(spec.required_flow_l_min, " L/min", 2)}</strong>
                <small>${formatUnit(spec.required_head_m, " m", 2)} de altura total | ${formatUnit(spec.required_pressure_kpa, " kPa", 2)}</small>
            </div>
            <div>
                <span>${recommended.meets_requirements ? "Modelo compatible sugerido" : "Mejor aproximacion catalogada"}</span>
                <strong>${recommended.model}</strong>
                <small>${recommended.type} | ${formatUnit(recommended.engine_power_hp, " HP", 1)}</small>
            </div>
            <small>${matching.length ? `${matching.length} modelo(s) cumplen. Toca para ver la lista.` : "Ningun modelo del catalogo cumple completamente. Toca para revisar detalles."}</small>
        </button>
    `;
}

function openPumpList() {
    const modal = $("pumpListModal");
    const list = $("pumpList");
    const summary = $("pumpListSummary");
    if (!modal || !list || !currentPumpEvaluation) {
        return;
    }

    const { catalog, matching, spec } = currentPumpEvaluation;
    if (summary) {
        const searchUrl = buildPumpSearchUrl(spec);
        summary.innerHTML = `
            Requerido para el terreno: ${formatUnit(spec.minimum_power_hp, " HP", 2)}, ${formatUnit(spec.required_flow_l_min, " L/min", 2)} y ${formatUnit(spec.required_head_m, " m", 2)} de altura total. ${spec.terrain_context || ""}
            <a class="pump-search-link" href="${searchUrl}" target="_blank" rel="noopener noreferrer">Buscar mas motobombas compatibles en internet</a>
        `;
    }

    const pumpsToShow = matching.length ? matching : catalog;
    list.innerHTML = pumpsToShow.map(pump => `
        <article class="pump-list-card ${pump.meets_requirements ? "suitable" : "limited"}">
            <div>
                <span>${pump.type || "Motobomba"}</span>
                <strong>${pump.model}</strong>
                <small>${pump.engine || "--"} | ${formatUnit(pump.engine_power_hp, " HP", 1)}</small>
            </div>
            <div><span>Caudal max.</span><strong>${formatUnit(pump.max_flow_l_min, " L/min", 0)}</strong><small>margen ${formatUnit(pump.flow_margin_l_min, " L/min", 2)}</small></div>
            <div><span>Altura max.</span><strong>${formatUnit(pump.max_head_m, " m", 1)}</strong><small>margen ${formatUnit(pump.head_margin_m, " m", 2)}</small></div>
            <div><span>Fuente</span><strong>${pump.source || "Catalogo"}</strong><small><a href="${pump.source_url}" target="_blank" rel="noopener noreferrer">ver ficha</a></small></div>
            <p>${pump.selection_note || ""}</p>
        </article>
    `).join("");

    modal.classList.add("active");
    modal.setAttribute("aria-hidden", "false");
}

function buildPumpSearchUrl(spec) {
    const hp = Math.ceil(Number(spec.minimum_power_hp) || 1);
    const flow = Math.ceil(Number(spec.required_flow_l_min) || 1);
    const head = Math.ceil(Number(spec.required_head_m) || 1);
    const query = `motobomba ${hp} HP ${flow} L/min ${head} m altura ficha tecnica`;
    return `https://www.google.com/search?q=${encodeURIComponent(query)}`;
}

function closePumpList() {
    const modal = $("pumpListModal");
    if (modal) {
        modal.classList.remove("active");
        modal.setAttribute("aria-hidden", "true");
    }
}

function renderMaterials(materials) {
    if (!materials || !Object.keys(materials).length) {
        return;
    }
    currentMaterials = materials;

    setText("matMainPipe", `${materials.main_pipe_type || "--"} ${materials.main_pipe_diameter_mm || "--"} mm`);
    setText("matPipeClass", materials.pipe_pressure_class || "clase presion");
    setText("matLateralPipe", `${materials.lateral_pipe_type || "--"} ${materials.lateral_diameter_mm || "--"} mm`);
    setText("matValve", `${materials.valve_type || "--"} ${materials.valve_diameter_mm || "--"} mm`);
    setText("matEmitters", materials.estimated_emitters ? formatNumber(materials.estimated_emitters, 0) : "--");
    setText("materialsMessage", materials.message || "Listado preliminar de materiales.");

    const list = $("materialsList");
    if (list) {
        const items = materials.items || [];
        list.innerHTML = items.length ? items.map(item => `
            <article class="material-item">
                <span>${item.category || "Material"}</span>
                <strong>${item.component || "--"}</strong>
                <small>${item.quantity || "--"}</small>
                <p>${item.purpose || ""}</p>
            </article>
        `).join("") : '<p class="empty-state">Sin materiales calculados.</p>';
    }

    const criteria = $("materialsCriteria");
    if (criteria) {
        criteria.innerHTML = `
            <div class="gauge-card"><span>Filtro</span><strong>${materials.filter_type || "--"}</strong><small>proteccion goteros</small></div>
            <div class="gauge-card"><span>Separacion gotero</span><strong>${formatUnit(materials.emitter_spacing_m, " m", 2)}</strong><small>supuesto base</small></div>
            <div class="gauge-card"><span>Separacion laterales</span><strong>${formatUnit(materials.lateral_spacing_m, " m", 2)}</strong><small>entre lineas</small></div>
            <div class="gauge-card"><span>Longitud laterales</span><strong>${formatUnit(materials.estimated_lateral_length_m, " m", 0)}</strong><small>estimada</small></div>
            <div class="gauge-card"><span>Emisor</span><strong>${materials.emitter_type || "--"}</strong><small>referencial</small></div>
            <div class="gauge-card"><span>Llave</span><strong>${formatUnit(materials.valve_diameter_mm, " mm", 0)}</strong><small>diametro sector</small></div>
        `;
    }
}

function openMaterialPopup(type) {
    const config = MATERIAL_POPUPS[type];
    const modal = $("materialPopupModal");
    const title = $("materialPopupTitle");
    const copy = $("materialPopupCopy");
    const photo = $("materialPopupPhoto");
    const list = $("materialPopupList");
    if (!config || !modal || !list) {
        return;
    }

    const materials = currentMaterials || {};
    const calculated = {
        main_pipe: `${materials.main_pipe_type || "HDPE"} ${materials.main_pipe_diameter_mm || "--"} mm ${materials.pipe_pressure_class || ""}`.trim(),
        laterals: `${materials.lateral_pipe_type || "Lateral de goteo"} ${materials.lateral_diameter_mm || 16} mm`,
        valves: `${materials.valve_type || "Valvula bola"} ${materials.valve_diameter_mm || "--"} mm`,
        emitters: `${materials.emitter_type || "Gotero"} | ${materials.estimated_emitters ? `${formatNumber(materials.estimated_emitters, 0)} unidades aprox.` : "cantidad segun trazado"}`
    };

    if (title) {
        title.textContent = config.title;
    }
    if (copy) {
        copy.textContent = `${config.copy} Seleccion calculada: ${calculated[type] || "--"}.`;
    }
    if (photo) {
        photo.className = "material-photo";
        photo.innerHTML = `
            <img src="${config.imageUrl}" alt="${config.imageAlt}" loading="lazy">
            <a href="${config.sourceUrl}" target="_blank" rel="noopener noreferrer">ver imagen/ficha real</a>
        `;
    }

    list.innerHTML = config.options.map(option => `
        <article class="material-option-card">
            <span>${option.name}</span>
            <strong>${option.spec}</strong>
            <p>${option.use}</p>
        </article>
    `).join("");

    modal.classList.add("active");
    modal.setAttribute("aria-hidden", "false");
}

function closeMaterialPopup() {
    const modal = $("materialPopupModal");
    if (modal) {
        modal.classList.remove("active");
        modal.setAttribute("aria-hidden", "true");
    }
}

function normalizePriority(priority) {
    return String(priority || "info")
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLowerCase()
        .replace(/\s+/g, "-");
}

function renderRecommendations(recommendations) {
    const container = $("recommendationList");
    if (!container) {
        return;
    }

    if (!recommendations.length) {
        container.innerHTML = '<p class="empty-state">No hay recomendaciones disponibles.</p>';
        return;
    }

    container.innerHTML = recommendations.map(rec => {
        const priorityClass = normalizePriority(rec.priority);
        return `
            <div class="recommendation-item">
                <span class="priority ${priorityClass}">${rec.priority || "Info"}</span>
                <div>
                    <strong>${rec.type || "Criterio"}</strong>
                    <p>${rec.message || ""}</p>
                    <small>${rec.action || ""}</small>
                </div>
            </div>
        `;
    }).join("");
}

function renderReport(data) {
    const content = $("reportContent");
    if (!content) {
        return;
    }

    const terrain = data.terrain_analysis || {};
    const hydraulic = data.hydraulic_analysis || {};
    const materials = data.materials_analysis || {};
    const design = data.design_recommendations || {};
    const dimensions = data.image_dimensions || {};
    const downloadBtn = $("reportDownloadBtn");

    if (downloadBtn) {
        downloadBtn.disabled = false;
    }

    content.innerHTML = `
        <div class="report-row"><span>Archivo</span><strong>${data.file_name || "--"}</strong></div>
        <div class="report-row"><span>Dimensiones</span><strong>${dimensions.width || "--"} x ${dimensions.height || "--"} px</strong></div>
        <div class="report-row"><span>Terreno</span><strong>Pendiente ${formatUnit(terrain.slope_degrees, "°", 2)}, desnivel ${formatUnit(terrain.elevation_difference, " m", 2)}</strong></div>
        <div class="report-row"><span>Hidraulica</span><strong>Riesgo ${hydraulic.hydraulic_risk || "--"}, perdida ${formatUnit(hydraulic.pressure_loss, " kPa", 2)}</strong></div>
        <div class="report-row"><span>Motobomba</span><strong>${hydraulic.recommended_pump?.model || "--"}, potencia requerida ${formatUnit(hydraulic.required_pump_power, " HP", 2)}, caudal requerido ${formatUnit(hydraulic.available_flow, " L/min", 2)}</strong></div>
        <div class="report-row"><span>Materiales</span><strong>${materials.main_pipe_type || "--"} ${materials.main_pipe_diameter_mm || "--"} mm, laterales ${materials.lateral_diameter_mm || "--"} mm, llave ${materials.valve_diameter_mm || "--"} mm</strong></div>
        <div class="report-row"><span>Supuestos</span><strong>${formatUnit(hydraulic.flow_per_hectare, " L/min/ha", 2)}, gotero ${formatUnit(hydraulic.emitter_operating_pressure, " kPa", 0)}, margen ${formatFactorAsPercent(hydraulic.pressure_safety_factor, 0)}</strong></div>
        <div class="report-row"><span>Diseno</span><strong>${design.complexity_level || "--"} | costo ${design.estimated_cost_level || "--"}</strong></div>
    `;
}

function escapeHtml(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function reportMetric(label, value) {
    return `
        <div class="pdf-metric">
            <span>${escapeHtml(label)}</span>
            <strong>${escapeHtml(value)}</strong>
        </div>
    `;
}

function downloadReportPdf() {
    const data = window.analysisResults;
    if (!data) {
        alert("Primero genera un analisis para descargar el reporte.");
        return;
    }

    const reportWindow = window.open("", "_blank");
    if (!reportWindow) {
        alert("El navegador bloqueo la ventana del reporte. Permite ventanas emergentes para descargar el PDF.");
        return;
    }

    reportWindow.document.open();
    reportWindow.document.write(buildReportPdfHtml(data));
    reportWindow.document.close();
    reportWindow.focus();

    setTimeout(() => {
        reportWindow.print();
    }, 450);
}

function buildReportPdfHtml(data) {
    const terrain = data.terrain_analysis || {};
    const hydraulic = data.hydraulic_analysis || {};
    const materials = data.materials_analysis || {};
    const design = data.design_recommendations || {};
    const dimensions = data.image_dimensions || {};
    const pump = hydraulic.recommended_pump || {};
    const spec = hydraulic.required_pump_spec || {};
    const recommendations = design.recommendations || [];
    const generatedAt = new Date().toLocaleString("es-CL");

    const recommendationRows = recommendations.length
        ? recommendations.map(rec => `
            <div class="pdf-recommendation">
                <span>${escapeHtml(rec.priority || "Info")}</span>
                <div>
                    <strong>${escapeHtml(rec.type || "Criterio")}</strong>
                    <p>${escapeHtml(rec.message || "")}</p>
                    <small>${escapeHtml(rec.action || "")}</small>
                </div>
            </div>
        `).join("")
        : '<p class="pdf-muted">No hay recomendaciones disponibles.</p>';
    const materialRows = (materials.items || []).length
        ? materials.items.map(item => `
            <div class="pdf-material">
                <span>${escapeHtml(item.category || "Material")}</span>
                <strong>${escapeHtml(item.component || "--")}</strong>
                <small>${escapeHtml(item.quantity || "--")}</small>
                <p>${escapeHtml(item.purpose || "")}</p>
            </div>
        `).join("")
        : '<p class="pdf-muted">No hay materiales calculados.</p>';

    return `
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Reporte riego - ${escapeHtml(data.file_name || "analisis")}</title>
    <style>
        @page { size: A4; margin: 14mm; }
        * { box-sizing: border-box; }
        body {
            margin: 0;
            color: #162033;
            background: #ffffff;
            font-family: "Segoe UI", Arial, sans-serif;
            line-height: 1.45;
        }
        .pdf-page {
            max-width: 980px;
            margin: 0 auto;
        }
        .pdf-hero {
            display: grid;
            grid-template-columns: 1.2fr 0.8fr;
            gap: 18px;
            padding: 22px;
            color: #ffffff;
            background: linear-gradient(135deg, #08111f, #0d5362 64%, #14a07a);
            border-radius: 14px;
        }
        .pdf-kicker {
            display: block;
            color: #8ff4ff;
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            margin-bottom: 8px;
        }
        h1, h2, h3, p { margin: 0; }
        h1 { font-size: 26px; line-height: 1.12; }
        .pdf-hero p { color: #c7e8f0; margin-top: 10px; }
        .pdf-meta {
            display: grid;
            gap: 8px;
            align-content: center;
            font-size: 12px;
        }
        .pdf-meta div {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            padding: 8px 0;
            border-bottom: 1px solid rgba(255,255,255,0.22);
        }
        .pdf-section {
            margin-top: 18px;
            padding: 18px;
            border: 1px solid #d8e2ee;
            border-radius: 12px;
            background: #f8fbff;
            break-inside: avoid;
        }
        .pdf-section h2 {
            color: #0b4b5b;
            font-size: 15px;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 12px;
        }
        .pdf-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
        }
        .pdf-metric {
            min-height: 76px;
            padding: 12px;
            border: 1px solid #dce7f3;
            border-radius: 10px;
            background: #ffffff;
        }
        .pdf-metric span {
            display: block;
            color: #607086;
            font-size: 10px;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }
        .pdf-metric strong {
            display: block;
            color: #092b36;
            font-family: Consolas, "Courier New", monospace;
            font-size: 17px;
            margin-top: 8px;
            overflow-wrap: anywhere;
        }
        .pdf-pump {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }
        .pdf-callout {
            padding: 14px;
            border-radius: 10px;
            background: #082033;
            color: #ffffff;
        }
        .pdf-callout span {
            display: block;
            color: #8ff4ff;
            font-size: 10px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }
        .pdf-callout strong {
            display: block;
            font-size: 20px;
            margin-top: 6px;
        }
        .pdf-callout small { color: #c7e8f0; }
        .pdf-recommendation {
            display: grid;
            grid-template-columns: 82px 1fr;
            gap: 12px;
            padding: 12px;
            border: 1px solid #dce7f3;
            border-radius: 10px;
            background: #ffffff;
            margin-top: 9px;
        }
        .pdf-recommendation > span {
            display: grid;
            place-items: center;
            min-height: 34px;
            border-radius: 7px;
            color: #08313d;
            background: #dff9ff;
            font-size: 11px;
            font-weight: 800;
            text-transform: uppercase;
        }
        .pdf-recommendation strong { color: #092b36; }
        .pdf-recommendation p { color: #3d4e64; margin-top: 4px; }
        .pdf-recommendation small { display: block; color: #697b91; margin-top: 4px; }
        .pdf-muted { color: #697b91; }
        .pdf-material {
            padding: 12px;
            border: 1px solid #dce7f3;
            border-radius: 10px;
            background: #ffffff;
            margin-top: 9px;
        }
        .pdf-material span {
            display: block;
            color: #607086;
            font-size: 10px;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }
        .pdf-material strong {
            display: block;
            color: #092b36;
            margin-top: 4px;
        }
        .pdf-material small {
            display: block;
            color: #0b4b5b;
            font-family: Consolas, "Courier New", monospace;
            margin-top: 3px;
        }
        .pdf-material p {
            color: #3d4e64;
            margin-top: 5px;
        }
        .pdf-footer {
            margin-top: 18px;
            padding-top: 10px;
            border-top: 1px solid #d8e2ee;
            color: #697b91;
            font-size: 11px;
            display: flex;
            justify-content: space-between;
            gap: 12px;
        }
        @media print {
            .pdf-section { break-inside: avoid; }
        }
    </style>
</head>
<body>
    <main class="pdf-page">
        <section class="pdf-hero">
            <div>
                <span class="pdf-kicker">Reporte tecnico</span>
                <h1>Sistema de recomendacion para riego por goteo</h1>
                <p>Resumen consolidado del analisis geoespacial e hidraulico para el terreno cargado.</p>
            </div>
            <div class="pdf-meta">
                <div><span>Archivo</span><strong>${escapeHtml(data.file_name || "--")}</strong></div>
                <div><span>Fecha</span><strong>${escapeHtml(generatedAt)}</strong></div>
                <div><span>Estado</span><strong>Completado</strong></div>
            </div>
        </section>

        <section class="pdf-section">
            <h2>Resumen Del Terreno</h2>
            <div class="pdf-grid">
                ${reportMetric("Dimensiones", `${dimensions.width || "--"} x ${dimensions.height || "--"} px`)}
                ${reportMetric("Area estimada", formatUnit(design.estimated_area, " ha", 2))}
                ${reportMetric("Longitud riego", formatUnit(design.estimated_drip_length, " m", 0))}
                ${reportMetric("Elevacion maxima", formatUnit(terrain.max_elevation, " m", 2))}
                ${reportMetric("Elevacion minima", formatUnit(terrain.min_elevation, " m", 2))}
                ${reportMetric("Desnivel", formatUnit(terrain.elevation_difference, " m", 2))}
                ${reportMetric("Pendiente media", formatUnit(terrain.slope_degrees, " grados", 2))}
                ${reportMetric("Zonas criticas", formatUnit(terrain.critical_zones_percentage, "%", 0))}
                ${reportMetric("Fuente elevacion", terrain.source || "--")}
            </div>
        </section>

        <section class="pdf-section">
            <h2>Analisis Hidraulico</h2>
            <div class="pdf-grid">
                ${reportMetric("Presion requerida", formatUnit(hydraulic.source_pressure, " kPa", 2))}
                ${reportMetric("Caudal requerido", formatUnit(hydraulic.available_flow, " L/min", 2))}
                ${reportMetric("Perdida de carga", formatUnit(hydraulic.pressure_loss, " kPa", 2))}
                ${reportMetric("Friccion", formatUnit(hydraulic.friction_loss, " kPa", 2))}
                ${reportMetric("Desnivel hidraulico", formatUnit(hydraulic.elevation_pressure_change, " kPa", 2))}
                ${reportMetric("Riesgo", hydraulic.hydraulic_risk || "--")}
            </div>
        </section>

        <section class="pdf-section">
            <h2>Motobomba Recomendada</h2>
            <div class="pdf-pump">
                <div class="pdf-callout">
                    <span>Requerimiento calculado</span>
                    <strong>${escapeHtml(formatUnit(spec.minimum_power_hp || hydraulic.required_pump_power, " HP", 2))}</strong>
                    <small>${escapeHtml(formatUnit(spec.required_flow_l_min || hydraulic.available_flow, " L/min", 2))} | ${escapeHtml(formatUnit(spec.required_head_m || hydraulic.required_total_head, " m", 2))}</small>
                </div>
                <div class="pdf-callout">
                    <span>Modelo sugerido</span>
                    <strong>${escapeHtml(pump.model || "--")}</strong>
                    <small>${escapeHtml(pump.type || "Motobomba")} | ${escapeHtml(formatUnit(pump.engine_power_hp, " HP", 1))}</small>
                </div>
            </div>
        </section>

        <section class="pdf-section">
            <h2>Materiales Del Sistema</h2>
            <div class="pdf-grid">
                ${reportMetric("Tuberia principal", `${materials.main_pipe_type || "--"} ${materials.main_pipe_diameter_mm || "--"} mm`)}
                ${reportMetric("Clase presion", materials.pipe_pressure_class || "--")}
                ${reportMetric("Laterales", `${materials.lateral_pipe_type || "--"} ${materials.lateral_diameter_mm || "--"} mm`)}
                ${reportMetric("Llave de paso", `${materials.valve_type || "--"} ${materials.valve_diameter_mm || "--"} mm`)}
                ${reportMetric("Filtro", materials.filter_type || "--")}
                ${reportMetric("Goteros", materials.estimated_emitters ? `${formatNumber(materials.estimated_emitters, 0)} unidades` : "--")}
            </div>
            ${materialRows}
        </section>

        <section class="pdf-section">
            <h2>Supuestos Configurables</h2>
            <div class="pdf-grid">
                ${reportMetric("Demanda de riego", formatUnit(hydraulic.flow_per_hectare, " L/min/ha", 2))}
                ${reportMetric("Presion gotero", formatUnit(hydraulic.emitter_operating_pressure, " kPa", 0))}
                ${reportMetric("Margen seguridad", formatFactorAsPercent(hydraulic.pressure_safety_factor, 0))}
                ${reportMetric("Rendimiento bomba", formatNumber(hydraulic.assumptions?.pump_efficiency, 2))}
                ${reportMetric("Diametro tuberia", formatUnit(hydraulic.pipe_diameter, " mm", 0))}
                ${reportMetric("Longitud critica", formatUnit(hydraulic.pipe_length, " m", 0))}
            </div>
        </section>

        <section class="pdf-section">
            <h2>Recomendaciones</h2>
            ${recommendationRows}
        </section>

        <footer class="pdf-footer">
            <span>USACH | Tesis 2026</span>
            <span>Reporte generado por el dashboard tecnico de riego</span>
        </footer>
    </main>
</body>
</html>
    `;
}

window.addEventListener("keydown", event => {
    if (event.key === "Escape") {
        closeMaterialPopup();
        closePumpList();
        closeMetricInfo();
        closeUploadModal();
    }
});

document.addEventListener("keydown", event => {
    const target = event.target;
    if (
        (target?.classList?.contains("material-summary-card") ||
            target?.classList?.contains("info-summary-card")) &&
        (event.key === "Enter" || event.key === " ")
    ) {
        event.preventDefault();
        target.click();
    }
});

console.log("Dashboard tecnico de riego cargado");
