const consulta$ = (id) => document.getElementById(id);
let consultaPaginaActual = 1;
let consultaTotalPaginas = 1;

function escConsulta(valor) {
  return String(valor ?? "").replace(/[&<>"']/g, (caracter) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[caracter]));
}

function parametrosConsulta() {
  const carga = new URLSearchParams(location.search).get("carga");
  return {
    q: consulta$("consulta-q").value.trim(),
    periodo: consulta$("consulta-periodo").value.trim(),
    programa: consulta$("consulta-programa").value.trim(),
    facultad: consulta$("consulta-facultad").value.trim(),
    estado_matricula: consulta$("consulta-estado").value.trim(),
    condicion: consulta$("consulta-condicion").value.trim(),
    carga,
    page: consultaPaginaActual,
    per_page: 20
  };
}

function actualizarResumenFiltros() {
  const ids = [
    "consulta-q",
    "consulta-facultad",
    "consulta-estado",
    "consulta-condicion",
    "consulta-periodo",
    "consulta-programa"
  ];
  const activos = ids.filter((id) => consulta$(id).value.trim()).length;
  consulta$("consulta-filtro-resumen").textContent =
    `Filtros activos: ${activos}`;
}

async function cargarConsultas() {
  const cuerpo = consulta$("consulta-tbody");
  cuerpo.innerHTML = '<tr><td colspan="6" class="empty-state">Consultando registros...</td></tr>';

  try {
    const resultado = await API.consultarEstudiantes(parametrosConsulta());
    consultaTotalPaginas = Math.max(resultado.pages || 1, 1);
    consulta$("consulta-contador").textContent = `${resultado.total || 0} registros encontrados`;
    consulta$("consulta-pagina").textContent = `Página ${resultado.page} de ${consultaTotalPaginas}`;
    consulta$("consulta-anterior").disabled = resultado.page <= 1;
    consulta$("consulta-siguiente").disabled = resultado.page >= consultaTotalPaginas;
    const carga = resultado.carga;
    const descripcion = document.getElementById("consulta-carga");
    if (descripcion) {
      descripcion.textContent = carga
        ? `Registros de la carga: ${carga.nombre}`
        : "Todos los registros cargados";
    }

    if (!resultado.estudiantes.length) {
      cuerpo.innerHTML = '<tr><td colspan="6" class="empty-state">No se encontraron registros.</td></tr>';
      return;
    }

    cuerpo.innerHTML = resultado.estudiantes.map((estudiante) => `
      <tr class="hover:bg-surface-container-low transition-colors">
        <td class="py-space-sm px-space-md">
          <img
            src="/frontend/assets/icons/Estudiante.png"
            alt="Estudiante"
            class="consulta-imagen"
            title="Imagen del estudiante"
          >
        </td>
        <td class="py-space-sm px-space-md font-data-mono text-data-mono text-primary">${escConsulta(estudiante.id_codigo_alumno)}</td>
        <td class="py-space-sm px-space-md font-medium">${escConsulta(estudiante.nombre_completo)}</td>
        <td class="py-space-sm px-space-md">${escConsulta(estudiante.num_dni)}</td>
        <td class="py-space-sm px-space-md">${escConsulta(estudiante.correo_inst)}</td>
        <td class="py-space-sm px-space-md text-right">
          <a class="action-btn" href="/frontend/paginas/estudiantes/detalle.html?id=${encodeURIComponent(estudiante.id_codigo_alumno)}">
            Ver detalle <span class="material-symbols-outlined text-sm">open_in_new</span>
          </a>
        </td>
      </tr>
    `).join("");
  } catch (error) {
    console.error("Error al consultar registros:", error);
    consulta$("consulta-contador").textContent = "";
    cuerpo.innerHTML = '<tr><td colspan="6" class="empty-state">No se pudieron consultar los registros.</td></tr>';
  }
}

function llenarOpciones(id, opciones, etiqueta) {
  const campo = consulta$(id);
  campo.innerHTML = `<option value="">${etiqueta}</option>` +
    opciones.map((opcion) => (
      `<option value="${escConsulta(opcion.valor)}">${escConsulta(opcion.texto)}</option>`
    )).join("");
}

async function cargarOpcionesConsulta() {
  const opciones = await API.opcionesConsulta();
  llenarOpciones("consulta-facultad", opciones.facultades, "Todas las facultades");
  llenarOpciones("consulta-programa", opciones.programas, "Todos los programas");
  llenarOpciones("consulta-periodo", opciones.periodos, "Todos los semestres");
  llenarOpciones("consulta-estado", opciones.estados_matricula, "Todos los estados");
  llenarOpciones("consulta-condicion", opciones.condiciones, "Todas las condiciones");

  const modulos = opciones.modulos;
  document.querySelector("[data-modulo='estudiantes'] small").textContent =
    Number(modulos.estudiantes).toLocaleString("es-PE");
  document.querySelector("[data-modulo='docentes'] small").textContent =
    Number(modulos.docentes).toLocaleString("es-PE");
  document.querySelector("[data-modulo='administrativos'] small").textContent =
    Number(modulos.administrativos).toLocaleString("es-PE");
  document.querySelector("[data-modulo='egresados'] small").textContent =
    Number(modulos.egresados_titulados).toLocaleString("es-PE");
}

document.addEventListener("DOMContentLoaded", async () => {
  await Promise.all([
    cargarComponente("sidebar", "/frontend/components/sidebar.html"),
    cargarComponente("header", "/frontend/components/header.html")
  ]);
  marcarNavActivo();
  iniciarReloj();
  await cargarOpcionesConsulta();
  consulta$("consulta-form").addEventListener("submit", (evento) => {
    evento.preventDefault();
    consultaPaginaActual = 1;
    cargarConsultas();
  });
  consulta$("consulta-limpiar").addEventListener("click", () => {
    consulta$("consulta-form").reset();
    consultaPaginaActual = 1;
    actualizarResumenFiltros();
    cargarConsultas();
  });
  consulta$("consulta-anterior").addEventListener("click", () => {
    if (consultaPaginaActual > 1) {
      consultaPaginaActual -= 1;
      cargarConsultas();
    }
  });
  consulta$("consulta-siguiente").addEventListener("click", () => {
    if (consultaPaginaActual < consultaTotalPaginas) {
      consultaPaginaActual += 1;
      cargarConsultas();
    }
  });
  document.querySelectorAll("#consulta-form input").forEach((campo) => {
    campo.addEventListener("input", actualizarResumenFiltros);
  });
  actualizarResumenFiltros();
  cargarConsultas();
});
