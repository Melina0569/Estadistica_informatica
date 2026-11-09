const API = {
    BASE_URL: "http://127.0.0.1:5000",

    async get(ruta) {
        const respuesta = await fetch(
            `${this.BASE_URL}${ruta}`,
            {cache: "no-store"}
        );

        if (!respuesta.ok) {
            throw new Error(
                `Error ${respuesta.status} en ${ruta}`
            );
        }

        return respuesta.json();
    },

    async post(ruta) {
        const respuesta = await fetch(
            `${this.BASE_URL}${ruta}`,
            {
                method: "POST"
            }
        );

        const cuerpo = await respuesta.json().catch(() => ({}));

        if (!respuesta.ok) {
            const detalle = cuerpo.detalle
                ? ` ${cuerpo.detalle}`
                : "";
            const error = new Error(
                `${cuerpo.error || cuerpo.mensaje || `Error ${respuesta.status} en ${ruta}`}${detalle}`
            );
            error.detalle = cuerpo.resumen_inconsistencias?.length
                ? `${error.message} ${cuerpo.resumen_inconsistencias.map(
                    (item) => `${item.campo}: ${item.mensaje || "valor inválido"}`
                ).join(" | ")}`
                : error.message;
            throw error;
        }

        return cuerpo;
    },

    async postJson(ruta, datos) {
        return this.requestJson(ruta, "POST", datos);
    },

    async put(ruta, datos) {
        return this.requestJson(ruta, "PUT", datos);
    },

    async patchJson(ruta, datos) {
        return this.requestJson(ruta, "PATCH", datos);
    },

    async requestJson(ruta, metodo, datos) {
        const respuesta = await fetch(`${this.BASE_URL}${ruta}`, {
            method: metodo,
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(datos)
        });
        const cuerpo = await respuesta.json().catch(() => ({}));
        if (!respuesta.ok) {
            throw new Error(cuerpo.error || cuerpo.mensaje || `Error ${respuesta.status} en ${ruta}`);
        }
        return cuerpo;
    },

    async postArchivo(ruta, archivo) {
        const datos = new FormData();
        datos.append("archivo", archivo);

        const respuesta = await fetch(
            `${this.BASE_URL}${ruta}`,
            {
                method: "POST",
                body: datos
            }
        );

        const cuerpo = await respuesta.json().catch(() => ({}));

        if (!respuesta.ok) {
            const detalle = cuerpo.detalle
                ? ` ${cuerpo.detalle}`
                : "";
            throw new Error(
                `${cuerpo.error || cuerpo.mensaje || `Error ${respuesta.status} en ${ruta}`}${detalle}`
            );
        }

        return cuerpo;
    },

    async delete(ruta) {
        const respuesta = await fetch(
            `${this.BASE_URL}${ruta}`,
            {
                method: "DELETE"
            }
        );

        const cuerpo = await respuesta.json().catch(() => ({}));

        if (!respuesta.ok) {
            const detalle = cuerpo.detalle
                ? ` ${cuerpo.detalle}`
                : "";
            throw new Error(
                `${cuerpo.error || cuerpo.mensaje || `Error ${respuesta.status} en ${ruta}`}${detalle}`
            );
        }

        return cuerpo;
    },

    analizarExcel(archivo) {
        return this.postArchivo(
            "/estudiantes/cargar-excel",
            archivo
        );
    },

    confirmarCarga() {
        return this.post("/estudiantes/confirmar-carga");
    },

    // Estudiantes
    getEstudiantes(page = 1, perPage = 20) {
        return this.get(
            `/estudiantes?page=${page}&per_page=${perPage}`
        );
    },

    getEstudiante(id) {
        return this.get(
            `/estudiantes/${encodeURIComponent(id)}`
        );
    },

    consultarEstudiantes(parametros = {}) {
        const query = new URLSearchParams(
            Object.fromEntries(
                Object.entries(parametros).filter(
                    ([, valor]) => valor !== undefined && valor !== null && valor !== ""
                )
            )
        );
        return this.get(`/consultas/estudiantes?${query.toString()}`);
    },

    opcionesConsulta() {
        return this.get("/consultas/opciones");
    },

    // Dashboard
    getResumen() {
        return this.get("/api/dashboard/resumen");
    },

    getIndicadores(parametros = {}) {
        const query = new URLSearchParams(parametros);
        return this.get(`/api/indicadores/resumen?${query.toString()}`);
    },

    getTablaIndicadores(parametros = {}) {
        const query = new URLSearchParams(parametros);
        return this.get(`/api/indicadores/tabla?${query.toString()}`);
    },

    urlExportarIndicadores(parametros = {}) {
        const query = new URLSearchParams(parametros);
        return `${this.BASE_URL}/api/indicadores/exportar?${query.toString()}`;
    },

    async descargarIndicadores(parametros = {}) {
        const respuesta = await fetch(this.urlExportarIndicadores(parametros));
        if (!respuesta.ok) {
            const cuerpo = await respuesta.json().catch(() => ({}));
            throw new Error(
                cuerpo.error || `Error ${respuesta.status} al exportar indicadores`
            );
        }
        return {
            archivo: await respuesta.blob(),
            nombre: respuesta.headers
                .get("Content-Disposition")
                ?.match(/filename="?([^"]+)"?/)?.[1] || "indicadores.xlsx",
        };
    },

    getArchivos(limite = 10) {
        return this.get(`/api/cargas?limite=${limite}`);
    },

    reiniciarBaseDatos() {
        return this.post("/api/base-datos/reiniciar");
    },

    eliminarCarga(id) {
        return this.delete(`/api/cargas/${encodeURIComponent(id)}`);
    },

    getInconsistencias(limite = 100) {
        return this.get(`/api/correcciones/inconsistencias?limite=${limite}`);
    },

    getReporteActivo() {
        return this.get("/api/correcciones/reporte-activo");
    },

    guardarReporteValidacion(archivo, reporte) {
        return this.postJson("/api/correcciones/reporte-validacion", {
            archivo,
            reporte: {
                estado: reporte.estado,
                total_filas: reporte.total_filas,
                total_inconsistencias: reporte.total_inconsistencias,
                resumen_inconsistencias: reporte.resumen_inconsistencias
            }
        });
    },

    guardarCorreccionReporte(datos) {
        return this.put("/api/correcciones/reporte-validacion/correccion", datos);
    },

    getDetalleInconsistencia(tabla, campo) {
        const query = new URLSearchParams({tabla, campo});
        return this.get(`/api/correcciones/inconsistencias/detalle?${query}`);
    },

    getAuditoriaCorrecciones(pagina = 1) {
        return this.get(`/api/correcciones/auditoria?pagina=${pagina}`);
    },

    corregirRegistro(datos) {
        return this.put("/api/correcciones/registro", datos);
    },

    corregirRegistros(datos) {
        return this.put("/api/correcciones/registros", datos);
    },

    getDocumentosPendientes() {
        return this.get("/api/correcciones/documentos");
    },

    crearDocumentoPendiente(datos) {
        return this.postJson("/api/correcciones/documentos", datos);
    },

    actualizarDocumentoPendiente(id, datos) {
        return this.patchJson(`/api/correcciones/documentos/${id}`, datos);
    }
};