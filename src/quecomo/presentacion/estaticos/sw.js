/*
 * Service worker de ¿Qué Como?
 *
 * Solo atiende la NAVEGACIÓN (abrir la app o recargar la página):
 *  - Intenta la red primero; la app siempre muestra datos actuales del servidor.
 *  - Si no hay conexión, el servidor responde con error 5xx o tarda más de
 *    ESPERA_MAXIMA_MS (por ejemplo, el plan gratuito de Render «despertando»),
 *    muestra la página /offline.html, que reintenta sola.
 *
 * No intercepta las peticiones de Gradio (API, cola, eventos), que siempre
 * van directo a la red.
 */

const VERSION = "quecomo-v1";
const PAGINA_SIN_CONEXION = "/offline.html";
const PRECARGA = [PAGINA_SIN_CONEXION, "/recursos/iconos/icono-192.png"];
const ESPERA_MAXIMA_MS = 12000;

self.addEventListener("install", (evento) => {
  evento.waitUntil(
    caches.open(VERSION).then((cache) => cache.addAll(PRECARGA)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (evento) => {
  evento.waitUntil(
    caches
      .keys()
      .then((claves) => Promise.all(claves.filter((c) => c !== VERSION).map((c) => caches.delete(c))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (evento) => {
  const solicitud = evento.request;
  if (solicitud.mode === "navigate") {
    evento.respondWith(navegar(solicitud));
    return;
  }
  // Recursos de la página de respaldo (ícono): primero la caché.
  const ruta = new URL(solicitud.url).pathname;
  if (solicitud.method === "GET" && PRECARGA.includes(ruta)) {
    evento.respondWith(caches.match(solicitud).then((r) => r || fetch(solicitud)));
  }
});

async function navegar(solicitud) {
  const limite = new Promise((resolver) => setTimeout(() => resolver(null), ESPERA_MAXIMA_MS));
  try {
    const respuesta = await Promise.race([fetch(solicitud), limite]);
    if (respuesta && respuesta.status < 500) return respuesta;
  } catch (_) {
    // Sin conexión: se muestra la página de respaldo.
  }
  const respaldo = await caches.match(PAGINA_SIN_CONEXION);
  return respaldo || Response.error();
}
