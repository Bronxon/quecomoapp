"""Genera los íconos de ¿Qué Como? para la web (PWA) y para Android.

La marca es la misma del encabezado (``presentacion/tema.py``): un sol a medio
ocultarse en el horizonte, sobre el azul noche del cielo.

Uso (desde la raíz del repositorio):

    python herramientas/generar_iconos.py

Escribe en:
    src/quecomo/presentacion/estaticos/iconos/   íconos web y favicon
    android/app/src/main/res/                    íconos del lanzador y splash
    tienda/                                      ícono de 512 px para Google Play

Solo requiere Pillow (ya viene como dependencia de Gradio).
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

RAIZ = Path(__file__).resolve().parent.parent
WEB = RAIZ / "src" / "quecomo" / "presentacion" / "estaticos" / "iconos"
RES = RAIZ / "android" / "app" / "src" / "main" / "res"
TIENDA = RAIZ / "tienda"

NOCHE_ARRIBA = (14, 26, 49)  # #0E1A31
NOCHE = (18, 32, 58)  # #12203A
NOCHE_ABAJO = (26, 56, 104)  # #1A3868
ATARDECER = (242, 122, 26)  # #F27A1A
ARENA = (255, 199, 153)  # #FFC799
CIELO_CLARO = (142, 173, 223)  # #8EADDF
BLANCO = (255, 255, 255)

SUPER = 4  # sobremuestreo para bordes suaves

# Densidades de Android: factor respecto a mdpi.
DENSIDADES = {"mdpi": 1, "hdpi": 1.5, "xhdpi": 2, "xxhdpi": 3, "xxxhdpi": 4}


# --------------------------------------------------------------------------- #
# Dibujo
# --------------------------------------------------------------------------- #


def _degradado(lado: int) -> Image.Image:
    """Cielo nocturno: degradado vertical de tres paradas."""
    img = Image.new("RGB", (1, lado))
    for y in range(lado):
        t = y / max(lado - 1, 1)
        if t < 0.55:
            a, b, k = NOCHE_ARRIBA, NOCHE, t / 0.55
        else:
            a, b, k = NOCHE, NOCHE_ABAJO, (t - 0.55) / 0.45
        img.putpixel((0, y), tuple(round(a[i] + (b[i] - a[i]) * k) for i in range(3)))
    return img.resize((lado, lado)).convert("RGBA")


def _marca(lado: int, ancho_marca: float, monocromo: bool = False, brillo: bool = True) -> Image.Image:
    """Dibuja la marca centrada en un lienzo transparente de ``lado`` px.

    La marca original mide 36 × 27 unidades (SVG de 44 × 44, x 4–40, y 13–40).
    ``ancho_marca`` es la fracción del lienzo que ocupa a lo ancho.
    """
    L = lado * SUPER
    capa = Image.new("RGBA", (L, L), (0, 0, 0, 0))
    u = ancho_marca * L / 36  # píxeles por unidad
    x0 = L / 2 - 18 * u  # unidad x=4 → borde izquierdo
    y0 = L / 2 - 13.5 * u - 13 * u  # centra verticalmente el rango y 13–40

    def X(v: float) -> float:
        return x0 + (v - 4) * u

    def Y(v: float) -> float:
        return y0 + v * u

    sol = BLANCO if monocromo else ATARDECER
    linea1 = BLANCO if monocromo else ARENA
    linea2 = BLANCO if monocromo else CIELO_CLARO

    if brillo and not monocromo:
        halo = Image.new("RGBA", (L, L), (0, 0, 0, 0))
        ImageDraw.Draw(halo).ellipse(
            [X(22 - 21), Y(28 - 21), X(22 + 21), Y(28 + 21)], fill=(*ATARDECER, 95)
        )
        halo = halo.filter(ImageFilter.GaussianBlur(radius=7 * u))
        capa.alpha_composite(halo)

    # Sol recortado por el horizonte (y < 28).
    disco = Image.new("RGBA", (L, L), (0, 0, 0, 0))
    ImageDraw.Draw(disco).ellipse([X(7), Y(13), X(37), Y(43)], fill=(*sol, 255))
    recorte = Image.new("L", (L, L), 0)
    ImageDraw.Draw(recorte).rectangle([0, 0, L, Y(28)], fill=255)
    disco.putalpha(Image.composite(disco.getchannel("A"), Image.new("L", (L, L), 0), recorte))
    capa.alpha_composite(disco)

    d = ImageDraw.Draw(capa)
    d.rounded_rectangle([X(4), Y(31), X(40), Y(34)], radius=1.5 * u, fill=(*linea1, 255))
    d.rounded_rectangle([X(10), Y(37), X(34), Y(40)], radius=1.5 * u, fill=(*linea2, 255))
    return capa.resize((lado, lado), Image.LANCZOS)


def icono_completo(lado: int, ancho_marca: float = 0.58, redondeo: float = 0.0) -> Image.Image:
    """Ícono con fondo (web, Play Store, lanzador heredado)."""
    fondo = _degradado(lado)
    fondo.alpha_composite(_marca(lado, ancho_marca))
    if redondeo:
        mascara = Image.new("L", (lado * SUPER,) * 2, 0)
        ImageDraw.Draw(mascara).rounded_rectangle(
            [0, 0, lado * SUPER - 1, lado * SUPER - 1], radius=redondeo * lado * SUPER, fill=255
        )
        fondo.putalpha(mascara.resize((lado, lado), Image.LANCZOS))
    return fondo


def circular(lado: int) -> Image.Image:
    img = icono_completo(lado, ancho_marca=0.5)
    mascara = Image.new("L", (lado * SUPER,) * 2, 0)
    ImageDraw.Draw(mascara).ellipse([0, 0, lado * SUPER - 1, lado * SUPER - 1], fill=255)
    img.putalpha(mascara.resize((lado, lado), Image.LANCZOS))
    return img


# --------------------------------------------------------------------------- #
# Salidas
# --------------------------------------------------------------------------- #


def _guardar(img: Image.Image, ruta: Path, sin_alfa: bool = False) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    if sin_alfa:
        img = img.convert("RGB")
    img.save(ruta, optimize=True)
    print("  ", ruta.relative_to(RAIZ))


def web() -> None:
    print("Web (PWA):")
    _guardar(icono_completo(192), WEB / "icono-192.png")
    _guardar(icono_completo(512), WEB / "icono-512.png")
    # «maskable»: la marca dentro del círculo seguro (80 % central).
    _guardar(icono_completo(512, ancho_marca=0.44), WEB / "icono-maskable-512.png")
    _guardar(icono_completo(180), WEB / "apple-touch-icon.png", sin_alfa=True)
    _guardar(icono_completo(64, ancho_marca=0.72, redondeo=0.22), WEB / "favicon.png")


def android() -> None:
    print("Android:")
    for nombre, f in DENSIDADES.items():
        carpeta = RES / f"mipmap-{nombre}"
        legado = round(48 * f)
        _guardar(icono_completo(legado, redondeo=0.12), carpeta / "ic_launcher.png")
        _guardar(circular(legado), carpeta / "ic_launcher_round.png")
        # Ícono adaptativo (108 dp): la zona segura es el círculo central de 66 dp.
        capa = round(108 * f)
        _guardar(_marca(capa, ancho_marca=0.42), carpeta / "ic_launcher_foreground.png")
        _guardar(_degradado(capa), carpeta / "ic_launcher_background.png", sin_alfa=True)
        _guardar(_marca(capa, ancho_marca=0.42, monocromo=True), carpeta / "ic_launcher_monochrome.png")
        # Imagen de la pantalla de bienvenida (160 dp).
        _guardar(_marca(round(160 * f), ancho_marca=0.9, brillo=False), RES / f"drawable-{nombre}" / "splash.png")


def tienda() -> None:
    print("Google Play:")
    _guardar(icono_completo(512), TIENDA / "icono-512.png")


if __name__ == "__main__":
    web()
    android()
    tienda()
