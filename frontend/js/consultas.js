const consulta$ = (id) => document.getElementById(id);
let consultaPaginaActual = 1;
let consultaTotalPaginas = 1;
let estudianteEdicionActual = null;
let datosEdicionActual = null;

const CAMPOS_EDITABLES = {
  estudiante: [
    ["tipo_doc_id", "Tipo de documento"], ["num_dni", "Número de documento"],
    ["apellido_pat", "Apellido paterno"], ["apellido_mat", "Apellido materno"],
    ["nombres", "Nombres"], ["sexo", "Sexo"], ["fecha_nac", "Fecha de nacimiento"],
    ["anio_fin_sec", "Año de fin de secundaria"], ["nacionalidad", "Nacionalidad"],
    ["estado_civil", "Estado civil"], ["correo_inst", "Correo institucional"],
    ["correo_per", "Correo personal"], ["distrito_domicilio", "Distrito de domicilio"],
    ["identi_etnica", "Identidad étnica"], ["lengua_nativa", "Lengua nativa"],
    ["idioma_extranjero", "Idioma extranjero"], ["telefono_fijo", "Teléfono fijo"],
    ["telefono_movil", "Teléfono móvil"],
  ],
  ingreso: [
    ["tipo_preparacion", "Tipo de preparación"], ["modalidad_ingreso", "Modalidad de ingreso"],
    ["periodo_ingreso", "Periodo de ingreso"],
  ],
  matricula: [
    ["nivel", "Nivel"], ["modalidad_estudio", "Modalidad de estudio"],
    ["periodo_mat", "Periodo"], ["regimen_matricula", "Régimen"],
    ["ciclo", "Ciclo / año de estudios"], ["permanencia", "Permanencia"],
    ["primer_mat", "Primer periodo"], ["creditos_acum_sem", "Créditos del semestre"],
    ["creditos_acum_total", "Créditos acumulados total"],
    ["cursos_mat_cat", "Cursos matriculados/aprobados"],
    ["promedio_pond", "Promedio ponderado"], ["ranking", "Ranking"],
  ],
};

function escConsulta(valor) {
  return String(valor ?? "").replace(/[&<>"']/g, (caracter) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[caracter]));
}

function actualizarValorEdicion() {
  if (!datosEdicionActual) return;
  const [tabla, identificador, campo] = consulta$("consulta-editar-campo").value.split("|");
  let registro = datosEdicionActual;
  if (tabla === "ingreso") {
    registro = (datosEdicionActual.ingresos || []).find((item) => String(item.id_ingreso) === identificador);
  } else if (tabla === "matricula") {
    registro = (datosEdicionActual.ingresos || [])
      .flatMap((ingreso) => ingreso.matriculas || [])
      .find((item) => String(item.id_matricula) === identificador);
  }
  consulta$("consulta-editar-valor").value = registro?.[campo] ?? "";
}

async function abrirEditorEstudiante(estudiante) {
  estudianteEdicionActual = estudiante;
  const dialogo = consulta$("consulta-editar-dialog");
  consulta$("consulta-editar-referencia").textContent =
    `${estudiante.nombre_completo} · Código ${estudiante.id_codigo_alumno}`;
  consulta$("consulta-editar-valor").value = "";
  consulta$("consulta-editar-motivo").value = "";
  consulta$("consulta-editar-mensaje").textContent = "";
  dialogo.showModal();
  try {
    datosEdicionActual = await API.getEstudiante(estudiante.id_codigo_alumno);
    const opciones = CAMPOS_EDITABLES.estudiante.map(([campo, texto]) =>
      `<option value="estudiante|${estudiante.id_codigo_alumno}|${campo}">${texto}</option>`
    );
    (datosEdicionActual.ingresos || []).forEach((ingreso) => {
      CAMPOS_EDITABLES.ingreso.forEach(([campo, texto]) => {
        opciones.push(`<option value="ingreso|${ingreso.id_ingreso}|${campo}">${texto} · ingreso ${ingreso.id_ingreso}</option>`);
      });
      (ingreso.matriculas || []).forEach((matricula) => {
        CAMPOS_EDITABLES.matricula.forEach(([campo, texto]) => {
          opciones.push(`<option value="matricula|${matricula.id_matricula}|${campo}">${texto} · matrícula ${formatearPeriodo(matricula.periodo_mat)}</option>`);
        });
      });
    });
    const campo = consulta$("consulta-editar-campo");
    campo.innerHTML = opciones.join("");
    actualizarValorEdicion();
  } catch (error) {
    consulta$("consulta-editar-mensaje").textContent =
      error.message || "No se pudo cargar el valor actual.";
  }
}

function cerrarEditorEstudiante() {
  consulta$("consulta-editar-dialog").close();
  estudianteEdicionActual = null;
  datosEdicionActual = null;
}

async function guardarEdicionEstudiante(evento) {
  evento.preventDefault();
  if (!estudianteEdicionActual) return;

  const valor = consulta$("consulta-editar-valor").value.trim();
  const motivo = consulta$("consulta-editar-motivo").value.trim();
  const mensaje = consulta$("consulta-editar-mensaje");
  if (!valor || !motivo) {
    mensaje.textContent = "El valor y el motivo son obligatorios.";
    return;
  }

  const boton = evento.submitter;
  boton.disabled = true;
  mensaje.textContent = "Guardando cambio...";
  try {
    const [tabla, idRegistro, campo] = consulta$("consulta-editar-campo").value.split("|");
    await API.corregirRegistro({
      tabla,
      id: idRegistro,
      campo,
      valor,
      motivo,
    });
    cerrarEditorEstudiante();
    await cargarConsultas();
  } catch (error) {
    mensaje.textContent = error.message || "No se pudo guardar el cambio.";
  } finally {
    boton.disabled = false;
  }
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

function sincronizarFiltrosEnUrl() {
  const parametros = new URLSearchParams();
  const campos = [
    ["q", "consulta-q"],
    ["periodo", "consulta-periodo"],
    ["programa", "consulta-programa"],
    ["facultad", "consulta-facultad"],
    ["estado_matricula", "consulta-estado"],
    ["condicion", "consulta-condicion"],
  ];
  campos.forEach(([nombre, id]) => {
    const valor = consulta$(id).value.trim();
    if (valor) parametros.set(nombre, valor);
  });
  if (consultaPaginaActual > 1) {
    parametros.set("page", String(consultaPaginaActual));
  }
  const url = parametros.toString()
    ? `${location.pathname}?${parametros}`
    : location.pathname;
  history.replaceState(null, "", url);
}

function restaurarFiltrosDesdeUrl() {
  const parametros = new URLSearchParams(location.search);
  const pagina = Number.parseInt(parametros.get("page") || "1", 10);
  consultaPaginaActual = Number.isFinite(pagina) && pagina > 0 ? pagina : 1;
  [
    ["q", "consulta-q"],
    ["periodo", "consulta-periodo"],
    ["programa", "consulta-programa"],
    ["facultad", "consulta-facultad"],
    ["estado_matricula", "consulta-estado"],
    ["condicion", "consulta-condicion"],
  ].forEach(([nombre, id]) => {
    const valor = parametros.get(nombre);
    if (valor !== null) consulta$(id).value = valor;
  });
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
          <button class="action-btn consulta-editar-btn" type="button" data-estudiante="${escConsulta(JSON.stringify(estudiante))}">
            Editar <span class="material-symbols-outlined text-sm">edit</span>
          </button>
          <a class="action-btn" href="/frontend/paginas/estudiantes/detalle.html?id=${encodeURIComponent(estudiante.id_codigo_alumno)}&return=${encodeURIComponent(location.pathname + location.search)}">
            Ver detalle <span class="material-symbols-outlined text-sm">open_in_new</span>
          </a>
        </td>
      </tr>
    `).join("");
    cuerpo.querySelectorAll(".consulta-editar-btn").forEach((boton) => {
      boton.addEventListener("click", () => {
        abrirEditorEstudiante(JSON.parse(boton.dataset.estudiante)).catch((error) => {
          console.error("No se pudo abrir el editor:", error);
        });
      });
    });
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
  llenarOpciones(
    "consulta-periodo",
    opciones.periodos.map((p) => ({ valor: p.valor, texto: formatearPeriodo(p.texto) })),
    "Todos los semestres"
  );
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
  document.querySelector("[data-modulo='graduados_titulados'] small").textContent =
    Number(modulos.graduados_titulados || 0).toLocaleString("es-PE");
}

document.addEventListener("DOMContentLoaded", async () => {
  await Promise.all([
    cargarComponente("sidebar", "/frontend/components/sidebar.html"),
    cargarComponente("header", "/frontend/components/header.html")
  ]);
  marcarNavActivo();
  iniciarReloj();
  await cargarOpcionesConsulta();
  restaurarFiltrosDesdeUrl();
  consulta$("consulta-form").addEventListener("submit", (evento) => {
    evento.preventDefault();
    consultaPaginaActual = 1;
    sincronizarFiltrosEnUrl();
    cargarConsultas();
  });
  consulta$("consulta-editar-campo").addEventListener("change", async () => {
    if (!estudianteEdicionActual) return;
    actualizarValorEdicion();
  });
  consulta$("consulta-editar-form").addEventListener("submit", guardarEdicionEstudiante);
  consulta$("consulta-editar-cerrar").addEventListener("click", cerrarEditorEstudiante);
  consulta$("consulta-editar-cancelar").addEventListener("click", cerrarEditorEstudiante);
  consulta$("consulta-limpiar").addEventListener("click", () => {
    consulta$("consulta-form").reset();
    consultaPaginaActual = 1;
    history.replaceState(null, "", location.pathname);
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
