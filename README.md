# Carruseles Automaticos

Skill de [Claude Code](https://docs.anthropic.com/en/docs/claude-code) para generar carruseles de Instagram con estilo **hand-drawn minimalista** usando [Kie AI (Nano Banana Pro)](https://kie.ai/).

Genera imagenes estilo acuarela y lapices de colores con tipografia handwritten, perfectas para carruseles educativos y de contenido.

![Estilo visual](https://img.shields.io/badge/Estilo-Hand--Drawn%20Watercolor-blue)
![Formato](https://img.shields.io/badge/Formato-1080x1350px%20(4:5)-green)
![API](https://img.shields.io/badge/API-Kie%20AI%20Nano%20Banana-purple)

---

## Que hace

A partir de un archivo markdown con el texto de cada slide, este skill:

1. Muestra un **brief** con la estructura del carrusel
2. Pregunta por **imagen de referencia** para la portada
3. Pregunta por **logos/assets** para integrar en slides de contenido
4. **Genera las imagenes** via Kie AI con estilo watercolor hand-drawn
5. Guarda todo organizado por bundle

## Resultado

Imagenes como estas (estilo ilustracion a mano):

| Portada | Contenido | Cierre |
|---------|-----------|--------|
| Ilustracion creativa + titulo grande | Fondo claro + logo real + bullets | Mensaje natural + @handle |

---

## Requisitos

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) instalado
- Python 3.8+
- API Key de [Kie AI](https://kie.ai/)
- Paquetes Python: `requests`, `python-dotenv`

## Instalacion

### 1. Clonar el repositorio

```bash
git clone https://github.com/santmun/carruselesdef.git
cd carruselesdef
```

### 2. Instalar dependencias Python

```bash
pip install requests python-dotenv
```

### 3. Configurar API Key

Crea un archivo `.env` en la raiz del proyecto:

```bash
KIE_AI_API_KEY=tu-api-key-de-kie-ai
```

Puedes obtener tu API key en [kie.ai](https://kie.ai/).

### 4. Copiar el skill a tu proyecto

Copia la carpeta del skill a tu proyecto de Claude Code:

```bash
# Desde la raiz de TU proyecto
mkdir -p .claude/skills/carousel-gen
cp carruselesdef/.claude/skills/carousel-gen/SKILL.md .claude/skills/carousel-gen/

# Copiar el script de generacion
mkdir -p scripts
cp carruselesdef/scripts/generate-carousel.py scripts/
```

---

## Uso

### Dentro de Claude Code

```
/carousel-gen [bundle_id]
```

Ejemplo:

```
/carousel-gen 2026-03-01-5-noticias-ia-semana
```

### Workflow interactivo

El skill sigue 4 pasos obligatorios:

```
PASO 1: Mostrar brief
   Claude lee el contenido de slides y te muestra una tabla resumen

PASO 2: Imagen de referencia para portada
   Te pregunta si tienes una imagen para inspirar la portada
   (logo 3D, escena, referencia visual)

PASO 3: Logos y assets
   Detecta herramientas mencionadas (n8n, Claude, ChatGPT...)
   y te pregunta si tienes logos para integrar

PASO 4: Generacion
   Ejecuta el script y genera todas las imagenes
```

### Standalone (sin Claude Code)

Tambien puedes usar el script directamente:

```bash
# Generacion completa
python3 scripts/generate-carousel.py "mi-bundle-id"

# Solo ver el brief (sin generar)
python3 scripts/generate-carousel.py "mi-bundle-id" --dry-run

# Regenerar slides especificos
python3 scripts/generate-carousel.py "mi-bundle-id" --regenerate-slides "2,4"

# Saltar preguntas interactivas (para automatizacion)
python3 scripts/generate-carousel.py "mi-bundle-id" --skip-interactive
```

---

## Estructura de archivos

```
carruselesdef/
├── README.md
├── .gitignore
├── .claude/
│   └── skills/
│       └── carousel-gen/
│           └── SKILL.md          # Definicion del skill para Claude Code
└── scripts/
    └── generate-carousel.py      # Script principal de generacion
```

### Estructura del bundle (output)

El script espera y genera archivos en esta estructura:

```
outputs/bundles/[bundle_id]/
├── repurpose-pack.md             # INPUT: texto de cada slide (tu lo creas)
└── carousel/
    ├── carousel-01.png           # OUTPUT: imagenes generadas
    ├── carousel-02.png
    ├── ...
    ├── manifest.json             # Metadata de generacion
    ├── carousel-assets-needed.md # Guia de assets opcionales
    └── assets/                   # Logos descargados
        ├── urls.json             # URLs originales de los assets
        └── *.png
```

---

## Formato del input (repurpose-pack.md)

El script lee slides de un archivo markdown. El formato esperado es:

```markdown
## Carrusel Instagram

### SLIDE 1 - Titulo de la Portada
\```
Texto principal de la portada
\```

### SLIDE 2 - Nombre del Slide
\```
- Punto 1
- Punto 2
- Punto 3
\```

### SLIDE 3 - Otro Slide
\```
Contenido del slide
\```

### SLIDE 7 - Cierre
\```
Si quieres aprender mas, sigueme
@tuhandle
\```
```

---

## Manejo de assets (logos e imagenes de referencia)

### Como funciona

Cuando el skill detecta herramientas mencionadas en los slides (Claude, ChatGPT, n8n, etc.), te pregunta si tienes logos para integrar. Si proporcionas URLs:

1. Descarga cada imagen a `carousel/assets/{entidad}.png`
2. Guarda las URLs originales en `carousel/assets/urls.json`
3. El script usa las URLs de `urls.json` como `image_input` en la API de Kie AI
4. Nano Banana integra los logos reales en las ilustraciones hand-drawn

### Donde va urls.json

**`urls.json` debe estar en `carousel/assets/`** (junto a los PNGs descargados).

```
carousel/
└── assets/
    ├── urls.json       <-- AQUI
    ├── claude.png
    ├── chatgpt.png
    └── headshot.png
```

El script busca `urls.json` en dos ubicaciones por compatibilidad:
1. `carousel/assets/urls.json` (ubicacion principal)
2. `carousel/urls.json` (fallback)

### Formato de urls.json

```json
{
  "claude": "https://example.com/claude-logo.png",
  "chatgpt": "https://example.com/chatgpt-logo.png",
  "headshot": "https://example.com/tu-foto.jpg"
}
```

---

## Estilo visual

### Caracteristicas

- Ilustraciones estilo **acuarela + lapices de colores**
- Tipografia **handwritten** (Nano Banana la escribe directamente en la imagen)
- Fondos claros: beige `#F5F1E8`, crema `#FAF9F6`, blanco `#FFFFFF`
- Elementos organicos e imperfectos (estilo "charming")
- Logos reales integrados via `image_input` de la API

### Tipos de slides

| Tipo | Descripcion |
|------|-------------|
| **Portada** | Ilustracion creativa e impactante + titulo grande + fondo beige watercolor |
| **Contenido** | Fondo blanco/crema + logo real (si hay) + texto en bullets |
| **Cierre** | Fondo beige + mensaje natural + handle + headshot del creador |

---

## Costos

| Concepto | Valor |
|----------|-------|
| Por imagen | ~$0.10 USD |
| Carrusel de 7 slides | ~$0.70 USD |
| Tiempo por slide | ~1 minuto |
| Tiempo total (7 slides) | ~7-10 minutos |

---

## Herramientas detectadas automaticamente

El script detecta menciones de estas herramientas para sugerir logos:

`n8n` `ChatGPT` `Claude` `Make` `WhatsApp` `Zapier` `Anthropic` `OpenAI` `Gemini`

---

## Troubleshooting

| Problema | Solucion |
|----------|----------|
| El script se queda colgado | Usa `--skip-interactive` y `PYTHONUNBUFFERED=1` |
| No encuentra repurpose-pack.md | Crea el archivo con el formato de arriba |
| API key no configurada | Crea `.env` con `KIE_AI_API_KEY=tu-key` |
| Logos no se integran / genericos | Verifica que `urls.json` esta en `carousel/assets/` con las URLs correctas |
| Timeout esperando resultado | API sobrecargada, usa `--regenerate-slides` |

---

## Personalizacion

### Cambiar aspect ratio

```python
ASPECT_RATIO = "4:5"   # Instagram carousel (1080x1350px)
# Cambiar a:
ASPECT_RATIO = "1:1"   # Cuadrado (1080x1080px)
ASPECT_RATIO = "9:16"  # Stories (1080x1920px)
```

### Agregar nuevas herramientas detectadas

Busca el diccionario `KNOWN_ENTITIES` en `generate-carousel.py` y agrega las tuyas.

---

## Licencia

MIT

---

## Creditos

- Imagenes generadas con [Kie AI - Nano Banana Pro](https://kie.ai/)
- Skill diseñado para [Claude Code](https://docs.anthropic.com/en/docs/claude-code) de Anthropic
