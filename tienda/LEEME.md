# Recursos para la ficha de Google Play

Todo lo que pide Play Console en **Crecimiento → Presencia en Play Store → Ficha principal de Play Store**.

| Archivo | Campo en Play Console | Requisito de Google Play |
|---|---|---|
| `icono-512.png` | Ícono de la app | 512 × 512 px, PNG |
| `grafico-destacado.png` | Gráfico de funciones | 1024 × 500 px, PNG/JPG sin transparencia |
| `capturas/telefono-01…06.png` | Capturas de pantalla del teléfono | 2 a 8 imágenes; estas son de 1080 × 1920 (9:16) |

Se regeneran con `python herramientas/generar_iconos.py` (íconos) y
`python herramientas/recursos_tienda.py` (capturas y gráfico, con la app en ejecución).

## Textos (español de Latinoamérica, `es-419`)

**Nombre de la app** (máx. 30): 
```
¿Qué Como? – Restaurantes
```

**Descripción breve** (máx. 80):
```
Busca, compara y evalúa restaurantes. Prototipo académico con datos de ejemplo.
```

**Descripción completa** (máx. 4000):
```
¿Qué Como? te ayuda a decidir dónde comer con información clara y reseñas en las que puedes confiar.

ESTA VERSIÓN ES UN PROTOTIPO ACADÉMICO: todos los restaurantes, usuarios y reseñas son ficticios y sirven para mostrar cómo funciona la app.

QUÉ PUEDES HACER
• Buscar restaurantes por tipo de comida, precio, distancia, horario, forma de pago en el local, calificación y promociones.
• Ver la ficha de cada restaurante: menú, horario, ubicación, promociones y reseñas.
• Comparar de 2 a 3 restaurantes lado a lado.
• Evaluar un restaurante después de tu consumo.

LA REGLA DE CONFIANZA
Solo puede evaluar quien tuvo un consumo real: el restaurante confirma y completa el consumo, y cada consumo permite una sola evaluación. Así las calificaciones reflejan visitas reales, no opiniones inventadas.

PRUEBA LOS TRES ROLES
Con el selector «Sesión de demostración» puedes entrar como cliente, como dueño de restaurante (para confirmar consumos y editar el menú) o como administrador (para moderar reseñas).

PRIVACIDAD
No necesitas cuenta. La app no pide tu nombre, correo ni ubicación, no tiene publicidad y no procesa pagos: el pago se hace en el restaurante. Lo que escribes solo lo ves tú y se borra al cerrar la app.

Proyecto de la materia de Ingeniería de Software, hecho en Hermosillo, Sonora.
```

**Categoría:** Comida y bebida · **Etiquetas sugeridas:** Restaurantes, Reseñas, Guía local

**Datos de contacto:** el correo de `QUECOMO_CORREO_CONTACTO` (obligatorio y público).
**Política de privacidad:** `https://TU-DOMINIO/privacidad`
