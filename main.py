from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse # Bunu ekledik

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

# Statik dosyaları (CSS, JS vb. varsa) kullanabilmek için
app.mount("/static", StaticFiles(directory="static"), name="static")
