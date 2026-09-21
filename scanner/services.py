import base64
import json
import re
from groq import Groq
from django.conf import settings
from .models import FoodItem


def encode_image_to_base64(image_file):
    image_file.seek(0)
    return base64.b64encode(image_file.read()).decode('utf-8')


def detect_food_from_image(image_file, image_content_type='image/jpeg'):
    client = Groq(api_key=settings.GROQ_API_KEY)
    base64_image = encode_image_to_base64(image_file)

    prompt = """Kamu adalah AI food scanner untuk aplikasi tracking carbon footprint makanan Indonesia.

Analisis foto makanan ini dan identifikasi SEMUA item makanan yang terlihat.
Untuk setiap item, berikan estimasi emisi karbon CO2 dalam gram berdasarkan data FAO dan OurWorldInData.

Referensi nilai CO2 per porsi sedang:
- Nasi putih: 240g CO2
- Ayam goreng: 890g CO2
- Tempe goreng: 285g CO2
- Tahu goreng: 195g CO2
- Ikan goreng: 450g CO2
- Rendang sapi: 3150g CO2
- Telur goreng: 220g CO2
- Sayuran tumis: 120-180g CO2
- Mie goreng: 380g CO2
- Es teh manis: 75g CO2

Untuk setiap item, sertakan juga bounding box lokasinya di gambar memakai skala 0-1000
(0,0 = pojok kiri atas gambar, 1000,1000 = pojok kanan bawah gambar), supaya bisa digambar
kotak penanda di atas foto.

Balas HANYA dengan JSON valid, tidak ada teks lain sebelum atau sesudah JSON.
Format response:
{
  "detected_items": [
    {
      "name": "nama makanan dalam Bahasa Indonesia",
      "name_en": "food name in English",
      "co2_grams": 240,
      "confidence": "high/medium/low",
      "serving_description": "deskripsi porsi yang terlihat",
      "category": "kategori makanan",
      "box": {"x_min": 0, "y_min": 0, "x_max": 500, "y_max": 500}
    }
  ],
  "total_co2_grams": 1234,
  "meal_type": "sarapan/makan siang/makan malam/snack",
  "notes": "catatan tambahan jika ada",
  "alternative_suggestion": "saran makanan alternatif yang lebih rendah karbon jika total CO2 tinggi"
}"""

    try:
        completion = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{image_content_type};base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.1,
            max_completion_tokens=1024,
            response_format={"type": "json_object"},
        )

        raw_response = completion.choices[0].message.content
        result = json.loads(raw_response)
        return result, raw_response

    except json.JSONDecodeError:
        try:
            json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return result, raw_response
        except Exception:
            pass
        return None, raw_response

    except Exception as e:
        return None, str(e)


def calculate_carbon_analogy(co2_grams):
    analogies = []

    motor_km = co2_grams / 200
    if motor_km >= 0.5:
        analogies.append(f"setara berkendara motor {motor_km:.1f} km")

    phone_hours = co2_grams / 8.5
    if phone_hours >= 1:
        analogies.append(f"setara mengisi daya HP {phone_hours:.0f} jam")

    if co2_grams > 500:
        flight_percent = (co2_grams / 180000) * 100
        analogies.append(f"setara {flight_percent:.2f}% dari 1 penerbangan Jakarta-Bali")

    return analogies[0] if analogies else f"{co2_grams}g CO2"


def get_carbon_status(co2_grams, daily_budget=2000):
    percentage = (co2_grams / daily_budget) * 100
    if percentage <= 30:
        return 'green', 'Pilihan Hijau'
    elif percentage <= 60:
        return 'yellow', 'Cukup Baik'
    else:
        return 'red', 'Karbon Tinggi'


def box_to_percent(box):
    if not box:
        return None
    try:
        x_min, y_min = float(box['x_min']), float(box['y_min'])
        x_max, y_max = float(box['x_max']), float(box['y_max'])
    except (KeyError, TypeError, ValueError):
        return None

    x_min, x_max = sorted((x_min, x_max))
    y_min, y_max = sorted((y_min, y_max))

    return {
        'left': f'{x_min / 10:.2f}',
        'top': f'{y_min / 10:.2f}',
        'width': f'{(x_max - x_min) / 10:.2f}',
        'height': f'{(y_max - y_min) / 10:.2f}',
    }


def match_food_items_to_db(detected_items):
    matched = []
    for item in detected_items:
        db_match = find_food_item(item.get('name', ''), item.get('name_en', ''))
        matched.append({
            'detected': item,
            'db_item': db_match
        })
    return matched


def find_food_item(name, name_en=''):
    name = (name or '').strip()
    name_en = (name_en or '').strip()
    db_match = None
    if name:
        db_match = FoodItem.objects.filter(name__iexact=name).first()
        if not db_match:
            db_match = FoodItem.objects.filter(name__icontains=name).first()
    if not db_match and name_en:
        db_match = FoodItem.objects.filter(name_en__iexact=name_en).first()
        if not db_match:
            db_match = FoodItem.objects.filter(name_en__icontains=name_en).first()
    return db_match
