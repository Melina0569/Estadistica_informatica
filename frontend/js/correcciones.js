let correccionSeleccionada = null;
let detalleActual = [];
let paginaAuditoria = 1;
const correccion$ = (id) => document.getElementById(id);
const escCorreccion = (v) => String(v ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
function mostrarCorreccionMensaje(texto, error = false) { const el = correccion$("correcciones-mensaje"); el.textContent = texto; el.className = `correcciones-mensaje ${error ? "error" : "visible"}`; }
const ejemplosCorreccion = {
  "Modalidad de ingreso": "Ejemplo: Ordinario, CEPUSM o Traslado interno",
  "Modalidad de estudio (presencial, semipresencial)": "Ejemplo: Presencial",
  "Modalidad de estudio": "Ejemplo: Presencial",
  "Créditos matriculados en el semestre": "Ejemplo: 22",
  "Nota promedio / Promedio ponderado acumulado": "Ejemplo: 14.500",
  "Permanencia": "Ejemplo: 1",
  "Periodo de matrícula": "Ejemplo: 20241",
  "Primer periodo de matrícula": "Ejemplo: 20201",
  "Régimen de matrícula": "Ejemplo: S",
  "Nombres": "Ejemplo: María Fernanda"
};
function ejemploCorreccion(campo) {
  return ejemplosCorreccion[campo] || "Ejemplo: escribe el valor correcto para todos los registros";
}
function actualizarVistaCorreccion() {
  const input = correccion$("correccion-valor-comun");
  const preview = correccion$("correccion-valor-preview");
  if (!input || !preview) return;
  preview.textContent = input.value.trim() || "El nuevo valor aparecerá aquí";
}
function actualizarReporteLocal(campo, valor) {
  const clave = "dataunmsm.ultimoReporteCarga";
  const guardado = localStorage.getItem(clave);
  if (!guardado) return;
  try {
    const datos = JSON.parse(guardado);
    const reporte = datos.reporte;
    if (!reporte) return;
    const resumen = Array.isArray(reporte.resumen_inconsistencias)
      ? reporte.resumen_inconsistencias
      : [];
    const pendiente = resumen.find((item) => item.campo === campo);
    reporte.resumen_inconsistencias = resumen.filter((item) => item.campo !== campo);
    if (Array.isArray(reporte.inconsistencias)) {
      reporte.inconsistencias = reporte.inconsistencias.filter(
        (item) => item.campo !== campo
      );
    }
    reporte.total_inconsistencias = Math.max(
      0,
      Number(reporte.total_inconsistencias || 0) - Number(pendiente?.cantidad || 0)
    );
    reporte.correcciones_aplicadas = Array.isArray(reporte.correcciones_aplicadas)
      ? reporte.correcciones_aplicadas.filter((item) => item.campo !== campo)
      : [];
    reporte.correcciones_aplicadas.push({campo, valor});
    if (reporte.total_inconsistencias === 0) {
      reporte.estado = "APTO";
      reporte.siguiente_paso = "El archivo está apto para confirmar la carga.";
      if (Array.isArray(reporte.vista_previa?.filas)) {
        reporte.vista_previa.filas.forEach((fila) => {
          fila.estado = "Apto";
          fila.inconsistencias = 0;
        });
      }
    }
    localStorage.setItem(clave, JSON.stringify(datos));
  } catch (error) {
    console.error("No se pudo actualizar el reporte local:", error);
  }
}
async function cargarCorrecciones() {
  try {
    const [inconsistencias, documentos, auditoria] = await Promise.all([API.getInconsistencias(), API.getDocumentosPendientes(), API.getAuditoriaCorrecciones(paginaAuditoria)]);
    correccion$("total-inconsistencias").textContent = inconsistencias.total.toLocaleString("es-PE");
    const totalDocumentos = correccion$("total-documentos");
    if (totalDocumentos) totalDocumentos.textContent = documentos.documentos.length.toLocaleString("es-PE");
    correccion$("resumen-inconsistencias").textContent = `${inconsistencias.tipos} componente(s) requieren revisión.`;
    correccion$("lista-inconsistencias").innerHTML = inconsistencias.inconsistencias.length ? inconsistencias.inconsistencias.map((item, i) => item.origen === "archivo" ? `<button class="issue-row" data-index="${i}"><span><strong>${escCorreccion(item.severidad)} · ${escCorreccion(item.etiqueta)}</strong><small>${escCorreccion(item.cantidad)} registro(s) del archivo ${escCorreccion(item.archivo)}</small></span><span class="issue-count">${escCorreccion(item.cantidad)}</span><span class="material-symbols-outlined">edit_note</span></button>` : `<button class="issue-row" data-index="${i}"><span><strong>${escCorreccion(item.severidad)} · ${escCorreccion(item.etiqueta)}</strong><small>${escCorreccion(item.cantidad)} registro(s) con este campo pendiente</small></span><span class="issue-count">${escCorreccion(item.cantidad)}</span><span class="material-symbols-outlined">arrow_forward</span></button>`).join("") : "<div class=\"correcciones-completadas\"><span class=\"material-symbols-outlined\">task_alt</span><div><strong>No se detectaron inconsistencias.</strong><p>Vuelve a Carga de planillas para seleccionar el archivo, analizarlo nuevamente y confirmar la carga.</p><a class=\"correccion-button\" href=\"/frontend/paginas/carga/index.html?reanalizar=1\"><span class=\"material-symbols-outlined\">upload_file</span>Volver a Carga de planillas</a></div></div>";
    correccion$("lista-documentos").innerHTML = documentos.documentos.length ? documentos.documentos.map(item => `<div class="document-row"><div><strong>${escCorreccion(item.tipo_documento)}</strong><small>${escCorreccion(item.codigo_alumno || "Sin código")} · ${escCorreccion(item.responsable || "Sin responsable")}</small></div><span class="status-pill">${escCorreccion(item.estado)}</span></div>`).join("") : "<p class=\"empty-correction\">No hay documentos pendientes.</p>";
    correccion$("tabla-auditoria").innerHTML = auditoria.auditoria.length ? auditoria.auditoria.map(item => `<tr><td>${new Date(item.creado_en).toLocaleString("es-PE")}</td><td>${escCorreccion(item.tabla)} #${escCorreccion(item.id_registro)}</td><td>${escCorreccion(item.campo)}</td><td>${escCorreccion(item.anterior || "vacío")} → ${escCorreccion(item.nuevo || "vacío")}</td><td>${escCorreccion(item.motivo)}</td></tr>`).join("") : "<tr><td colspan=\"5\" class=\"empty-correction\">Aún no hay correcciones.</td></tr>";
    const paginacion = correccion$("paginacion-auditoria");
    if (paginacion) {
      paginacion.innerHTML = auditoria.paginas > 1
        ? `<button class="correccion-button secondary" type="button" id="auditoria-anterior" ${paginaAuditoria <= 1 ? "disabled" : ""}>Anterior</button><span>Página ${auditoria.pagina} de ${auditoria.paginas} · ${auditoria.total} corrección(es)</span><button class="correccion-button secondary" type="button" id="auditoria-siguiente" ${paginaAuditoria >= auditoria.paginas ? "disabled" : ""}>Siguiente</button>`
        : auditoria.total
          ? `<span>${auditoria.total} corrección(es)</span>`
          : "";
      paginacion.querySelector("#auditoria-anterior")?.addEventListener("click", () => {
        paginaAuditoria -= 1;
        cargarCorrecciones();
      });
      paginacion.querySelector("#auditoria-siguiente")?.addEventListener("click", () => {
        paginaAuditoria += 1;
        cargarCorrecciones();
      });
    }
    correccion$("lista-inconsistencias").querySelectorAll("button.issue-row").forEach(btn => btn.addEventListener("click", () => {
      const grupo = inconsistencias.inconsistencias[Number(btn.dataset.index)];
      if (grupo.origen === "archivo") abrirCorreccionArchivo(grupo);
      else abrirDetalle(grupo);
    }));
  } catch (error) { mostrarCorreccionMensaje(error.message, true); return false; }
  return true;
}
function abrirCorreccionArchivo(grupo) {
  correccionSeleccionada = grupo;
  detalleActual = [];
  correccion$("correccion-referencia").innerHTML = `<span class="dialog-context-icon material-symbols-outlined">upload_file</span><span><strong>${escCorreccion(grupo.etiqueta)}</strong><small>${escCorreccion(grupo.cantidad)} registros del archivo ${escCorreccion(grupo.archivo)}</small></span>`;
  correccion$("tabla-correccion-wrap").innerHTML = `<div class="dialog-intro">Define un valor único para corregir este campo en todos los registros detectados.</div><label class="bulk-value-label">Nuevo valor<input id="correccion-valor-comun" class="bulk-value" placeholder="${escCorreccion(ejemploCorreccion(grupo.campo))}" required/><small class="field-example">${escCorreccion(ejemploCorreccion(grupo.campo))}</small></label><div class="value-preview"><span>Vista previa</span><div><strong>Valor actual</strong><span class="preview-old">Vacío o inválido</span><span class="material-symbols-outlined">arrow_forward</span><strong>Nuevo valor</strong><span id="correccion-valor-preview" class="preview-new">El nuevo valor aparecerá aquí</span></div></div><p class="table-caption">La corrección se aplicará a los ${escCorreccion(grupo.cantidad)} registros cuando vuelvas a analizar el archivo.</p>`;
  correccion$("correccion-motivo").value = "";
  correccion$("correccion-valor-comun").addEventListener("input", actualizarVistaCorreccion);
  correccion$("correccion-dialog").showModal();
}
async function abrirDetalle(grupo) {
  const detalle = await API.getDetalleInconsistencia(grupo.tabla, grupo.campo);
  detalleActual = detalle.registros;
  correccion$("lista-inconsistencias").innerHTML = `<div class="detail-heading"><button class="back-button" id="volver-componentes"><span class="material-symbols-outlined">arrow_back</span> Componentes</button><strong>${escCorreccion(grupo.etiqueta)} · ${escCorreccion(grupo.cantidad)} registro(s)</strong></div><div class="bulk-actions"><button class="correccion-button" id="abrir-correccion-masiva"><span class="material-symbols-outlined">edit_note</span> Corregir conjunto</button></div>${detalle.registros.slice(0, 100).map(item => `<div class="issue-row detail-row"><span><strong>${escCorreccion(item.tabla)} #${escCorreccion(item.id)}</strong><small>${escCorreccion(item.campo)} · valor pendiente</small></span><span class="material-symbols-outlined">check_circle</span></div>`).join("")}${detalle.registros.length > 100 ? `<p class="empty-correction">Se muestran 100 de ${escCorreccion(detalle.registros.length)} registros en esta vista.</p>` : ""}`;
  correccion$("volver-componentes").addEventListener("click", cargarCorrecciones);
  correccion$("abrir-correccion-masiva").addEventListener("click", () => abrirCorreccion(grupo));
}
function abrirCorreccion(grupo) {
  correccionSeleccionada = grupo;
  correccion$("correccion-referencia").innerHTML = `<span class="dialog-context-icon material-symbols-outlined">edit_note</span><span><strong>${escCorreccion(grupo.etiqueta)}</strong><small>${escCorreccion(grupo.cantidad)} registros pendientes en la base de datos</small></span>`;
  correccion$("tabla-correccion-wrap").innerHTML = `<label class="bulk-value-label">Nuevo valor<input id="correccion-valor-comun" class="bulk-value" placeholder="${escCorreccion(ejemploCorreccion(grupo.campo))}" required/><small class="field-example">${escCorreccion(ejemploCorreccion(grupo.campo))}</small></label><div class="value-preview"><span>Vista previa</span><div><strong>Valor actual</strong><span class="preview-old">Vacío o inválido</span><span class="material-symbols-outlined">arrow_forward</span><strong>Nuevo valor</strong><span id="correccion-valor-preview" class="preview-new">El nuevo valor aparecerá aquí</span></div></div><p class="table-caption">Vista previa de ${Math.min(detalleActual.length, 100)} registros que serán actualizados:</p><table class="correction-table"><thead><tr><th>Registro</th><th>Campo</th></tr></thead><tbody>${detalleActual.slice(0, 100).map(item => `<tr><td>${escCorreccion(item.tabla)} #${escCorreccion(item.id)}</td><td>${escCorreccion(item.campo)}</td></tr>`).join("")}</tbody></table>`;
  correccion$("correccion-motivo").value = "";
  correccion$("correccion-valor-comun").addEventListener("input", actualizarVistaCorreccion);
  correccion$("correccion-dialog").showModal();
}
document.addEventListener("DOMContentLoaded", () => {
  correccion$("actualizar-correcciones")?.addEventListener("click", cargarCorrecciones);
  correccion$("form-correccion")?.addEventListener("submit", async (event) => { event.preventDefault(); const motivo = correccion$("correccion-motivo").value.trim(); const valorComun = correccion$("correccion-valor-comun")?.value.trim(); const correcciones = detalleActual.map(item => ({tabla: item.tabla, campo: item.campo, id: item.id})); if (!motivo || !valorComun || (!correcciones.length && !correccionSeleccionada?.origen)) { mostrarCorreccionMensaje("Indica un valor común y un motivo.", true); return; } try { if (correccionSeleccionada?.origen === "archivo") { await API.guardarCorreccionReporte({campo: correccionSeleccionada.campo, valor: valorComun, motivo}); actualizarReporteLocal(correccionSeleccionada.campo, valorComun); } else { await API.corregirRegistros({correcciones, valor_comun: valorComun, motivo}); } correccion$("correccion-dialog").close(); const actualizada = await cargarCorrecciones(); if (actualizada) mostrarCorreccionMensaje("Corrección guardada. Vuelve a Carga para revisar la vista previa actualizada y confirmar la carga."); } catch (error) { mostrarCorreccionMensaje(error.message, true); } });
  correccion$("cerrar-correccion")?.addEventListener("click", () => correccion$("correccion-dialog").close());
  correccion$("cancelar-correccion")?.addEventListener("click", () => correccion$("correccion-dialog").close());
  correccion$("correccion-dialog")?.addEventListener("click", event => { if (event.target === correccion$("correccion-dialog")) correccion$("correccion-dialog").close(); });
  correccion$("nuevo-documento")?.addEventListener("click", () => correccion$("documento-dialog").showModal());
  correccion$("cancelar-documento")?.addEventListener("click", () => correccion$("documento-dialog").close());
  correccion$("guardar-documento")?.addEventListener("click", async (event) => { event.preventDefault(); try { await API.crearDocumentoPendiente({ codigo_alumno: correccion$("documento-codigo").value, tipo_documento: correccion$("documento-tipo").value, descripcion: correccion$("documento-descripcion").value, responsable: correccion$("documento-responsable").value }); correccion$("documento-dialog").close(); const actualizada = await cargarCorrecciones(); if (actualizada) mostrarCorreccionMensaje("Documento pendiente registrado y vista actualizada."); } catch (error) { mostrarCorreccionMensaje(error.message, true); } });
  cargarCorrecciones();
});
