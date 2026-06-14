import pymysql
import os

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "warung_db")
DB_PORT = int(os.getenv("DB_PORT", "3306"))

def get_connection(with_db=True):
    if with_db:
        return pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=DB_PORT,
            cursorclass=pymysql.cursors.DictCursor
        )
    else:
        return pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
            cursorclass=pymysql.cursors.DictCursor
        )

def init_db():
    # 1. Buat database jika belum ada
    conn = get_connection(with_db=False)
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    conn.commit()
    conn.close()

    # 2. Hubungkan ke database dan buat tabel-tabel
    conn = get_connection(with_db=True)
    cursor = conn.cursor()
    
    # 1. users
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
    
    # 2. barang
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS barang (
        id INT AUTO_INCREMENT PRIMARY KEY,
        kode_barang VARCHAR(20) UNIQUE NOT NULL,
        nama_barang VARCHAR(100) NOT NULL,
        kategori VARCHAR(50) NOT NULL,
        harga_jual INT NOT NULL,
        stok FLOAT NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
    
    # 3. transaksi
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transaksi (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nomor_nota VARCHAR(50) UNIQUE NOT NULL,
        tanggal DATETIME NOT NULL,
        total_bayar INT NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
    
    # 4. detail_transaksi
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS detail_transaksi (
        id INT AUTO_INCREMENT PRIMARY KEY,
        transaksi_id INT NOT NULL,
        barang_id INT NOT NULL,
        jumlah FLOAT NOT NULL,
        subtotal INT NOT NULL,
        FOREIGN KEY (transaksi_id) REFERENCES transaksi (id) ON DELETE CASCADE,
        FOREIGN KEY (barang_id) REFERENCES barang (id) ON DELETE RESTRICT
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
    
    # 5. prediksi
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS prediksi (
        id INT AUTO_INCREMENT PRIMARY KEY,
        barang_id INT NOT NULL,
        tanggal_prediksi DATETIME NOT NULL,
        periode_target VARCHAR(30) NOT NULL,
        jumlah_prediksi FLOAT NOT NULL,
        rekomendasi_stok FLOAT NOT NULL,
        FOREIGN KEY (barang_id) REFERENCES barang (id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print(f"Database MySQL '{DB_NAME}' berhasil diinisialisasi.")
