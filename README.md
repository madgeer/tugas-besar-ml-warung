# Sistem Prediksi Stok & Rekomendasi Penjualan - Toko Setia Ciawi

Aplikasi cerdas berbasis web untuk membantu manajemen stok inventaris dan strategi penjualan pada **Toko Setia Ciawi**. Sistem ini menggunakan algoritma **Decision Tree Regressor** untuk memprediksi jumlah stok barang yang perlu dibeli di periode berikutnya (ML RESTOCK) dan algoritma **Apriori** untuk memberikan rekomendasi produk pelengkap (CROSS-SELLING) secara real-time pada kasir.


## Arsitektur Teknologi
Sistem didevelop dengan arsitektur modern decoupled:
1. **Frontend (Streamlit)**: Antarmuka kasir dan dasbor pemilik toko yang interaktif, responsif, dan kaya visual (premium UI styling).
2. **Backend (FastAPI)**: REST API berkinerja tinggi sebagai jembatan logika transaksi, komputasi rekomendasi restock, inferensi ML, serta pembentukan aturan asosiasi Apriori.
3. **Database (MySQL)**: Media penyimpanan persisten untuk master barang, transaksi penjualan harian, histori detail item transaksi, cache prediksi, dan user account.
4. **Machine Learning (Scikit-Learn & Joblib)**: Engine pemodelan Decision Tree Regressor untuk menganalisis data musiman (weekly/monthly) serta fluktuasi penjualan produk.


## Struktur Proyek
```text
tugas-besar/
├── backend/
│   ├── app.py                # FastAPI Server & Endpoints
│   ├── database.py           # Inisialisasi skema & koneksi MySQL
│   ├── ml_engine.py          # Preprocessing data & Decision Tree Training/Prediction
│   ├── apriori_engine.py     # Penambangan Aturan Asosiasi (Zero-Dependency)
│   └── model_decision_tree.joblib  # Hasil dump model ML terlatih
├── docs/
│   └── rancangan.md          # Dokumen Perancangan Sistem Lengkap
├── frontend/
│   └── app.py                # Aplikasi Streamlit Dashboard & Kasir
├── data.csv                  # Dataset asli historis transaksi Toko Setia Ciawi
├── seed_db.py                # Script inisialisasi schema, cleansing data, & seeding
├── requirements.txt          # Daftar pustaka dependensi Python
└── README.md                 # Petunjuk instalasi & penggunaan ini
```


## Skema Basis Data (MySQL)
Sistem ini menggunakan tipe data **`FLOAT`** pada kuantitas penjualan (`jumlah`) dan persediaan (`stok`) untuk menampung unit pecahan/desimal dari barang sembako (seperti telur `0.5 Kg` atau gula `0.25 Kg`) tanpa mengalami pemotongan pembulatan (*truncation*).

Tabel yang digunakan:
* **`users`**: Data otentikasi pemilik (default: `admin` / `admin`).
* **`barang`**: Master data produk (kode, nama standar, kategori, harga jual, stok).
* **`transaksi`**: Nomor nota unik, tanggal transaksi, dan total pembayaran.
* **`detail_transaksi`**: Detail item per nota (barang ID, jumlah kuantitas, subtotal).
* **`prediksi`**: Caching histori hasil prediksi penjualan produk dan rekomendasi restock bulanan.


## Fitur Utama & Pola Bisnis Terintegrasi
* **Dasbor Analytics & Alert Stok**: Menampilkan omzet penjualan total, variasi produk, dan peringatan instan untuk produk yang stok fisiknya menipis (di bawah 10 unit).
* **Pencatatan Transaksi & Auto-Potong Stok**: Modul kasir terintegrasi yang otomatis memotong stok barang di database setelah transaksi dikonfirmasi.
* **Rekomendasi Apriori Live (Cross-Selling)**: Memberikan rekomendasi produk tambahan secara otomatis di kasir saat produk tertentu dipilih.
  - *Aturan Bisnis Terdeteksi*: Jika pelanggan membeli **Masako**, sistem merekomendasikan **Minyak Goreng Curah** dan **Tepung Tapioka** dengan tingkat keyakinan (*confidence*) hingga **88%** (pola belanja bahan gorengan).
* **Pola Waktu Khusus Anak PAUD**:
  - *Aturan Seeding*: Histori transaksi makanan ringan (seperti ciki, permen, biskuit) khusus pada hari **Senin, Selasa, dan Rabu** otomatis diset pada pukul **09:00 - 10:00 pagi** (mengikuti pola waktu anak PAUD pulang sekolah agar model ML mendeteksi lonjakan musiman ini secara tajam).
* **Modul Prediksi ML (Decision Tree)**: Memprediksi penjualan bulanan produk dan menghitung jumlah barang yang harus dipesan/dibeli lagi berdasarkan sisa stok gudang dan *safety stock*.


## Langkah Instalasi & Menjalankan Aplikasi

### 1. Prasyarat (Prerequisites)
* Python versi 3.10 ke atas terinstall di komputer.
* MySQL Server terinstall dan sedang berjalan (XAMPP/Laragon/Docker).

### 2. Kloning & Pembuatan Virtual Environment
Buka terminal/PowerShell di folder proyek Anda:
```bash
# Buat virtual environment
python -m venv venv

# Aktifkan virtual environment (Windows)
.\venv\Scripts\activate
```

### 3. Instalasi Dependensi
Instal seluruh pustaka python yang dibutuhkan:
```bash
pip install -r requirements.txt
```

### 4. Setup MySQL Database
Pastikan MySQL Anda sudah aktif pada port default `3306`. Secara bawaan, sistem akan membuat database bernama `warung_db` dengan user `root` dan tanpa password. Jika Anda ingin mengubah kredensial database, silakan ubah berkas `backend/database.py` atau gunakan Environment Variables (`DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_PORT`).

### 5. Cleansing, Seeding & Training Awal
Jalankan script `seed_db.py` untuk mengosongkan database lama, memproses data desimal dari `data.csv`, serta melatih model ML pertama kali:
```bash
python seed_db.py
```
*Output sukses akan menunjukkan pemetaan **84 produk** dan status model ML berhasil dilatih.*

### 6. Menjalankan Server Backend (FastAPI)
Jalankan server backend FastAPI pada port `8000`:
```bash
uvicorn backend.app:app --reload
```

### 7. Menjalankan Dashboard Frontend (Streamlit)
Buka terminal baru, aktifkan venv, lalu jalankan aplikasi antarmuka Streamlit:
```bash
streamlit run frontend/app.py
```

Setelah itu, aplikasi Streamlit otomatis terbuka di browser Anda (biasanya di `http://localhost:8501`). Silakan masuk menggunakan akun default:
* **Username**: `admin`
* **Password**: `admin`

