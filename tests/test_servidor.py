"""Pruebas del servidor web y de lo que necesita la app Android (PWA / TWA)."""

from __future__ import annotations

import copy
import re
from pathlib import Path

import gradio as gr
import pytest
from fastapi.testclient import TestClient

from quecomo.configuracion import crear_aplicacion, datos_por_sesion
from quecomo.presentacion.interfaz import construir_interfaz
from quecomo.presentacion.servidor import (
    ESTATICOS,
    PAQUETE_PREDETERMINADO,
    ConfiguracionMovil,
    crear_servidor,
    manifiesto_web,
)
from quecomo.presentacion.vista import Vista

RAIZ = Path(__file__).resolve().parent.parent
HUELLA = "14:6D:E9:83:C5:73:06:50:D8:EE:B9:95:2F:34:FC:64:16:A0:83:42:E6:1D:BE:A8:8A:04:96:B2:3F:CF:44:E5"


@pytest.fixture(scope="module")
def cliente():
    configuracion = ConfiguracionMovil(
        paquete_android="mx.quecomo.app",
        huellas_sha256=(HUELLA,),
        responsable="Equipo <¿Qué Como?>",
        correo_contacto="contacto@ejemplo.com",
        domicilio="Hermosillo, Sonora",
    )
    servidor = crear_servidor(construir_interfaz(crear_aplicacion()), configuracion)
    with TestClient(servidor) as c:
        yield c


# --------------------------------------------------------------------------- #
# Rutas
# --------------------------------------------------------------------------- #


def test_salud(cliente):
    respuesta = cliente.get("/salud")
    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "ok"


def test_la_interfaz_se_sirve_en_la_raiz_con_service_worker(cliente):
    respuesta = cliente.get("/")
    assert respuesta.status_code == 200
    # Gradio inserta la cabecera propia (service worker, color de tema) al cargar.
    assert "serviceWorker" in respuesta.text
    assert "theme-color" in respuesta.text


@pytest.mark.parametrize("ruta", ["/manifest.json", "/manifest.webmanifest"])
def test_manifiesto_web_instalable(cliente, ruta):
    respuesta = cliente.get(ruta)
    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"].startswith("application/manifest+json")
    m = respuesta.json()
    assert m["name"] == "¿Qué Como?"
    assert m["start_url"] == "/" and m["scope"] == "/"
    assert m["display"] == "standalone"
    tamanos = {(i["sizes"], i["purpose"]) for i in m["icons"]}
    assert {("192x192", "any"), ("512x512", "any"), ("512x512", "maskable")} <= tamanos


def test_los_iconos_del_manifiesto_existen(cliente):
    for icono in manifiesto_web()["icons"]:
        respuesta = cliente.get(icono["src"])
        assert respuesta.status_code == 200, icono["src"]
        assert respuesta.headers["content-type"] == "image/png"


def test_assetlinks_declara_paquete_y_huella(cliente):
    respuesta = cliente.get("/.well-known/assetlinks.json")
    assert respuesta.status_code == 200
    [declaracion] = respuesta.json()
    assert declaracion["relation"] == ["delegate_permission/common.handle_all_urls"]
    assert declaracion["target"] == {
        "namespace": "android_app",
        "package_name": "mx.quecomo.app",
        "sha256_cert_fingerprints": [HUELLA],
    }


def test_service_worker_controla_todo_el_sitio(cliente):
    respuesta = cliente.get("/sw.js")
    assert respuesta.status_code == 200
    assert "javascript" in respuesta.headers["content-type"]
    assert respuesta.headers["service-worker-allowed"] == "/"
    assert respuesta.headers["cache-control"] == "no-cache"


def test_pagina_sin_conexion(cliente):
    respuesta = cliente.get("/offline.html")
    assert respuesta.status_code == 200
    assert "/salud" in respuesta.text  # reintenta sola


def test_aviso_de_privacidad_publico_y_escapado(cliente):
    respuesta = cliente.get("/privacidad")
    assert respuesta.status_code == 200
    assert "Aviso de privacidad" in respuesta.text
    assert "contacto@ejemplo.com" in respuesta.text
    assert "Equipo &lt;¿Qué Como?&gt;" in respuesta.text  # sin inyección de HTML
    assert "$responsable" not in respuesta.text


# --------------------------------------------------------------------------- #
# Configuración
# --------------------------------------------------------------------------- #


def test_sin_huellas_assetlinks_es_una_lista_vacia():
    assert ConfiguracionMovil().enlaces_de_activos() == []


def test_configuracion_desde_entorno_normaliza_huellas():
    c = ConfiguracionMovil.desde_entorno(
        {"QUECOMO_ANDROID_SHA256": f" {HUELLA.lower()} ,\n{HUELLA} ", "QUECOMO_ANDROID_PAQUETE": "io.github.equipo.quecomo"}
    )
    assert c.huellas_sha256 == (HUELLA, HUELLA)
    assert c.paquete_android == "io.github.equipo.quecomo"


def test_configuracion_por_defecto():
    c = ConfiguracionMovil.desde_entorno({})
    assert c.paquete_android == PAQUETE_PREDETERMINADO
    assert "[pendiente: configura QUECOMO_RESPONSABLE]" in c.aviso_privacidad()


@pytest.mark.parametrize("huella", ["14:6D", "SHA256:14:6D", HUELLA.replace(":", "")])
def test_huella_invalida_falla_al_iniciar(huella):
    with pytest.raises(ValueError, match="QUECOMO_ANDROID_SHA256"):
        ConfiguracionMovil.desde_entorno({"QUECOMO_ANDROID_SHA256": huella})


@pytest.mark.parametrize("paquete", ["quecomo", "mx.que-como.app", "1mx.app"])
def test_paquete_invalido_falla_al_iniciar(paquete):
    with pytest.raises(ValueError, match="QUECOMO_ANDROID_PAQUETE"):
        ConfiguracionMovil(paquete_android=paquete)


def test_paquete_coincide_en_android_render_y_servidor():
    """El mismo nombre de paquete en los tres lugares, o la TWA no se verifica."""
    gradle = (RAIZ / "android" / "gradle.properties").read_text(encoding="utf-8")
    render = (RAIZ / "render.yaml").read_text(encoding="utf-8")
    [en_gradle] = re.findall(r"^quecomo\.applicationId=(\S+)$", gradle, re.M)
    [en_render] = re.findall(r"QUECOMO_ANDROID_PAQUETE\s*\n\s*value:\s*(\S+)", render)
    assert en_gradle == en_render == PAQUETE_PREDETERMINADO


def test_estaticos_empaquetados():
    for nombre in ("sw.js", "offline.html", "privacidad.html", "iconos/favicon.png"):
        assert (ESTATICOS / nombre).is_file(), nombre


# --------------------------------------------------------------------------- #
# Datos por sesión
# --------------------------------------------------------------------------- #


def _estado(demo: gr.Blocks) -> gr.State:
    [estado] = [b for b in demo.blocks.values() if isinstance(b, gr.State)]
    return estado


def test_modo_aislado_crea_una_vista_nueva_por_sesion():
    demo = construir_interfaz(fabrica_sesion=crear_aplicacion)
    inicial = _estado(demo).value
    assert callable(inicial)
    a, b = inicial(), inicial()
    assert isinstance(a, Vista) and a is not b and a.app is not b.app
    assert demo.state_session_capacity == 1000


def test_lo_que_registra_una_sesion_no_lo_ve_otra():
    inicial = _estado(construir_interfaz(fabrica_sesion=crear_aplicacion)).value
    ana, otra_persona = inicial(), inicial()
    assert ana.primera_evaluable(1) == 2
    mensaje, _ = ana.registrar_evaluacion(1, 2, 5, "Excelente servicio y comida.")
    assert mensaje.startswith("✅")
    assert ana.primera_evaluable(1) != 2
    assert otra_persona.primera_evaluable(1) == 2


def test_modo_compartido_usa_la_misma_vista(app_demo):
    inicial = _estado(construir_interfaz(app_demo)).value
    assert inicial() is inicial()
    assert inicial().app is app_demo


def test_gradio_puede_copiar_la_vista_sin_duplicarla(app_demo):
    """Gradio aplica deepcopy al estado; la vista debe conservarse por referencia."""
    vista = Vista(app_demo)
    assert copy.deepcopy(vista) is vista


@pytest.mark.parametrize(
    ("valor", "esperado"), [(None, True), ("1", True), ("si", True), ("0", False), ("false", False), ("No", False)]
)
def test_datos_por_sesion_desde_entorno(monkeypatch, valor, esperado):
    if valor is None:
        monkeypatch.delenv("QUECOMO_DATOS_POR_SESION", raising=False)
    else:
        monkeypatch.setenv("QUECOMO_DATOS_POR_SESION", valor)
    assert datos_por_sesion() is esperado
