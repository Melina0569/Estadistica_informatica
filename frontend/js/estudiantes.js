document.addEventListener("DOMContentLoaded", async () => {
    try {
        const resultado = await API.getEstudiantes(1, 5);

        console.log("Respuesta de Flask:", resultado);
    } catch (error) {
        console.error("Error de conexión:", error);
    }
});