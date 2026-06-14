import os
import random
import hashlib
from datetime import datetime
import pandas as pd

from backend.database import get_connection, init_db
from backend.ml_engine import train_decision_tree

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def get_standard_product(name, unit):
    # Strip spaces
    name = name.strip()
    unit = unit.strip()
    
    # Case insensitivity
    name_lower = name.lower()
    unit_lower = unit.lower()
    
    # Defaults
    std_name = name
    category = "Lainnya"
    price = 5000
    
    if "aida" in name_lower:
        std_name = "Aida (Bungkus)"
        category = "Bumbu Dapur"
        price = 3000
    # --- ROKOK STANDARDIZATION ---
    elif "jarim coklat" in name_lower or "jarum cokelat" in name_lower or "jarum coklat" in name_lower or "jarim coklat" in name_lower:
        if "batang" in unit_lower:
            std_name = "Rokok Djarum Coklat (Batang)"
            price = 1500
        else:
            std_name = "Rokok Djarum Coklat (Bungkus)"
            price = 16000
        category = "Rokok"
    elif "jarum super" in name_lower or "rokok super" in name_lower or "rokok jarum" in name_lower or name_lower == "jarum":
        if "batang" in unit_lower:
            std_name = "Rokok Djarum Super (Batang)"
            price = 2200
        else:
            std_name = "Rokok Djarum Super (Bungkus)"
            price = 24000
        category = "Rokok"
    elif "rokok ggm" in name_lower or "garam merah" in name_lower:
        std_name = "Rokok Gudang Garam Merah (Bungkus)"
        category = "Rokok"
        price = 17000
    elif "rokok st mas" in name_lower or "st mas" in name_lower:
        std_name = "Rokok ST Mas (Bungkus)"
        category = "Rokok"
        price = 14000
    elif "tembakau jangkar" in name_lower:
        std_name = "Tembakau Jangkar (Bungkus)"
        category = "Rokok"
        price = 10000
    elif "pahpir" in name_lower or "papir" in name_lower:
        std_name = "Kertas Papir (Bungkus)"
        category = "Rokok"
        price = 2000
    # -----------------------------
    elif "air mineral" in name_lower:
        if "dus" in unit_lower:
            std_name = "Air Mineral (Dus)"
            category = "Minuman"
            price = 35000
        else:
            std_name = "Air Mineral (Botol)"
            category = "Minuman"
            price = 4000
    elif "amplop" in name_lower:
        std_name = "Amplop (Lembar)"
        category = "Alat Tulis"
        price = 1000
    elif "baterai" in name_lower:
        std_name = "Baterai ABC (Pcs)"
        category = "Perlengkapan Rumah"
        price = 12000
    elif "bawang merah" in name_lower or (name_lower == "bawang" and "merah" in name_lower) or (name_lower == "bawang" and "ons" in unit_lower):
        std_name = "Bawang Merah (Ons)"
        category = "Sembako"
        price = 4000
    elif "bawang putih" in name_lower:
        std_name = "Bawang Putih (Ons)"
        category = "Sembako"
        price = 4500
    elif "beng-beng" in name_lower or "bengbeng" in name_lower:
        std_name = "Beng-Beng (Bungkus)"
        category = "Makanan Ringan"
        price = 2500
    elif "biskuit arden" in name_lower:
        std_name = "Biskuit Arden (Bungkus)"
        category = "Makanan Ringan"
        price = 3500
    elif "biskuit roma" in name_lower:
        std_name = "Biskuit Roma (Bungkus)"
        category = "Makanan Ringan"
        price = 8000
    elif "bodrex" in name_lower:
        std_name = "Bodrex (Strip)"
        category = "Obat-obatan"
        price = 3000
    elif "cheetos" in name_lower:
        std_name = "Cheetos (Bungkus)"
        category = "Makanan Ringan"
        price = 2500
    elif "chiki balls" in name_lower:
        std_name = "Chiki Balls (Bungkus)"
        category = "Makanan Ringan"
        price = 2500
    elif "chitato" in name_lower:
        std_name = "Chitato (Bungkus)"
        category = "Makanan Ringan"
        price = 5000
    elif "choki choki" in name_lower or "chokichoki" in name_lower:
        std_name = "Choki Choki (Bungkus)"
        category = "Makanan Ringan"
        price = 1500
    elif "cokelat" in name_lower or "coklat" in name_lower:
        if "rokok" not in name_lower:
            std_name = "Cokelat (Bungkus)"
            category = "Makanan Ringan"
            price = 10000
    elif "detergen rinso" in name_lower or name_lower == "rinso":
        std_name = "Detergen Rinso (Bungkus)"
        category = "Sabun & Deterjen"
        price = 5000
    elif "energen" in name_lower:
        std_name = "Energen (Bungkus)"
        category = "Minuman"
        price = 2500
    elif "garam" in name_lower:
        std_name = "Garam (Bungkus)"
        category = "Bumbu Dapur"
        price = 3000
    elif "gas lpg" in name_lower or "lpg" in name_lower:
        std_name = "Gas LPG (Tabung)"
        category = "Perlengkapan Rumah"
        price = 22000
    elif "gilet" in name_lower or "cukur" in name_lower:
        std_name = "Gilet Alat Cukur (Pcs)"
        category = "Perlengkapan Mandi"
        price = 5000
    elif "gula merah" in name_lower:
        std_name = "Gula Merah (Buah)"
        category = "Sembako"
        price = 3000
    elif "gula pasir" in name_lower:
        std_name = "Gula Pasir (Kg)"
        category = "Sembako"
        price = 18000
    elif "hansaplas" in name_lower:
        std_name = "Hansaplas (Pcs)"
        category = "Obat-obatan"
        price = 1500
    elif "indomie goreng" in name_lower:
        std_name = "Indomie Goreng (Bungkus)"
        category = "Mie Instan"
        price = 3500
    elif "indomie rebus" in name_lower:
        std_name = "Indomie Rebus (Bungkus)"
        category = "Mie Instan"
        price = 3500
    elif "kamper" in name_lower:
        std_name = "Kamper (Bungkus)"
        category = "Perlengkapan Rumah"
        price = 7000
    elif "kapas" in name_lower:
        std_name = "Kapas (Bungkus)"
        category = "Perlengkapan Mandi"
        price = 6000
    elif "kapur sirih" in name_lower:
        std_name = "Kapur Sirih (Bungkus)"
        category = "Lainnya"
        price = 2000
    elif "kecap" in name_lower:
        std_name = "Kecap (Bungkus)"
        category = "Bumbu Dapur"
        price = 2000
    elif "kertas wajit" in name_lower:
        std_name = "Kertas Wajit (Lembar)"
        category = "Alat Tulis"
        price = 1500
    elif "kerupuk" in name_lower:
        std_name = "Kerupuk (Bungkus)"
        category = "Makanan Ringan"
        price = 5000
    elif "kopi abc" in name_lower:
        std_name = "Kopi ABC (Bungkus)"
        category = "Minuman"
        price = 3000
    elif "kopi good day" in name_lower or "kopi goodday" in name_lower:
        std_name = "Kopi Good Day (Bungkus)"
        category = "Minuman"
        price = 3000
    elif "kopi kapal api" in name_lower or "kopi kapalapi" in name_lower:
        std_name = "Kopi Kapal Api (Bungkus)"
        category = "Minuman"
        price = 3000
    elif "kopi presco" in name_lower:
        std_name = "Kopi Presco (Bungkus)"
        category = "Minuman"
        price = 2000
    elif "kue" in name_lower:
        std_name = "Kue (Bungkus)"
        category = "Makanan Ringan"
        price = 5000
    elif "ladaku" in name_lower:
        std_name = "Ladaku (Bungkus)"
        category = "Bumbu Dapur"
        price = 2000
    elif "lakban" in name_lower:
        std_name = "Lakban (Roll)"
        category = "Alat Tulis"
        price = 8000
    elif "lem alteco" in name_lower:
        std_name = "Lem Alteco (Pcs)"
        category = "Alat Tulis"
        price = 7000
    elif "map" in name_lower:
        std_name = "Map (Lembar)"
        category = "Alat Tulis"
        price = 2000
    elif "masako" in name_lower:
        std_name = "Masako (Bungkus)"
        category = "Bumbu Dapur"
        price = 1000
    elif "materai" in name_lower:
        std_name = "Materai (Lembar)"
        category = "Alat Tulis"
        price = 12000
    elif "merica" in name_lower:
        std_name = "Merica (Bungkus)"
        category = "Bumbu Dapur"
        price = 1000
    elif "minyak goreng curah" in name_lower:
        std_name = "Minyak Goreng Curah (Kg)"
        category = "Sembako"
        price = 17000
    elif "molto" in name_lower:
        std_name = "Molto (Bungkus)"
        category = "Sabun & Deterjen"
        price = 1000
    elif "pampers" in name_lower:
        std_name = "Pampers (Pcs)"
        category = "Kebutuhan Bayi"
        price = 5000
    elif "pembalut" in name_lower:
        std_name = "Pembalut (Bungkus)"
        category = "Perlengkapan Mandi"
        price = 10000
    elif "pepsodent" in name_lower or "pepsoden" in name_lower:
        std_name = "Pepsodent (Tube)"
        category = "Perlengkapan Mandi"
        price = 12000
    elif "permen" in name_lower:
        std_name = "Permen (Pcs)"
        category = "Makanan Ringan"
        price = 500
    elif "pulpen" in name_lower:
        std_name = "Pulpen (Pcs)"
        category = "Alat Tulis"
        price = 3000
    elif "puring nasi" in name_lower:
        std_name = "Puring Nasi (Lembar)"
        category = "Lainnya"
        price = 5000
    elif "rautan pensil" in name_lower or "rautan" in name_lower:
        std_name = "Rautan Pensil (Pcs)"
        category = "Alat Tulis"
        price = 2000
    elif "royko" in name_lower or "royco" in name_lower:
        std_name = "Royco (Bungkus)"
        category = "Bumbu Dapur"
        price = 1000
    elif "sabun colek" in name_lower:
        std_name = "Sabun Colek (Bungkus)"
        category = "Sabun & Deterjen"
        price = 3000
    elif "sabun lifebuoy" in name_lower or "sabun mandi" in name_lower or "lifebuoy" in name_lower:
        std_name = "Sabun Mandi (Bungkus)"
        category = "Sabun & Deterjen"
        price = 4500
    elif "sabun sunlight" in name_lower or "sunlight" in name_lower:
        std_name = "Sabun Sunlight (Bungkus)"
        category = "Sabun & Deterjen"
        price = 2500
    elif "sasa" in name_lower:
        std_name = "Sasa (Bungkus)"
        category = "Bumbu Dapur"
        price = 1500
    elif "sendal" in name_lower or "sandal" in name_lower:
        std_name = "Sandal (Pasang)"
        category = "Lainnya"
        price = 15000
    elif "shampo" in name_lower or "shampoo" in name_lower:
        std_name = "Shampo (Bungkus)"
        category = "Sabun & Deterjen"
        price = 1000
    elif "silet" in name_lower:
        std_name = "Silet (Pcs)"
        category = "Perlengkapan Mandi"
        price = 2000
    elif "sosis" in name_lower:
        std_name = "Sosis (Bungkus)"
        category = "Makanan Ringan"
        price = 2000
    elif "super pel" in name_lower or "superpel" in name_lower:
        std_name = "Super Pel (Bungkus)"
        category = "Sabun & Deterjen"
        price = 1500
    elif "susu kental manis" in name_lower or "susu kental" in name_lower:
        std_name = "Susu Kental Manis (Kaleng)"
        category = "Minuman"
        price = 12000
    elif "teh gelas" in name_lower:
        std_name = "Teh Gelas (Cup)"
        category = "Minuman"
        price = 1500
    elif "teh pucuk" in name_lower:
        std_name = "Teh Pucuk (Botol)"
        category = "Minuman"
        price = 4000
    elif "telur" in name_lower or "telor" in name_lower:
        if "butir" in unit_lower:
            std_name = "Telur (Butir)"
            category = "Sembako"
            price = 2000
        else:
            std_name = "Telur (Kg)"
            category = "Sembako"
            price = 26000
    elif "tepung serbaguna" in name_lower:
        std_name = "Tepung Serbaguna (Bungkus)"
        category = "Sembako"
        price = 6000
    elif "tepung tapioka" in name_lower:
        std_name = "Tepung Tapioka (Kg)"
        category = "Sembako"
        price = 12000
    elif "tepung terigu" in name_lower or "tepung tepung terigu" in name_lower:
        if "kg" in unit_lower or unit_lower == "kg":
            std_name = "Tepung Terigu (Kg)"
            category = "Sembako"
            price = 12000
        else:
            std_name = "Tepung Terigu (Bungkus)"
            category = "Sembako"
            price = 12000
    elif "terasi" in name_lower:
        std_name = "Terasi (Bungkus)"
        category = "Bumbu Dapur"
        price = 1000
    elif "tisu" in name_lower:
        std_name = "Tisu (Pack)"
        category = "Perlengkapan Rumah"
        price = 6000
    elif "tolak angin" in name_lower:
        std_name = "Tolak Angin (Bungkus)"
        category = "Obat-obatan"
        price = 4000
    elif "wafer super star" in name_lower or "super star" in name_lower:
        std_name = "Wafer Super Star (Bungkus)"
        category = "Makanan Ringan"
        price = 2000
        
    return std_name, category, price

def seed_data():
    print("Memulai seeding basis data MySQL Toko Setia Ciawi...")
    
    # Baca data.csv terlebih dahulu untuk validasi keberadaannya
    csv_path = "data.csv"
    if not os.path.exists(csv_path):
        print(f"Error: file {csv_path} tidak ditemukan di root folder!")
        return
        
    df = pd.read_csv(csv_path)
    print(f"- Berhasil memuat {len(df)} baris data transaksi dari {csv_path}")
    
    # 1. Bersihkan database lama (drop tables) & inisialisasi skema baru
    conn = get_connection(with_db=False)
    cursor = conn.cursor()
    
    # Dapatkan DB_NAME dari database.py
    from backend.database import DB_NAME
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    conn.commit()
    conn.close()
    
    conn = get_connection(with_db=True)
    cursor = conn.cursor()
    
    print("- Membersihkan tabel database lama jika ada...")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    cursor.execute("DROP TABLE IF EXISTS prediksi")
    cursor.execute("DROP TABLE IF EXISTS detail_transaksi")
    cursor.execute("DROP TABLE IF EXISTS transaksi")
    cursor.execute("DROP TABLE IF EXISTS barang")
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    conn.commit()
    
    # Re-create tables
    init_db()
    print("- Inisialisasi skema database baru berhasil.")
    
    # 2. Seed Admin User
    admin_pass = hash_password("admin")
    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", ("admin", admin_pass))
    conn.commit()
    print("- Berhasil menambahkan user default: admin / admin")
    
    # 3. Standardisasi master barang dari data.csv
    df["Nama_barang_clean"] = df["Nama_barang"].str.strip()
    df["Satuan_clean"] = df["Satuan"].str.strip()
    
    std_products = []
    for idx, row in df.iterrows():
        std_name, category, price = get_standard_product(row["Nama_barang_clean"], row["Satuan_clean"])
        std_products.append((std_name, category, price))
        
    df["Nama_barang_std"] = [p[0] for p in std_products]
    df["Kategori"] = [p[1] for p in std_products]
    df["Harga_jual"] = [p[2] for p in std_products]
    
    # Get unique products
    unique_prods = df.groupby(["Nama_barang_std", "Kategori", "Harga_jual"]).size().reset_index()
    
    barang_insert_data = []
    for i, row in unique_prods.iterrows():
        kode_barang = f"BRG-{i+1:03d}"
        nama_barang = row["Nama_barang_std"]
        kategori = row["Kategori"]
        harga_jual = int(row["Harga_jual"])
        stok = 100.0 # Set default initial stock of 100.0 (float) for all products
        barang_insert_data.append((kode_barang, nama_barang, kategori, harga_jual, stok))
        
    cursor.executemany(
        "INSERT INTO barang (kode_barang, nama_barang, kategori, harga_jual, stok) VALUES (%s, %s, %s, %s, %s)",
        barang_insert_data
    )
    conn.commit()
    print(f"- Berhasil menambahkan {len(barang_insert_data)} jenis master data produk ke tabel 'barang'")
    
    # Ambil kembali mapping ID produk
    cursor.execute("SELECT id, nama_barang, harga_jual FROM barang")
    db_products = cursor.fetchall()
    prod_map = {row["nama_barang"]: {"id": row["id"], "harga": row["harga_jual"]} for row in db_products}
    
    # 4. Memproses dan menyimpan transaksi & detail transaksi
    transaksi_groups = df.groupby("ID_Transaksi")
    
    transaksi_data = []
    detail_data = []
    
    print("- Mengelompokkan dan menyiapkan data transaksi...")
    for trx_id, group in transaksi_groups:
        first_row = group.iloc[0]
        # Bersihkan tanggal dari spasi
        tanggal_clean = str(first_row["Tanggal"]).replace(" ", "")
        tanggal_parsed = pd.to_datetime(tanggal_clean, format="%Y-%m-%d")
        
        # Cek apakah transaksi mengandung makanan ringan
        has_snacks = any(row["Kategori"] == "Makanan Ringan" for _, row in group.iterrows())
        # Cek apakah hari transaksi adalah Senin (0), Selasa (1), atau Rabu (2)
        is_mon_to_wed = tanggal_parsed.weekday() in [0, 1, 2]
        
        # Jika Senin-Rabu dan beli makanan ringan, jam diset ke 9 - 10 pagi (hour = 9)
        if has_snacks and is_mon_to_wed:
            hour = 9
        else:
            # Jika tidak, gunakan jam acak 8-20 (kecuali jam 9 agar pola terlihat kontras)
            hour = random.choice([8, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20])
            
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        tanggal_dt = tanggal_parsed.replace(hour=hour, minute=minute, second=second)
        tanggal_str = tanggal_dt.strftime("%Y-%m-%d %H:%M:%S")
        
        total_bayar = 0
        temp_details = []
        
        for idx, row in group.iterrows():
            nama_std = row["Nama_barang_std"]
            jumlah = float(str(row["Jumlah"]).replace(",", "."))
            p_info = prod_map[nama_std]
            p_id = p_info["id"]
            harga = p_info["harga"]
            
            subtotal = int(round(jumlah * harga))
            total_bayar += subtotal
            temp_details.append((p_id, jumlah, subtotal))
            
        transaksi_data.append((trx_id, tanggal_str, total_bayar))
        
        for item in temp_details:
            detail_data.append((trx_id, item[0], item[1], item[2]))
            
    # Batch Insert Transaksi
    cursor.executemany(
        "INSERT INTO transaksi (nomor_nota, tanggal, total_bayar) VALUES (%s, %s, %s)",
        transaksi_data
    )
    conn.commit()
    print(f"  * Berhasil menyimpan {len(transaksi_data)} nota transaksi.")
    
    # Ambil mapping nomor_nota ke ID transaksi dari DB
    cursor.execute("SELECT id, nomor_nota FROM transaksi")
    db_trx = cursor.fetchall()
    trx_map = {row["nomor_nota"]: row["id"] for row in db_trx}
    
    # Ganti nomor_nota di detail dengan transaksi_id
    final_detail_data = []
    for detail in detail_data:
        nota = detail[0]
        trx_id = trx_map[nota]
        final_detail_data.append((trx_id, detail[1], detail[2], detail[3]))
        
    # Batch Insert Detail Transaksi
    cursor.executemany(
        "INSERT INTO detail_transaksi (transaksi_id, barang_id, jumlah, subtotal) VALUES (%s, %s, %s, %s)",
        final_detail_data
    )
    conn.commit()
    print(f"  * Berhasil menyimpan {len(final_detail_data)} item transaksi detail.")
    
    conn.close()
    print("- Proses Seeding selesai dengan sukses!")
    
    # 5. Jalankan training model pertama kali agar langsung siap dipakai
    print("- Melatih model Decision Tree menggunakan data Toko Setia Ciawi...")
    train_res = train_decision_tree()
    print(f"  * Status Training: {train_res}")

if __name__ == "__main__":
    seed_data()
