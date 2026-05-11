import os
import httpx

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

load_dotenv()

MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY")
MINIMAX_MODEL = os.getenv("MINIMAX_MODEL", "MiniMax-M2.7")
MINIMAX_BASE_URL = os.getenv("MINIMAX_BASE_URL", "https://api.minimax.io/v1")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- DATA ----------------
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

DELIVERED_STATUS = "Teslim edildi"

# ---------------- FRONTEND ----------------
@app.get("/")
def home():
    return FileResponse("static/index.html")

# ---------------- SIMPLE API ----------------
@app.get("/products")
def get_products():
    return products

@app.get("/orders")
def get_orders():
    return orders


# ---------------- CHAT (RULE-BASED) ----------------
@app.get("/chat")
def chat(message: str):

    msg = message.lower()

    # stok sorgusu
    if "stok" in msg:
        for p in products:
            if p["name"].lower() in msg:
                return {"answer": f"{p['name']} stok: {p['stock']}"}

    # sipariş sorgusu
    if "sipariş" in msg:
        for o in orders:
            if str(o["id"]) in msg:
                return {"answer": f"Sipariş {o['id']} durumu: {o['status']}"}

    # düşük stok
    if "düşük" in msg:
        low = [p["name"] for p in products if p["stock"] < 50]
        return {"answer": f"Düşük stok: {', '.join(low)}"}

    return {"answer": "Anlayamadım"}


# ---------------- AI CORE CLIENT (DRY FIX) ----------------
async def call_minimax(messages: list):

    if not MINIMAX_API_KEY:
        raise HTTPException(status_code=500, detail="API key yok")

    async with httpx.AsyncClient(timeout=30) as client:

        res = await client.post(
            f"{MINIMAX_BASE_URL}/text/chatcompletion_v2",
            json={
                "model": MINIMAX_MODEL,
                "messages": messages
            },
            headers={
                "Authorization": f"Bearer {MINIMAX_API_KEY}",
                "Content-Type": "application/json",
            },
        )

    if res.status_code != 200:
        raise HTTPException(status_code=502, detail=res.text)

    data = res.json()

    try:
        return data["choices"][0]["message"]["content"]
    except Exception:
        return "AI cevap üretilemedi"


# ---------------- SYSTEM PROMPT ----------------
def system_prompt():
    return f"""
Sen bir stok ve sipariş analiz AI’sın.

VERİ:
Ürünler: {products}
Siparişler: {orders}

KURALLAR:
- Soru SORMA
- Açıklama yapma, sadece rapor yaz
- Dashboard formatında kısa ol
- Sonunda soru işareti kullanma

FORMAT:
- Başlık
- Madde madde analiz
- Özet
"""


# ---------------- AI CHAT ----------------
class AiChatRequest(BaseModel):
    message: str


@app.post("/ai-chat")
async def ai_chat(req: AiChatRequest):

    messages = [
        {"role": "system", "content": system_prompt()},
        {"role": "user", "content": req.message},
    ]

    result = await call_minimax(messages)

    return {"answer": result}


# ---------------- TAB AI ----------------
class TabReq(BaseModel):
    type: str
    products: list
    orders: list


@app.post("/ai-tab-analysis")
async def tab_ai(req: TabReq):

    if req.type == "stock":
        prompt = f"Stok analizi yap: {req.products}"

    elif req.type == "live":
        prompt = f"Anlık sipariş analizi: {req.orders}"

    else:
        prompt = f"Geçmiş sipariş analizi: {req.orders}"

    messages = [
        {"role": "system", "content": "Sen profesyonel veri analiz AI’sın."},
        {"role": "user", "content": prompt},
    ]

    result = await call_minimax(messages)

    return {"result": result}


# ---------------- STATIC ----------------
app.mount("/static", StaticFiles(directory="static"), name="static")
