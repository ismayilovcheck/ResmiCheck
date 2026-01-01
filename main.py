from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import re
import openai
import os

# OPENAI API açarını əvəz et: https://platform.openai.com/account/api-keys
openai.api_key = "YOUR_OPENAI_API_KEY"

app = FastAPI(title="ResmiCheck AI + Qaydalar")

# CORS (frontend üçün açıq)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class TextRequest(BaseModel):
    text: str

@app.post("/analyze")
def analyze_text(data: TextRequest):
    text = data.text.strip()
    if not text:
        return {"result": "Zəhmət olmasa mətni daxil edin."}

    # ---------- ƏVVƏLKİ QAYDALAR ---------- #
    problems = []

    # Qeyri-rəsmi ifadələr
    informal_patterns = [
        r"\bsalam\b",
        r"\bnecə\b",
        r"\bçox sağ ol\b",
        r"\bsağ ol\b",
        r"\bxahiş edirəm\b"
    ]

    for pattern in informal_patterns:
        if re.search(pattern, text.lower()):
            problems.append("Qeyri-rəsmi ifadələr aşkar edildi.")

    # Çox qısa mətn
    if len(text.split()) < 25:
        problems.append("Mətn rəsmi sənəd üçün çox qısadır.")

    # Böyük hərf + nida
    if re.search(r"[A-ZƏÖÜİĞÇ]{4,}!", text):
        problems.append("Rəsmi mətndə böyük hərf və nida uyğun deyil.")

    # ---------- AI İNTEQRASİYASI ---------- #
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Sən rəsmi sənəd yoxlama AI-sən. Mətnin rəsmi olub olmadığını yoxla, dil, ton, uzunluq və səhvləri qeyd et. Düzəliş təklif et."},
                {"role": "user", "content": text}
            ],
            max_tokens=500,
            temperature=0.2
        )

        ai_result = response['choices'][0]['message']['content'].strip()

    except Exception as e:
        ai_result = f"AI yoxlaması mümkün olmadı: {str(e)}"

    # ---------- NƏTİCƏ BİRLƏŞDİRİLMƏSİ ---------- #
    if problems:
        result_text = "Əvvəlki qaydalar üzrə aşkar olunan problemlər:\n" + "\n".join(f"- {p}" for p in problems) + "\n\nAI yoxlaması:\n" + ai_result
    else:
        result_text = "Əvvəlki qaydalara əsasən heç bir problem aşkar edilmədi.\n\nAI yoxlaması:\n" + ai_result

    return {"result": result_text}
