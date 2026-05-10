import json
import os

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse # Bunu ekledik
from pydantic import BaseModel

load_dotenv()

MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY")
MINIMAX_MODEL = os.getenv("MINIMAX_MODEL", "MiniMax-M2.7")
MINIMAX_BASE_URL = os.getenv("MINIMAX_BASE_URL", "https://api.minimax.io/v1")
MINIMAX_TIMEOUT_SECONDS = 30

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

products = [
    {"id": 1, "name": "Domates", "stock": 40},
    {"id": 2, "name": "Salatalık", "stock": 120},
    {"id": 3, "name": "Patates", "stock": 10}
]

orders = [
    {"id": 101, "customer": "Ali", "status": "Kargoda"},
    {"id": 102, "customer": "Ayşe", "status": "Hazırlanıyor"},
    {"id": 103, "customer": "Mehmet", "status": "Teslim edildi"}
]

# --- KRİTİK DEĞİŞİKLİK BURADA ---
@app.get("/")
def home():
    # Artık mesaj döndürmüyoruz, direkt HTML dosyasını gönderiyoruz
    return FileResponse("static/index.html") 

@app.get("/products")
def get_products():
    return products

@app.get("/orders")
def get_orders():
    return orders

@app.get("/chat")
def chat(message: str):
    message = message.lower()
    if "stok" in message or "kaç" in message:
        for p in products:
            if p["name"].lower() in message:
                return {"answer": f"{p['name']} stok: {p['stock']}"}
    if "sipariş" in message:
        for o in orders:
            if str(o["id"]) in message:
                return {"answer": f"Sipariş {o['id']} durumu: {o['status']}"}
    if "düşük" in message:
        low = [p["name"] for p in products if p["stock"] < 50]
        return {"answer": f"Düşük stoklu ürünler: {', '.join(low)}"}
    
    return {"answer": "Anlayamadım, tekrar sor"}

class AiChatRequest(BaseModel):
    message: str


def build_inventory_context() -> str:
    return json.dumps(
        {"products": products, "orders": orders},
        ensure_ascii=False,
    )


def build_system_prompt() -> str:
    return (
        "Sen bir Türkçe stok ve sipariş asistanısın. "
        "Kullanıcının sorularını yalnızca aşağıda verilen JSON verisine dayanarak yanıtla. "
        "Veride olmayan bilgileri uydurma; bilmiyorsan açıkça söyle. "
        "Kısa, net ve Türkçe yanıt ver.\n\n"
        f"VERİ:\n{build_inventory_context()}"
    )


async def call_minimax(user_message: str) -> str:
    if not MINIMAX_API_KEY or MINIMAX_API_KEY.startswith("replace_with_"):
        raise HTTPException(status_code=500, detail="MINIMAX_API_KEY tanımlı değil")

    payload = {
        "model": MINIMAX_MODEL,
        "messages": [
            {"role": "system", "content": build_system_prompt()},
            {"role": "user", "content": user_message},
        ],
    }
    headers = {
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json",
    }
    url = f"{MINIMAX_BASE_URL}/text/chatcompletion_v2"

    async with httpx.AsyncClient(timeout=MINIMAX_TIMEOUT_SECONDS) as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"MiniMax bağlantı hatası: {exc}")

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"MiniMax hata {response.status_code}: {response.text}",
        )

    data = response.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise HTTPException(status_code=502, detail=f"Beklenmeyen MiniMax yanıtı: {data}")


@app.post("/ai-chat")
async def ai_chat(request: AiChatRequest):
    answer = await call_minimax(request.message)
    return {"answer": answer}


# Statik dosyaları (CSS, JS vb. varsa) kullanabilmek için
app.mount("/static", StaticFiles(directory="static"), name="static")
