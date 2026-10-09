import os
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google import genai
from google.genai import types
import json

app = FastAPI()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

class TodayWorkout(BaseModel):
    distance_km: float
    duration_minutes: float
    actual_pace: str

class WorkoutRequest(BaseModel):
    target_distance_km: float
    target_pace: str
    today_workout: TodayWorkout

@app.post("/api/recommendation")
async def get_recommendation(request: WorkoutRequest):
    prompt = f"""
    Kamu adalah pelatih lari profesional.
    
    DATA LATIHAN HARI INI:
    - Jarak Tempuh: {request.today_workout.distance_km} KM
    - Durasi: {request.today_workout.duration_minutes} Menit
    - Pace Aktual: {request.today_workout.actual_pace}
    
    TARGET UTAMA PELARI:
    - Target Jarak: {request.target_distance_km} KM
    - Target Pace: {request.target_pace}
    
    TUGAS PELATIH:
    1. Analisis performa lari hari ini dibandingkan dengan target utama pelari.
    2. Tentukan 1 jenis latihan spesifik yang HARUS DILAKUKAN BESOK (misal: Rest Day / Easy Recovery Run / Interval Training / Tempo Run / Long Run).
    
    Kembalikan respon HANYA dalam format JSON valid dengan struktur persis seperti ini:
    {{
      "workout_type": "string (Nama latihan untuk BESOK)",
      "target_distance_km": float (Jarak rekomendasi untuk BESOK),
      "target_pace": "string (Pace rekomendasi untuk BESOK)",
      "advice": "string (Evaluasi singkat latihan hari ini, alasan memilih latihan besok, zona detak jantung, dan tips pemulihan/eksekusi)"
    }}
    """

    # Menggunakan model 2.0-flash dan fallback 1.5-flash
    candidate_models = ["gemini-2.0-flash", "gemini-1.5-flash"]

    for model_name in candidate_models:
        try:
            print(f"Mencoba memanggil model: {model_name}...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            return json.loads(response.text)

        except Exception as e:
            print(f"Gagal memanggil {model_name}: {e}")
            time.sleep(1)

    raise HTTPException(
        status_code=503, 
        detail="Server AI sedang sibuk. Silakan coba lagi beberapa saat lagi."
    )
