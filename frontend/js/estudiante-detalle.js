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

function renderizarMatricula(matricula) {
  const campos = [
    ["Nivel", matricula.nivel],
    ["Modalidad de estudio", matricula.modalidad_estudio],
    ["Periodo", matricula.periodo_mat],
    ["Régimen", matricula.regimen_matricula],
    ["Ciclo / año de estudios", matricula.ciclo],
    ["Permanencia", matricula.permanencia],
    ["Primer periodo", matricula.primer_mat],
    ["Créditos acumulados del semestre", matricula.creditos_acum_sem],
    ["Créditos acumulados total", matricula.creditos_acum_total],
    ["Cursos matriculados/aprobados", matricula.cursos_mat_cat],
    ["Promedio ponderado", matricula.promedio_pond],
    ["Ranking", matricula.ranking],
  ];

  return `
    <article class="border border-surface-container rounded-lg p-space-md">
      <h4 class="font-label-md text-label-md text-primary font-bold">
        Matrícula ${escDetalle(matricula.periodo_mat) || ""}
      </h4>
      <dl class="grid grid-cols-2 md:grid-cols-4 gap-space-md mt-space-md">
        ${listaCamposDetalle(campos)}
      </dl>
    </article>
  `;
}

document.addEventListener("DOMContentLoaded", async () => {
  await Promise.all([
    cargarComponente("sidebar", "/frontend/components/sidebar.html"),
    cargarComponente("header", "/frontend/components/header.html")
  ]);
  marcarNavActivo();
  iniciarReloj();

  const id = new URLSearchParams(location.search).get("id");
  const panel = document.getElementById("estudiante-detalle");

  if (!id) {
    panel.textContent = "No se indicó un código de estudiante.";
    return;
  }

  try {
    const estudiante = await API.getEstudiante(id);
    const ingresos = (estudiante.ingresos || []).map((ingreso) => `
      <article class="border border-surface-container rounded-lg p-space-md">
        <div class="flex flex-wrap justify-between gap-space-sm">
          <strong>${escDetalle(ingreso.programa) || "Programa no registrado"}</strong>
          <span class="font-data-mono-sm text-data-mono-sm text-outline">${escDetalle(ingreso.periodo_ingreso) || "—"}</span>
        </div>
        <p class="font-body-sm text-body-sm text-on-surface-variant mt-space-2xs">
          ${escDetalle(ingreso.facultad)} · ${escDetalle(ingreso.especialidad)} · ${escDetalle(ingreso.sede)}
        </p>
        <dl class="grid grid-cols-2 md:grid-cols-4 gap-space-md mt-space-md">
          ${listaCamposDetalle([
            ["ID de ingreso", ingreso.id_ingreso],
            ["Tipo de preparación", ingreso.tipo_preparacion],
            ["Modalidad de ingreso", ingreso.modalidad_ingreso],
            ["Periodo de ingreso", ingreso.periodo_ingreso],
            ["Facultad", ingreso.facultad],
            ["Código de programa", ingreso.cod_prog],
            ["Programa", ingreso.programa],
            ["Especialidad", ingreso.especialidad],
            ["Sede", ingreso.sede],
          ])}
        </dl>
        <div class="mt-space-lg">
          <h4 class="font-label-md text-label-md text-primary font-bold">
            Matrículas (${(ingreso.matriculas || []).length})
          </h4>
          <div class="space-y-space-sm mt-space-sm">
            ${(ingreso.matriculas || []).map(renderizarMatricula).join("") ||
              '<p class="text-on-surface-variant">No hay matrículas registradas.</p>'}
          </div>
        </div>
      </article>
    `).join("");

    panel.innerHTML = `
      <div class="flex flex-col md:flex-row md:items-center gap-space-lg">
        <img
                src="/frontend/assets/icons/Estudiante.png"
                alt="Estudiante"
                class="detalle-icono-estudiante"
            >
        <div>
          <span class="font-label-sm text-label-sm uppercase tracking-wider text-outline">Ficha del estudiante</span>
          <h1 class="font-headline-xl text-headline-xl text-primary mt-space-xs">${escDetalle(estudiante.nombres)} ${escDetalle(estudiante.apellido_pat)} ${escDetalle(estudiante.apellido_mat)}</h1>
          <p class="font-data-mono text-data-mono text-secondary mt-space-2xs">${escDetalle(estudiante.id_codigo_alumno)}</p>
        </div>
      </div>
      <section class="mt-space-xl">
        <h2 class="font-headline-sm text-headline-sm text-primary font-bold">Información personal</h2>
        <dl class="grid grid-cols-1 md:grid-cols-3 gap-space-lg mt-space-md">
          ${listaCamposDetalle([
            ["Código del estudiante", estudiante.id_codigo_alumno],
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
            ["Distrito de domicilio", estudiante.distrito_domicilio],
            ["Identidad étnica", estudiante.identi_etnica],
            ["Lengua nativa", estudiante.lengua_nativa],
            ["Idioma extranjero", estudiante.idioma_extranjero],
          ])}
        </dl>
      </section>
      <section class="mt-space-xl">
        <h2 class="font-headline-sm text-headline-sm text-primary font-bold">Información relacionada</h2>
        <dl class="grid grid-cols-1 md:grid-cols-3 gap-space-lg mt-space-md">
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
      <div class="mt-space-xl">
        <h2 class="font-headline-sm text-headline-sm text-primary font-bold">Historial académico</h2>
        <div class="space-y-space-sm mt-space-md">
          ${ingresos || '<p class="text-on-surface-variant">No hay ingresos académicos registrados.</p>'}
        </div>
      </div>
    `;
  } catch (error) {
    console.error("Error al consultar el estudiante:", error);
    panel.textContent = error.message || "No se pudo consultar el estudiante.";
  }
});
