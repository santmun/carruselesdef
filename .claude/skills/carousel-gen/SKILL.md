---
name: carousel-gen
description: Genera carruseles Instagram con estilo hand-drawn minimalista usando Kie AI (Nano Banana Pro). Workflow interactivo que muestra brief, pregunta por assets/logos y genera imagenes 1080x1350px.
allowed-tools: Read, Write, Bash(python3:*), Bash(cd:*), Bash(curl:*), Bash(ls:*), Bash(mkdir:*), Bash(cp:*), Bash(export:*), Glob, Grep, AskUserQuestion
user-invocable: true
---

# Generador de Carruseles Instagram - Kie AI (Nano Banana Pro)

Skill para generar carruseles Instagram con estilo hand-drawn minimalista watercolor.

## Uso

```
/carousel-gen [bundle_id]
```

**Parametros:**
- `bundle_id`: ID del bundle (ej: 2026-03-01-5-noticias-ia-semana)

## Workflow Interactivo (4 pasos obligatorios)

**REGLA PRINCIPAL**: NUNCA generar directamente. Siempre seguir los 4 pasos en orden.

### PASO 1: Mostrar Brief

1. Leer `repurpose-pack.md` del bundle:
   ```
   outputs/bundles/[bundle_id]/repurpose-pack.md
   ```
2. Buscar la seccion "Carrusel Instagram" y extraer slides
3. Si no existe, CREAR el archivo con formato correcto:
   ```markdown
   ## Carrusel Instagram

   ### SLIDE 1 - Titulo de Portada
   \```
   Contenido de la portada
   \```

   ### SLIDE 2 - Titulo del Slide
   \```
   Bullet 1
   Bullet 2
   \```
   ```
4. Ejecutar dry-run para detectar entidades:
   ```bash
   cd "/Users/santiagomunoz/Documents/Copia de agentesanmunoz"
   python3 scripts/generate-carousel.py "[bundle_id]" --dry-run
   ```
   O analizar manualmente buscando: n8n, ChatGPT, Claude, Make, WhatsApp, Zapier, Gemini, etc.

5. Mostrar brief al usuario en tabla:
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

### PASO 2: Preguntar por Imagen de Referencia para Portada

**SIEMPRE preguntar:**

"Para la portada quiero crear una ilustracion CREATIVA e IMPACTANTE.
Tienes alguna imagen de referencia para inspirar la portada?

Por ejemplo:
- Un logo en 3D que quieras que aparezca
- Una escena o estilo visual particular
- Una imagen de referencia de otra cuenta

Pega la URL o dime 'sin referencia' y creare algo creativo."

**Si da URL**: Descargar a `/carousel/assets/portada-ref.png`, agregar a `urls.json`
**Si dice "sin referencia"**: El prompt creativo genera algo automaticamente

### PASO 3: Preguntar por Logos/Assets

**Si hay entidades detectadas:**

"Detecte entidades en X slides. Tienes logos que quieras integrar?
- Logo de Claude: pega la URL
- Logo de ChatGPT: pega la URL
Dame las URLs en formato: `entidad -> URL`
O dime 'sin assets' para generar solo con ilustraciones."

**Procesamiento de URLs:**
1. Descargar cada imagen a `/outputs/bundles/[bundle_id]/carousel/assets/{entidad}.png`
2. Guardar URLs originales en `/outputs/bundles/[bundle_id]/carousel/assets/urls.json`:
   ```json
   {
     "n8n": "https://...",
     "claude": "https://..."
   }
   ```
   **IMPORTANTE**: `urls.json` DEBE estar en `carousel/assets/` (junto a los PNGs).
   El script busca ahi primero. Si por alguna razon esta en `carousel/`, tambien lo encuentra.

**HEADSHOT OBLIGATORIO en slide de cierre:**
- Agregar a `urls.json`: `{"headshot": "https://res.cloudinary.com/db7fnd2u9/image/upload/v1770766130/77745902bd53042e9840da2eb48e7dc0_tplv-tiktokx-cropcenter_1080_1080_1_diczzc.jpg"}`
- Descargar a `/carousel/assets/headshot.png`

### PASO 4: Generar Carrusel

Ejecutar con `--skip-interactive` y `PYTHONUNBUFFERED=1`:

```bash
cd "/Users/santiagomunoz/Documents/Copia de agentesanmunoz"
PYTHONUNBUFFERED=1 python3 scripts/generate-carousel.py "[bundle_id]" --skip-interactive
```

- `--skip-interactive`: OBLIGATORIO desde Claude Code (evita input() bloqueante)
- `PYTHONUNBUFFERED=1`: Para ver output en tiempo real
- La API key se lee automaticamente de `.env`

**Regenerar slides especificos:**
```bash
PYTHONUNBUFFERED=1 python3 scripts/generate-carousel.py "[bundle_id]" --skip-interactive --regenerate-slides "2,4"
```

## Estilo Visual: Hand-Drawn Minimalista

- Ilustraciones estilo acuarela + lapices de colores
- Tipografia handwritten (Nano Banana la escribe)
- Fondos claros (beige #F5F1E8, crema #FAF9F6, blanco #FFFFFF)
- Elementos organicos e imperfectos (charming)
- SIN avatares/fotos del creador (excepto slide cierre con headshot)

### Estructura de Slides
- **Slide 1 (Portada)**: Ilustracion CREATIVA e IMPACTANTE + titulo grande
- **Slides 2-6 (Contenido)**: Fondo blanco/crema + logo real + texto bullets
- **Slide 7 (Cierre)**: Fondo beige + mensaje natural invitante + @sanmunoz.ia + headshot

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
/outputs/bundles/[bundle_id]/carousel/
├── carousel-01.png through carousel-10.png
├── manifest.json
└── carousel-assets-needed.md
```

Google Drive: `CAROUSEL/[bundle_id]/`

## Tiempos y Costos

- ~1 min por slide (solo 1 generacion por slide)
- 7 slides ~ 7-10 minutos total
- Costo: ~$0.70 para 7 slides (~$0.10/imagen)

## Herramientas Detectadas Automaticamente

n8n, ChatGPT, Claude, Make, WhatsApp, Zapier, Anthropic, OpenAI, Gemini

## Troubleshooting

**"El script se queda colgado"**
-> SIEMPRE usar `--skip-interactive` y `PYTHONUNBUFFERED=1`

**"No encuentra repurpose-pack.md"**
-> Crear el archivo con formato correcto (### SLIDE N - Titulo + bloque ```)

**"API key no configurada"**
-> Se lee de `.env` automaticamente. Verificar que existe el archivo.

**"Logos inventados/genericos"**
-> Verificar que `urls.json` tiene las URLs correctas
-> El script pasa URLs como `image_input` a la API

**"Timeout esperando resultado"**
-> La API esta sobrecargada, usa `--regenerate-slides` para reintentar slides fallidos
