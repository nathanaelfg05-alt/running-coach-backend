import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

app = FastAPI()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

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

    # Daftar model yang dicoba
    candidate_models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
    
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY
    }

    last_error = ""

    async with httpx.AsyncClient(timeout=30.0) as client:
        for model in candidate_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "response_mime_type": "application/json"
                }
            }

            try:
                print(f"Mencoba HTTP Request ke model: {model}...")
                response = await client.post(url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    # Ambil teks JSON dari struktur respon Gemini
                    raw_text = data['candidates'][0]['content']['parts'][0]['text']
                    import json
                    return json.loads(raw_text)
                else:
                    last_error = f"Status {response.status_code}: {response.text}"
                    print(f"Gagal {model}: {last_error}")

            except Exception as e:
                last_error = str(e)
                print(f"Error {model}: {e}")

    raise HTTPException(
        status_code=503,
        detail=f"Gagal memanggil Gemini API: {last_error}"
    )
