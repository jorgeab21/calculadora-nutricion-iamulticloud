import json
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("Falta configurar la variable de entorno GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_INSTRUCTION = """
Eres un nutricionista experto. Analiza la imagen de comida proporcionada y devuelve un objeto JSON estricto con la siguiente estructura:
{
    "food_identified": "Nombre descriptivo del plato",
    "calories": 0,
    "protein_g": 0,
    "carbs_g": 0,
    "fats_g": 0,
    "micronutrients": "Breve descripción de vitaminas/minerales clave presentes"
}
Asegúrate de que los valores numéricos sean números (no texto).
No incluyas texto fuera del JSON. Si no puedes identificar la comida, haz tu mejor estimación.
"""

def analyze_food_image_with_vertex(image_bytes: bytes, mime_type: str = "image/jpeg", retries: int = 3) -> dict:
    ""
    import time
    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[
                    SYSTEM_INSTRUCTION,
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2,
                )
            )
            return json.loads(response.text.strip())
        except json.JSONDecodeError:
            return {"error": "El modelo no devolvió un JSON válido."}
        except Exception as e:
            if ("503" in str(e) or "429" in str(e)) and attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            return {"error": str(e)}

async def analyze_food_image_with_vertex_async(image_bytes: bytes, mime_type: str = "image/jpeg", retries: int = 3) -> dict:
    ""
    import asyncio
    for attempt in range(retries):
        try:
            response = await client.aio.models.generate_content(
                model='gemini-2.5-flash',
                contents=[
                    SYSTEM_INSTRUCTION,
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2,
                )
            )
            return json.loads(response.text.strip())
        except json.JSONDecodeError:
            return {"error": "El modelo no devolvió un JSON válido."}
        except Exception as e:
            if ("503" in str(e) or "429" in str(e)) and attempt < retries - 1:
                await asyncio.sleep(2 ** attempt)
                continue
            return {"error": str(e)}
