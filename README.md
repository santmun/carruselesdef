# Carruseles Automaticos

Skill de [Claude Code](https://docs.anthropic.com/en/docs/claude-code) para generar carruseles de Instagram con estilo **hand-drawn minimalista** usando [Kie AI (Nano Banana Pro)](https://kie.ai/).

Genera imagenes estilo acuarela y lapices de colores con tipografia handwritten, perfectas para carruseles educativos y de contenido.

![Estilo visual](https://img.shields.io/badge/Estilo-Hand--Drawn%20Watercolor-blue)
![Formato](https://img.shields.io/badge/Formato-1080x1350px%20(4:5)-green)
![API](https://img.shields.io/badge/API-Kie%20AI%20Nano%20Banana-purple)

---

## Que hace

Solo dale un **tema** y el **numero de slides**. El skill se encarga de todo:

1. **Genera el contenido** de cada slide automaticamente
2. Muestra un **brief** con la estructura del carrusel
3. Pregunta por **imagen de referencia** para la portada
4. Pregunta por **logos/assets** para integrar en slides de contenido
5. **Genera todas las imagenes EN PARALELO** via Kie AI
6. Guarda todo organizado por bundle

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
- Paquetes Python: `requests`, `python-dotenv`, `Pillow`

## Instalacion

### 1. Clonar el repositorio

```bash
git clone https://github.com/santmun/carruselesdef.git
cd carruselesdef
```

### 2. Instalar dependencias Python

```bash
pip install requests python-dotenv Pillow
```

### 3. Configurar API Key

Copia el archivo de ejemplo y agrega tu API key:

```bash
cp .env.example .env
```

Edita `.env` y reemplaza `tu-api-key-aqui` con tu API key de [kie.ai](https://kie.ai/).

### 4. (Opcional) Copiar a otro proyecto

Si quieres usar el skill en otro proyecto de Claude Code:

```bash
# Desde la raiz de TU proyecto
mkdir -p .claude/skills/carousel-gen scripts
cp carruselesdef/.claude/skills/carousel-gen/SKILL.md .claude/skills/carousel-gen/
cp carruselesdef/scripts/generate-carousel.py scripts/
cp carruselesdef/.env.example .env.example
```

---

## Uso

### Dentro de Claude Code

```
/carousel-gen [tema] [numero_de_slides]
```

Ejemplos:

```
/carousel-gen 5 herramientas IA para emprendedores 7
/carousel-gen como usar ChatGPT para crear contenido 5
/carousel-gen tendencias de IA en 2026 8
```

El skill automaticamente:
- Genera un `bundle_id` basado en la fecha y el tema
- Crea todas las carpetas necesarias
- Genera el contenido de los slides
- Ejecuta el workflow interactivo

### Workflow interactivo

El skill sigue 4 pasos obligatorios:

```
PASO 1: Mostrar brief
   Claude genera el contenido y te muestra una tabla resumen

PASO 2: Imagen de referencia para portada
   Te pregunta si tienes una imagen para inspirar la portada
   (logo 3D, escena, referencia visual)

PASO 3: Logos y assets
   Detecta herramientas mencionadas (n8n, Claude, ChatGPT...)
   y te pregunta si tienes logos para integrar

PASO 4: Generacion en paralelo
   Ejecuta el script y genera todas las imagenes al mismo tiempo
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
├── .env.example                     # Template de configuracion
├── .gitignore
├── .claude/
│   └── skills/
│       └── carousel-gen/
│           └── SKILL.md             # Definicion del skill para Claude Code
└── scripts/
    └── generate-carousel.py         # Script principal de generacion
```

### Estructura del bundle (output)

El script crea y genera archivos en esta estructura:

```
outputs/bundles/[bundle_id]/
├── repurpose-pack.md                # Texto de cada slide (auto-generado)
└── carousel/
    ├── carousel-01.png              # Imagenes generadas
    ├── carousel-02.png
    ├── ...
    ├── manifest.json                # Metadata de generacion
    ├── carousel-assets-needed.md    # Guia de assets opcionales
    └── assets/                      # Logos descargados
        ├── urls.json                # URLs originales de los assets
        └── *.png
```

---

## Formato del input (repurpose-pack.md)

El script lee slides de un archivo markdown. Cuando usas `/carousel-gen`, el contenido se genera automaticamente. El formato es:

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

### Imagen de referencia para portada

Puedes proporcionar una imagen de referencia para inspirar el diseno de la portada. El script la detecta automaticamente:

1. Se descarga a `carousel/assets/portada-ref.png`
2. Se guarda la URL en `carousel/assets/urls.json` con key `"portada-ref"`
3. El script la asigna automaticamente al slide 1
4. Kie AI la usa como inspiracion para composicion, colores y estilo

### Logos de herramientas

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
    ├── portada-ref.png
    ├── claude.png
    └── chatgpt.png
```

### Formato de urls.json

```json
{
  "portada-ref": "https://example.com/mi-imagen-referencia.png",
  "claude": "https://example.com/claude-logo.png",
  "chatgpt": "https://example.com/chatgpt-logo.png"
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
| **Cierre** | Fondo beige + mensaje natural + handle |

---

## Costos y tiempos

| Concepto | Valor |
|----------|-------|
| Por imagen | ~$0.10 USD |
| Carrusel de 7 slides | ~$0.70 USD |
| Generacion | **EN PARALELO** (todas al mismo tiempo) |
| Tiempo total (7 slides) | ~2-3 minutos |

---

## Configuracion opcional

### Google Drive sync

Si quieres copiar los carruseles automaticamente a Google Drive, agrega en `.env`:

```bash
GOOGLE_DRIVE_CAROUSEL_PATH=/Users/tu-usuario/Library/CloudStorage/GoogleDrive-.../Mi unidad/CAROUSEL
```

---

## Herramientas detectadas automaticamente

El script detecta menciones de estas herramientas para sugerir logos:

`n8n` `ChatGPT` `Claude` `Make` `WhatsApp` `Zapier` `Anthropic` `OpenAI` `Gemini`

---

## Troubleshooting

| Problema | Solucion |
|----------|----------|
| El script se queda colgado | Usa `--skip-interactive` y `PYTHONUNBUFFERED=1` |
| No encuentra repurpose-pack.md | El skill lo crea automaticamente. Si usas standalone, crealo con el formato de arriba |
| API key no configurada | Crea `.env` con `KIE_AI_API_KEY=tu-key` (copia `.env.example`) |
| Logos no se integran / genericos | Verifica que `urls.json` esta en `carousel/assets/` con las URLs correctas |
| Imagen de referencia no se envia | Verifica que `portada-ref.png` existe en `carousel/assets/` y `urls.json` tiene `"portada-ref"` |
| Timeout esperando resultado | API sobrecargada, usa `--regenerate-slides` para reintentar |
| Credits insufficient | Recarga creditos en kie.ai, luego usa `--regenerate-slides "6,7,8"` para los que faltaron |
| ModuleNotFoundError | Ejecuta `pip install requests python-dotenv Pillow` |

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
