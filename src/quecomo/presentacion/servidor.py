"""Servidor HTTP de ¿Qué Como?: la interfaz Gradio más lo que necesita la app Android.

La app de Android es una *Trusted Web Activity* (TWA): abre este mismo sitio
a pantalla completa con el motor de Chrome. Para eso el sitio debe:

1. Servir un **manifiesto web** (``/manifest.json``) e íconos.
2. Demostrar que la app es suya con **Digital Asset Links**
   (``/.well-known/assetlinks.json``), que contiene el nombre del paquete y la
   huella SHA-256 del certificado con que Google Play firma la app.
3. Ofrecer una **página de respaldo** cuando no hay conexión (service worker).
4. Publicar un **aviso de privacidad** en una URL pública (lo exige Google Play).

Variables de entorno (todas opcionales):

| Variable                  | Uso                                                          |
|---------------------------|--------------------------------------------------------------|
| QUECOMO_ANDROID_PAQUETE   | Nombre del paquete Android (por defecto ``mx.quecomo.app``)  |
| QUECOMO_ANDROID_SHA256    | Huella(s) SHA-256 del certificado, separadas por comas       |
| QUECOMO_RESPONSABLE       | Responsable del tratamiento de datos (aviso de privacidad)   |
| QUECOMO_CORREO_CONTACTO   | Correo de contacto (aviso de privacidad y derechos ARCO)     |
| QUECOMO_DOMICILIO         | Domicilio del responsable (aviso de privacidad)              |
"""

from __future__ import annotations

import html
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from string import Template

import gradio as gr
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .. import __version__
from .interfaz import construir_interfaz
from .tema import CSS, NOCHE, TEMA

ESTATICOS = Path(__file__).resolve().parent / "estaticos"
PAQUETE_PREDETERMINADO = "mx.quecomo.app"
FECHA_AVISO = "10 de octubre de 2026"

_HUELLA = re.compile(r"^([0-9A-F]{2}:){31}[0-9A-F]{2}$")
_PAQUETE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*(\.[a-zA-Z][a-zA-Z0-9_]*)+$")

#: Se inserta en el <head> de la página de Gradio.
CABECERA_HTML = f"""
<meta name="theme-color" content="{NOCHE}">
<meta name="description" content="Encuentra, compara y evalúa restaurantes con reseñas respaldadas por consumos reales.">
<link rel="apple-touch-icon" href="/recursos/iconos/apple-touch-icon.png">
<script>
  document.documentElement.lang = "es-MX";
  if ("serviceWorker" in navigator) {{
    var registrarSW = function () {{ navigator.serviceWorker.register("/sw.js").catch(function () {{}}); }};
    // Gradio inserta esta cabecera después de cargar la página: «load» ya pudo ocurrir.
    if (document.readyState === "complete") registrarSW();
    else window.addEventListener("load", registrarSW);
  }}
</script>
"""


@dataclass(frozen=True)
class ConfiguracionMovil:
    """Datos que el sitio publica para la app Android y Google Play."""

    paquete_android: str = PAQUETE_PREDETERMINADO
    huellas_sha256: tuple[str, ...] = ()
    responsable: str = ""
    correo_contacto: str = ""
    domicilio: str = ""

    def __post_init__(self) -> None:
        if not _PAQUETE.match(self.paquete_android):
            raise ValueError(f"QUECOMO_ANDROID_PAQUETE no es un nombre de paquete válido: {self.paquete_android!r}")
        for huella in self.huellas_sha256:
            if not _HUELLA.match(huella):
                raise ValueError(
                    "QUECOMO_ANDROID_SHA256 debe contener huellas con el formato "
                    f"AB:CD:...:EF (32 pares hexadecimales). Recibido: {huella!r}"
                )

    @classmethod
    def desde_entorno(cls, entorno: Mapping[str, str] | None = None) -> ConfiguracionMovil:
        e = os.environ if entorno is None else entorno
        huellas = tuple(h.upper() for h in re.split(r"[,\s]+", e.get("QUECOMO_ANDROID_SHA256", "")) if h)
        return cls(
            paquete_android=e.get("QUECOMO_ANDROID_PAQUETE", "").strip() or PAQUETE_PREDETERMINADO,
            huellas_sha256=huellas,
            responsable=e.get("QUECOMO_RESPONSABLE", "").strip(),
            correo_contacto=e.get("QUECOMO_CORREO_CONTACTO", "").strip(),
            domicilio=e.get("QUECOMO_DOMICILIO", "").strip(),
        )

    def enlaces_de_activos(self) -> list[dict]:
        """Contenido de ``/.well-known/assetlinks.json``."""
        if not self.huellas_sha256:
            return []
        return [
            {
                "relation": ["delegate_permission/common.handle_all_urls"],
                "target": {
                    "namespace": "android_app",
                    "package_name": self.paquete_android,
                    "sha256_cert_fingerprints": list(self.huellas_sha256),
                },
            }
        ]

    def aviso_privacidad(self) -> str:
        pendiente = "[pendiente: configura {}]".format
        valores = {
            "responsable": self.responsable or pendiente("QUECOMO_RESPONSABLE"),
            "correo": self.correo_contacto or pendiente("QUECOMO_CORREO_CONTACTO"),
            "domicilio": self.domicilio or pendiente("QUECOMO_DOMICILIO"),
            "fecha": FECHA_AVISO,
        }
        plantilla = Template((ESTATICOS / "privacidad.html").read_text(encoding="utf-8"))
        return plantilla.substitute({k: html.escape(v, quote=True) for k, v in valores.items()})


def manifiesto_web() -> dict:
    """Manifiesto de la aplicación web progresiva (PWA)."""
    iconos = "/recursos/iconos"
    return {
        "id": "/",
        "name": "¿Qué Como?",
        "short_name": "Qué Como",
        "description": "Encuentra, compara y evalúa restaurantes con reseñas respaldadas por consumos reales.",
        "lang": "es-MX",
        "dir": "ltr",
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "orientation": "any",
        "background_color": NOCHE,
        "theme_color": NOCHE,
        "categories": ["food", "lifestyle"],
        "icons": [
            {"src": f"{iconos}/icono-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": f"{iconos}/icono-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
            {"src": f"{iconos}/icono-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        ],
    }


def crear_servidor(
    demo: gr.Blocks | None = None,
    configuracion: ConfiguracionMovil | None = None,
) -> FastAPI:
    """Crea la aplicación FastAPI con las rutas propias y Gradio montado en ``/``.

    Las rutas propias se registran **antes** de montar Gradio para que tengan
    prioridad (por ejemplo, ``/manifest.json``, que Gradio también define).
    """
    demo = demo or construir_interfaz()
    configuracion = configuracion or ConfiguracionMovil.desde_entorno()
    servidor = FastAPI(title="¿Qué Como?", docs_url=None, redoc_url=None, openapi_url=None)

    @servidor.get("/salud", include_in_schema=False)
    def salud() -> dict:
        return {"estado": "ok", "version": __version__}

    @servidor.get("/manifest.json", include_in_schema=False)
    @servidor.get("/manifest.webmanifest", include_in_schema=False)
    def manifiesto() -> JSONResponse:
        return JSONResponse(manifiesto_web(), media_type="application/manifest+json")

    @servidor.get("/.well-known/assetlinks.json", include_in_schema=False)
    def assetlinks() -> JSONResponse:
        return JSONResponse(configuracion.enlaces_de_activos(), headers={"Cache-Control": "public, max-age=300"})

    @servidor.get("/sw.js", include_in_schema=False)
    def service_worker() -> FileResponse:
        return FileResponse(
            ESTATICOS / "sw.js",
            media_type="text/javascript",
            headers={"Cache-Control": "no-cache", "Service-Worker-Allowed": "/"},
        )

    @servidor.get("/offline.html", include_in_schema=False)
    def sin_conexion() -> FileResponse:
        return FileResponse(ESTATICOS / "offline.html", media_type="text/html")

    @servidor.get("/privacidad", include_in_schema=False)
    def privacidad() -> HTMLResponse:
        return HTMLResponse(configuracion.aviso_privacidad())

    servidor.mount("/recursos/iconos", StaticFiles(directory=ESTATICOS / "iconos"), name="iconos")

    return gr.mount_gradio_app(
        servidor,
        demo,
        path="/",
        footer_links=[],
        favicon_path=str(ESTATICOS / "iconos" / "favicon.png"),
        theme=TEMA,
        css=CSS,
        head=CABECERA_HTML,
        pwa=False,
        ssr_mode=False,
    )


__all__ = ["CABECERA_HTML", "ConfiguracionMovil", "crear_servidor", "manifiesto_web"]
