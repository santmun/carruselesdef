#!/usr/bin/env python3
"""
generate-carousel.py - Genera carruseles Instagram usando Kie AI (Nano Banana)

Uso:
    python3 generate-carousel.py <bundle_id>
    python3 generate-carousel.py <bundle_id> --regenerate-slides "2,4,6"

Ejemplo:
    python3 generate-carousel.py 2026-01-14-chatbot-whatsapp-n8n
    python3 generate-carousel.py 2026-01-14-chatbot-whatsapp-n8n --regenerate-slides "3"

Requisitos:
    - Variable de entorno KIE_AI_API_KEY configurada
    - Archivo repurpose-pack.md con texto de slides
"""

import os
import sys
import json
import time
import re
import shutil
import argparse
import requests
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime
from dotenv import load_dotenv

# Cargar .env desde la raiz del proyecto
load_dotenv(Path(__file__).parent.parent / ".env")

# Configuración
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUTS_DIR = PROJECT_ROOT / "outputs" / "bundles"
TEMPLATES_DIR = PROJECT_ROOT / "templates"

# Google Drive - Carpeta de carruseles
GOOGLE_DRIVE_CAROUSEL = Path.home() / "Library" / "CloudStorage" / "GoogleDrive-contacto@innovandohorizontes.com" / "Mi unidad" / "CAROUSEL"

# API Kie AI
KIE_API_BASE = "https://api.kie.ai/api/v1/jobs"
KIE_CREATE_TASK = f"{KIE_API_BASE}/createTask"
KIE_RECORD_INFO = f"{KIE_API_BASE}/recordInfo"

# Configuración de generación
ASPECT_RATIO = "4:5"  # Instagram carousel (1080x1350px)
RESOLUTION = "2K"
FORMAT = "png"
MAX_POLL_ATTEMPTS = 60  # 5 minutos máximo
POLL_INTERVAL = 5  # segundos


def get_api_key() -> str:
    """Obtiene la API key de Kie AI."""
    api_key = os.environ.get("KIE_AI_API_KEY")
    if not api_key:
        print("❌ Error: Variable de entorno KIE_AI_API_KEY no configurada")
        print("   Ejecuta: export KIE_AI_API_KEY='tu-api-key'")
        sys.exit(1)
    return api_key


def parse_repurpose_pack(bundle_path: Path) -> Optional[List[Dict[str, str]]]:
    """Parsea repurpose-pack.md y extrae slides de Instagram Carousel."""
    repurpose_file = bundle_path / "repurpose-pack.md"

    if not repurpose_file.exists():
        print(f"❌ Error: No se encontró {repurpose_file}")
        return None

    with open(repurpose_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Extraer sección de Instagram Carousel
    carousel_match = re.search(
        r'##\s*[^\n]*?(?:Carrusel|Instagram|📱)[^\n]*?\n+(.*?)(?=\n##\s+[^#]|\Z)',
        content,
        re.DOTALL | re.IGNORECASE
    )

    if not carousel_match:
        print("❌ Error: No se encontró sección de Carrusel Instagram en repurpose-pack.md")
        return None

    carousel_text = carousel_match.group(1).strip()

    # Extraer slides individuales
    slides = []

    # Intentar con formato ### SLIDE (nuevo)
    slide_pattern_hash = r'###\s+SLIDE\s+(\d+)\s*-\s*([^\n]+)\s*\n```\s*\n(.*?)\n```'
    matches = list(re.finditer(slide_pattern_hash, carousel_text, re.DOTALL))

    # Si no encuentra, intentar con formato **SLIDE** (antiguo)
    if not matches:
        slide_pattern_star = r'\*\*SLIDE (\d+)(?:\s*-\s*([^\*\n]+))?\*\*\s*\n```\s*\n(.*?)\n```'
        matches = list(re.finditer(slide_pattern_star, carousel_text, re.DOTALL))

    for match in matches:
        slide_num = int(match.group(1))
        slide_title = match.group(2).strip() if match.group(2) else f"Slide {slide_num}"
        slide_content = match.group(3).strip()

        slides.append({
            "number": slide_num,
            "title": slide_title,
            "content": slide_content
        })

    if not slides:
        print("❌ Error: No se pudieron extraer slides del carrusel")
        return None

    print(f"   ✅ Encontrados {len(slides)} slides")
    return slides


def detect_tools_in_text(text: str) -> List[str]:
    """Detecta menciones de herramientas/apps en el texto."""
    tools_keywords = {
        "n8n": ["n8n", "n8n.io"],
        "chatgpt": ["chatgpt", "chat gpt", "gpt"],
        "claude": ["claude", "claude ai"],
        "make": ["make", "make.com", "integromat"],
        "whatsapp": ["whatsapp", "whatsapp business"],
        "zapier": ["zapier"],
        "anthropic": ["anthropic"],
        "openai": ["openai"],
    }

    found_tools = []
    text_lower = text.lower()

    for tool, keywords in tools_keywords.items():
        for keyword in keywords:
            if keyword in text_lower:
                if tool not in found_tools:
                    found_tools.append(tool)
                break

    return found_tools


def detect_entities_in_slides(slides: List[Dict]) -> Dict[int, List[str]]:
    """
    Detecta entidades (herramientas, empresas, temas) en cada slide.

    Returns:
        Dict mapping slide number to list of detected entities
        Example: {2: ['chatgpt', 'openai'], 5: ['claude', 'anthropic']}
    """
    entities_by_slide = {}

    # Known entities to detect
    KNOWN_ENTITIES = {
        # Project-specific entities first (higher priority in asset mapping)
        'openclaw': ['openclaw', 'open claw', 'clawdbot', 'moltbot'],
        'peter-steinberger': ['peter steinberger', 'steipete', 'pspdfkit'],
        'seedance': ['seedance', 'bytedance', 'seed dance'],
        'tiktok': ['tiktok'],
        'disney': ['disney', 'hollywood'],
        'tom-cruise': ['tom cruise', 'brad pitt'],
        # General entities
        'chatgpt': ['chatgpt', 'gpt', 'openai'],
        'claude': ['claude', 'anthropic'],
        'gemini': ['gemini', 'google ai', 'bard'],
        'n8n': ['n8n'],
        'whatsapp': ['whatsapp'],
        'zapier': ['zapier'],
        'make': ['make', 'integromat'],
        'midjourney': ['midjourney'],
        'eu': ['eu ', 'european union', 'europa'],
        'ai act': ['ai act', 'regulatory'],
    }

    for slide in slides:
        slide_num = slide['number']
        slide_text = f"{slide['title']} {slide['content']}".lower()

        detected = []
        for entity, keywords in KNOWN_ENTITIES.items():
            if any(keyword in slide_text for keyword in keywords):
                detected.append(entity)

        if detected:
            entities_by_slide[slide_num] = detected

    return entities_by_slide


def download_asset_from_url(url: str, entity: str, assets_dir: Path) -> Optional[Path]:
    """
    Descarga una imagen desde URL y la guarda en assets/.

    Args:
        url: URL de la imagen proporcionada por el usuario
        entity: Nombre de la entidad (chatgpt, claude, etc.)
        assets_dir: Carpeta /carousel/assets/

    Returns:
        Path al archivo descargado, o None si falla
    """
    try:
        from PIL import Image
        from io import BytesIO

        response = requests.get(url, timeout=10)
        response.raise_for_status()

        # Abrir imagen y convertir a PNG
        img = Image.open(BytesIO(response.content))

        # Convert to RGB if needed (for transparency handling)
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background

        # Save as PNG
        asset_path = assets_dir / f"{entity}.png"
        img.save(asset_path, 'PNG')

        print(f"   ✅ Asset descargado: {asset_path.name}")
        return asset_path

    except Exception as e:
        print(f"   ❌ Error descargando asset: {e}")
        return None


def generate_creative_integration_prompt(
    slide_type: str,
    title: str,
    content: str,
    entity: Optional[str] = None,
    has_asset: bool = False
) -> str:
    """
    Genera prompt con integración creativa contextual del asset.

    Adapta la integración según:
    - Tipo de slide (portada, contenido, cierre)
    - Tema del slide
    - Entidad detectada
    - Si hay asset disponible
    """

    # Base style for all slides
    base_style = """Instagram carousel slide (1080x1350px, ratio 4:5).

STYLE: Hand-drawn watercolor and colored pencil illustration.
Minimalist, friendly, educational aesthetic.
- Fondos claros (beige #F5F1E8, crema #FAF9F6, blanco)
- Tipografía handwritten escrita por la IA
- Elementos orgánicos e imperfectos (charming)
- SIN avatares de personas

"""

    if slide_type == "portada":
        if has_asset and entity:
            return f"""{base_style}

PORTADA DE CARRUSEL - IMPACTANTE Y CREATIVA - Con Asset de {entity}:

Título: {title}

INSTRUCCIÓN CLAVE: Crea una ilustración CREATIVA, INESPERADA y LLAMATIVA.
NO hagas una portada genérica con iconos simples. Piensa en algo fuera de lo común.

IDEAS DE ILUSTRACIÓN CREATIVA (elige o combina):
- El logo de {entity} en 3D gigante interactuando con el mundo (aplastando, sosteniendo, construyendo algo)
- Personajes animales o robots usando/adorando el logo de {entity}
- El logo de {entity} como centro de un universo o galaxia dibujada
- Una escena dramática o divertida con el logo como protagonista
- El logo transformándose en algo inesperado (máquina, criatura, edificio)
- Perspectiva forzada: logo gigante con personajes tiny mirándolo asombrados

REQUISITOS VISUALES:
- Background watercolor wash en beige/crema con salpicaduras de color
- Ilustración GRANDE que ocupe al menos 50% del slide
- Sensación de movimiento, energía, dinamismo
- Título en tipografía handwritten bold: "{title}"

TEXT CONTENT:
{content}

COMPOSITION:
- Ilustración dominante (centro o tercio superior, grande y llamativa)
- Título grande navy blue (#1A365D), 72-80pt handwritten
- NO watermark, NO username, NO branding text
- Safe margins: 60px all sides
"""
        else:
            return f"""{base_style}

PORTADA DE CARRUSEL - IMPACTANTE Y CREATIVA - Sin Asset:

Título: {title}

INSTRUCCIÓN CLAVE: Crea una ilustración CREATIVA, INESPERADA y LLAMATIVA.
NO hagas una portada genérica con iconos simples. Piensa en algo fuera de lo común.

IDEAS DE ILUSTRACIÓN CREATIVA (elige o combina):
- Una escena dramática o surrealista que represente el tema
- Objetos cotidianos en situaciones imposibles o divertidas
- Personajes animales o robots en acción relacionada con el tema
- Perspectiva forzada o isométrica con muchos detalles
- Algo que cause curiosidad y haga querer ver el siguiente slide
- Metáforas visuales inesperadas (ej: un pulpo controlando 5 computadoras para "automatización")

REQUISITOS VISUALES:
- Background: Soft beige (#F5F1E8) con salpicaduras de watercolor vibrantes
- Ilustración GRANDE y DOMINANTE (mínimo 50% del slide)
- Colores más vibrantes que los slides internos (blues, naranjas, verdes intensos)
- Sensación de movimiento, energía, dinamismo
- Hand-drawn con watercolor pero con MÁS detalle que slides normales

TEXT CONTENT:
"{content}"

TEXT STYLING:
- Main title: Large handwritten BOLD font, navy blue (#1A365D), 72-80pt
- Subtitle: Medium handwritten, dark gray (#374151), 32pt
- NO watermark, NO username, NO branding text

COMPOSITION:
- Ilustración dominante al centro
- Título arriba o integrado con la ilustración
- Subtítulo abajo
- Safe margins: 60px all sides
"""

    elif slide_type == "contenido":
        if has_asset and entity:
            content_preview = content[:200] if len(content) > 200 else content
            return f"""{base_style}

SLIDE DE CONTENIDO - Con Asset de {entity}:

Título: {title}
Contenido: {content}

LAYOUT:
- Logo/imagen de {entity} integrado contextualmente (120-160px)
- Texto principal en bullets handwritten
- Background blanco/crema limpio

INTEGRACIÓN CREATIVA según contexto:
- Si habla de capacidades: Logo + iconos ilustrados de features
- Si habla de casos de uso: Logo + mini escenas dibujadas de uso
- Si es noticia: Imagen de la noticia + elementos informativos dibujados
- Si es comparación: Logo + elementos de comparación visual

CONTEXTO DEL SLIDE:
{content_preview}...

Adapta la integración visual para que el asset COMPLEMENTE el mensaje, no solo decore.

TEXT STYLING:
- Title: Large handwritten font, navy blue (#1A365D), 48-56pt
- Body text: Medium handwritten, black (#1F2937), 28-36pt
- Bullets: Hand-drawn dots or checkmarks
- NO watermark, NO username, NO branding text

COMPOSITION:
- Top 25%: Title + Logo integration
- Middle 50%: Illustration + text content
- Bottom 25%: Breathing room
- Margins: 60px all sides
"""
        else:
            return f"""{base_style}

SLIDE DE CONTENIDO - Sin Asset:

Título: {title}

BACKGROUND: Clean white (#FFFFFF) with very subtle beige paper texture.
Light watercolor wash in one corner (8-12% opacity).

MAIN ILLUSTRATION:
- Central conceptual illustration related to topic
- Style: Simple sketchy lines, watercolor fill
- Colors: Soft blues, greens, or oranges (pastel)
- Hand-drawn charm, imperfect but intentional

TEXT CONTENT:
"{content}"

TEXT STYLING:
- Title: Large handwritten font, navy blue (#1A365D), 48-56pt
- Body text: Medium handwritten, black (#1F2937), 28-36pt
- Bullets: Hand-drawn dots or checkmarks
- NO watermark, NO username, NO branding text

COMPOSITION:
- Top 25%: Title
- Middle 50%: Illustration + text content
- Bottom 25%: Breathing room
- Margins: 60px all sides
"""

    else:  # cierre
        if has_asset and entity:
            return f"""{base_style}

SLIDE DE CIERRE - Con Asset de {entity}:

Contenido: {content}

INSTRUCCIÓN IMPORTANTE: Este es un slide de cierre amigable, NO escribas la palabra "CTA" en ningún lado.
El mensaje debe sentirse natural y cercano, como una invitación entre amigos.

LAYOUT:
- Logo pequeño de {entity} integrado naturalmente (80-100px)
- Ilustración positiva y cálida (cohete despegando, puerta abriéndose, camino hacia adelante)
- Texto principal en caja hand-drawn acogedora
- Background beige con watercolor accents cálidos

INTEGRACIÓN:
- Logo discreto pero visible
- Texto invitante: el contenido tal como está, SIN agregar "CTA" ni "Call to Action"
- Elementos positivos dibujados (flechas, estrellas, corazones, sparkles)

TEXT STYLING:
- Texto principal: Large bold handwritten, black, 48-56pt
- "@sanmunoz.ia": Visible y destacado, handwritten, 36pt

COMPOSITION:
- Ilustración cálida arriba
- Texto invitante al centro (en caja hand-drawn)
- @sanmunoz.ia destacado
- Friendly, welcoming feel
- Margins: 60px all sides
"""
        else:
            return f"""{base_style}

SLIDE DE CIERRE - Sin Asset:

Contenido: {content}

INSTRUCCIÓN IMPORTANTE: Este es un slide de cierre amigable, NO escribas la palabra "CTA" en ningún lado.
El mensaje debe sentirse natural y cercano, como una invitación entre amigos.

BACKGROUND: Soft beige (#F5F1E8) with warm watercolor wash.

MAIN ILLUSTRATION:
- Warm, inviting illustration (cohete despegando, puerta abriéndose, mano señalando adelante)
- Style: Simple line drawing with watercolor fill
- Colors: Warm blues and oranges
- Hand-drawn, welcoming feel

TEXT CONTENT:
"{content}"

IMPORTANTE: Escribe el texto TAL COMO ESTÁ arriba. No agregues "CTA", "Call to Action" ni nada similar.

TEXT STYLING:
- Texto principal: Medium-large handwritten, navy blue, 48pt
- "@sanmunoz.ia": Destacado, bold handwritten, 36pt

COMPOSITION:
- Ilustración top
- Texto invitante al centro (en caja hand-drawn)
- @sanmunoz.ia prominente
- Friendly, inviting feel
- Margins: 60px all sides
"""

    return base_style


def generate_prompt_for_slide(slide: Dict[str, str], slide_type: str) -> str:
    """DEPRECATED: Usa generate_creative_integration_prompt() en su lugar."""

    slide_num = slide["number"]
    title = slide["title"]
    content = slide["content"]

    # Base del prompt (común para todos)
    base = f"""Instagram carousel slide (1080x1350px, ratio 4:5).

STYLE: Hand-drawn watercolor and colored pencil illustration.
Minimalist, friendly, educational aesthetic. Clean and approachable.

"""

    # Portada
    if slide_type == "portada":
        return base + f"""BACKGROUND: Soft beige (#F5F1E8) with subtle paper texture.
Light blue watercolor wash in top right corner (15% opacity).

MAIN ILLUSTRATION:
- Decorative icons arranged tastefully (top third)
- Style: Simple line drawings with watercolor fill
- Colors: Soft blues, greens, oranges (pastel palette)
- Hand-drawn imperfect lines (charming, not perfect)

TEXT CONTENT:
"{content}"

TEXT STYLING:
- Main title: Large handwritten bold font, navy blue (#1A365D), 72-80pt
- Subtitle: Medium handwritten, dark gray (#374151), 32pt
- All text has slight hand-drawn waviness
- Natural integration into illustration
- Soft drop shadow, not harsh

DECORATIVE ELEMENTS:
- Small hand-drawn stars scattered around
- Doodle-style underline or bracket
- Corner flourishes: simple leaf or branch motifs
- NO watermark, NO username, NO branding text

COMPOSITION:
- Top 30%: Title text
- Middle 40%: Decorative illustrations
- Bottom 30%: Subtitle text
- Friendly, inviting, educational feel
- Safe margins: 60px all sides
"""

    # Slide de contenido
    elif slide_type == "contenido":
        return base + f"""BACKGROUND: Clean white (#FFFFFF) with very subtle beige paper texture.
Light watercolor wash in one corner (8-12% opacity, vary color).

MAIN ILLUSTRATION:
- Central conceptual illustration related to topic
- Style: Simple sketchy lines, watercolor fill
- Colors: Soft blues, greens, or oranges (pastel)
- Size: Takes up middle 35% of slide
- Hand-drawn charm, imperfect but intentional

TEXT CONTENT:
"{content}"

TEXT STYLING:
- Title: Large handwritten font, navy blue (#1A365D), 48-56pt
- Body text: Medium handwritten, black (#1F2937), 28-36pt
- Bullets: Hand-drawn dots or checkmarks
- Natural spacing, breathable layout
- Organic baseline (slightly uneven)

DECORATIVE ELEMENTS:
- Hand-drawn separators (dotted lines, waves)
- Small icons or doodles related to topic
- Corner detail: simple arrow or asterisk
- NO watermark, NO username, NO branding text

COMPOSITION:
- Top 25%: Title
- Middle 50%: Illustration + text content
- Bottom 25%: Additional info or breathing room
- Clean, scannable, educational
- Margins: 60px all sides
"""

    # Slide de cierre/CTA
    elif slide_type == "cierre":
        return base + f"""BACKGROUND: Soft beige (#F5F1E8) with light blue watercolor wash
in bottom right corner (18% opacity, organic bleed).

MAIN ILLUSTRATION:
- Celebratory or inviting illustration (lightbulb, open book, or sparkles)
- Style: Simple line drawing with watercolor fill
- Colors: Warm blues and oranges (friendly palette)
- Size: 180x180px, centered top
- Hand-drawn, welcoming feel

TEXT CONTENT:
"{content}"

TEXT STYLING:
- Question/Hook: Medium handwritten, navy blue, 48pt
- CTA: Large bold handwritten, black, 56pt
- Secondary: Smaller handwritten, dark gray, 32pt
- All text friendly and inviting
- Natural hand-drawn character

DECORATIVE ELEMENTS:
- Hand-drawn box around CTA (dashed or solid, imperfect)
- Small arrows pointing to CTA
- Corner flourishes or stars
- "@sanmunoz.ia" prominente y destacado, handwritten 36pt

COMPOSITION:
- Top 25%: Illustration
- Middle 50%: CTA text
- Bottom 25%: @sanmunoz.ia
- Centered, inviting layout
- Warm, friendly energy
- Margins: 60px all sides
"""

    # Fallback genérico
    else:
        return base + f"""BACKGROUND: White or soft beige with subtle watercolor accent.

TEXT CONTENT:
"{content}"

STYLE: Hand-drawn, friendly, educational. Safe margins 60px all sides.
NO watermark, NO username, NO branding text.
"""


def determine_slide_type(slide_num: int, total_slides: int) -> str:
    """Determina el tipo de slide basado en su posición."""
    if slide_num == 1:
        return "portada"
    elif slide_num == total_slides:
        return "cierre"
    else:
        return "contenido"


def create_kie_task(api_key: str, prompt: str, image_input: Optional[List[str]] = None) -> Optional[str]:
    """
    Crea una tarea en Kie AI (nano-banana-pro) y retorna el taskId.

    Args:
        api_key: Kie AI API key
        prompt: Prompt de generación
        image_input: Lista opcional de URLs de imágenes de referencia (logos, etc.)

    Returns:
        taskId de la tarea creada, o None si falla
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    input_params = {
        "prompt": prompt,
        "aspect_ratio": ASPECT_RATIO,
        "resolution": RESOLUTION,
        "output_format": FORMAT
    }

    # Pasar logos/assets como image_input (referencia visual)
    if image_input:
        input_params["image_input"] = image_input

    payload = {
        "model": "nano-banana-pro",
        "input": input_params
    }

    try:
        response = requests.post(KIE_CREATE_TASK, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()

        if result.get("code") == 200:
            task_id = result.get("data", {}).get("taskId")
            if task_id:
                return task_id
            print(f"   ❌ Error: No se recibió taskId de Kie AI")
            print(f"   📋 Respuesta: {result}")
            return None
        else:
            print(f"   ❌ Error: No se recibió taskId de Kie AI")
            print(f"   📋 Respuesta: {result}")
            return None

    except Exception as e:
        print(f"   ❌ Error creando tarea: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   📋 Respuesta HTTP: {e.response.text}")
        return None


def poll_task_status(api_key: str, task_id: str) -> Optional[str]:
    """Hace polling del status de una tarea hasta que complete."""
    headers = {"Authorization": f"Bearer {api_key}"}

    for attempt in range(MAX_POLL_ATTEMPTS):
        try:
            response = requests.get(
                KIE_RECORD_INFO,
                headers=headers,
                params={"taskId": task_id},
                timeout=30
            )
            response.raise_for_status()

            data = response.json().get("data") or {}
            state = data.get("state", "")

            if state == "success":
                result_json = data.get("resultJson", "{}")
                result = json.loads(result_json)
                urls = result.get("resultUrls", [])
                if urls:
                    return urls[0]
                else:
                    print(f"   ❌ Tarea completada pero sin URLs en resultado")
                    return None

            elif state == "fail":
                fail_msg = data.get("failMsg", "Unknown error")
                print(f"   ❌ Tarea falló: {fail_msg}")
                return None

            elif state in ["waiting", "queuing", "generating"]:
                print(f"   Estado: {state}... ({attempt + 1}/{MAX_POLL_ATTEMPTS})")
                time.sleep(POLL_INTERVAL)

            else:
                print(f"   ⚠️  Estado desconocido: '{state}' (intento {attempt + 1}/{MAX_POLL_ATTEMPTS})")
                time.sleep(POLL_INTERVAL)

        except Exception as e:
            print(f"   ❌ Error en polling: {e}")
            time.sleep(POLL_INTERVAL)

    print(f"   ❌ Timeout esperando resultado (intentos: {MAX_POLL_ATTEMPTS})")
    return None


def download_image(url: str, output_path: Path) -> bool:
    """Descarga imagen desde URL."""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return True

    except Exception as e:
        print(f"   ❌ Error descargando imagen: {e}")
        return False


def upload_asset_to_kie(api_key: str, asset_path: Path) -> Optional[str]:
    """
    Obtiene URL pública de un asset para usar con Kie AI.

    Primero busca en urls.json (URLs de Cloudinary u otras CDN públicas).
    Si no encuentra, intenta subir a Kie AI como fallback.

    Args:
        api_key: API key de Kie AI
        asset_path: Path al archivo de imagen local

    Returns:
        URL pública del asset, o None si falla
    """
    # Buscar URL pública en urls.json
    # Busca en: 1) carousel/assets/ (junto al asset), 2) carousel/ (directorio padre)
    entity_name = asset_path.stem.lower()
    urls_candidates = [
        asset_path.parent / "urls.json",          # carousel/assets/urls.json
        asset_path.parent.parent / "urls.json",    # carousel/urls.json
    ]
    for urls_file in urls_candidates:
        if urls_file.exists():
            try:
                with open(urls_file, "r") as f:
                    urls_map = json.load(f)
                if entity_name in urls_map:
                    public_url = urls_map[entity_name]
                    print(f"   ✅ URL pública encontrada: {entity_name} (desde {urls_file.parent.name}/urls.json)")
                    return public_url
            except Exception:
                pass

    # Fallback: intentar subir a Kie AI
    upload_url = "https://api.kie.ai/api/v1/files/upload"
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        with open(asset_path, 'rb') as f:
            files = {'file': (asset_path.name, f, 'image/png')}
            response = requests.post(upload_url, headers=headers, files=files)
            response.raise_for_status()
            result = response.json()
            file_url = result.get("data", {}).get("url")
            if not file_url:
                print(f"   ❌ No se recibió URL del archivo subido")
                return None
            return file_url

    except Exception as e:
        print(f"   ❌ Error subiendo asset: {e}")
        return None


def find_asset_for_slide(assets_dir: Path, tools: List[str]) -> Optional[Path]:
    """
    Busca un asset apropiado para un slide basado en las herramientas detectadas.

    Args:
        assets_dir: Directorio donde están los assets
        tools: Lista de herramientas detectadas en el slide

    Returns:
        Path al asset encontrado, o None si no hay match
    """
    if not tools or not assets_dir.exists():
        return None

    # Buscar archivos que coincidan con las herramientas detectadas
    for tool in tools:
        # Buscar variantes: tool-logo.png, tool.png, tool-icon.png
        patterns = [
            f"{tool}-logo.png",
            f"{tool}.png",
            f"{tool}-icon.png"
        ]

        for pattern in patterns:
            asset_path = assets_dir / pattern
            if asset_path.exists():
                return asset_path

    return None


def edit_slide_with_logo(
    api_key: str,
    generated_image_url: str,
    logo_url: str,
    slide_title: str,
    slide_content: str,
    slide_type: str
) -> Optional[str]:
    """
    Edita un slide generado para integrar un logo real usando nano-banana-edit.

    Pasa la imagen generada + logo como image_urls (ambas URLs públicas).
    nano-banana-edit soporta hasta 10 image_urls.

    Args:
        api_key: API key de Kie AI
        generated_image_url: URL de la imagen generada por nano-banana-pro
        logo_url: URL pública del logo (Cloudinary, etc.)
        slide_title: Título del slide
        slide_content: Contenido textual del slide
        slide_type: Tipo de slide (portada/contenido/cierre)

    Returns:
        URL de la imagen editada, o None si falla
    """
    edit_prompt = f"""Edit this carousel slide to integrate the provided logo/icon image naturally.

THE SECOND IMAGE IS A LOGO. You must:
1. Place the real logo from the second image onto the slide
2. Position it prominently (top-center or beside the title)
3. Keep the logo EXACTLY as it is - do not redraw or modify the logo
4. Size: approximately 150-200px

CRITICAL - DO NOT:
- Redraw or reinvent the logo
- Change the logo colors or shape
- Remove any existing text from the slide

PRESERVE:
- All existing text content on the slide
- Hand-drawn watercolor background style
- Overall composition and layout
- Beige/cream/white color scheme

Slide title: {slide_title}
Slide type: {slide_type}
"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "google/nano-banana-edit",
        "input": {
            "prompt": edit_prompt,
            "image_urls": [generated_image_url, logo_url],
            "output_format": "png",
            "image_size": "4:5"
        }
    }

    try:
        print(f"   ⏳ Editando con nano-banana-edit (integrando logo)...")

        response = requests.post(KIE_CREATE_TASK, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()

        if result.get("code") == 200:
            task_id = result.get("data", {}).get("taskId")
            if not task_id:
                print(f"   ❌ No se recibió taskId de nano-banana-edit")
                return None
        else:
            print(f"   ❌ Error nano-banana-edit: {result}")
            return None

        print(f"   Esperando resultado edit (taskId: {task_id[:12]}...)...")
        image_url = poll_task_status(api_key, task_id)

        return image_url

    except Exception as e:
        print(f"   ❌ Error en edición: {e}")
        return None


def generate_assets_needed_md(bundle_id: str, bundle_path: Path, slides: List[Dict], tool_detections: Dict[int, List[str]]):
    """Genera archivo carousel-assets-needed.md con guía de assets opcionales."""

    assets_file = bundle_path / "carousel" / "carousel-assets-needed.md"

    # Determinar qué slides podrían beneficiarse de assets
    slides_with_opportunities = []

    for slide in slides:
        slide_num = slide["number"]
        tools = tool_detections.get(slide_num, [])

        if tools:
            slides_with_opportunities.append({
                "slide": slide,
                "tools": tools
            })

    if not slides_with_opportunities:
        # No hay oportunidades, solo crear mensaje básico
        content = f"""# Guía de Assets para Carrusel Instagram

**Bundle:** {bundle_id}
**Total slides:** {len(slides)}
**Generado:** {datetime.now().strftime("%Y-%m-%d %H:%M")}

---

## 📊 Resumen

Este carrusel fue generado con ilustraciones genéricas hand-drawn.
No se detectaron menciones claras de herramientas específicas que requieran logos.

✅ **Las ilustraciones genéricas están listas para publicar.**

Si en el futuro quieres agregar logos reales de herramientas específicas,
puedes usar la regeneración automática con el comando `--regenerate-slides`.

---

## 🔄 Workflow de Regeneración

Si quisieras agregar assets reales:

1. Consigue logos oficiales en alta calidad (PNG con fondo transparente, 512x512px)
2. Guárdalos en: `/carousel/assets/[tool]-logo.png`
3. Ejecuta: `python3 scripts/generate-carousel.py {bundle_id} --regenerate-slides "N"`

El sistema automáticamente:
- Detecta el asset apropiado
- Usa nano-banana-edit para overlay del logo
- Mantiene el estilo hand-drawn original
- Sobrescribe el slide con la versión mejorada

---
"""
    else:
        # Hay oportunidades, generar guía completa
        tool_list = ", ".join(sorted(set([t for item in slides_with_opportunities for t in item["tools"]])))

        content = f"""# Guía de Assets para Carrusel Instagram

**Bundle:** {bundle_id}
**Total slides:** {len(slides)}
**Herramientas detectadas:** {tool_list}
**Generado:** {datetime.now().strftime("%Y-%m-%d %H:%M")}

---

## 📊 Resumen

Este carrusel fue generado con ilustraciones genéricas hand-drawn.
Se detectaron {len(slides_with_opportunities)} slides que mencionan herramientas específicas.

**OPCIONAL:** Solo agrega assets si:
- Tienes logos oficiales de alta calidad
- Quieres look más profesional/branded
- El contenido se beneficia de logos reconocibles

Si las ilustraciones genéricas se ven bien, ¡publícalo así! 🎨

---

## 🎯 Workflow: Agregar Assets y Regenerar

### Paso 1: Conseguir Logos

Descarga logos oficiales en alta calidad:

"""

        # Generar lista de herramientas únicas
        unique_tools = sorted(set([t for item in slides_with_opportunities for t in item["tools"]]))
        for tool in unique_tools:
            content += f"""**{tool.title()}:**
- Formato: PNG con fondo transparente
- Tamaño: 512x512px o mayor
- Fuente: Sitio oficial o búsqueda Google
- Guardar como: `/carousel/assets/{tool}-logo.png`

"""

        content += f"""### Paso 2: Guardar Assets

Copia los logos descargados a:
```
{bundle_path}/carousel/assets/
```

Nombres recomendados:
"""

        for tool in unique_tools:
            content += f"- {tool}-logo.png\n"

        content += f"""

### Paso 3: Regenerar Slides

Ejecuta el comando de regeneración:
```bash
python3 scripts/generate-carousel.py "{bundle_id}" --regenerate-slides "NUMEROS"
```

Ejemplo regenerar slides 2 y 5:
```bash
python3 scripts/generate-carousel.py "{bundle_id}" --regenerate-slides "2,5"
```

El script automáticamente:
1. Busca assets en `/carousel/assets/`
2. Usa nano-banana-edit para overlay de logos
3. Mantiene estilo hand-drawn original
4. Sobrescribe slides originales con versiones mejoradas
5. Sincroniza a Google Drive automáticamente

---

## 🛠️ Slides Sugeridos para Regenerar

"""

        for item in slides_with_opportunities:
            slide = item["slide"]
            tools = item["tools"]

            content += f"""**Slide {slide["number"]} - {slide["title"]}:**
- Herramienta: {", ".join(tools)}
- Asset sugerido: {tools[0]}-logo.png
- Comando: `python3 scripts/generate-carousel.py {bundle_id} --regenerate-slides "{slide["number"]}"`

"""

        content += f"""---

## ✅ Checklist

- [ ] Descargar logos oficiales
- [ ] Copiar a /carousel/assets/
- [ ] Ejecutar regeneración
- [ ] Verificar resultados en Google Drive

## 💡 Consejos

- Los assets se incorporan automáticamente vía nano-banana-edit
- El estilo hand-drawn original se mantiene
- Solo regenera slides que necesiten logos
- Puedes regenerar múltiples veces si no te gusta el resultado

---
"""

    # Escribir archivo
    with open(assets_file, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"   ✅ Guía de assets guardada: {assets_file.name}")


def generate_manifest(bundle_id: str, carousel_dir: Path, slides_generated: List[Dict]):
    """Genera manifest.json con metadata de la generación."""
    manifest = {
        "success": True,
        "bundle_id": bundle_id,
        "generated_at": datetime.now().isoformat(),
        "total_slides": len(slides_generated),
        "carousel": slides_generated
    }

    manifest_file = carousel_dir / "manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"   ✅ Manifest generado: manifest.json")


def copy_to_google_drive(bundle_id: str, carousel_dir: Path):
    """Copia carrusel a Google Drive."""
    if not GOOGLE_DRIVE_CAROUSEL.exists():
        print(f"   ⚠️  Carpeta Google Drive no encontrada: {GOOGLE_DRIVE_CAROUSEL}")
        return

    # Crear subcarpeta para este bundle
    drive_bundle_dir = GOOGLE_DRIVE_CAROUSEL / bundle_id
    drive_bundle_dir.mkdir(parents=True, exist_ok=True)

    # Copiar todos los archivos PNG y manifest
    for file in carousel_dir.glob("carousel-*.png"):
        shutil.copy2(file, drive_bundle_dir / file.name)

    manifest_file = carousel_dir / "manifest.json"
    if manifest_file.exists():
        shutil.copy2(manifest_file, drive_bundle_dir / "manifest.json")

    # Copiar guía de assets si existe
    assets_guide = carousel_dir / "carousel-assets-needed.md"
    if assets_guide.exists():
        shutil.copy2(assets_guide, drive_bundle_dir / "carousel-assets-needed.md")

    print(f"   ✅ Copiado a Google Drive: CAROUSEL/{bundle_id}/")


def main():
    parser = argparse.ArgumentParser(description="Genera carruseles Instagram con Nano Banana")
    parser.add_argument("bundle_id", help="ID del bundle (ej: 2026-01-14-chatbot-whatsapp-n8n)")
    parser.add_argument("--skip-interactive", action="store_true",
                        help="Salta input() interactivo, usa assets ya existentes en /carousel/assets/")
    parser.add_argument("--regenerate-slides", type=str, default=None,
                        help="Lista de slides a regenerar (ej: '2,4,6')")
    parser.add_argument("--dry-run", action="store_true",
                        help="Solo muestra brief y entidades detectadas, no genera imagenes")

    args = parser.parse_args()
    bundle_id = args.bundle_id

    print(f"\n{'='*60}")
    print(f"CAROUSEL GENERATOR - Nano Banana")
    print(f"{'='*60}")
    print(f"\n📦 Bundle: {bundle_id}")

    # Validar bundle existe
    bundle_path = OUTPUTS_DIR / bundle_id
    if not bundle_path.exists():
        print(f"❌ Error: Bundle no encontrado en {bundle_path}")
        sys.exit(1)

    print(f"📁 Path: {bundle_path}\n")

    # Parsear slides
    print("📖 Parseando repurpose-pack.md...")
    slides = parse_repurpose_pack(bundle_path)

    if not slides:
        sys.exit(1)

    # Crear directorio carousel y assets
    carousel_dir = bundle_path / "carousel"
    carousel_dir.mkdir(exist_ok=True)

    assets_dir = carousel_dir / "assets"
    assets_dir.mkdir(exist_ok=True)

    # FASE 1: Detectar entidades en slides y mostrar brief
    print("\n" + "="*60)
    print("BRIEF DEL CARRUSEL")
    print("="*60)

    entities_by_slide = detect_entities_in_slides(slides)

    # Mostrar brief completo
    print(f"\nTotal slides: {len(slides)}")
    print(f"Formato: Instagram Carousel (1080x1350px, 4:5)")
    print(f"Estilo: Hand-drawn watercolor minimalista\n")

    for slide in slides:
        slide_num = slide["number"]
        slide_type = determine_slide_type(slide_num, len(slides))
        entities = entities_by_slide.get(slide_num, [])
        entity_str = f" | Entidades: {', '.join(entities)}" if entities else ""

        print(f"  Slide {slide_num} [{slide_type}]: {slide['title']}{entity_str}")

    # Resumen de entidades
    all_entities = set()
    for ents in entities_by_slide.values():
        all_entities.update(ents)

    if all_entities:
        print(f"\nEntidades detectadas: {', '.join(sorted(all_entities))}")
        print(f"Slides con entidades: {len(entities_by_slide)} de {len(slides)}")
    else:
        print(f"\nNo se detectaron entidades (herramientas/empresas) en los slides")

    print(f"\n" + "="*60)

    # Si es dry-run, terminar aqui
    if args.dry_run:
        print(f"\n(dry-run) Brief mostrado. No se generaron imagenes.")
        print(f"Ejecuta sin --dry-run para generar las imagenes.")
        sys.exit(0)

    # Obtener API key (solo si vamos a generar)
    api_key = get_api_key()

    # FASE 2: Mapeo de assets existentes
    print(f"\nMAPEO DE ASSETS\n")

    asset_map = {}  # Maps slide_num -> (Path to asset, entity name)

    if entities_by_slide:
        # Siempre buscar assets existentes en la carpeta
        existing_assets = list(assets_dir.glob("*.png"))

        if existing_assets:
            print(f"   Assets encontrados en /carousel/assets/:")
            for asset in existing_assets:
                print(f"      - {asset.name}")

            # Map existing assets to slides
            for slide_num, entities in entities_by_slide.items():
                for entity in entities:
                    asset_path = assets_dir / f"{entity}.png"
                    if asset_path.exists():
                        asset_map[slide_num] = (asset_path, entity)
                        print(f"      -> '{entity}.png' asignado a slide {slide_num}")
                        break  # One asset per slide

            print(f"\n   Assets mapeados: {len(asset_map)}")

        elif not args.skip_interactive:
            # Interactive collection ONLY if --skip-interactive is NOT set
            print(f"   Modo interactivo: preguntando por assets...\n")
            for slide_num, entities in entities_by_slide.items():
                slide = next(s for s in slides if s['number'] == slide_num)

                print(f"\n   Slide {slide_num} - {slide['title']}")
                print(f"   Detecte: {', '.join(entities)}")

                for entity in entities:
                    print(f"\n   Tienes una imagen para {entity}?")
                    print(f"   - Pega URL de imagen")
                    print(f"   - O escribe 'skip' para continuar sin imagen")

                    user_input = input(f"   {entity} -> ").strip()

                    if user_input.lower() == 'skip':
                        print(f"   Continuando sin asset para {entity}")
                        continue

                    if not user_input.startswith('http'):
                        print(f"   URL invalida, continuando sin asset")
                        continue

                    asset_path = download_asset_from_url(user_input, entity, assets_dir)

                    if asset_path:
                        asset_map[slide_num] = (asset_path, entity)
                        print(f"   Asset registrado para slide {slide_num}")
                        break

            print(f"\n   Assets recolectados: {len(asset_map)}")
        else:
            print(f"   Modo no-interactivo: no hay assets, generando solo con ilustraciones")
    else:
        print(f"   No hay entidades detectadas, generando solo con ilustraciones")

    # Auto-assign headshot to cierre (last slide) if available
    last_slide_num = slides[-1]["number"]
    headshot_path = assets_dir / "headshot.png"
    if headshot_path.exists() and last_slide_num not in asset_map:
        asset_map[last_slide_num] = (headshot_path, "headshot")
        print(f"\n   🎤 Headshot asignado automáticamente a slide {last_slide_num} (cierre)")

    # Parse --regenerate-slides filter
    only_slides = None
    if args.regenerate_slides:
        only_slides = set(int(s.strip()) for s in args.regenerate_slides.split(","))
        print(f"\n🔄 Regenerando solo slides: {sorted(only_slides)}\n")

    # FASE 3: Generar slides con integracion creativa
    print(f"\nGENERANDO SLIDES\n")

    slides_generated = []
    start_time = time.time()

    for idx, slide in enumerate(slides, 1):
        slide_num = slide["number"]
        slide_type = determine_slide_type(slide_num, len(slides))

        # Skip slides not in regeneration list
        if only_slides and slide_num not in only_slides:
            print(f"Slide {slide_num}/{len(slides)} - {slide['title']} (saltando)")
            continue

        print(f"Slide {slide_num}/{len(slides)} - {slide['title']}")
        print(f"   Tipo: {slide_type}")

        has_asset = slide_num in asset_map
        entity = asset_map[slide_num][1] if has_asset else None

        if has_asset:
            print(f"   Con asset de: {entity}")

        prompt = generate_creative_integration_prompt(
            slide_type=slide_type,
            title=slide["title"],
            content=slide["content"],
            entity=entity,
            has_asset=has_asset
        )

        # Resolver URL del logo si tiene asset
        image_input = None
        if has_asset:
            asset_path = asset_map[slide_num][0]
            logo_url = upload_asset_to_kie(api_key, asset_path)  # Retorna URL pública de urls.json
            if logo_url:
                image_input = [logo_url]

        print(f"   Creando tarea en Kie AI...")
        task_id = create_kie_task(api_key, prompt, image_input)

        if not task_id:
            print(f"   Saltando slide {slide_num} (error creando tarea)\n")
            continue

        print(f"   Esperando resultado (taskId: {task_id[:12]}...)...")
        image_url = poll_task_status(api_key, task_id)

        if not image_url:
            print(f"   Saltando slide {slide_num} (timeout o error)\n")
            continue

        output_filename = f"carousel-{slide_num:02d}.png"
        output_path = carousel_dir / output_filename

        print(f"   Descargando imagen...")
        if download_image(image_url, output_path):
            print(f"   Guardado: {output_filename}\n")

            slides_generated.append({
                "id": slide_num,
                "type": slide_type,
                "title": slide["title"],
                "filename": output_filename,
                "success": True,
                "with_asset": entity if has_asset else None
            })
        else:
            print(f"   Error descargando imagen\n")

        if idx < len(slides):
            time.sleep(2)

    # Generar assets guide
    print("\nGenerando guia de assets...")
    generate_assets_needed_md(bundle_id, bundle_path, slides, entities_by_slide)

    # Generar manifest
    print("Generando manifest...")
    generate_manifest(bundle_id, carousel_dir, slides_generated)

    # Copiar a Google Drive
    print("\nCopiando a Google Drive...")
    copy_to_google_drive(bundle_id, carousel_dir)

    # Reporte final
    elapsed_time = time.time() - start_time
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)

    print(f"\n" + "="*60)
    print(f"CARRUSEL GENERADO EXITOSAMENTE")
    print(f"="*60)
    print(f"\nUbicacion: {carousel_dir}")
    print(f"Imagenes: {len(slides_generated)} slides generados")
    print(f"Google Drive: CAROUSEL/{bundle_id}/")
    print(f"Costo estimado: ~${len(slides_generated) * 0.10:.2f}")
    print(f"Tiempo: {minutes}m {seconds}s")
    print(f"\n" + "="*60 + "\n")


if __name__ == "__main__":
    main()
