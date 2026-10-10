"""Punto de entrada de ¿Qué Como?

Uso local:
    python app.py                      → http://127.0.0.1:7860

En la nube (Render, Railway, etc.) la plataforma define la variable PORT;
en ese caso la app escucha en 0.0.0.0:$PORT automáticamente.

El servidor sirve la interfaz Gradio y, además, lo que necesita la app de
Android (manifiesto web, service worker, /.well-known/assetlinks.json y el
aviso de privacidad). Ver ``src/quecomo/presentacion/servidor.py`` y
``docs/13_android_y_google_play.md``.

Variables de entorno opcionales:
    PORT                      Puerto asignado por la plataforma de despliegue.
    QUECOMO_ZONA_HORARIA      Zona horaria para «abierto ahora» (por defecto America/Hermosillo).
    QUECOMO_DATOS_POR_SESION  1 (defecto): cada visitante tiene sus propios datos; 0: compartidos.
    QUECOMO_ANDROID_PAQUETE   Paquete de la app Android (por defecto mx.quecomo.app).
    QUECOMO_ANDROID_SHA256    Huella(s) SHA-256 del certificado de firma, separadas por comas.
    QUECOMO_RESPONSABLE, QUECOMO_CORREO_CONTACTO, QUECOMO_DOMICILIO
                              Datos del aviso de privacidad (/privacidad).
    GRADIO_SERVER_NAME        Dirección de escucha (sobrescribe el valor automático).
    GRADIO_SERVER_PORT        Puerto (sobrescribe el valor automático).
"""

import os
import sys
from pathlib import Path

# Permite ejecutar `python app.py` sin instalar el paquete.
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import uvicorn  # noqa: E402

from quecomo.presentacion.servidor import crear_servidor  # noqa: E402

app = crear_servidor()


def configuracion_servidor() -> tuple[str, int]:
    """Host y puerto: en la nube usa 0.0.0.0:$PORT; en local, 127.0.0.1:7860."""
    puerto_nube = os.getenv("PORT")
    host = os.getenv("GRADIO_SERVER_NAME") or ("0.0.0.0" if puerto_nube else "127.0.0.1")
    puerto = int(os.getenv("GRADIO_SERVER_PORT") or puerto_nube or 7860)
    return host, puerto


if __name__ == "__main__":
    host, puerto = configuracion_servidor()
    # proxy_headers: detrás del proxy HTTPS de Render, respeta X-Forwarded-Proto
    # para que las URL que genera Gradio usen https.
    uvicorn.run(app, host=host, port=puerto, proxy_headers=True, forwarded_allow_ips="*")
