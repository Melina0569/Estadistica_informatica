const cargaForm = document.getElementById("carga-form");
const archivoInput = document.getElementById("archivo");
const analizarBtn = document.getElementById("analizar-btn");
const confirmarBtn = document.getElementById("confirmar-btn");
const limpiarBtn = document.getElementById("limpiar-btn");
const dropZone = document.getElementById("drop-zone");
const fileName = document.getElementById("file-name");
const dropTitle = document.getElementById("drop-title");
const dropDescription = document.getElementById("drop-description");
const resultadoPanel = document.getElementById("resultado-panel");
const resultadoEstado = document.getElementById("resultado-estado");
const resultadoResumen = document.getElementById("resultado-resumen");
const resultadoMensaje = document.getElementById("resultado-mensaje");
const archivoResumen = document.getElementById("archivo-resumen");
const vistaPrevia = document.getElementById("vista-previa");
const vistaPreviaResumen = document.getElementById("vista-previa-resumen");
const vistaPreviaPaginacion = document.getElementById("vista-previa-paginacion");
const vistaPreviaFilas = document.getElementById("vista-previa-filas");
const moduloInconsistencias = document.getElementById("modulo-inconsistencias");
const inconsistenciasResumen = document.getElementById("inconsistencias-resumen");
const inconsistenciasCasos = document.getElementById("inconsistencias-casos");
const inconsistencias = document.getElementById("inconsistencias");
const irCorrecciones = document.getElementById("ir-correcciones");
const tipoPlanillaLabel = document.getElementById("tipo-planilla-label");
const progresoCarga = document.getElementById("progreso-carga");
const progresoTitulo = document.getElementById("progreso-titulo");
const progresoPorcentaje = document.getElementById("progreso-porcentaje");
const progresoBarra = document.getElementById("progreso-barra");
const progresoDetalle = document.getElementById("progreso-detalle");
const progresoTrack = progresoCarga.querySelector("[role='progressbar']");
const actualizarAnalisisBtn = document.getElementById("actualizar-analisis-btn");
const entitySelectorGroup = document.getElementById("entity-selector-group");
const carouselViewport = document.querySelector(".carga-carousel-viewport");
const carouselControls = document.querySelectorAll("[data-carousel-direction]");

let tipoPlanilla = "estudiantes";
let ultimoReporte = null;
let progresoIntervalo = null;
let progresoActual = 0;
let carruselIndice = 0;
let carruselIntervalo = null;
let seleccionarArchivoParaActualizar = false;
const CLAVE_REPORTE_CARGA = "dataunmsm.ultimoReporteCarga";

function escapar(texto) {
    return String(texto ?? "").replace(
        /[&<>"']/g,
        (caracter) => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;"
        }[caracter])
    );
}

function archivoSeleccionado() {
    const archivo = archivoInput.files[0];
    if (!archivo) {
        throw new Error("Selecciona un archivo Excel.");
    }
    return archivo;
}

function mostrarArchivo(archivo) {
    fileName.hidden = false;
    fileName.textContent = `${archivo.name} · ${(archivo.size / 1024 / 1024).toFixed(2)} MB`;
    dropTitle.textContent = "Archivo seleccionado";
    dropDescription.textContent = "Presiona «Analizar archivo» para consultar la validación del backend.";
}

function guardarReporte(reporte, archivo) {
    const reportePersistible = {
        estado: reporte.estado,
        total_filas: reporte.total_filas,
        total_inconsistencias: reporte.total_inconsistencias,
        inconsistencias: reporte.inconsistencias,
        resumen_inconsistencias: reporte.resumen_inconsistencias,
        correcciones_aplicadas: reporte.correcciones_aplicadas,
        siguiente_paso: reporte.siguiente_paso,
        vista_previa: reporte.vista_previa,
        id_carga: reporte.id_carga
    };

    // Las correcciones automáticas y el detalle completo pueden contener
    // miles de registros; solo se necesita este resumen para restaurar la vista.
    try {
        localStorage.removeItem(CLAVE_REPORTE_CARGA);
        localStorage.setItem(CLAVE_REPORTE_CARGA, JSON.stringify({
            reporte: reportePersistible,
            archivo: {
                name: archivo.name,
                size: archivo.size,
                lastModified: archivo.lastModified
            },
            guardadoEn: new Date().toISOString()
        }));
    } catch (error) {
        console.error("No se pudo guardar el resumen del análisis:", error);
    }
}

function eliminarReporteGuardado() {
    localStorage.removeItem(CLAVE_REPORTE_CARGA);
}

function restaurarReporteGuardado() {
    const guardado = localStorage.getItem(CLAVE_REPORTE_CARGA);
    if (!guardado) return;

    try {
        const datos = JSON.parse(guardado);
        if (!datos.reporte || !datos.archivo?.name) return;
        ultimoReporte = datos.reporte;
        mostrarArchivo(datos.archivo);
        mostrarResultado(
            datos.reporte,
            "Análisis restaurado. Selecciona el mismo archivo para confirmar la carga.",
            datos.reporte.estado === "APTO" ? "ok" : "error"
        );
        renderizarReporte(datos.reporte, datos.archivo);
        confirmarBtn.disabled = datos.reporte.estado !== "APTO";
    } catch (error) {
        console.error("No se pudo restaurar el análisis guardado:", error);
        eliminarReporteGuardado();
    }
}

function limpiarResultado() {
    ultimoReporte = null;
    resultadoPanel.hidden = false;
    confirmarBtn.disabled = true;
    resultadoEstado.className = "carga-status";
    resultadoEstado.textContent = "";
    resultadoResumen.textContent = "";
    resultadoMensaje.textContent = "";
    resultadoMensaje.className = "carga-message";
    archivoResumen.hidden = true;
    archivoResumen.textContent = "";
    vistaPrevia.hidden = false;
    vistaPreviaResumen.textContent =
        "Analiza un archivo para consultar sus primeras filas.";
    vistaPreviaPaginacion.textContent = "";
    vistaPreviaFilas.innerHTML = `
        <tr>
            <td colspan="8">La vista previa aparecerá después del análisis.</td>
        </tr>
    `;
    moduloInconsistencias.hidden = false;
    inconsistenciasResumen.textContent =
        "El resultado de validación se mostrará aquí.";
    inconsistenciasCasos.textContent = "";
    inconsistencias.innerHTML = `
        <div class="carga-message">
            Aún no se han detectado inconsistencias porque no se ha analizado un archivo.
        </div>
    `;
}

function actualizarProgreso(valor) {
    progresoActual = Math.max(0, Math.min(100, valor));
    progresoPorcentaje.textContent = `${progresoActual}%`;
    progresoBarra.style.width = `${progresoActual}%`;
    progresoTrack.setAttribute("aria-valuenow", String(progresoActual));
}

function iniciarProgreso(titulo, detalle) {
    window.clearInterval(progresoIntervalo);
    progresoCarga.hidden = false;
    progresoTitulo.textContent = titulo;
    progresoDetalle.textContent = detalle;
    progresoBarra.classList.remove("is-complete");
    actualizarProgreso(8);

    progresoIntervalo = window.setInterval(() => {
        if (progresoActual >= 92) return;
        const incremento = progresoActual < 45 ? 5 : 2;
        actualizarProgreso(Math.min(92, progresoActual + incremento));
    }, 350);
}

function finalizarProgreso(detalle) {
    window.clearInterval(progresoIntervalo);
    progresoIntervalo = null;
    progresoTitulo.textContent = "¡Proceso completado!";
    progresoDetalle.textContent = detalle;
    progresoBarra.classList.add("is-complete");
    actualizarProgreso(100);
}

function cancelarProgreso() {
    window.clearInterval(progresoIntervalo);
    progresoIntervalo = null;
    progresoCarga.hidden = true;
    progresoBarra.classList.remove("is-complete");
    actualizarProgreso(0);
}

function mostrarSerpentinas() {
    const capa = document.createElement("div");
    capa.className = "carga-confetti-layer";
    capa.setAttribute("aria-hidden", "true");

    const colores = ["#0058be", "#28a094", "#f0b429", "#ba1a1a", "#1e293b"];
    for (let indice = 0; indice < 42; indice += 1) {
        const serpentina = document.createElement("span");
        serpentina.className = "carga-confetti";
        serpentina.style.left = `${Math.random() * 100}%`;
        serpentina.style.setProperty(
            "--confetti-color",
            colores[indice % colores.length]
        );
        serpentina.style.setProperty(
            "--confetti-duration",
            `${1.4 + Math.random() * 1.4}s`
        );
        serpentina.style.setProperty(
            "--confetti-delay",
            `${Math.random() * .35}s`
        );
        serpentina.style.setProperty(
            "--confetti-drift",
            `${-120 + Math.random() * 240}px`
        );
        serpentina.style.setProperty(
            "--confetti-rotation",
            `${Math.random() * 180}deg`
        );
        capa.appendChild(serpentina);
    }

    document.body.appendChild(capa);
    window.setTimeout(() => capa.remove(), 3200);
}

function mostrarResultado(reporte, mensaje, tipo) {
    resultadoPanel.hidden = false;
    resultadoEstado.className = `carga-status carga-status-${tipo}`;
    resultadoEstado.textContent = reporte.estado || "Resultado";
    resultadoResumen.textContent = reporte.total_inconsistencias === undefined
        ? ""
        : `${reporte.total_inconsistencias} inconsistencia(s) reportada(s) por el backend.`;
    resultadoMensaje.className = `carga-message ${tipo === "ok" ? "is-ok" : "is-error"}`;
    resultadoMensaje.textContent = mensaje;
}

function renderizarReporte(reporte, archivo) {
    const problemas = Array.isArray(reporte.inconsistencias)
        ? reporte.inconsistencias
        : [];
    const totalProblemas = Number.isFinite(Number(reporte.total_inconsistencias))
        ? Number(reporte.total_inconsistencias)
        : problemas.length;
    const resumenProblemas = Array.isArray(reporte.resumen_inconsistencias)
        ? reporte.resumen_inconsistencias
        : [];
    const correccionesAplicadas = Array.isArray(reporte.correcciones_aplicadas)
        ? reporte.correcciones_aplicadas
        : [];
    const filas = reporte.vista_previa?.filas || [];
    const encabezado = document.querySelector(".carga-preview-table thead tr");
    encabezado?.querySelectorAll("[data-correccion-header]").forEach((celda) => celda.remove());
    correccionesAplicadas.forEach((item) => {
        const celda = document.createElement("th");
        celda.dataset.correccionHeader = "true";
        celda.textContent = item.campo;
        encabezado?.appendChild(celda);
    });

    archivoResumen.hidden = false;
    archivoResumen.innerHTML = [
        `<span>Archivo: ${escapar(archivo.name)}</span>`,
        `<span>Filas: ${escapar(reporte.total_filas ?? "—")}</span>`,
        `<span>Estado: ${escapar(reporte.estado ?? "—")}</span>`
    ].join("");

    vistaPrevia.hidden = false;
    vistaPreviaResumen.textContent =
        `Mostrando ${filas.length} de ${reporte.total_filas ?? filas.length} fila(s) identificadas.`;
    vistaPreviaPaginacion.textContent =
        filas.length ? `1 - ${filas.length}` : "Sin filas";
    vistaPreviaFilas.innerHTML = filas.length
        ? filas.map((fila) => {
            const observado = fila.estado === "Observado";
            return `
                <tr>
                    <td class="carga-preview-row">${escapar(fila.fila_excel)}</td>
                    <td class="carga-preview-code">${escapar(fila.codigo_alumno ?? "—")}</td>
                    <td class="carga-preview-code">${escapar(fila.documento ?? "—")}</td>
                    <td>${escapar(fila.nombre || "—")}</td>
                    <td>
                        <strong>${escapar(fila.facultad || "—")}</strong>
                        <br><span>${escapar(fila.programa || "—")}</span>
                    </td>
                    <td>${escapar(fila.ciclo ?? "—")}</td>
                    <td>${escapar(fila.modalidad_ingreso || "—")}</td>
                    <td>
                        <span class="carga-row-status ${observado ? "is-error" : "is-ok"}">
                            ${observado ? "Observado" : "Apto"}
                        </span>
                    </td>
                    ${correccionesAplicadas.map((item) => `<td>${escapar(item.valor)}</td>`).join("")}
                </tr>
            `;
        }).join("")
        : `<tr><td colspan="8">El backend no devolvió filas para la vista previa.</td></tr>`;

    moduloInconsistencias.hidden = false;
    inconsistenciasResumen.textContent = resumenProblemas.length
        ? `Se agruparon ${totalProblemas} caso(s) en ${resumenProblemas.length} tipo(s). Revisa el detalle en Correcciones.`
        : "El backend no reportó inconsistencias para este archivo.";
    inconsistenciasCasos.textContent = `${totalProblemas} caso(s)`;
    irCorrecciones.hidden = !totalProblemas;

    if (!resumenProblemas.length) {
        inconsistencias.innerHTML = `
            <div class="carga-message is-ok">
                No se detectaron inconsistencias ni observaciones en la validación.
            </div>
        `;
        return;
    }

    inconsistencias.innerHTML = resumenProblemas.map((problema) => `
        <article class="carga-issue">
            <div class="carga-issue-head">
                <div class="carga-issue-title">
                    ${escapar(problema.tipo || "Observación")} · ${escapar(problema.campo || "Registro")}
                </div>
                <span class="carga-issue-count">${escapar(problema.cantidad)} caso(s)</span>
            </div>
            <div class="carga-issue-detail">${escapar(problema.mensaje ?? "Inconsistencia reportada.")}</div>
            <div class="carga-issue-detail carga-issue-summary">
                ${escapar(problema.cantidad ?? 0)} registro(s) requieren revisión.
            </div>
            ${problema.sugerencia
                ? `<div class="carga-issue-detail">Sugerencia: ${escapar(problema.sugerencia)}</div>`
                : ""}
        </article>
    `).join("");
}

function seleccionarTipo(boton) {
    const nuevoTipo = boton.dataset.tipo;
    if (nuevoTipo !== "estudiantes") {
        window.alert("Este módulo aún no tiene una ruta Flask de importación disponible.");
        return;
    }

    tipoPlanilla = nuevoTipo;
    document.querySelectorAll(".carga-entity-card").forEach((elemento) => {
        const seleccionado = elemento === boton;
        elemento.classList.toggle("is-selected", seleccionado);
        elemento.setAttribute("aria-pressed", String(seleccionado));
    });
    tipoPlanillaLabel.textContent = "Estudiantes";
}

function columnasCarrusel() {
    if (window.innerWidth <= 640) return 1;
    if (window.innerWidth <= 900) return 2;
    return 4;
}

function actualizarCarrusel() {
    const tarjetas = entitySelectorGroup.querySelectorAll(".carga-entity-card");
    const columnas = columnasCarrusel();
    const maximo = Math.max(0, tarjetas.length - columnas);
    carruselIndice = carruselIndice > maximo ? 0 : carruselIndice;
    const primeraTarjeta = tarjetas[0];
    const anchoTarjeta = primeraTarjeta.getBoundingClientRect().width;
    const espacio = tarjetas.length > 1
        ? tarjetas[1].getBoundingClientRect().left
            - primeraTarjeta.getBoundingClientRect().right
        : 0;
    const desplazamiento = Math.round(carruselIndice * (anchoTarjeta + espacio));
    entitySelectorGroup.style.transform =
        `translateX(-${desplazamiento}px)`;
}

function avanzarCarrusel() {
    const maximo = Math.max(
        0,
        entitySelectorGroup.children.length - columnasCarrusel()
    );
    carruselIndice = carruselIndice >= maximo ? 0 : carruselIndice + 1;
    actualizarCarrusel();
}

function moverCarrusel(direccion) {
    const maximo = Math.max(
        0,
        entitySelectorGroup.children.length - columnasCarrusel()
    );
    carruselIndice = direccion > 0
        ? (carruselIndice >= maximo ? 0 : carruselIndice + 1)
        : (carruselIndice <= 0 ? maximo : carruselIndice - 1);
    actualizarCarrusel();
    iniciarCarrusel();
}

function iniciarCarrusel() {
    window.clearInterval(carruselIntervalo);
    carruselIntervalo = window.setInterval(avanzarCarrusel, 4500);
}

carouselControls.forEach((control) => {
    control.addEventListener("click", () => {
        moverCarrusel(Number(control.dataset.carouselDirection));
    });
});

document.querySelectorAll(".carga-entity-card").forEach((boton) => {
    boton.addEventListener("click", () => seleccionarTipo(boton));
});

window.addEventListener("resize", actualizarCarrusel);
actualizarCarrusel();
iniciarCarrusel();

archivoInput.addEventListener("change", () => {
    limpiarResultado();
    if (archivoInput.files[0]) {
        eliminarReporteGuardado();
        mostrarArchivo(archivoInput.files[0]);
        if (seleccionarArchivoParaActualizar) {
            seleccionarArchivoParaActualizar = false;
            cargaForm.requestSubmit();
        }
    }
});

["dragenter", "dragover"].forEach((evento) => {
    dropZone.addEventListener(evento, (event) => {
        event.preventDefault();
        dropZone.classList.add("is-dragging");
    });
});

["dragleave", "drop"].forEach((evento) => {
    dropZone.addEventListener(evento, (event) => {
        event.preventDefault();
        dropZone.classList.remove("is-dragging");
    });
});

dropZone.addEventListener("drop", (event) => {
    const archivo = event.dataTransfer.files[0];
    if (!archivo) return;

    const nombre = archivo.name.toLowerCase();
    if (!nombre.endsWith(".xlsx") && !nombre.endsWith(".xls")) {
        window.alert("El archivo debe tener extensión .xlsx o .xls.");
        return;
    }

    const transferencia = new DataTransfer();
    transferencia.items.add(archivo);
    archivoInput.files = transferencia.files;
    limpiarResultado();
    mostrarArchivo(archivo);
});

cargaForm.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const archivo = archivoSeleccionado();
    confirmarBtn.disabled = true;
    analizarBtn.disabled = true;
    limpiarResultado();
    iniciarProgreso(
        "Analizando archivo...",
        "El servidor está leyendo y validando las filas del Excel."
    );

    try {
        const reporte = await API.analizarExcel(archivo);
        ultimoReporte = reporte;
        const apto = reporte.estado === "APTO";
        finalizarProgreso(
            apto
                ? "La validación terminó sin bloqueos."
                : "La validación terminó con observaciones."
        );
        mostrarResultado(
            reporte,
            apto
                ? "El backend considera el archivo apto para continuar."
                : reporte.siguiente_paso || "Corrige las inconsistencias antes de confirmar.",
            apto ? "ok" : "error"
        );
        renderizarReporte(reporte, archivo);
        guardarReporte(reporte, archivo);
        confirmarBtn.disabled = !apto;
        if (apto) mostrarSerpentinas();
    } catch (error) {
        ultimoReporte = null;
        cancelarProgreso();
        mostrarResultado({}, error.message, "error");
    } finally {
        analizarBtn.disabled = false;
    }
});

confirmarBtn.addEventListener("click", async () => {
    if (!ultimoReporte || ultimoReporte.estado !== "APTO") return;

    confirmarBtn.disabled = true;
    analizarBtn.disabled = true;
    limpiarResultado();
    iniciarProgreso(
        "Confirmando carga...",
        "El servidor está guardando los datos y registrando el historial."
    );

    try {
        const respuesta = await API.confirmarCarga();
        finalizarProgreso("Los datos fueron guardados correctamente.");
        mostrarResultado(
            respuesta,
            respuesta.mensaje || "La carga fue confirmada por el backend.",
            "ok"
        );
        confirmarBtn.disabled = true;
        eliminarReporteGuardado();
        archivoInput.value = "";
        fileName.hidden = true;
        mostrarSerpentinas();
    } catch (error) {
        cancelarProgreso();
        const detalle = error.detalle || error.message;
        mostrarResultado({}, detalle, "error");
        confirmarBtn.disabled = false;
    } finally {
        analizarBtn.disabled = false;
    }
});

limpiarBtn.addEventListener("click", () => {
    archivoInput.value = "";
    eliminarReporteGuardado();
    fileName.hidden = true;
    fileName.textContent = "";
    dropTitle.textContent = "Arrastra un archivo aquí o explora tu equipo";
    dropDescription.textContent = "La validación se ejecutará antes de guardar cualquier registro.";
    limpiarResultado();
});

actualizarAnalisisBtn.addEventListener("click", () => {
    if (archivoInput.files[0]) {
        cargaForm.requestSubmit();
        return;
    }

    seleccionarArchivoParaActualizar = true;
    resultadoMensaje.className = "carga-message visible";
    resultadoMensaje.textContent =
        "Para actualizar este análisis, vuelve a seleccionar el archivo original.";
    archivoInput.click();
});

async function restaurarReporteDesdeBackend() {
    try {
        const respuesta = await API.getReporteActivo();
        if (!respuesta.reporte) return;
        const archivo = {
            name: respuesta.archivo,
            size: 0,
            lastModified: 0
        };
        let reporte = respuesta.reporte;
        const guardado = localStorage.getItem(CLAVE_REPORTE_CARGA);
        if (guardado) {
            try {
                const local = JSON.parse(guardado);
                if (local.reporte?.id_carga === respuesta.id_carga) {
                    reporte = {...local.reporte, ...respuesta.reporte};
                }
            } catch (error) {
                console.warn("Se ignoró el resumen local inválido:", error);
            }
        }
        ultimoReporte = reporte;
        guardarReporte(reporte, archivo);
        mostrarArchivo(archivo);
        mostrarResultado(
            reporte,
            reporte.estado === "APTO"
                ? "El análisis apto está listo para confirmar la carga."
                : "Análisis restaurado desde el backend. Corrige las inconsistencias pendientes.",
            reporte.estado === "APTO" ? "ok" : "error"
        );
        renderizarReporte(reporte, archivo);
        confirmarBtn.disabled = reporte.estado !== "APTO";
    } catch (error) {
        console.error("No se pudo restaurar el análisis desde el backend:", error);
    }
}

restaurarReporteDesdeBackend().then(() => {
    if (!ultimoReporte) restaurarReporteGuardado();
});

if (new URLSearchParams(window.location.search).get("reanalizar") === "1") {
    resultadoMensaje.className = "carga-message visible";
    resultadoMensaje.textContent =
        "Selecciona nuevamente el archivo corregido y pulsa «Actualizar análisis» para comprobar los cambios antes de confirmar la carga.";
    window.history.replaceState({}, document.title, window.location.pathname);
}
