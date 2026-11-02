// ---------- Utilidades ----------
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, c => ({ "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;" }[c]));
const num = (n) => (n || n === 0) ? Number(n).toLocaleString("es-PE") : "—";
const periodoAcademicoLocal = (fecha = new Date()) => (
  `${fecha.getFullYear()}-${fecha.getMonth() < 6 ? "1" : "2"}`
);
const CLAVE_PERIODO_ACADEMICO = "dataunmsm.periodoAcademico";

function periodoAcademicoConfigurado() {
  return localStorage.getItem(CLAVE_PERIODO_ACADEMICO)
    || periodoAcademicoLocal();
}

function mostrarPeriodoAcademico() {
  const periodo = $("periodo-actual");
  if (!periodo) return;
  const valor = periodoAcademicoConfigurado();
  periodo.textContent = valor;
  periodo.title = "Haz clic para configurar el periodo académico";
}

function configurarPeriodoAcademico() {
  const actual = periodoAcademicoConfigurado().split("-");
  const anio = $("periodo-anio");
  const semestre = $("periodo-semestre");
  const error = $("periodo-error");
  if (!anio || !semestre) return;
  anio.innerHTML = "";
  for (let valor = new Date().getFullYear() - 2; valor <= new Date().getFullYear() + 3; valor += 1) {
    anio.insertAdjacentHTML("beforeend", `<option value="${valor}">${valor}</option>`);
  }
  anio.value = actual[0];
  semestre.value = actual[1] || "1";
  actualizarVistaPreviaPeriodo();
  error.hidden = true;
  $("periodo-modal").hidden = false;
  semestre.focus();
}

function actualizarVistaPreviaPeriodo() {
  const preview = $("periodo-preview-valor");
  const anio = $("periodo-anio")?.value;
  const semestre = $("periodo-semestre")?.value;
  if (preview && anio && semestre) preview.textContent = `${anio}-${semestre}`;
}

function cerrarConfiguracionPeriodo() {
  const modal = $("periodo-modal");
  if (modal) modal.hidden = true;
}

function guardarPeriodoAcademico() {
  const anio = $("periodo-anio")?.value;
  const semestre = $("periodo-semestre")?.value;
  const error = $("periodo-error");
  if (!/^\d{4}$/.test(anio || "") || !["1", "2"].includes(semestre)) {
    error.textContent = "Selecciona un año y un semestre válidos.";
    error.hidden = false;
    return;
  }
  localStorage.setItem(CLAVE_PERIODO_ACADEMICO, `${anio}-${semestre}`);
  mostrarPeriodoAcademico();
  cerrarConfiguracionPeriodo();
}

function inicializarPeriodoAcademico() {
  const periodo = $("periodo-actual");
  if (!periodo || periodo.dataset.inicializado === "true") return;
  mostrarPeriodoAcademico();
  periodo.addEventListener("click", configurarPeriodoAcademico);
  $("configurar-periodo")?.addEventListener(
    "click",
    configurarPeriodoAcademico
  );
  $("cerrar-periodo")?.addEventListener("click", cerrarConfiguracionPeriodo);
  $("cancelar-periodo")?.addEventListener("click", cerrarConfiguracionPeriodo);
  $("guardar-periodo")?.addEventListener("click", guardarPeriodoAcademico);
  $("periodo-anio")?.addEventListener("change", actualizarVistaPreviaPeriodo);
  $("periodo-semestre")?.addEventListener("change", actualizarVistaPreviaPeriodo);
  document.querySelector("[data-cerrar-periodo]")?.addEventListener(
    "click",
    cerrarConfiguracionPeriodo
  );
  periodo.dataset.inicializado = "true";
}

// ---------- Componentes (sidebar, header, footer) ----------
async function cargarComponente(id, ruta) {
  const el = $(id);
  if (!el) return;
  el.innerHTML = await (await fetch(ruta)).text();
  if (id === "sidebar") inicializarPeriodoAcademico();
}

function marcarNavActivo() {
  const actual = location.pathname;
  document.querySelectorAll(".nav-link").forEach(a => {
    const ruta = a.dataset.path;
    const activo = ruta.endsWith("/")
      ? actual.startsWith(ruta)
      : actual === ruta || (ruta === "/index.html" && actual === "/");
    a.classList.toggle("active", activo);
    if (activo) a.setAttribute("aria-current", "page");
  });
}

function iniciarReloj() {
  const fecha = $("header-date"), hora = $("header-time");
  if (!fecha || !hora) return;
  const tick = () => {
    const d = new Date();
    fecha.textContent = d.toLocaleDateString("es-PE", { day: "numeric", month: "long", year: "numeric" });
    hora.textContent = d.toLocaleTimeString("es-PE", { hour: "2-digit", minute: "2-digit" });
  };
  tick();
  setInterval(tick, 30000);
}

// ---------- Dashboard ----------
const BADGES = {
  completado: {
    clase: "badge-ok",
    texto: "Completado",
    accion: "Abrir planilla",
    icono: "open_in_new",
    deshabilitado: false
  },
  observaciones: {
    clase: "badge-obs",
    texto: "Con observaciones",
    accion: "Ver detalle",
    icono: "visibility",
    deshabilitado: false
  },
  revision: {
    clase: "badge-rev",
    texto: "En revisión",
    accion: "Ver detalle",
    icono: "visibility",
    deshabilitado: false
  },
  eliminado: {
    clase: "badge-eliminado",
    texto: "Eliminado",
    accion: "Planilla eliminada",
    icono: "block",
    deshabilitado: true
  }
};

function pintarResumen(r) {
  $("kpi-archivos").textContent        = num(r.archivosHoy);
  $("kpi-validadas").textContent       = num(r.validados);
  $("kpi-observadas").textContent      = num(r.conObservaciones);
  $("kpi-registros").textContent       = num(r.registrosProcesados);
  $("kpi-inconsistencias").textContent = num(r.inconsistencias);
  const periodo = $("periodo-actual");
  if (periodo) {
    const periodoActual = periodoAcademicoConfigurado();
    periodo.textContent = periodoActual;
    periodo.title = `Periodo configurado: ${periodoActual}`;
  }
}

function filaArchivo(a) {
  const estado = String(a.estado || "").trim().toLowerCase();

  const clave = estado === "eliminado"
    ? "eliminado"
    : estado.includes("observ")
      ? "observaciones"
      : estado.includes("complet") ||
        estado === "validado" ||
        estado === "apto"
        ? "completado"
        : "revision";

  const b = BADGES[clave];

  const botonAccion = b.deshabilitado
    ? `
      <button
        type="button"
        class="action-btn"
        disabled
        aria-disabled="true"
        title="Esta carga fue eliminada"
      >
        ${b.accion}
        <span class="material-symbols-outlined text-sm">
          ${b.icono}
        </span>
      </button>
    `
    : `
      <a
        class="action-btn"
        href="/frontend/paginas/consultas/index.html?carga=${encodeURIComponent(a.id)}"
      >
        ${b.accion}
        <span class="material-symbols-outlined text-sm">
          ${b.icono}
        </span>
      </a>
    `;

  const botonEliminar = b.deshabilitado
    ? `
      <button
        type="button"
        class="action-btn"
        disabled
        aria-disabled="true"
        title="Esta carga ya fue eliminada"
      >
        Eliminar
        <span class="material-symbols-outlined text-sm">delete</span>
      </button>
    `
    : `
      <button
        type="button"
        class="action-btn js-eliminar-carga"
        data-id="${esc(a.id)}"
        data-nombre="${esc(a.nombre)}"
      >
        Eliminar
        <span class="material-symbols-outlined text-sm">delete</span>
      </button>
    `;

  return `
    <tr class="hover:bg-surface-container-low transition-colors">
      <td class="py-space-sm px-space-md">
        <div class="font-data-mono text-data-mono text-primary font-bold">
          ${esc(a.nombre)}
        </div>
        <div class="font-data-mono-sm text-data-mono-sm text-outline">
          ${num(a.registros)} registros
        </div>
      </td>

      <td class="py-space-sm px-space-md">${esc(a.tipo)}</td>
      <td class="py-space-sm px-space-md font-medium">${esc(a.dependencia)}</td>

      <td class="py-space-sm px-space-md">
        <div class="font-medium">${esc(a.subidoPor)}</div>
        <div class="text-outline">${esc(a.cargo)}</div>
      </td>

      <td class="py-space-sm px-space-md font-data-mono-sm text-data-mono-sm text-on-surface-variant">
        ${esc(a.hora)}
      </td>

      <td class="py-space-sm px-space-md">
        <span class="badge ${b.clase}">
          <span class="dot"></span>${b.texto}
        </span>
      </td>

      <td class="py-space-sm px-space-md text-right">
        <div class="flex justify-end gap-space-xs">
          ${botonAccion}
          ${botonEliminar}
        </div>
      </td>
    </tr>
  `;
}

async function eliminarCarga(id, nombre) {
  const confirmado = window.confirm(
    `¿Desea eliminar la carga "${nombre}"? ` +
    "Se revertirán los cambios que esta carga realizó."
  );

  if (!confirmado) return;

  const boton = document.querySelector(
    `.js-eliminar-carga[data-id="${CSS.escape(String(id))}"]`
  );
  const textoOriginal = boton ? boton.innerHTML : "";
  const progreso = $("eliminacion-progreso");
  const barra = $("eliminacion-barra");
  const porcentaje = $("eliminacion-porcentaje");
  const detalle = $("eliminacion-detalle");
  let porcentajeActual = 8;
  let progresoIntervalo = null;

  const actualizarProgreso = (valor) => {
    porcentajeActual = Math.max(0, Math.min(100, valor));
    barra.style.width = `${porcentajeActual}%`;
    porcentaje.textContent = `${porcentajeActual}%`;
    progreso.querySelector("[role='progressbar']")
      .setAttribute("aria-valuenow", String(porcentajeActual));
  };

  const detenerProgreso = () => {
    window.clearInterval(progresoIntervalo);
    progresoIntervalo = null;
  };

  try {
    progreso.hidden = false;
    document.body.classList.add("is-eliminando-carga");
    actualizarProgreso(8);
    progresoIntervalo = window.setInterval(() => {
      if (porcentajeActual >= 90) return;
      actualizarProgreso(porcentajeActual < 45 ? porcentajeActual + 5 : porcentajeActual + 2);
      detalle.textContent = porcentajeActual < 45
        ? "Preparando la reversión de los registros."
        : "Restaurando valores y eliminando registros creados.";
    }, 500);

    if (boton) {
      boton.disabled = true;
      boton.setAttribute("aria-busy", "true");
      boton.innerHTML = `
        <span class="material-symbols-outlined text-sm">progress_activity</span>
        Eliminando...
      `;
    }
    await API.eliminarCarga(id);
    detenerProgreso();
    actualizarProgreso(100);
    barra.classList.add("is-complete");
    detalle.textContent = "La carga fue revertida correctamente.";
    await cargarDashboard();
    await new Promise((resolve) => window.setTimeout(resolve, 800));
  } catch (error) {
    detenerProgreso();
    progreso.hidden = true;
    document.body.classList.remove("is-eliminando-carga");
    console.error("Error al eliminar la carga:", error);
    window.alert(
      error.message || "No se pudo eliminar la carga."
    );
    if (boton) {
      boton.disabled = false;
      boton.removeAttribute("aria-busy");
      boton.innerHTML = textoOriginal;
    }
  } finally {
    detenerProgreso();
    progreso.hidden = true;
    document.body.classList.remove("is-eliminando-carga");
    barra.classList.remove("is-complete");
  }
}

async function reiniciarBaseDatos() {
  const confirmado = window.confirm(
    "Esta acción eliminará TODOS los registros y el historial de cargas. " +
    "No se puede deshacer. ¿Desea continuar?"
  );

  if (!confirmado) return;

  const confirmacionFinal = window.prompt(
    "Para confirmar, escriba REINICIAR:"
  );

  if (confirmacionFinal !== "REINICIAR") return;

  const boton = $("reiniciar-base-datos-btn");
  if (boton) {
    boton.disabled = true;
    boton.setAttribute("aria-busy", "true");
  }

  try {
    await API.reiniciarBaseDatos();
    window.alert("La base de datos y el historial fueron reiniciados.");
    await cargarDashboard();
  } catch (error) {
    console.error("Error al reiniciar la base de datos:", error);
    window.alert(error.message || "No se pudo reiniciar la base de datos.");
  } finally {
    if (boton) {
      boton.disabled = false;
      boton.removeAttribute("aria-busy");
    }
  }
}

let archivos = [];

function pintarTabla(lista) {
  const tbody = $("files-tbody");
  if (!lista.length) {
    tbody.innerHTML = `<tr><td colspan="7" class="empty-state">
      ${archivos.length ? "Ningún archivo coincide con el filtro." : 'Aún no hay planillas cargadas. <a href="/frontend/paginas/carga/index.html">Cargar un archivo Excel</a>'}
    </td></tr>`;
  } else {
    tbody.innerHTML = lista.map(filaArchivo).join("");
  }
  $("rows-count-indicator").textContent = `Mostrando ${lista.length} de ${archivos.length} archivos`;
}

function filtrarTabla() {
  const q = $("table-search-input").value.toLowerCase().trim();
  pintarTabla(archivos.filter(a =>
    [a.nombre, a.tipo, a.dependencia, a.subidoPor].join(" ").toLowerCase().includes(q)));
}

async function cargarDashboard() {
    try {
        const [resumen, lista] = await Promise.all([
            API.getResumen(),
            API.getArchivos(10)
        ]);

        archivos = Array.isArray(lista) ? lista : [];

        pintarResumen(resumen || {});
        pintarTabla(archivos);

    } catch (error) {
        console.error(
            "Error al cargar el dashboard:",
            error
        );

        pintarResumen({});

        const tbody = document.getElementById("files-tbody");

        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="empty-state">
                        No se pudo cargar la información.
                        Verifique la conexión con el backend.
                    </td>
                </tr>
            `;
        }

        const indicador = document.getElementById(
            "rows-count-indicator"
        );

        if (indicador) {
            indicador.textContent = "";
        }
    }
}

// ---------- Inicio ----------
document.addEventListener("DOMContentLoaded", async () => {
    await Promise.all([
        cargarComponente(
            "sidebar",
            "/frontend/components/sidebar.html"
        ),
        cargarComponente(
            "header",
            "/frontend/components/header.html"
        ),
        cargarComponente(
            "footer",
            "/frontend/components/footer.html"
        )
    ]);

    marcarNavActivo();
    iniciarReloj();
    inicializarPeriodoAcademico();

    if ($("files-tbody")) {
        $("reiniciar-base-datos-btn")?.addEventListener(
            "click",
            reiniciarBaseDatos
        );

        $("table-search-input").addEventListener(
            "input",
            filtrarTabla
        );

        $("refresh-grid-btn").addEventListener(
            "click",
            cargarDashboard
        );

        $("files-tbody").addEventListener("click", (evento) => {
            const boton = evento.target.closest(".js-eliminar-carga");
            if (!boton) return;

            eliminarCarga(
                boton.dataset.id,
                boton.dataset.nombre
            );
        });

        cargarDashboard();
    }
});
