import os
import hashlib
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException, status, Query
from pydantic import BaseModel
import pymysql

from backend.database import get_connection, init_db
from backend.ml_engine import predict_sales_for_period, train_decision_tree
from backend.apriori_engine import get_association_rules, get_recommendations_for_item

# Inisialisasi basis data jika belum ada
init_db()

app = FastAPI(title="Sistem Prediksi Penjualan Warung", version="1.0.0")

# --- Hashing Helper ---
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# --- Pydantic Schemas ---
class UserLogin(BaseModel):
    username: str
    password: str

class UserRegister(BaseModel):
    username: str
    password: str

class BarangCreate(BaseModel):
    kode_barang: str
    nama_barang: str
    kategori: str
    harga_jual: int
    stok: float

class BarangUpdate(BaseModel):
    nama_barang: str
    kategori: str
    harga_jual: int
    stok: float

class TransactionDetailInput(BaseModel):
    barang_id: int
    jumlah: float
    subtotal: int

class TransactionCreate(BaseModel):
    nomor_nota: str
    total_bayar: int
    items: List[TransactionDetailInput]

# --- API Endpoints ---

# 1. Autentikasi
@app.post("/api/register")
def register(user: UserRegister):
    conn = get_connection()
    cursor = conn.cursor()
    hashed = hash_password(user.password)
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (user.username, hashed))
        conn.commit()
    except pymysql.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Username sudah terdaftar.")
    conn.close()
    return {"message": "User berhasil didaftarkan."}

@app.post("/api/login")
def login(user: UserLogin):
    conn = get_connection()
    cursor = conn.cursor()
    hashed = hash_password(user.password)
    cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (user.username, hashed))
    db_user = cursor.fetchone()
    conn.close()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Username atau password salah.")
    return {"username": db_user["username"], "message": "Login berhasil."}


# 2. CRUD Barang
@app.get("/api/barang")
def list_barang():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM barang")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.post("/api/barang")
def create_barang(item: BarangCreate):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO barang (kode_barang, nama_barang, kategori, harga_jual, stok) VALUES (%s, %s, %s, %s, %s)",
            (item.kode_barang, item.nama_barang, item.kategori, item.harga_jual, item.stok)
        )
        conn.commit()
    except pymysql.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Kode barang sudah digunakan.")
    conn.close()
    return {"message": "Barang berhasil ditambahkan."}

@app.put("/api/barang/{barang_id}")
def update_barang(barang_id: int, item: BarangUpdate):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM barang WHERE id = %s", (barang_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Barang tidak ditemukan.")
    
    cursor.execute(
        "UPDATE barang SET nama_barang = %s, kategori = %s, harga_jual = %s, stok = %s WHERE id = %s",
        (item.nama_barang, item.kategori, item.harga_jual, item.stok, barang_id)
    )
    conn.commit()
    conn.close()
    return {"message": "Barang berhasil diperbarui."}

@app.delete("/api/barang/{barang_id}")
def delete_barang(barang_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM barang WHERE id = %s", (barang_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Barang tidak ditemukan.")
    
    try:
        cursor.execute("DELETE FROM barang WHERE id = %s", (barang_id,))
        conn.commit()
    except pymysql.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Barang tidak dapat dihapus karena sudah ada riwayat transaksi.")
    conn.close()
    return {"message": "Barang berhasil dihapus."}


# 3. Transaksi Penjualan
@app.post("/api/transaksi")
def create_transaksi(trx: TransactionCreate):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Validasi stok untuk semua item terlebih dahulu
    for item in trx.items:
        cursor.execute("SELECT stok, nama_barang FROM barang WHERE id = %s", (item.barang_id,))
        res = cursor.fetchone()
        if not res:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Barang ID {item.barang_id} tidak ditemukan.")
        if res["stok"] < item.jumlah:
            conn.close()
            raise HTTPException(
                status_code=400, 
                detail=f"Stok tidak cukup untuk barang '{res['nama_barang']}'. Sisa stok: {res['stok']}, diminta: {item.jumlah}."
            )
            
    # Mulai transaksi penyimpanan data
    try:
        tanggal_skrg = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO transaksi (nomor_nota, tanggal, total_bayar) VALUES (%s, %s, %s)",
            (trx.nomor_nota, tanggal_skrg, trx.total_bayar)
        )
        transaksi_id = cursor.lastrowid
        
        for item in trx.items:
            # Insert detail
            cursor.execute(
                "INSERT INTO detail_transaksi (transaksi_id, barang_id, jumlah, subtotal) VALUES (%s, %s, %s, %s)",
                (transaksi_id, item.barang_id, item.jumlah, item.subtotal)
            )
            # Potong stok otomatis
            cursor.execute(
                "UPDATE barang SET stok = stok - %s WHERE id = %s",
                (item.jumlah, item.barang_id)
            )
            
        conn.commit()
    except pymysql.IntegrityError:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=400, detail="Nomor nota sudah terdaftar.")
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Terjadi kesalahan: {str(e)}")
        
    conn.close()
    return {"message": "Transaksi berhasil disimpan, stok diperbarui secara otomatis."}


# 4. Prediksi & Rekomendasi Restock
@app.get("/api/prediksi")
def get_prediksi(
    barang_id: int = Query(..., description="ID barang yang dianalisis"),
    periode: str = Query(..., description="Periode target (Format: YYYY-MM)"),
    safety_stock: float = Query(20.0, description="Jumlah safety stock untuk cadangan stok aman")
):
    """
    Mengambil prediksi penjualan untuk barang tertentu pada periode target.
    Mengimplementasikan Caching Data:
    Jika data prediksi sudah ada di database pada tabel `prediksi`, langsung kembalikan.
    Jika belum ada, lakukan kalkulasi via Decision Tree, hitung rekomendasi restock, simpan ke db (cache), lalu kembalikan.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Cek Caching di database
    cursor.execute(
        """
        SELECT p.*, b.nama_barang, b.stok as sisa_stok 
        FROM prediksi p
        JOIN barang b ON p.barang_id = b.id
        WHERE p.barang_id = %s AND p.periode_target = %s
        ORDER BY p.tanggal_prediksi DESC LIMIT 1
        """,
        (barang_id, periode)
    )
    cached = cursor.fetchone()
    
    if cached:
        # Cek jika sisa_stok saat ini berubah, kita hitung ulang rekomendasi restock yang dinamis
        # Rekomendasi Restock = Hasil Prediksi + Safety Stock - Sisa Stok
        jumlah_prediksi = cached["jumlah_prediksi"]
        sisa_stok = cached["sisa_stok"]
        rekomendasi_stok = max(0, jumlah_prediksi + safety_stock - sisa_stok)
        
        # Update nilai rekomendasi ter-update di DB
        cursor.execute(
            "UPDATE prediksi SET rekomendasi_stok = %s WHERE id = %s",
            (rekomendasi_stok, cached["id"])
        )
        conn.commit()
        conn.close()
        
        return {
            "cached": True,
            "barang_id": cached["barang_id"],
            "nama_barang": cached["nama_barang"],
            "periode_target": cached["periode_target"],
            "jumlah_prediksi": jumlah_prediksi,
            "rekomendasi_stok": rekomendasi_stok,
            "sisa_stok": sisa_stok,
            "tanggal_prediksi": cached["tanggal_prediksi"]
        }
        
    conn.close()

    # 2. Jika tidak ada di cache, lakukan inferensi Machine Learning
    try:
        # Parse periode target
        year, month = map(int, periode.split("-"))
    except ValueError:
        raise HTTPException(status_code=400, detail="Format periode harus YYYY-MM (contoh: 2026-07).")
        
    res = predict_sales_for_period(barang_id, year, month)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["message"])
        
    # Hitung rekomendasi restock
    jumlah_prediksi = res["jumlah_prediksi"]
    sisa_stok = res["sisa_stok"]
    rekomendasi_stok = max(0, jumlah_prediksi + safety_stock - sisa_stok)
    
    # 3. Simpan ke database (Caching)
    conn = get_connection()
    cursor = conn.cursor()
    tanggal_pred = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        """
        INSERT INTO prediksi (barang_id, tanggal_prediksi, periode_target, jumlah_prediksi, rekomendasi_stok)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (barang_id, tanggal_pred, periode, jumlah_prediksi, rekomendasi_stok)
    )
    conn.commit()
    conn.close()
    
    return {
        "cached": False,
        "barang_id": barang_id,
        "nama_barang": res["nama_barang"],
        "periode_target": periode,
        "jumlah_prediksi": jumlah_prediksi,
        "rekomendasi_stok": rekomendasi_stok,
        "sisa_stok": sisa_stok,
        "tanggal_prediksi": tanggal_pred,
        "weekly_predictions": res["weekly_predictions"],
        "mean_mae": res["mean_mae"]
    }


# 5. Retrain Model
@app.post("/api/train")
def train_model():
    res = train_decision_tree()
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["message"])
    return res


# 6. Dashboard Analytics
@app.get("/api/dashboard")
def get_dashboard_summary():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Hitung total omzet (total total_bayar)
    cursor.execute("SELECT SUM(total_bayar) as omzet FROM transaksi")
    omzet_res = cursor.fetchone()
    total_omzet = omzet_res["omzet"] if omzet_res["omzet"] else 0
    
    # 2. Hitung total jenis barang & total stok fisik
    cursor.execute("SELECT COUNT(*) as jenis_barang, SUM(stok) as total_stok FROM barang")
    stok_res = cursor.fetchone()
    jenis_barang = stok_res["jenis_barang"] if stok_res["jenis_barang"] else 0
    total_stok = stok_res["total_stok"] if stok_res["total_stok"] else 0
    
    # 3. Peringatan Stok Menipis (stok < 10)
    cursor.execute("SELECT id, kode_barang, nama_barang, kategori, stok FROM barang WHERE stok < 10 ORDER BY stok ASC")
    low_stock = cursor.fetchall()
    
    # 4. Transaksi Terbaru (5 baris)
    cursor.execute("SELECT * FROM transaksi ORDER BY tanggal DESC LIMIT 5")
    recent_trx = cursor.fetchall()
    
    conn.close()
    
    return {
        "total_omzet": total_omzet,
        "jenis_barang": jenis_barang,
        "total_stok": total_stok,
        "low_stock_alerts": [dict(item) for item in low_stock],
        "recent_transactions": [dict(trx) for trx in recent_trx]
    }


# 7. Laporan Penjualan Detail
@app.get("/api/laporan")
def get_laporan(
    start_date: Optional[str] = Query(None, description="Tanggal awal filter (Format: YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Tanggal akhir filter (Format: YYYY-MM-DD)")
):
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
    SELECT 
        t.nomor_nota, 
        t.tanggal, 
        b.nama_barang, 
        d.jumlah, 
        d.subtotal
    FROM detail_transaksi d
    JOIN transaksi t ON d.transaksi_id = t.id
    JOIN barang b ON d.barang_id = b.id
    """
    
    params = []
    conditions = []
    
    if start_date:
        conditions.append("t.tanggal >= %s")
        params.append(f"{start_date} 00:00:00")
    if end_date:
        conditions.append("t.tanggal <= %s")
        params.append(f"{end_date} 23:59:59")
        
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
        
    query += " ORDER BY t.tanggal DESC"
    
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


# 8. Apriori Association Rules
@app.get("/api/apriori")
def list_apriori_rules(
    min_support: float = Query(0.02, description="Batas minimal support (default: 0.02)"),
    min_confidence: float = Query(0.3, description="Batas minimal confidence (default: 0.3)")
):
    try:
        rules = get_association_rules(min_support, min_confidence)
        return rules
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal memproses Apriori: {str(e)}")

@app.get("/api/rekomendasi/{barang_id}")
def get_rekomendasi(
    barang_id: int,
    min_support: float = Query(0.02, description="Batas minimal support (default: 0.02)"),
    min_confidence: float = Query(0.3, description="Batas minimal confidence (default: 0.3)")
):
    try:
        recs = get_recommendations_for_item(barang_id, min_support, min_confidence)
        return recs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal mendapatkan rekomendasi: {str(e)}")
