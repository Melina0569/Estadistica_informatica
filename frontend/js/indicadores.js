const indicador$ = (id) => document.getElementById(id);
let indicadoresDatos = null;
let opcionesIndicadores = null;
let estadoGrafico = null;

const formatoNumero = (valor) => Number(valor || 0).toLocaleString("es-PE");
const escaparIndicador = (valor) => String(valor ?? "").replace(/[&<>"']/g, (c) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
}[c]));

function mostrarMensajeIndicador(texto, tipo = "info") {
  const mensaje = indicador$("indicador-mensaje");
  mensaje.textContent = texto;
  mensaje.className = `indicator-message is-visible ${tipo}`;
}

function llenarSelect(id, filas, etiqueta) {
  indicador$(id).innerHTML = `<option value="">${etiqueta}</option>` +
    filas.map((fila) => (
      `<option value="${escaparIndicador(fila.valor || fila.nombre)}">${escaparIndicador(fila.texto || fila.nombre)}</option>`
    )).join("");
}

function actualizarFiltrosAcademicos() {
  const facultad = indicador$("builder-facultad").value;
  const programa = indicador$("builder-programa").value;
  const programas = (opcionesIndicadores.programas || []).filter((fila) => (
    !facultad || fila.facultad === facultad
  ));
  const carreras = (opcionesIndicadores.carreras || []).filter((fila) => (
    (!facultad || fila.facultad === facultad) &&
    (!programa || fila.programa === programa)
  ));
  llenarSelect("builder-programa", programas, "Todos los programas");
  if (programas.some((fila) => fila.valor === programa)) {
    indicador$("builder-programa").value = programa;
  }
  llenarSelect("builder-carrera", carreras, "Todas las carreras");
}

function pintarBarras(id, filas) {
  const maximo = Math.max(...filas.map((fila) => fila.total), 1);
  indicador$(id).innerHTML = filas.map((fila) => `
    <div class="bar-row">
      <span class="bar-label" title="${escaparIndicador(fila.nombre)}">${escaparIndicador(fila.nombre)}</span>
      <span class="bar-value">${formatoNumero(fila.total)}</span>
      <div class="bar-track"><div class="bar-fill" style="width:${fila.total / maximo * 100}%"></div></div>
    </div>
  `).join("") || "<p>No hay datos para mostrar.</p>";
}

function filasSeleccionadas() {
  const dimension = indicador$("builder-dimension").value;
  return dimension === "periodo"
    ? indicadoresDatos.por_periodo
    : dimension === "beca"
      ? indicadoresDatos.por_beca
      : indicadoresDatos.por_facultad;
}

function parametrosTabla() {
  return {
    tipo: indicador$("builder-tipo").value,
    dimension: indicador$("builder-dimension").value,
    metrica: indicador$("builder-metrica").value,
    facultad: indicador$("builder-facultad").value,
    programa: indicador$("builder-programa").value,
    carrera: indicador$("builder-carrera").value,
    genero: indicador$("builder-genero").value,
    beca: indicador$("builder-beca").value,
    periodo: indicador$("builder-periodo").value,
    modalidad: indicador$("builder-modalidad").value,
    nivel: indicador$("builder-nivel").value,
    ciclo: indicador$("builder-ciclo").value,
    buscar: indicador$("builder-buscar").value.trim(),
    columnas: [...document.querySelectorAll("#columnas-reporte input:checked")]
      .map((entrada) => entrada.value)
      .join(","),
  };
}

function datosGrafico(filas) {
  const metrica = indicador$("builder-metrica").value;
  const datos = filas.map((fila) => ({
    nombre: fila.nombre,
    valor: metrica === "participacion"
      ? Number(fila.participacion || 0)
      : Number(fila.total || 0),
  }));
  if (indicador$("builder-dimension").value === "periodo") {
    datos.sort((a, b) => String(a.nombre).localeCompare(String(b.nombre)));
  }
  return datos;
}

function dibujarGrafico(filas, seleccionado = null) {
  const contenedor = indicador$("grafico-indicador");
  const canvas = indicador$("canvas-indicador");
  const dimension = indicador$("builder-dimension").value;
  const tipoSolicitado = indicador$("builder-grafico").value;
  const tipo = tipoSolicitado === "lineas" && dimension !== "periodo"
    ? "barras"
    : tipoSolicitado;
  const datos = datosGrafico(filas).slice(0, 30);
  if (!datos.length) {
    contenedor.hidden = true;
    return;
  }

  const ancho = Math.max(720, Math.min(1200, contenedor.clientWidth || 900));
  const alto = tipo === "circular" ? 440 : tipo === "barras"
    ? Math.max(420, datos.length * 32 + 70)
    : 420;
  const escala = window.devicePixelRatio || 1;
  canvas.width = ancho * escala;
  canvas.height = alto * escala;
  canvas.style.width = `${ancho}px`;
  canvas.style.height = `${alto}px`;
  const contexto = canvas.getContext("2d");
  contexto.scale(escala, escala);
  contexto.clearRect(0, 0, ancho, alto);
  contexto.font = '12px Inter, sans-serif';
  contexto.fillStyle = "#091426";
  const colores = ["#0058be", "#2170e4", "#50a2ff", "#06a77d", "#f59e0b", "#d9485f"];
  const total = datos.reduce((suma, fila) => suma + fila.valor, 0) || 1;
  estadoGrafico = { datos, filas, colores, total, tipo, ancho, alto, seleccionado };

  if (tipo === "circular") {
    const centroX = ancho / 2;
    const centroY = alto / 2;
    const radio = Math.min(145, alto / 2 - 35);
    let inicio = -Math.PI / 2;
    datos.forEach((fila, indice) => {
      const arco = fila.valor / total * Math.PI * 2;
      contexto.beginPath();
      contexto.moveTo(centroX, centroY);
      contexto.arc(centroX, centroY, radio, inicio, inicio + arco);
      contexto.closePath();
      contexto.fillStyle = colores[indice % colores.length];
      if (seleccionado === indice) {
        contexto.shadowColor = "#091426";
        contexto.shadowBlur = 12;
      }
      contexto.fill();
      contexto.shadowBlur = 0;
      inicio += arco;
    });
  } else if (tipo === "barras") {
    const margen = { arriba: 25, derecha: 85, abajo: 25, izquierda: 190 };
    const anchoPlot = ancho - margen.izquierda - margen.derecha;
    const maximo = Math.max(...datos.map((fila) => fila.valor), 1);
    datos.forEach((fila, indice) => {
      const y = margen.arriba + indice * 32;
      const anchoBarra = fila.valor / maximo * anchoPlot;
      contexto.fillStyle = "#091426";
      contexto.textAlign = "right";
      contexto.fillText(String(fila.nombre).slice(0, 28), margen.izquierda - 12, y + 16);
      contexto.textAlign = "left";
      contexto.fillStyle = "#eaf1fc";
      contexto.fillRect(margen.izquierda, y + 4, anchoPlot, 18);
      contexto.fillStyle = colores[indice % colores.length];
      contexto.fillRect(margen.izquierda, y + 4, anchoBarra, 18);
      contexto.fillStyle = "#091426";
      contexto.font = '600 12px "JetBrains Mono", monospace';
      contexto.fillText(formatoNumero(fila.valor), margen.izquierda + anchoBarra + 8, y + 18);
      contexto.font = '12px Inter, sans-serif';
    });
  } else {
    const margen = { arriba: 25, derecha: 25, abajo: tipo === "lineas" ? 70 : 55, izquierda: 55 };
    const anchoPlot = ancho - margen.izquierda - margen.derecha;
    const altoPlot = alto - margen.arriba - margen.abajo;
    const maximo = Math.max(...datos.map((fila) => fila.valor), 1);
    contexto.strokeStyle = "#dbe5f3";
    contexto.lineWidth = 1;
    for (let i = 0; i <= 4; i += 1) {
      const y = margen.arriba + altoPlot - (altoPlot * i / 4);
      contexto.beginPath();
      contexto.moveTo(margen.izquierda, y);
      contexto.lineTo(ancho - margen.derecha, y);
      contexto.stroke();
      contexto.fillStyle = "#68758a";
      contexto.fillText(formatoNumero(maximo * i / 4), 8, y + 4);
    }
    const paso = anchoPlot / Math.max(datos.length, 1);
    if (tipo === "lineas") {
      contexto.strokeStyle = "#0058be";
      contexto.lineWidth = 3;
      contexto.beginPath();
      datos.forEach((fila, indice) => {
        const x = margen.izquierda + paso * indice + paso / 2;
        const y = margen.arriba + altoPlot - fila.valor / maximo * altoPlot;
        indice ? contexto.lineTo(x, y) : contexto.moveTo(x, y);
      });
      contexto.stroke();
    }
    datos.forEach((fila, indice) => {
      const x = margen.izquierda + paso * indice + paso / 2;
      const altura = fila.valor / maximo * altoPlot;
      const y = margen.arriba + altoPlot - altura;
      contexto.fillStyle = tipo === "lineas" ? "#2170e4" : colores[indice % colores.length];
      if (tipo === "lineas") {
        contexto.beginPath();
        contexto.arc(x, y, 4, 0, Math.PI * 2);
        contexto.fill();
      } else {
        contexto.fillRect(x - Math.max(4, paso * .3), y, Math.max(8, paso * .6), altura);
      }
      contexto.save();
      contexto.translate(x, alto - 18);
      contexto.rotate(-Math.PI / 5);
      contexto.fillStyle = "#091426";
      contexto.fillText(String(fila.nombre).slice(0, 18), 0, 0);
      contexto.restore();
    });
  }
  indicador$("leyenda-grafico").innerHTML = datos.map((fila, indice) => `
    <button class="chart-legend-item${seleccionado === indice ? " is-selected" : ""}" type="button" data-grafico-indice="${indice}">
      <span class="chart-legend-color" style="background:${colores[indice % colores.length]}"></span>
      <span class="chart-legend-name">${escaparIndicador(fila.nombre)}</span>
      <span class="chart-legend-value">${formatoNumero(fila.valor)}</span>
      <span class="chart-legend-percent">${(fila.valor / total * 100).toFixed(2)}%</span>
    </button>
  `).join("");
  document.querySelectorAll("[data-grafico-indice]").forEach((elemento) => {
    elemento.addEventListener("click", () => dibujarGrafico(filas, Number(elemento.dataset.graficoIndice)));
  });
  contenedor.hidden = false;
  if (tipoSolicitado === "lineas" && dimension !== "periodo") {
    mostrarMensajeIndicador("Para dimensiones categóricas se muestran barras, que permiten comparar mejor los valores.");
  }
}

function mostrarTooltipGrafico(indice, x, y) {
  const tooltip = indicador$("grafico-tooltip");
  const fila = estadoGrafico?.datos[indice];
  if (!fila) {
    tooltip.hidden = true;
    return;
  }
  tooltip.innerHTML = `<strong>${escaparIndicador(fila.nombre)}</strong><br>${formatoNumero(fila.valor)} · ${(fila.valor / estadoGrafico.total * 100).toFixed(2)}%`;
  tooltip.style.left = `${x + 14}px`;
  tooltip.style.top = `${y + 14}px`;
  tooltip.hidden = false;
}

function indiceGraficoEnPunto(evento) {
  if (!estadoGrafico) return null;
  const canvas = indicador$("canvas-indicador");
  const rect = canvas.getBoundingClientRect();
  const x = (evento.clientX - rect.left) * canvas.width / rect.width / (window.devicePixelRatio || 1);
  const y = (evento.clientY - rect.top) * canvas.height / rect.height / (window.devicePixelRatio || 1);
  if (estadoGrafico.tipo === "circular") {
    const centroX = estadoGrafico.ancho / 2;
    const centroY = estadoGrafico.alto / 2;
    const distancia = Math.hypot(x - centroX, y - centroY);
    if (distancia > 150) return null;
    let angulo = Math.atan2(y - centroY, x - centroX) + Math.PI / 2;
    if (angulo < 0) angulo += Math.PI * 2;
    let acumulado = 0;
    for (let indice = 0; indice < estadoGrafico.datos.length; indice += 1) {
      acumulado += estadoGrafico.datos[indice].valor / estadoGrafico.total * Math.PI * 2;
      if (angulo <= acumulado) return indice;
    }
  }
  return null;
}

function descargarGrafico() {
  if (!estadoGrafico) return;
  const { datos, colores, total, tipo, seleccionado } = estadoGrafico;
  const exportCanvas = document.createElement("canvas");
  const ancho = 1400;
  const alto = tipo === "circular" ? Math.max(850, 260 + datos.length * 42) : 900;
  exportCanvas.width = ancho * 2;
  exportCanvas.height = alto * 2;
  const contexto = exportCanvas.getContext("2d");
  contexto.scale(2, 2);
  contexto.fillStyle = "#ffffff";
  contexto.fillRect(0, 0, ancho, alto);
  contexto.fillStyle = "#123b63";
  contexto.font = '700 26px Inter, sans-serif';
  contexto.fillText("Indicadores y reportes", 50, 55);
  contexto.font = '16px Inter, sans-serif';
  contexto.fillStyle = "#68758a";
  contexto.fillText("Distribución por categorías", 50, 82);

  if (tipo === "circular") {
    const centroX = 410;
    const centroY = 315;
    const radio = 205;
    let inicio = -Math.PI / 2;
    datos.forEach((fila, indice) => {
      const arco = fila.valor / total * Math.PI * 2;
      contexto.beginPath();
      contexto.moveTo(centroX, centroY);
      contexto.arc(centroX, centroY, radio, inicio, inicio + arco);
      contexto.closePath();
      contexto.fillStyle = colores[indice % colores.length];
      contexto.fill();
      inicio += arco;
    });
    if (seleccionado !== null) {
      const fila = datos[seleccionado];
      contexto.fillStyle = "#ffffff";
      contexto.fillRect(centroX - 150, 18, 300, 42);
      contexto.strokeStyle = colores[seleccionado % colores.length];
      contexto.strokeRect(centroX - 150, 18, 300, 42);
      contexto.fillStyle = "#091426";
      contexto.textAlign = "center";
      contexto.font = '600 12px Inter, sans-serif';
      contexto.fillText(
        `${String(fila.nombre).slice(0, 34)} · ${(fila.valor / total * 100).toFixed(2)}%`,
        centroX,
        44,
      );
      contexto.textAlign = "left";
    }
    datos.forEach((fila, indice) => {
      const y = 125 + indice * 42;
      contexto.fillStyle = colores[indice % colores.length];
      contexto.fillRect(760, y - 14, 18, 18);
      contexto.fillStyle = "#091426";
      contexto.font = '15px Inter, sans-serif';
      contexto.fillText(`${fila.nombre} — ${formatoNumero(fila.valor)} (${(fila.valor / total * 100).toFixed(2)}%)`, 790, y);
    });
  } else {
    datos.forEach((fila, indice) => {
      const y = 130 + indice * 24;
      const anchoBarra = fila.valor / Math.max(...datos.map((item) => item.valor), 1) * 760;
      contexto.fillStyle = "#091426";
      contexto.font = '13px Inter, sans-serif';
      contexto.fillText(String(fila.nombre).slice(0, 45), 50, y + 13);
      contexto.fillStyle = colores[indice % colores.length];
      contexto.fillRect(300, y, anchoBarra, 18);
      contexto.fillStyle = "#091426";
      contexto.fillText(formatoNumero(fila.valor), 1080, y + 14);
    });
  }
  const enlace = document.createElement("a");
  enlace.download = "grafico_indicadores.png";
  enlace.href = exportCanvas.toDataURL("image/png");
  document.body.appendChild(enlace);
  enlace.click();
  enlace.remove();
}

function renderizarDetalle(datos) {
  const columnas = datos.columnas || [];
  return `
    <table>
      <thead><tr>${columnas.map((columna) => `<th>${escaparIndicador(columna)}</th>`).join("")}</tr></thead>
      <tbody>${(datos.filas || []).map((fila) => `
        <tr>${columnas.map((columna) => `<td>${escaparIndicador(fila[columna])}</td>`).join("")}</tr>
      `).join("")}</tbody>
    </table>
  `;
}

async function descargarTablaIndicadores() {
  try {
    const descarga = await API.descargarIndicadores(parametrosTabla());
    const enlace = document.createElement("a");
    enlace.href = URL.createObjectURL(descarga.archivo);
    enlace.download = descarga.nombre;
    enlace.click();
    URL.revokeObjectURL(enlace.href);
    mostrarMensajeIndicador("El archivo Excel se descargó correctamente.");
  } catch (error) {
    console.error("Error al exportar indicadores:", error);
    mostrarMensajeIndicador(error.message || "No se pudo exportar el indicador.", "error");
  }
}

async function generarTabla({ desplazar = true } = {}) {
  const tabla = indicador$("tabla-indicador");

  try {
    const datos = await API.getTablaIndicadores(parametrosTabla());
    if (datos.tipo === "detalle") {
      if (!datos.filas?.length) {
        tabla.hidden = true;
        estadoGrafico = null;
        mostrarMensajeIndicador("No hay registros con los filtros seleccionados.", "error");
        return;
      }
      tabla.innerHTML = renderizarDetalle(datos);
      tabla.hidden = false;
      indicador$("grafico-indicador").hidden = true;
      estadoGrafico = null;
      mostrarMensajeIndicador(
        `Reporte detallado generado: ${formatoNumero(datos.total)} registros.`
      );
      if (desplazar) {
        tabla.scrollIntoView({ behavior: "smooth", block: "nearest" });
      }
      return;
    }
    const filas = datos.filas || [];
    const metrica = datos.metrica;
    if (!filas.length) {
      tabla.hidden = true;
      mostrarMensajeIndicador("No hay datos con los filtros seleccionados.", "error");
      return;
    }

    const encabezado = metrica === "participacion" ? "Participación" : "Total";
    tabla.innerHTML = `
      <table>
        <thead><tr><th>Dimensión</th><th>${encabezado}</th></tr></thead>
        <tbody>${filas.map((fila) => `
          <tr><td>${escaparIndicador(fila.nombre)}</td><td>${
            metrica === "participacion"
              ? `${fila.participacion.toFixed(2)}%`
              : formatoNumero(fila.total)
          }</td></tr>
        `).join("")}</tbody>
        <tfoot><tr><th>Total</th><th>${
          metrica === "participacion" ? "100%" : formatoNumero(datos.total)
        }</th></tr></tfoot>
      </table>
    `;
    tabla.hidden = false;
    dibujarGrafico(filas);
    mostrarMensajeIndicador(
      `Tabla generada correctamente: ${filas.length} categorías y ${formatoNumero(datos.total)} estudiantes.`
    );
    if (desplazar) {
      tabla.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  } catch (error) {
    console.error("Error al generar tabla:", error);
    tabla.hidden = true;
    mostrarMensajeIndicador(error.message || "No se pudo generar la tabla.", "error");
  }
}

function pintarIndicadores(datos) {
  indicadoresDatos = datos;
  const kpis = datos.kpis;
  indicador$("kpi-estudiantes").textContent = formatoNumero(kpis.estudiantes);
  indicador$("kpi-ingresos").textContent = formatoNumero(kpis.programas);
  indicador$("kpi-matriculas").textContent = formatoNumero(kpis.matriculas);
  indicador$("kpi-facultades").textContent =
    formatoNumero(kpis.facultades);
  Object.entries(datos.modulos).forEach(([modulo, total]) => {
    const nodo = indicador$(`modulo-${modulo}`);
    if (nodo) nodo.textContent = formatoNumero(total);
  });
  pintarBarras("facultades-chart", datos.por_facultad);
  pintarBarras("periodos-chart", datos.por_periodo);
  const totalBecas = datos.por_beca.reduce((total, fila) => total + Number(fila.total || 0), 0);
  indicador$("becas-list").innerHTML = datos.por_beca.map((fila, indice) => {
    const porcentaje = totalBecas ? (Number(fila.total || 0) / totalBecas) * 100 : 0;
    return `
      <div class="legend-row beca-row">
        <span class="legend-row-dot color-${indice % 5}"></span>
        <span class="legend-row-name">${escaparIndicador(fila.nombre)}</span>
        <strong>${formatoNumero(fila.total)}</strong>
        <small>${porcentaje.toFixed(2)}%</small>
        <span class="legend-row-track"><span style="width:${porcentaje}%"></span></span>
      </div>
    `;
  }).join("");
  generarTabla({ desplazar: false });
}

async function cargarIndicadores() {
  try {
    const datos = await API.getIndicadores({
      facultad: indicador$("filtro-facultad").value,
      periodo: indicador$("filtro-periodo").value
    });
    pintarIndicadores(datos);
  } catch (error) {
    console.error("Error al cargar indicadores:", error);
    mostrarMensajeIndicador(error.message || "No se pudieron cargar los indicadores.", "error");
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  try {
    await Promise.all([
      cargarComponente("sidebar", "/frontend/components/sidebar.html"),
      cargarComponente("header", "/frontend/components/header.html")
    ]);
    marcarNavActivo();
    iniciarReloj();
    const opciones = await API.opcionesConsulta();
    opcionesIndicadores = opciones;
    llenarSelect("filtro-facultad", opciones.facultades, "Todas las facultades");
    llenarSelect("filtro-periodo", opciones.periodos, "Todos los periodos");
    llenarSelect("builder-facultad", opciones.facultades, "Todas las facultades");
    llenarSelect("builder-programa", opciones.programas, "Todos los programas");
    llenarSelect("builder-carrera", opciones.carreras, "Todas las carreras");
    llenarSelect("builder-genero", opciones.generos, "Todos los géneros");
    llenarSelect("builder-beca", opciones.becas, "Todas las becas");
    llenarSelect("builder-periodo", opciones.periodos, "Todos los periodos");
    llenarSelect("builder-modalidad", opciones.estados_matricula, "Todas las modalidades");
    llenarSelect("builder-nivel", opciones.niveles, "Todos los niveles");
    llenarSelect("builder-ciclo", opciones.ciclos, "Todos los ciclos");
    await cargarIndicadores();
    indicador$("actualizar-indicadores").addEventListener("click", cargarIndicadores);
    indicador$("limpiar-indicadores").addEventListener("click", () => {
      indicador$("filtro-facultad").value = "";
      indicador$("filtro-periodo").value = "";
      cargarIndicadores();
    });
    indicador$("filtro-facultad").addEventListener("change", cargarIndicadores);
    indicador$("filtro-periodo").addEventListener("change", cargarIndicadores);
    indicador$("builder-dimension").addEventListener("change", generarTabla);
    indicador$("builder-metrica").addEventListener("change", generarTabla);
    indicador$("builder-tipo").addEventListener("change", generarTabla);
    indicador$("builder-grafico").addEventListener("change", generarTabla);
    indicador$("descargar-grafico").addEventListener("click", descargarGrafico);
    indicador$("canvas-indicador").addEventListener("mousemove", (evento) => {
      const indice = indiceGraficoEnPunto(evento);
      const rect = evento.currentTarget.getBoundingClientRect();
      mostrarTooltipGrafico(indice, evento.clientX - rect.left, evento.clientY - rect.top);
    });
    indicador$("canvas-indicador").addEventListener("mouseleave", () => {
      indicador$("grafico-tooltip").hidden = true;
    });
    indicador$("canvas-indicador").addEventListener("click", (evento) => {
      const indice = indiceGraficoEnPunto(evento);
      if (indice !== null) {
        dibujarGrafico(estadoGrafico.filas, indice);
        const rect = evento.currentTarget.getBoundingClientRect();
        mostrarTooltipGrafico(indice, evento.clientX - rect.left, evento.clientY - rect.top);
      }
    });
    [
      "builder-genero",
      "builder-beca",
      "builder-periodo",
      "builder-modalidad",
      "builder-nivel",
      "builder-ciclo",
    ].forEach((id) => indicador$(id).addEventListener("change", generarTabla));
    indicador$("builder-facultad").addEventListener("change", () => {
      indicador$("builder-programa").value = "";
      indicador$("builder-carrera").value = "";
      actualizarFiltrosAcademicos();
      generarTabla();
    });
    indicador$("builder-programa").addEventListener("change", () => {
      indicador$("builder-carrera").value = "";
      actualizarFiltrosAcademicos();
      generarTabla();
    });
    indicador$("builder-carrera").addEventListener("change", generarTabla);
    indicador$("builder-buscar").addEventListener("keydown", (evento) => {
      if (evento.key === "Enter") generarTabla();
    });
    indicador$("generar-indicador").addEventListener("click", generarTabla);
    indicador$("exportar-indicador").addEventListener("click", descargarTablaIndicadores);
  } catch (error) {
    console.error("Error al inicializar indicadores:", error);
    mostrarMensajeIndicador(error.message || "No se pudo inicializar el módulo.", "error");
  }
});
