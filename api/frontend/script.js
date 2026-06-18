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
    setText("metricSlope", formatUnit(terrain.slope_percentage, "%", 2));
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
    setText("terrainSlope", formatUnit(terrain.slope_percentage, "%", 2));
    setText("terrainCritical", formatUnit(terrain.critical_zones_percentage, "%", 0));

    setText("hydPressure", formatNumber(hydraulic.source_pressure, 2));
    setText("hydFlow", formatNumber(hydraulic.available_flow, 2));
    setText("hydLoss", formatNumber(hydraulic.pressure_loss, 2));
    setText("hydRisk", hydraulic.hydraulic_risk || "--");

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

    renderRecommendations(design.recommendations || []);
    renderReport(analysisData);
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
        <div class="report-row"><span>Terreno</span><strong>Pendiente ${formatUnit(terrain.slope_percentage, "%", 2)}, desnivel ${formatUnit(terrain.elevation_difference, " m", 2)}</strong></div>
        <div class="report-row"><span>Hidraulica</span><strong>Riesgo ${hydraulic.hydraulic_risk || "--"}, perdida ${formatUnit(hydraulic.pressure_loss, " kPa", 2)}</strong></div>
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
