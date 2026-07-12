const API_URL = "http://localhost:5000";
const HEALTH_ENDPOINT = "/api/v1/health";
const DOCS_ENDPOINT = "/api/v1/docs";

const modules = {
    inicio: "Inicio",
    terreno: "Terreno",
    hidraulica: "Hidraulica",
    agua: "Agua y materiales",
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

async function submitAnalysis() {
    const file = $("fileInput")?.files[0];
    if (!file) {
        alert("Selecciona una imagen antes de iniciar el analisis.");
        return;
    }

    try {
        const formData = new FormData();
        formData.append("file", file);
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
        switchTab("terreno");
    } catch (error) {
        alert(`Error al enviar el archivo:\n${error.message}`);
        setText("footerState", "Error analisis");
    } finally {
        setLoadingState(false);
    }
}

function displayAnalysisResults(analysisData) {
    if (!analysisData) {
        return;
    }

    const terrain = analysisData.terrain_analysis || {};
    const hydraulic = analysisData.hydraulic_analysis || {};
    const water = analysisData.water_analysis || {};
    const design = analysisData.design_recommendations || {};

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
    setText("waterStatus", "Activo");
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
    setText("hydSurfaceLimit", formatUnit(design.pump_surface_limit, " ha", 2));

    setText("waterPh", formatNumber(water.ph, 2));
    setText("waterSalinity", formatNumber(water.salinity_ppm, 0));
    setText("waterHardness", formatNumber(water.hardness_mg_l, 0));
    setText("waterQuality", water.water_quality || "--");
    setText("materialStatus", water.recommended_material ? "Generado" : "Pendiente");
    setText("materialRecommendation", water.recommended_material || "No hay recomendacion disponible.");

    setText("designArea", formatNumber(design.estimated_area, 2));
    setText("designLength", formatNumber(design.estimated_drip_length, 0));
    setText("designComplexity", design.complexity_level || "--");
    setText("designCost", design.estimated_cost_level || "--");

    renderHydraulicCharts(hydraulic);
    renderPumpCatalog(hydraulic);
    renderWaterCharts(water);
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
        { label: "Presion fuente", value: hydraulic.source_pressure, max: 250, unit: " kPa", color: "var(--cyan)" },
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
        <div class="gauge-card"><span>Diametro</span><strong>${formatUnit(hydraulic.pipe_diameter, " mm", 0)}</strong><small>tuberia base</small></div>
        <div class="gauge-card"><span>Longitud</span><strong>${formatUnit(hydraulic.pipe_length, " m", 0)}</strong><small>tramo critico</small></div>
        <div class="gauge-card"><span>Presion final</span><strong>${formatUnit(hydraulic.final_pressure, " kPa", 2)}</strong><small>salida estimada</small></div>
        <div class="gauge-card"><span>Caudal</span><strong>${formatUnit(hydraulic.available_flow, " L/min", 2)}</strong><small>sector</small></div>
        <div class="gauge-card"><span>Riesgo</span><strong>${hydraulic.hydraulic_risk || "--"}</strong><small>criterio hidraulico</small></div>
        <div class="gauge-card"><span>Altura total</span><strong>${formatUnit(hydraulic.required_total_head, " m", 2)}</strong><small>carga dinamica</small></div>
        <div class="gauge-card"><span>Potencia</span><strong>${formatUnit(hydraulic.required_pump_power, " HP", 2)}</strong><small>con eficiencia 60%</small></div>
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
    if (!catalog.length) {
        container.innerHTML = '<p class="empty-state">Sin catalogo evaluado.</p>';
        if (status) {
            status.textContent = "Pendiente";
        }
        return;
    }

    const recommended = hydraulic.recommended_pump?.model;
    if (status) {
        status.textContent = recommended || "Referencial";
    }

    container.innerHTML = catalog.map(pump => {
        const isSelected = pump.model === recommended;
        const isSuitable = Boolean(pump.suitable_for_required_head);
        return `
            <div class="pump-card ${isSelected ? "selected" : ""} ${isSuitable ? "suitable" : "limited"}">
                <div>
                    <span>${pump.type || "Motobomba"}</span>
                    <strong>${pump.model}</strong>
                    <small>${pump.engine || "--"} | ${formatUnit(pump.engine_power_hp, " HP", 1)}</small>
                </div>
                <div><span>Caudal max.</span><strong>${formatUnit(pump.max_flow_l_min, " L/min", 0)}</strong></div>
                <div><span>Altura max.</span><strong>${formatUnit(pump.max_head_m, " m", 1)}</strong></div>
                <div><span>Superficie</span><strong>${formatUnit(pump.max_surface_ha, " ha", 2)}</strong></div>
                <small>${pump.selection_note || ""}</small>
            </div>
        `;
    }).join("");
}

function renderWaterCharts(water) {
    const chemistryChart = $("waterChemistryChart");
    const materialChart = $("materialCompatibilityChart");
    if (!chemistryChart || !materialChart) {
        return;
    }

    const rows = [
        { label: "pH", value: water.ph, max: 14, unit: "", color: "var(--cyan)", decimals: 2 },
        { label: "Salinidad", value: water.salinity_ppm, max: 2000, unit: " ppm", color: "var(--orange)", decimals: 0 },
        { label: "Dureza", value: water.hardness_mg_l, max: 500, unit: " mg/L", color: "var(--purple)", decimals: 0 }
    ];

    chemistryChart.innerHTML = rows.map(row => `
        <div class="chart-row">
            <span>${row.label}</span>
            <div class="chart-track">
                <span class="chart-fill" style="--value:${clampPercent(row.value, row.max)}%; --fill:${row.color};"></span>
            </div>
            <strong class="chart-value">${formatUnit(row.value, row.unit, row.decimals)}</strong>
        </div>
    `).join("");

    const compatibility = water.material_compatibility || {};
    const entries = Object.entries(compatibility);
    if (!entries.length) {
        materialChart.innerHTML = '<p class="empty-state">Sin compatibilidad calculada.</p>';
        return;
    }

    materialChart.innerHTML = entries.map(([name, status]) => {
        const statusClass = normalizePriority(status).includes("media") ? "media" : normalizePriority(status).includes("baja") ? "baja" : "";
        return `
            <div class="compat-card ${statusClass}">
                <span>${name.replace(/_/g, " ")}</span>
                <strong>${status}</strong>
            </div>
        `;
    }).join("");
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
    const water = data.water_analysis || {};
    const design = data.design_recommendations || {};
    const dimensions = data.image_dimensions || {};

    setText("reportState", "Disponible");

    content.innerHTML = `
        <div class="report-row"><span>Archivo</span><strong>${data.file_name || "--"}</strong></div>
        <div class="report-row"><span>Dimensiones</span><strong>${dimensions.width || "--"} x ${dimensions.height || "--"} px</strong></div>
        <div class="report-row"><span>Terreno</span><strong>Pendiente ${formatUnit(terrain.slope_degrees, "°", 2)}, desnivel ${formatUnit(terrain.elevation_difference, " m", 2)}</strong></div>
        <div class="report-row"><span>Hidraulica</span><strong>Riesgo ${hydraulic.hydraulic_risk || "--"}, perdida ${formatUnit(hydraulic.pressure_loss, " kPa", 2)}</strong></div>
        <div class="report-row"><span>Motobomba</span><strong>${hydraulic.recommended_pump?.model || "--"}, potencia requerida ${formatUnit(hydraulic.required_pump_power, " HP", 2)}, superficie limite ${formatUnit(design.pump_surface_limit, " ha", 2)}</strong></div>
        <div class="report-row"><span>Agua</span><strong>pH ${formatNumber(water.ph, 2)}, calidad ${water.water_quality || "--"}</strong></div>
        <div class="report-row"><span>Diseno</span><strong>${design.complexity_level || "--"} | costo ${design.estimated_cost_level || "--"}</strong></div>
    `;
}

window.addEventListener("keydown", event => {
    if (event.key === "Escape") {
        closeUploadModal();
    }
});

console.log("Dashboard tecnico de riego cargado");
