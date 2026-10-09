import os
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google import genai
from google.genai import types
import json

app = FastAPI()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Inisialisasi client
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
      "target_distance_km": float (Jarak rekomendasi untuk BESOK)",
      "target_pace": "string (Pace rekomendasi untuk BESOK)",
      "advice": "string (Evaluasi singkat latihan hari ini, alasan memilih latihan besok, zona detak jantung, dan tips pemulihan/eksekusi)"
    }}
    """

    # Menggunakan prefix 'models/' sesuai standar SDK google-genai
    candidate_models = [
        "models/gemini-2.5-flash",
        "models/gemini-1.5-flash",
        "gemini-2.5-flash"
    ]

    last_error = ""
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
            last_error = str(e)
            print(f"Gagal memanggil {model_name}: {e}")
            time.sleep(1)

    raise HTTPException(
        status_code=503, 
        detail=f"Gagal memanggil AI: {last_error}"
    )
