from dotenv import load_dotenv
load_dotenv()
import json
import os
import asyncio
import time
from collections import defaultdict
from agent import analyze_food_image_with_vertex_async

GOLDEN_SET_DIR = "GoldenSet"
GROUND_TRUTH_FILE = os.path.join(GOLDEN_SET_DIR, "ground_truth.json")
MAX_CONCURRENT_REQUESTS = 5
MAX_RETRIES = 3
INITIAL_BACKOFF = 2  # segundos

def calculate_error(expected: float, predicted: float) -> float:
    ""
    if expected == 0:
        return 0.0
    return abs(expected - predicted) / expected

async def process_image_with_retry(img_name, img_path, expected_data, semaphore):
    ""
    async with semaphore:
        print(f"[{img_name}] Iniciando análisis...")
        if not os.path.exists(img_path):
            dummy_jpeg = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xdb\x00C\x01\t\t\t\x0c\x0b\x0c\x18\r\r\x182!\x1c!22222222222222222222222222222222222222222222222222\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x03\x01"\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16\x17\x18\x19\x1a%&\'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xc4\x00\x1c\x01\x00\x02\x03\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\xff\xc4\x00\xda\x11\x00\x02\x01\x02\x04\x04\x03\x04\x07\x05\x04\x04\x00\x01\x02w\x00\x01\x02\x03\x11\x04\x05!1\x06\x12AQ\x07aq\x13"2\x81\x08\x14B\x91\xa1\xb1\xc1\t#3R\xf0\x15br\xd1\n\x16$4\xe1%\xf1\x17\x18\x19\x1a&\'()*56789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00?\x00\xfd\xfc\xa2\x8a(\xa0\x0f\xff\xd9'
            with open(img_path, "wb") as f:
                f.write(dummy_jpeg)

        with open(img_path, "rb") as f:
            image_bytes = f.read()

        category = expected_data["category"]
        expected_metrics = expected_data["metrics"]

        for attempt in range(MAX_RETRIES):
            try:
                mime = "image/png" if img_name.lower().endswith(".png") else "image/jpeg"
                result = await analyze_food_image_with_vertex_async(image_bytes, mime_type=mime)
                if "error" in result:
                    raise Exception(result["error"])

                print(f"[{img_name}] Completado con éxito.")
                errors = {}
                for metric in ["calories", "protein_g", "carbs_g", "fats_g"]:
                    err = calculate_error(expected_metrics[metric], result.get(metric, 0))
                    errors[metric] = err

                return {
                    "status": "success",
                    "img_name": img_name,
                    "category": category,
                    "errors": errors
                }

            except Exception as e:
                err_msg = str(e)
                if "429" in err_msg or "quota" in err_msg.lower():
                    backoff = INITIAL_BACKOFF * (2 ** attempt)
                    print(f"[{img_name}] Cuota excedida/Error. Reintentando en {backoff}s... (Intento {attempt+1}/{MAX_RETRIES})")
                    await asyncio.sleep(backoff)
                else:
                    print(f"[{img_name}] Fallo definitivo: {err_msg}")
                    break

        return {
            "status": "failed",
            "img_name": img_name,
            "category": category,
            "errors": None
        }

async def run_tests_async():
    if not os.path.exists(GROUND_TRUTH_FILE):
        print(f"No se encontró el archivo {GROUND_TRUTH_FILE}. Por favor genera el dataset primero.")
        return

    with open(GROUND_TRUTH_FILE, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)

    print(f"Iniciando pruebas asíncronas para {len(ground_truth)} imágenes...\n")
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    tasks = []
    for img_name, data in ground_truth.items():
        img_path = os.path.join(GOLDEN_SET_DIR, img_name)
        tasks.append(process_image_with_retry(img_name, img_path, data, semaphore))

    start_time = time.time()
    results = await asyncio.gather(*tasks)
    end_time = time.time()
    total_errors_general = {"calories": [], "protein_g": [], "carbs_g": [], "fats_g": []}
    errors_by_category = defaultdict(lambda: {"calories": [], "protein_g": [], "carbs_g": [], "fats_g": []})

    successful = 0
    failed = 0

    for res in results:
        if res["status"] == "success":
            successful += 1
            cat = res["category"]
            for metric, err in res["errors"].items():
                total_errors_general[metric].append(err)
                errors_by_category[cat][metric].append(err)
        else:
            failed += 1
    print("\n" + "="*50)
    print("REPORTE FINAL DE PRECISIÓN (Margen de Error %)")
    print("="*50)
    print(f"Imágenes Procesadas: {successful} éxitos | {failed} fallos")
    print(f"Tiempo de ejecución: {end_time - start_time:.2f} segundos\n")

    if successful == 0:
        print("Ninguna imagen fue procesada con éxito. Revisa tus credenciales GCP.")
        return

    print("--- ERROR GENERAL PROMEDIO ---")
    for metric, err_list in total_errors_general.items():
        if err_list:
            avg_err = (sum(err_list) / len(err_list)) * 100
            print(f"  {metric.capitalize()}: {avg_err:.2f}%")

    print("\n--- ERROR PROMEDIO POR CATEGORÍA ---")
    for cat, metrics_dict in errors_by_category.items():
        print(f"[{cat}]")
        for metric, err_list in metrics_dict.items():
            if err_list:
                avg_err = (sum(err_list) / len(err_list)) * 100
                print(f"  - {metric.capitalize()}: {avg_err:.2f}%")
        print()

if __name__ == "__main__":
    asyncio.run(run_tests_async())
