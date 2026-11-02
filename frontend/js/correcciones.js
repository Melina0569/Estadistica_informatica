let correccionSeleccionada = null;
let detalleActual = [];
const correccion$ = (id) => document.getElementById(id);
const escCorreccion = (v) => String(v ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
function mostrarCorreccionMensaje(texto, error = false) { const el = correccion$("correcciones-mensaje"); el.textContent = texto; el.className = `correcciones-mensaje ${error ? "error" : "visible"}`; }
async function cargarCorrecciones() {
  try {
    const [inconsistencias, documentos, auditoria] = await Promise.all([API.getInconsistencias(), API.getDocumentosPendientes(), API.getAuditoriaCorrecciones()]);
    correccion$("total-inconsistencias").textContent = inconsistencias.total.toLocaleString("es-PE");
    correccion$("resumen-inconsistencias").textContent = `${inconsistencias.tipos} componente(s) requieren revisión.`;
    correccion$("lista-inconsistencias").innerHTML = inconsistencias.inconsistencias.length ? inconsistencias.inconsistencias.map((item, i) => `<button class="issue-row" data-index="${i}"><span><strong>${escCorreccion(item.severidad)} · ${escCorreccion(item.etiqueta)}</strong><small>${escCorreccion(item.cantidad)} registro(s) con este campo pendiente</small></span><span class="issue-count">${escCorreccion(item.cantidad)}</span><span class="material-symbols-outlined">arrow_forward</span></button>`).join("") : "<p class=\"empty-correction\">No se detectaron inconsistencias.</p>";
    correccion$("lista-documentos").innerHTML = documentos.documentos.length ? documentos.documentos.map(item => `<div class="document-row"><div><strong>${escCorreccion(item.tipo_documento)}</strong><small>${escCorreccion(item.codigo_alumno || "Sin código")} · ${escCorreccion(item.responsable || "Sin responsable")}</small></div><span class="status-pill">${escCorreccion(item.estado)}</span></div>`).join("") : "<p class=\"empty-correction\">No hay documentos pendientes.</p>";
    correccion$("tabla-auditoria").innerHTML = auditoria.auditoria.length ? auditoria.auditoria.map(item => `<tr><td>${new Date(item.creado_en).toLocaleString("es-PE")}</td><td>${escCorreccion(item.tabla)} #${escCorreccion(item.id_registro)}</td><td>${escCorreccion(item.campo)}</td><td>${escCorreccion(item.anterior || "vacío")} → ${escCorreccion(item.nuevo || "vacío")}</td><td>${escCorreccion(item.motivo)}</td></tr>`).join("") : "<tr><td colspan=\"5\" class=\"empty-correction\">Aún no hay correcciones.</td></tr>";
    correccion$("lista-inconsistencias").querySelectorAll(".issue-row").forEach(btn => btn.addEventListener("click", () => abrirDetalle(inconsistencias.inconsistencias[Number(btn.dataset.index)])));
  } catch (error) { mostrarCorreccionMensaje(error.message, true); }
}
async function abrirDetalle(grupo) {
  const detalle = await API.getDetalleInconsistencia(grupo.tabla, grupo.campo);
  detalleActual = detalle.registros;
  correccion$("lista-inconsistencias").innerHTML = `<div class="detail-heading"><button class="back-button" id="volver-componentes"><span class="material-symbols-outlined">arrow_back</span> Componentes</button><strong>${escCorreccion(grupo.etiqueta)} · ${escCorreccion(grupo.cantidad)} registro(s)</strong></div><div class="bulk-actions"><button class="correccion-button" id="abrir-correccion-masiva"><span class="material-symbols-outlined">edit_note</span> Corregir conjunto</button></div>${detalle.registros.slice(0, 100).map(item => `<div class="issue-row detail-row"><span><strong>${escCorreccion(item.tabla)} #${escCorreccion(item.id)}</strong><small>${escCorreccion(item.campo)} · valor vacío</small></span><span class="material-symbols-outlined">check_circle</span></div>`).join("")}${detalle.registros.length > 100 ? `<p class="empty-correction">Se muestran 100 de ${escCorreccion(detalle.registros.length)} registros en esta vista.</p>` : ""}`;
  correccion$("volver-componentes").addEventListener("click", cargarCorrecciones);
  correccion$("abrir-correccion-masiva").addEventListener("click", () => abrirCorreccion(grupo));
}
function abrirCorreccion(grupo) {
  correccionSeleccionada = grupo;
  correccion$("correccion-referencia").textContent = `${grupo.etiqueta} · ${grupo.cantidad} registro(s)`;
  correccion$("tabla-correccion-wrap").innerHTML = `<label class="bulk-value-label">Valor que se aplicará a los ${escCorreccion(grupo.cantidad)} registros<input id="correccion-valor-comun" class="bulk-value" placeholder="Ej. Presencial" required/></label><p class="table-caption">Vista previa de ${Math.min(detalleActual.length, 100)} registros que serán actualizados:</p><table class="correction-table"><thead><tr><th>Registro</th><th>Campo</th></tr></thead><tbody>${detalleActual.slice(0, 100).map(item => `<tr><td>${escCorreccion(item.tabla)} #${escCorreccion(item.id)}</td><td>${escCorreccion(item.campo)}</td></tr>`).join("")}</tbody></table>`;
  correccion$("correccion-motivo").value = "";
  correccion$("correccion-dialog").showModal();
}
document.addEventListener("DOMContentLoaded", () => {
  correccion$("actualizar-correcciones")?.addEventListener("click", cargarCorrecciones);
  correccion$("form-correccion")?.addEventListener("submit", async (event) => { event.preventDefault(); const motivo = correccion$("correccion-motivo").value.trim(); const valorComun = correccion$("correccion-valor-comun")?.value.trim(); const correcciones = detalleActual.map(item => ({tabla: item.tabla, campo: item.campo, id: item.id})); if (!motivo || !valorComun || !correcciones.length) { mostrarCorreccionMensaje("Indica un valor común y un motivo.", true); return; } try { await API.corregirRegistros({correcciones, valor_comun: valorComun, motivo}); correccion$("correccion-dialog").close(); mostrarCorreccionMensaje(`${correcciones.length} correcciones guardadas y auditadas.`); cargarCorrecciones(); } catch (error) { mostrarCorreccionMensaje(error.message, true); } });
  correccion$("cerrar-correccion")?.addEventListener("click", () => correccion$("correccion-dialog").close());
  correccion$("cancelar-correccion")?.addEventListener("click", () => correccion$("correccion-dialog").close());
  correccion$("correccion-dialog")?.addEventListener("click", event => { if (event.target === correccion$("correccion-dialog")) correccion$("correccion-dialog").close(); });
  correccion$("nuevo-documento")?.addEventListener("click", () => correccion$("documento-dialog").showModal());
  correccion$("guardar-documento")?.addEventListener("click", async (event) => { event.preventDefault(); try { await API.crearDocumentoPendiente({ codigo_alumno: correccion$("documento-codigo").value, tipo_documento: correccion$("documento-tipo").value, descripcion: correccion$("documento-descripcion").value, responsable: correccion$("documento-responsable").value }); correccion$("documento-dialog").close(); mostrarCorreccionMensaje("Documento pendiente registrado."); cargarCorrecciones(); } catch (error) { mostrarCorreccionMensaje(error.message, true); } });
  cargarCorrecciones();
});
