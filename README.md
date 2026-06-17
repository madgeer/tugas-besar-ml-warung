# 🏪 Sistem Pendukung Keputusan Toko Setia Ciawi
> **Tugas Besar Machine Learning - Semester 4**

Repositori ini berisi implementasi sistem kecerdasan buatan untuk membantu pemilik kelontong **Toko Setia Ciawi** dalam mengoptimalkan manajemen stok barang dan menyusun strategi penjualan kasir.

---

## 📌 Anggota Tim & Kontribusi
* **Peran Tim:** Pemodelan Machine Learning, Pembersihan Data, & Pengembangan Antarmuka Web (Streamlit).

---

## 🚀 Fitur Utama Aplikasi
1. **Dashboard Dataset:** Analisis deskriptif interaktif dari data transaksi riil (`data.csv`).
2. **Prediksi Penjualan & Rekomendasi Restock:** Menggunakan model **Decision Tree Regressor** untuk memprediksi penjualan mingguan produk dan memberikan rekomendasi jumlah barang yang harus di-restock berdasarkan batas aman (*Safety Stock*).
3. **Strategi Cross-Selling Kasir:** Menggunakan algoritma **Apriori** untuk menemukan aturan asosiasi barang (*Market Basket Analysis*) guna merekomendasikan produk pendamping saat transaksi di kasir.

---

## 🛠️ Arsitektur Machine Learning

Sistem ini menggabungkan dua metode pembelajaran mesin:

### 1. Supervised Learning (Prediksi Kebutuhan Stok)
* **Algoritma:** `DecisionTreeRegressor` (max_depth=3, min_samples_split=20).
* **Fitur Input:**
  * `barang_id`: Representasi numerik unik produk.
  * `bulan`: Bulan target proyeksi.
  * `minggu_ke`: Minggu target dalam sebulan (1 s/d 5).
  * `penjualan_bulan_lalu` (Lag Feature): Total volume penjualan produk pada bulan sebelumnya.
* **Pipeline Pemrosesan:** `StandardScaler` ➔ `DecisionTreeRegressor`.
* **Metode Evaluasi:** 5-Fold Cross Validation.
* **Skor MAE (Mean Absolute Error):** ±3.11 unit laku per minggu.

### 2. Unsupervised Learning (Analisis Keranjang Belanja)
* **Algoritma:** `Apriori` & `Association Rules` (mlxtend).
* **Konfigurasi Aturan:**
  * Minimum Support: 2% (`min_support = 0.02`)
  * Minimum Confidence: 30% (`min_confidence = 0.3`)

---

## 📂 Struktur Direktori Proyek

```text
tugas-besar/
│
├── data.csv                   # Dataset historis transaksi kasir (sudah bersih)
├── model.joblib               # Pipeline model Decision Tree hasil training (.joblib)
├── requirements.txt           # Daftar dependensi library Python
│
├── notebook.ipynb             # Jupyter Notebook laporan pemodelan & analisis (utama)
├── tugas_besar.py             # Script Python hasil ekstraksi notebook (sekat sel interaktif)
├── app_deployment.py          # Dashboard UI interaktif berbasis Streamlit
│
└── .venv/                     # Virtual environment Python (lokal)
```

---

## 🧹 Pembersihan Kualitas Data (*Data Cleaning*)
Sebelum model dilatih, dataset [data.csv](data.csv) telah melalui tahap pembersihan data otomatis:
1. **Desimal Koma ke Titik:** Mengubah pemisah pecahan desimal pada kolom `Jumlah` (contoh: `3,25` menjadi `3.25`) agar terbaca sebagai angka numerik oleh model.
2. **Merge Typo Label Produk:** Menyatukan label produk yang identik tetapi memiliki kesalahan ketik (contoh: `Rokok Jarum Cokelat` & `Rokok Jarim Coklat` disatukan menjadi `Rokok Jarum Coklat`).

---

## 💻 Cara Menginstal & Menjalankan Aplikasi

### 1. Prasyarat (Prerequisites)
Pastikan Python 3.8+ telah terinstal pada komputer Anda.

### 2. Instalasi Dependensi
Buka terminal/PowerShell di folder proyek dan jalankan perintah berikut untuk menginstal seluruh kebutuhan library:
```bash
pip install -r requirements.txt
```

### 3. Menjalankan Model Training (Opsional)
Jika ingin melatih ulang model Decision Tree dan memperbarui berkas `.joblib`:
```bash
python tugas_besar.py
```

### 4. Menjalankan Dashboard Streamlit
Untuk membuka antarmuka web interaktif di browser lokal Anda:
```bash
python -m streamlit run app_deployment.py
```
Aplikasi secara otomatis akan terbuka di browser Anda pada alamat: **`http://localhost:8501`**
