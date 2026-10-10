"""Genera las capturas y el gráfico destacado para la ficha de Google Play.

Requisitos: la app ejecutándose (``python app.py``) y Playwright con Chromium:

    pip install playwright && playwright install chromium
    python herramientas/recursos_tienda.py                    # usa http://127.0.0.1:7860
    python herramientas/recursos_tienda.py --url http://127.0.0.1:7861 --fuentes DIR

``--fuentes`` (opcional) es una carpeta con ``manrope-latin-{400..800}-normal.woff2``
(por ejemplo, de ``npm i @fontsource/manrope``). Sirve cuando el equipo no tiene
acceso a Google Fonts; si se omite, se usa la fuente que cargue la página.

Salida en ``tienda/``:
    capturas/telefono-0N-*.png   1080 × 1920 (9:16), formato que acepta Google Play
    grafico-destacado.png        1024 × 500, sin transparencia
"""

from __future__ import annotations

import argparse
from pathlib import Path

from playwright.sync_api import BrowserContext, Page, sync_playwright

RAIZ = Path(__file__).resolve().parent.parent
TIENDA = RAIZ / "tienda"
PESOS = (400, 500, 600, 700, 800)
CHROMIUM: str | None = None  # ruta opcional a un Chromium ya instalado (--chromium)


def _rutas_fuentes(ctx: BrowserContext, carpeta: Path | None) -> None:
    if carpeta is None:
        return
    css = "\n".join(
        f"@font-face{{font-family:'Manrope';font-weight:{w};font-display:block;"
        f"src:url(https://fonts.gstatic.com/local/manrope-{w}.woff2) format('woff2');}}"
        for w in PESOS
    )
    ctx.route("https://fonts.googleapis.com/**", lambda r: r.fulfill(content_type="text/css", body=css))

    def fuente(r):  # type: ignore[no-untyped-def]
        peso = r.request.url.rsplit("-", 1)[1].split(".")[0]
        r.fulfill(content_type="font/woff2", body=(carpeta / f"manrope-latin-{peso}-normal.woff2").read_bytes())

    ctx.route("https://fonts.gstatic.com/local/**", fuente)


def _pestana(p: Page, nombre: str) -> None:
    visible = p.locator('[role="tablist"] button[role="tab"]', has_text=nombre)
    if visible.count():
        visible.first.click()
    else:
        p.locator('button[aria-label="More tabs"]').click()
        p.wait_for_timeout(300)
        p.locator('button[aria-label="More tabs"] + div button', has_text=nombre).first.click()
    p.wait_for_timeout(900)


def _elegir(p: Page, etiqueta: str, opcion: str) -> None:
    campo = p.get_by_label(etiqueta).first
    campo.click()
    campo.fill(opcion[:8])  # filtra la lista de opciones
    p.wait_for_timeout(400)
    p.get_by_role("option", name=opcion).first.click()
    p.wait_for_timeout(500)


def capturas(url: str, fuentes: Path | None) -> None:
    salida = TIENDA / "capturas"
    salida.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        navegador = pw.chromium.launch(executable_path=CHROMIUM, args=["--no-proxy-server"])
        ctx = navegador.new_context(
            viewport={"width": 360, "height": 640}, device_scale_factor=3,
            is_mobile=True, has_touch=True, locale="es-MX",
        )
        ctx.set_default_timeout(20000)
        _rutas_fuentes(ctx, fuentes)
        p = ctx.new_page()
        p.goto(url, wait_until="load")
        p.wait_for_selector("table")
        p.wait_for_timeout(1500)

        def foto(nombre: str) -> None:
            p.wait_for_timeout(500)
            p.screenshot(path=salida / f"telefono-{nombre}.png")
            print("  ", (salida / f"telefono-{nombre}.png").relative_to(RAIZ))

        def arriba() -> None:
            p.evaluate("window.scrollTo(0, 0)")

        foto("01-inicio")

        p.get_by_label("¿Qué se te antoja?").fill("tacos")
        p.get_by_role("button", name="Buscar", exact=True).click()
        p.wait_for_timeout(1000)
        p.get_by_text("restaurante(s) encontrado(s)").scroll_into_view_if_needed()
        p.evaluate("window.scrollBy(0, -12)")
        foto("02-busqueda")

        arriba()
        _pestana(p, "Ficha")
        _elegir(p, "Restaurante", "Tacos La Lumbre")
        p.locator("h2", has_text="Tacos La Lumbre").first.scroll_into_view_if_needed()
        p.evaluate("window.scrollBy(0, -24)")
        foto("03-ficha")

        arriba()
        _pestana(p, "Comparar")
        varios = p.get_by_label("Elige de 2 a 3 restaurantes").first
        varios.click()  # la lista queda abierta mientras se eligen varios
        for nombre in ("Tacos La Lumbre", "Asadero Los Mezquites"):
            varios.fill(nombre[:8])
            p.wait_for_timeout(400)
            p.get_by_role("option", name=nombre).first.click()
            p.wait_for_timeout(400)
        p.keyboard.press("Escape")
        p.get_by_role("button", name="Comparar", exact=True).click()
        p.wait_for_timeout(1200)
        p.get_by_role("button", name="Comparar", exact=True).scroll_into_view_if_needed()
        p.evaluate("window.scrollBy(0, 200)")
        foto("04-comparar")

        arriba()
        _pestana(p, "Evaluar")
        p.get_by_role("button", name="Evaluar restaurante").click()
        p.wait_for_timeout(1000)
        p.get_by_label("★★★★★ 5").last.check()
        p.get_by_label("Comentario").fill("Excelentes tacos al carbón y muy buena atención.")
        p.get_by_role("button", name="Evaluar restaurante").scroll_into_view_if_needed()
        p.evaluate("window.scrollBy(0, -60)")
        foto("05-evaluar")

        p.get_by_role("button", name="Publicar evaluación").click()
        p.wait_for_timeout(1200)
        foto("06-publicada")
        navegador.close()


GRAFICO = """<!doctype html><html><head><meta charset="utf-8"><style>
html,body{margin:0;width:1024px;height:500px;overflow:hidden}
body{font-family:Manrope,system-ui,sans-serif;color:#fff;position:relative;
 background:radial-gradient(60% 95% at 80% 125%,#FFC07A 0%,#F27A1A 28%,rgba(242,122,26,.45) 46%,rgba(242,122,26,0) 66%),
 linear-gradient(180deg,#0E1A31 0%,#12203A 55%,#1A3868 100%)}
.barra{position:absolute;left:0;right:0;bottom:0;height:8px;background:linear-gradient(90deg,#2456A6,#F27A1A)}
.c{position:absolute;left:72px;top:96px}
.marca{display:flex;align-items:center;gap:22px}
h1{margin:0;font-size:84px;font-weight:800;letter-spacing:-.035em;line-height:1}
p{margin:26px 0 0;font-size:31px;font-weight:500;color:#D5DFEF;max-width:22ch;line-height:1.3}
.chip{display:inline-block;margin-top:30px;padding:9px 20px;border-radius:999px;font-size:21px;font-weight:600;
 color:#FFE4CC;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.18)}
</style></head><body>
<div class="c"><div class="marca">
<svg width="84" height="84" viewBox="0 0 44 44"><defs><clipPath id="h"><rect width="44" height="28"/></clipPath></defs>
<circle cx="22" cy="28" r="15" fill="#F27A1A" clip-path="url(#h)"/><rect x="4" y="31" width="36" height="3" rx="1.5" fill="#FFC799"/>
<rect x="10" y="37" width="24" height="3" rx="1.5" fill="#8EADDF"/></svg>
<h1>¿Qué Como?</h1></div>
<p>Elige dónde comer con reseñas de quienes realmente fueron.</p>
<span class="chip">Buscar · Comparar · Evaluar</span></div>
<div class="barra"></div></body></html>"""


def grafico_destacado(fuentes: Path | None) -> None:
    with sync_playwright() as pw:
        navegador = pw.chromium.launch(executable_path=CHROMIUM, args=["--no-proxy-server"])
        ctx = navegador.new_context(viewport={"width": 1024, "height": 500})
        p = ctx.new_page()
        html = GRAFICO
        if fuentes is not None:
            import base64

            def cara(w: int) -> str:
                datos = base64.b64encode((fuentes / f"manrope-latin-{w}-normal.woff2").read_bytes()).decode()
                return f"@font-face{{font-family:Manrope;font-weight:{w};src:url(data:font/woff2;base64,{datos}) format('woff2');}}"

            caras = "".join(cara(w) for w in PESOS)
            html = html.replace("<style>", "<style>" + caras, 1)
        p.set_content(html)
        p.wait_for_timeout(500)
        destino = TIENDA / "grafico-destacado.png"
        p.screenshot(path=destino, omit_background=False)
        navegador.close()
    from PIL import Image

    Image.open(destino).convert("RGB").save(destino)  # Google Play: sin canal alfa
    print("  ", destino.relative_to(RAIZ))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", default="http://127.0.0.1:7860")
    parser.add_argument("--fuentes", type=Path, default=None)
    parser.add_argument("--chromium", default=None, help="ruta a un ejecutable de Chromium (opcional)")
    args = parser.parse_args()
    CHROMIUM = args.chromium
    print("Google Play:")
    grafico_destacado(args.fuentes)
    capturas(args.url, args.fuentes)
