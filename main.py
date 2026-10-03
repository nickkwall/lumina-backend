from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3

app = FastAPI(title="Lumina Public API")

# Habilita acesso de qualquer origem (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializa o banco de dados SQLite local
def init_db():
    conn = sqlite3.connect("lumina.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS medicoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            corrente REAL NOT NULL,
            potencia REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

class Medicao(BaseModel):
    corrente: float
    potencia: float

# Rota POST para receber leituras do ESP8266
@app.post("/api/medicoes")
async def receber_medicao(medicao: Medicao):
    try:
        conn = sqlite3.connect("lumina.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO medicoes (corrente, potencia) VALUES (?, ?)",
            (medicao.corrente, medicao.potencia)
        )
        conn.commit()
        conn.close()
        return {"status": "sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Rota GET para consultar a última medição no dashboard
@app.get("/api/medicoes/ultima")
async def ultima_medicao():
    conn = sqlite3.connect("lumina.db")
    cursor = conn.cursor()
    cursor.execute("SELECT corrente, potencia, timestamp FROM medicoes ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {"corrente": row[0], "potencia": row[1], "timestamp": row[2]}
    return {"mensagem": "Nenhuma medição encontrada"}

# Rota GET para obter histórico recente para gráficos
@app.get("/api/medicoes/historico")
async def historico_medicoes(limite: int = 50):
    conn = sqlite3.connect("lumina.db")
    cursor = conn.cursor()
    cursor.execute("SELECT corrente, potencia, timestamp FROM medicoes ORDER BY id DESC LIMIT ?", (limite,))
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {"corrente": r[0], "potencia": r[1], "timestamp": r[2]}
        for r in rows
    ]