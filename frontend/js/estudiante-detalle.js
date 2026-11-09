function escDetalle(valor) {
  return String(valor ?? "").replace(/[&<>"']/g, (caracter) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[caracter]));
}

function campoDetalle(titulo, valor) {
  return `
    <div>
      <dt class="font-label-sm text-label-sm text-outline">${titulo}</dt>
      <dd class="mt-space-2xs">${escDetalle(valor) || "—"}</dd>
    </div>
  `;
}

function listaCamposDetalle(campos) {
  return campos.map(([titulo, valor]) => campoDetalle(titulo, valor)).join("");
}

function clavePeriodo(matricula, indice) {
  return String(matricula.periodo_mat || `matricula-${indice}`);
}

function leerPeriodosGuardados(idEstudiante) {
  try {
    return new Set(JSON.parse(
      sessionStorage.getItem(`historial-academico:${idEstudiante}`) || "[]"
    ));
  } catch (error) {
    console.warn("No se pudo recuperar el estado del historial académico:", error);
    return new Set();
  }
}

function guardarPeriodo(idEstudiante, periodo) {
  try {
    const periodosGuardados = leerPeriodosGuardados(idEstudiante);
    periodosGuardados.add(periodo);
    sessionStorage.setItem(
      `historial-academico:${idEstudiante}`,
      JSON.stringify([...periodosGuardados])
    );
    return true;
  } catch (error) {
    console.warn("No se pudo guardar el estado del historial académico:", error);
    return false;
  }
}

function renderizarMatricula(matricula, indice, periodosGuardados, abierta = false) {
  const periodo = clavePeriodo(matricula, indice);
  const campos = [
    ["Nivel", matricula.nivel],
    ["Modalidad de estudio", matricula.modalidad_estudio],
    ["Ciclo / año de estudios", matricula.ciclo],
    ["Permanencia", matricula.permanencia],
    ["Primer periodo", matricula.primer_mat],
    ["Periodo", matricula.periodo_mat],
    ["Régimen", matricula.regimen_matricula],
    ["Créditos acumulados del semestre", matricula.creditos_acum_sem],
    ["Créditos acumulados total", matricula.creditos_acum_total],
    ["Cursos matriculados/aprobados", matricula.cursos_mat_cat],
    ["Promedio ponderado", matricula.promedio_pond],
    ["Ranking", matricula.ranking],
  ];

  return `
    <article class="historial-periodo${abierta ? " is-open" : ""}${periodosGuardados.has(periodo) ? " is-saved" : ""}" data-periodo="${escDetalle(periodo)}">
      <button type="button" class="historial-periodo-trigger" aria-expanded="${abierta}">
        <span class="historial-periodo-title">
          <span class="material-symbols-outlined" aria-hidden="true">calendar_month</span>
          <span>
            <small>Periodo académico:</small>
            <span class="historial-periodo-year">
              <strong>${escDetalle(matricula.periodo_mat) || "Sin periodo"}</strong>
              <small class="historial-periodo-ingreso">ID: ${escDetalle(matricula.id_ingreso) || "—"}</small>
            </span>
          </span>
        </span>
        <span class="historial-periodo-status">${periodosGuardados.has(periodo) ? "Guardada" : "Ver información"}</span>
        <span class="material-symbols-outlined historial-periodo-chevron" aria-hidden="true">expand_more</span>
      </button>
      <div class="historial-periodo-content" aria-hidden="${!abierta}">
        <div class="historial-periodo-inner">
          <dl class="historial-periodo-fields">
            ${listaCamposDetalle(campos)}
          </dl>
        </div>
      </div>
    </article>
  `;
}

function renderizarIngresoUniversitario(ingreso) {
  return `
    <article class="universidad-item">
      <div class="universidad-item-head">
        <span class="material-symbols-outlined" aria-hidden="true">account_balance</span>
        <div>
          <strong>${escDetalle(ingreso.programa) || "Programa no registrado"}</strong>
        </div>
      </div>
      <dl class="universidad-fields">
        ${listaCamposDetalle([
          ["Facultad", ingreso.facultad],
          ["Código de programa", ingreso.cod_prog],
          ["Especialidad", ingreso.especialidad],
          ["Modalidad de ingreso", ingreso.modalidad_ingreso],
          ["Sede", ingreso.sede],
        ])}
      </dl>
    </article>
  `;
}

function claveIngresoUniversitario(ingreso) {
  return [
    ingreso.programa,
    ingreso.facultad,
    ingreso.cod_prog,
    ingreso.especialidad,
    ingreso.modalidad_ingreso,
    ingreso.sede,
  ].map(normalizarValorIngreso).join("|");
}

function normalizarValorIngreso(valor) {
  const normalizado = String(valor ?? "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim();

  return ["", "-", "--", "---", "----", "n a", "na", "no aplica"].includes(normalizado)
    ? ""
    : normalizado;
}

function ingresosUnicos(ingresos) {
  const vistos = new Set();
  return ingresos.filter((ingreso) => {
    const clave = claveIngresoUniversitario(ingreso);
    if (vistos.has(clave)) {
      return false;
    }
    vistos.add(clave);
    return true;
  });
}

document.addEventListener("DOMContentLoaded", async () => {
  await Promise.all([
    cargarComponente("sidebar", "/frontend/components/sidebar.html"),
    cargarComponente("header", "/frontend/components/header.html")
  ]);
  marcarNavActivo();
  iniciarReloj();

  const id = new URLSearchParams(location.search).get("id");
  const retorno = new URLSearchParams(location.search).get("return");
  const botonVolver = document.querySelector(".detalle-volver");
  if (retorno && retorno.startsWith("/frontend/paginas/consultas/")) {
    botonVolver.href = retorno;
  }
  const panel = document.getElementById("estudiante-detalle");

  if (!id) {
    panel.textContent = "No se indicó un código de estudiante.";
    return;
  }

  try {
    const estudiante = await API.getEstudiante(id);
    const periodosGuardados = leerPeriodosGuardados(estudiante.id_codigo_alumno || id);
    const ingresos = estudiante.ingresos || [];
    const ingresosMostrados = ingresosUnicos(ingresos);
    const matriculas = ingresos.flatMap((ingreso) =>
      (ingreso.matriculas || []).map((matricula) => ({
        ...matricula,
        id_ingreso: ingreso.id_ingreso,
      }))
    );
    const promedios = matriculas
      .map((matricula) => Number(matricula.promedio_pond))
      .filter((promedio) => Number.isFinite(promedio));
    const promedioGeneral = promedios.length
      ? promedios.reduce((total, promedio) => total + promedio, 0) / promedios.length
      : 0;

    panel.innerHTML = `
      <div class="detalle-ficha">
        <header class="detalle-ficha-header">
          <img src="/frontend/assets/icons/Estudiante.png" alt="Estudiante" class="detalle-ficha-icon">
          <div>
            <span class="detalle-eyebrow">Ficha del estudiante</span>
            <h1>${escDetalle(estudiante.nombres)} ${escDetalle(estudiante.apellido_pat)} ${escDetalle(estudiante.apellido_mat)}</h1>
            <p>Código: <strong>${escDetalle(estudiante.id_codigo_alumno)}</strong></p>
          </div>
        </header>
        <div class="detalle-layout">
          <aside class="detalle-sidebar">
            <section class="detalle-card">
              <h2><span class="material-symbols-outlined" aria-hidden="true">person</span>Información personal</h2>
              <dl class="detalle-fields">
                ${listaCamposDetalle([
            ["Tipo de documento", estudiante.tipo_doc_id],
            ["Número de documento", estudiante.num_dni],
            ["Nombres", estudiante.nombres],
            ["Apellido paterno", estudiante.apellido_pat],
            ["Apellido materno", estudiante.apellido_mat],
            ["Sexo", estudiante.sexo],
            ["Fecha de nacimiento", estudiante.fecha_nac],
            ["Nacionalidad", estudiante.nacionalidad],
            ["Estado civil", estudiante.estado_civil],
            ["Correo institucional", estudiante.correo_inst],
            ["Correo personal", estudiante.correo_per],
            ["Teléfono fijo", estudiante.telefono_fijo],
            ["Teléfono móvil", estudiante.telefono_movil],
                ])}
              </dl>
            </section>
            <section class="detalle-card">
              <h2><span class="material-symbols-outlined" aria-hidden="true">location_on</span>Datos de procedencia</h2>
              <dl class="detalle-fields">
                ${listaCamposDetalle([
            ["Colegio de procedencia", estudiante.colegio],
            ["Beca", estudiante.beca],
            ["Discapacidad", estudiante.discapacidad],
            ["Movilidad", estudiante.movilidad],
            ["País de nacimiento", estudiante.ubigeo && estudiante.ubigeo.pais_nac],
            ["Departamento de nacimiento", estudiante.ubigeo && estudiante.ubigeo.dep_nac],
            ["Provincia de nacimiento", estudiante.ubigeo && estudiante.ubigeo.provincia_nac],
            ["Distrito de nacimiento", estudiante.ubigeo && estudiante.ubigeo.distrito_nac],
                ])}
              </dl>
            </section>
          </aside>
          <div class="detalle-main">
            <section class="detalle-card universidad-card">
              <h2><span class="material-symbols-outlined" aria-hidden="true">account_balance</span>Información universitaria</h2>
              <div class="universidad-list">
                ${ingresosMostrados.map(renderizarIngresoUniversitario).join("") ||
                  '<p class="detalle-empty">No hay información universitaria registrada.</p>'}
              </div>
            </section>
            <section class="detalle-card historial-card">
              <div class="historial-heading">
                <h2><span class="material-symbols-outlined" aria-hidden="true">bar_chart</span>Historial académico</h2>
                <div class="historial-stats">
                  <span><small>Total de matrículas</small><strong>${matriculas.length}</strong></span>
                  <span><small>Promedio general</small><strong>${promedioGeneral ? promedioGeneral.toFixed(2) : "—"}</strong></span>
                </div>
              </div>
              <div class="historial-list">
                ${matriculas.map((matricula, indice) =>
                  renderizarMatricula(matricula, indice, periodosGuardados, indice === 0)
                ).join("") || '<p class="detalle-empty">No hay matrículas registradas.</p>'}
              </div>
            </section>
          </div>
        </div>
      </div>
    `;

    panel.querySelectorAll(".historial-periodo-trigger").forEach((boton) => {
      boton.addEventListener("click", () => {
        const tarjeta = boton.closest(".historial-periodo");
        const contenido = tarjeta.querySelector(".historial-periodo-content");
        const abierta = tarjeta.classList.toggle("is-open");
        boton.setAttribute("aria-expanded", String(abierta));
        contenido.setAttribute("aria-hidden", String(!abierta));
        if (abierta) {
          tarjeta.querySelector(".historial-periodo-status").textContent = "Cerrar información";
          return;
        }
        const guardada = guardarPeriodo(estudiante.id_codigo_alumno || id, tarjeta.dataset.periodo);
        tarjeta.classList.toggle("is-saved", guardada);
        tarjeta.querySelector(".historial-periodo-status").textContent = guardada
          ? "Guardada"
          : "Información cerrada";
      });
    });
  } catch (error) {
    console.error("Error al consultar el estudiante:", error);
    panel.textContent = error.message || "No se pudo consultar el estudiante.";
  }
});
