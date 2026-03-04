---
name: carousel-gen
description: Genera carruseles Instagram con estilo hand-drawn minimalista usando Kie AI (Nano Banana Pro). El usuario solo necesita dar el tema y numero de slides. El flujo auto-crea carpetas, genera contenido y produce imagenes 1080x1350px. Generacion en paralelo.
allowed-tools: Read, Write, Bash(python3:*), Bash(cd:*), Bash(curl:*), Bash(ls:*), Bash(mkdir:*), Bash(cp:*), Bash(export:*), Bash(pip3:*), Glob, Grep, AskUserQuestion, Edit
user-invocable: true
---

# Generador de Carruseles Instagram - Kie AI (Nano Banana Pro)

Skill para generar carruseles Instagram con estilo hand-drawn minimalista watercolor.
Todas las imagenes se generan EN PARALELO para maxima velocidad.

## Uso

```
/carousel-gen [tema] [numero_de_slides]
```

**Parametros:**
- `tema`: Tema del carrusel (ej: "5 herramientas IA para automatizar tu negocio")
- `numero_de_slides`: Cantidad de slides a generar (ej: 7). Default: 7

**Ejemplos:**
```
/carousel-gen 5 herramientas IA para emprendedores 7
/carousel-gen como usar ChatGPT para crear contenido 5
/carousel-gen tendencias de IA en 2026 8
```

## Workflow Automatico (4 pasos obligatorios)

**REGLA PRINCIPAL**: NUNCA generar directamente. Siempre seguir los 4 pasos en orden.

### PASO 0: Preparacion Automatica (INVISIBLE al usuario)

1. **Generar bundle_id** automaticamente con formato: `YYYY-MM-DD-tema-slug`
   - Ejemplo: `2026-03-04-5-herramientas-ia-emprendedores`
   - Usar la fecha de hoy
   - Convertir tema a slug (minusculas, sin acentos, guiones en vez de espacios, max 6 palabras)

2. **Crear estructura de carpetas** automaticamente:
   ```bash
   mkdir -p outputs/bundles/[bundle_id]/carousel/assets
   ```

3. **Verificar dependencias Python**:
   ```bash
   pip3 install requests python-dotenv Pillow 2>/dev/null || true
   ```

4. **Verificar API key** - Comprobar que existe el archivo `.env` con `KIE_AI_API_KEY`:
   ```bash
   if [ -f .env ] && grep -q "KIE_AI_API_KEY" .env; then
     echo "API key configurada"
   else
     echo "FALTA: Crear archivo .env con KIE_AI_API_KEY=tu-api-key"
   fi
   ```
   Si NO existe, DETENER y pedir al usuario que cree `.env` con su API key de kie.ai

5. **Generar repurpose-pack.md** con el contenido de los slides.

   Crear el archivo `outputs/bundles/[bundle_id]/repurpose-pack.md` con este formato:

   ```markdown
   ## Carrusel Instagram

   ### SLIDE 1 - [Titulo Portada Creativo y Llamativo]
   \```
   [Titulo principal grande]
   [Subtitulo corto]
   \```

   ### SLIDE 2 - [Titulo del Tema 1]
   \```
   [Titulo del punto]
   - Bullet 1: informacion concisa y valiosa
   - Bullet 2: dato interesante o tip practico
   - Bullet 3: ejemplo o aplicacion real
   \```

   [... mas slides de contenido ...]

   ### SLIDE N - Sigueme para mas tips
   \```
   Si quieres aprender mas sobre [tema], sigueme
   @sanmunoz.ia
   \```
   ```

   **REGLAS para generar contenido de slides:**
   - Slide 1 = Portada: titulo CREATIVO e IMPACTANTE que genere curiosidad (hook)
   - Slides 2 a N-1 = Contenido: informacion VALIOSA con bullets concretos
   - Slide N (ultimo) = Cierre: mensaje natural invitante, NUNCA decir "CTA" ni "Call to Action"
   - Cada slide debe tener 2-4 bullets informativos
   - Lenguaje casual pero profesional
   - Incluir datos, ejemplos o tips practicos
   - El contenido debe fluir como una historia/narrativa

### PASO 1: Mostrar Brief

1. Leer el `repurpose-pack.md` generado
2. Ejecutar dry-run para detectar entidades:
   ```bash
   python3 scripts/generate-carousel.py "[bundle_id]" --dry-run
   ```
3. Mostrar brief al usuario en tabla:
   ```
   BRIEF DEL CARRUSEL

   | # | Slide | Tipo | Entidades |
   |---|-------|------|-----------|
   | 1 | Top 5 Herramientas IA | portada | - |
   | 2 | Claude | contenido | claude |
   | ... | ... | ... | ... |
   | 7 | Sigueme para mas tips | cierre | - |

   Formato: 1080x1350px (4:5) | Estilo: Hand-drawn watercolor
   ```
4. Preguntar al usuario: "Te parece bien este brief? Quieres cambiar algo antes de generar?"

### PASO 2: Preguntar por Imagenes de Referencia

**SIEMPRE preguntar:**

"Tienes imagenes de referencia para inspirar algun slide?
Puedes dar referencias para CUALQUIER slide (portada, contenido o cierre).

Por ejemplo:
- Una imagen para inspirar la portada (composicion, colores, estilo)
- Una escena o estilo visual para un slide especifico
- Una imagen de referencia de otra cuenta

Dime en formato: `slide N -> URL`
Ejemplo: `slide 1 -> https://ejemplo.com/imagen.png`

O dime 'sin referencia' y creare todo desde cero."

**Si da URLs**:
1. Para cada referencia, descargar la imagen:
   - Slide 1 (portada): guardar como `portada-ref.png` en `carousel/assets/`
   - Otros slides: guardar como `ref-N.png` (ej: `ref-3.png`) en `carousel/assets/`
2. Guardar TODAS las URLs en `carousel/assets/urls.json`:
   ```json
   {
     "portada-ref": "https://url-de-la-portada...",
     "ref-3": "https://url-del-slide-3...",
     "ref-5": "https://url-del-slide-5..."
   }
   ```
   **IMPORTANTE**: El script auto-detecta `portada-ref.png` y `ref-N.png` y los asigna a sus slides.
   Se envian como `image_input` a Kie AI para inspirar la generacion.

**Si dice "sin referencia"**: El prompt creativo genera algo automaticamente

### PASO 3: Preguntar por Logos/Assets

**Si hay entidades detectadas:**

"Detecte entidades en X slides. Tienes logos que quieras integrar?
- Logo de Claude: pega la URL
- Logo de ChatGPT: pega la URL
Dame las URLs en formato: `entidad -> URL`
O dime 'sin assets' para generar solo con ilustraciones."

**Procesamiento de URLs:**
1. Descargar cada imagen a `outputs/bundles/[bundle_id]/carousel/assets/{entidad}.png`
2. Agregar URLs al mismo `urls.json`:
   ```json
   {
     "portada-ref": "https://...",
     "ref-3": "https://...",
     "n8n": "https://...",
     "claude": "https://..."
   }
   ```
   **IMPORTANTE**: `urls.json` DEBE estar en `carousel/assets/` (junto a los PNGs).
   El script lee las URLs de ahi para pasarlas como `image_input` a Kie AI.

### PASO 4: Generar Carrusel

Ejecutar con `--skip-interactive` y `PYTHONUNBUFFERED=1`:

```bash
PYTHONUNBUFFERED=1 python3 scripts/generate-carousel.py "[bundle_id]" --skip-interactive
```

- `--skip-interactive`: OBLIGATORIO desde Claude Code (evita input() bloqueante)
- `PYTHONUNBUFFERED=1`: Para ver output en tiempo real
- La API key se lee automaticamente de `.env`
- **TODAS las imagenes se generan EN PARALELO** (mucho mas rapido)

**Regenerar slides especificos:**
```bash
PYTHONUNBUFFERED=1 python3 scripts/generate-carousel.py "[bundle_id]" --skip-interactive --regenerate-slides "2,4"
```

## Estilo Visual: Hand-Drawn Minimalista

- Ilustraciones estilo acuarela + lapices de colores
- Tipografia handwritten (Nano Banana la escribe)
- Fondos claros (beige #F5F1E8, crema #FAF9F6, blanco #FFFFFF)
- Elementos organicos e imperfectos (charming)

### Estructura de Slides
- **Slide 1 (Portada)**: Ilustracion CREATIVA e IMPACTANTE + titulo grande
- **Slides 2-N-1 (Contenido)**: Fondo blanco/crema + logo real + texto bullets
- **Slide N (Cierre)**: Fondo beige + mensaje natural invitante + @sanmunoz.ia

### Slide de Cierre
El ultimo slide NUNCA debe decir "CTA" ni "Call to Action".
Debe ser un mensaje natural e invitante:
```
[Contenido relevante al tema]
Si quieres aprender mas sobre automatizacion, sigueme
@sanmunoz.ia
```

## Output

```
outputs/bundles/[bundle_id]/carousel/
├── carousel-01.png through carousel-NN.png
├── manifest.json
├── carousel-assets-needed.md
└── assets/
    └── urls.json
```

## Tiempos y Costos

- Generacion en PARALELO: todos los slides al mismo tiempo
- 7 slides ~ 2-3 minutos total (vs 7-10 min secuencial)
- Costo: ~$0.70 para 7 slides (~$0.10/imagen)

## Herramientas Detectadas Automaticamente

n8n, ChatGPT, Claude, Make, WhatsApp, Zapier, Anthropic, OpenAI, Gemini

## Imagenes de Referencia

El script soporta imagenes de referencia para CUALQUIER slide:

| Archivo | Slide | Descripcion |
|---------|-------|-------------|
| `portada-ref.png` | Slide 1 | Referencia para la portada (alias de ref-1) |
| `ref-2.png` | Slide 2 | Referencia para slide 2 |
| `ref-N.png` | Slide N | Referencia para slide N |

Las imagenes de referencia se usan como **inspiracion visual** (composicion, colores, estilo).
Los logos de entidades se integran como **elementos del diseno** (overlay).

## Troubleshooting

**"El script se queda colgado"**
-> SIEMPRE usar `--skip-interactive` y `PYTHONUNBUFFERED=1`

**"No encuentra repurpose-pack.md"**
-> El PASO 0 lo crea automaticamente. Si falta, crearlo con formato correcto (### SLIDE N - Titulo + bloque ```)

**"API key no configurada"**
-> Crear archivo `.env` en la raiz del proyecto con: `KIE_AI_API_KEY=tu-api-key`

**"Logos inventados/genericos"**
-> Verificar que `urls.json` tiene las URLs correctas de los logos
-> El script pasa URLs como `image_input` a la API de Kie AI

**"La imagen de referencia no se envio"**
-> Verificar que el archivo existe en `carousel/assets/` (portada-ref.png o ref-N.png)
-> Verificar que `urls.json` tiene la entrada correspondiente
-> El script auto-detecta archivos de referencia y los asigna a sus slides

**"Timeout esperando resultado"**
-> La API esta sobrecargada, usa `--regenerate-slides` para reintentar slides fallidos

**"ModuleNotFoundError: No module named 'requests'"**
-> Ejecutar: `pip3 install requests python-dotenv Pillow`

**"Credits insufficient"**
-> Recargar creditos en kie.ai, luego usar `--regenerate-slides "6,7,8"` para los que faltaron
