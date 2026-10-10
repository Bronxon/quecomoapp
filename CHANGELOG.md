# Registro de cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/). Versionado [SemVer](https://semver.org/lang/es/).

## [0.4.0] — 2026-10-10

### Agregado
- **App para Android** (`android/`): Trusted Web Activity con `androidbrowserhelper 2.7.3`, `targetSdk 36` (requisito de Google Play desde el 31/08/2026), `minSdk 24`, ícono adaptativo con versión monocromática y pantalla de bienvenida.
- `presentacion/servidor.py`: FastAPI con Gradio montado en `/` y rutas para la app: `/manifest.json`, `/sw.js`, `/offline.html`, `/.well-known/assetlinks.json`, `/privacidad`, `/salud`.
- Service worker: si no hay conexión o el servidor tarda (plan gratuito «despertando»), muestra «Conectando…» y recarga solo al recuperar la conexión.
- Aviso de privacidad público (`/privacidad`), configurable con variables de entorno.
- Flujo `android.yml`: compila el AAB firmado con la llave de subida y publica la huella SHA-256.
- Recursos de la ficha de Google Play (`tienda/`) y scripts que los regeneran (`herramientas/`).
- `docs/13_android_y_google_play.md`. 30 pruebas nuevas (146 en total).

### Cambiado
- **Datos por sesión** (`QUECOMO_DATOS_POR_SESION=1` por defecto): cada visitante trabaja con su propia copia de los datos de demostración; nadie ve ni altera lo que registra otra persona.
- Interfaz móvil: sin desplazamiento horizontal en pantallas de 360 px, barra de sesión en una columna, áreas táctiles de 44 px y menú «Más» para las pestañas que no caben. La pestaña «Ficha del restaurante» ahora se llama «Ficha».
- `app.py` arranca con Uvicorn (`proxy_headers` para HTTPS detrás de Render). `render.yaml` con `healthCheckPath: /salud` y las variables nuevas.

### Corregido
- Se restauran `.python-version` (antes `python-version`, que Render ignoraba) y `.github/workflows/pruebas.yml` (la insignia del README apuntaba a un flujo inexistente). Se agrega `.gitignore`.

## [0.3.0] — 2026-10-10

### Eliminado
- Pestaña **«Mis transacciones»**. Ninguna pestaña se llama ya «Transacciones»; en el panel del locatario la sub-pestaña ahora es «Confirmar consumos».

### Cambiado
- El registro de consumo (HU-06) pasa a una sección plegable **«Registrar un consumo nuevo»** dentro de **Evaluar**.
- Nueva identidad visual «atardecer en el desierto»: paleta naranja–azul, tipografía Manrope, encabezado con degradado, pestañas sin emojis con subrayado naranja y modo oscuro. Todo en `presentacion/tema.py`.
- Lenguaje de la interfaz: «consumo» en lugar de «transacción»; los motivos de rechazo se redactan en la vista a partir de `MotivoRechazo`.
- Botones: «Publicar evaluación», «Registrar consumo», «Cancelar consumo».
- Capturas de pantalla actualizadas.

### Agregado
- 2 pruebas de presentación (116 en total).

## [0.2.0] — 2026-10-10

### Eliminado
- Opción de pago en línea **«Transferencia»** en toda la interfaz: filtro de búsqueda, ficha del restaurante, comparación, formulario del locatario y datos de demostración.

### Agregado
- **RN-07:** ¿Qué Como? no ofrece ni procesa pagos en línea. Solo se aceptan formas de pago en el local (efectivo, tarjeta de débito, tarjeta de crédito), validadas en el dominio.
- Aviso en «Mis transacciones» y en «Acerca de»: la app no procesa pagos; se paga en el restaurante.
- 4 pruebas nuevas (114 en total).

### Cambiado
- Etiquetas: «Forma de pago en el local», «Formas de pago aceptadas en el local», «Pago en el local» (comparación), «Importe consumido (MXN)».

## [0.1.1] — 2026-10-10

### Agregado
- Despliegue en Render: `render.yaml` y `.python-version` (Python 3.13).

### Corregido
- `app.py` escucha en `0.0.0.0:$PORT` cuando la plataforma define `PORT`; en local sigue usando `127.0.0.1:7860`.

## [0.1.0] — 2026-10-10

Primera versión del MVP, construida a partir del *Documento Fundamental de Desarrollo* (Actividades 1–4).

### Agregado
- Dominio: `Usuario`, `Restaurante`, `Transaccion` (máquina de estados con historial), `Evaluacion`, `Menu`, `Producto`, `Promocion`, `Ubicacion`, `Horario`.
- Caso de uso CU-01 con `ControladorEvaluacion` y todas sus extensiones.
- Búsqueda con 8 filtros y 4 criterios de orden; comparación de 2 a 3 restaurantes; ficha completa.
- Registro y control de transacciones con autorización por rol (CA-08).
- Panel del locatario (HU-09, HU-10, HU-11) y panel de administración con moderación.
- Interfaz web en Gradio con datos ficticios e inicio de sesión simulado.
- 110 pruebas automatizadas y CI en GitHub Actions.
- Documentación en español: visión, historias, requisitos, CU-01, dominio, arquitectura, diseño dinámico, trazabilidad, pruebas, análisis legal preliminar y validación de negocio.

### Decisiones respecto al documento original
- `buscarPorUsuarioYEstablecimiento` devuelve una lista (puede haber varias transacciones).
- `Evaluacion.registrar()` se asignó al repositorio (`guardar`) para reducir acoplamiento.
- Se agregaron `Horario`, roles de usuario, estado de evaluación y la relación Locatario → Restaurante.
- El administrador no puede confirmar ni completar transacciones.
- El ranking muestra el promedio simple pero ordena con un promedio ponderado.

### Pendiente
- HU-12 / RN-02 (evaluación del restaurante hacia el cliente).
- Persistencia, autenticación real, aviso de privacidad y términos de uso.
- Mitigación del sesgo del locatario.
