import os
import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeRegressor
from sklearn.model_selection import KFold
from sklearn.metrics import mean_absolute_error
import joblib
from backend.database import get_connection

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model_decision_tree.joblib")

def load_data_from_db():
    """
    Mengambil data transaksi historis dari SQLite dan menggabungkannya
    menjadi dataset untuk training.
    """
    conn = get_connection()
    cursor = conn.cursor()
    query = """
    SELECT 
        t.tanggal, 
        d.barang_id, 
        d.jumlah, 
        b.harga_jual, 
        b.nama_barang
    FROM detail_transaksi d
    JOIN transaksi t ON d.transaksi_id = t.id
    JOIN barang b ON d.barang_id = b.id
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["tanggal", "barang_id", "jumlah", "harga_jual", "nama_barang"])
    conn.close()
    return df

def preprocess_and_feature_engineering(df):
    """
    Melakukan data cleaning dan feature engineering:
    - Ekstraksi Tahun, Bulan, dan Hari dari Tanggal.
    - Hitung Minggu ke-X (1-5).
    - Agregasi kuantitas penjualan per (tahun, bulan, minggu_ke, barang_id).
    - Tambahkan Lag Feature: penjualan_bulan_lalu (penjualan produk tersebut pada bulan sebelumnya).
    """
    if df.empty:
        return pd.DataFrame(), []

    # 1. Konversi tanggal
    df['tanggal'] = pd.to_datetime(df['tanggal'])
    df['tahun'] = df['tanggal'].dt.year
    df['bulan'] = df['tanggal'].dt.month
    df['hari'] = df['tanggal'].dt.day
    
    # 2. Hitung minggu ke-X dalam sebulan (1 s/d 5)
    df['minggu_ke'] = ((df['hari'] - 1) // 7) + 1
    df['minggu_ke'] = df['minggu_ke'].clip(1, 5)

    # 3. Agregasi penjualan mingguan per barang
    # Target: total jumlah barang terjual pada minggu tersebut
    aggregated = df.groupby(['tahun', 'bulan', 'minggu_ke', 'barang_id', 'harga_jual']).agg(
        jumlah_terjual=('jumlah', 'sum')
    ).reset_index()

    # 4. Tambahkan Lag Feature: penjualan_bulan_lalu
    # Kita hitung total penjualan per barang pada masing-masing bulan (tahun, bulan, barang_id)
    monthly_sales = df.groupby(['tahun', 'bulan', 'barang_id'])['jumlah'].sum().reset_index()
    monthly_sales.rename(columns={'jumlah': 'penjualan_bulan_lalu'}, inplace=True)

    # Untuk mempermudah join, kita buat kolom kunci bulan lalu
    # Jika bulan berjalan adalah M, maka bulan lalu adalah M-1.
    aggregated['tahun_lalu'] = aggregated['tahun']
    aggregated['bulan_lalu'] = aggregated['bulan'] - 1
    
    # Handle pergantian tahun (jika bulan = 1, bulan lalu adalah 12 tahun lalu)
    jan_mask = aggregated['bulan'] == 1
    aggregated.loc[jan_mask, 'tahun_lalu'] = aggregated['tahun'] - 1
    aggregated.loc[jan_mask, 'bulan_lalu'] = 12

    # Lakukan merge untuk mendapatkan fitur penjualan_bulan_lalu
    aggregated = pd.merge(
        aggregated,
        monthly_sales,
        left_on=['tahun_lalu', 'bulan_lalu', 'barang_id'],
        right_on=['tahun', 'bulan', 'barang_id'],
        how='left',
        suffixes=('', '_temp')
    )

    # Drop kolom temporer hasil merge
    aggregated.drop(columns=['tahun_temp', 'bulan_temp', 'tahun_lalu', 'bulan_lalu'], errors='ignore', inplace=True)
    
    # Isi nilai NaN pada penjualan_bulan_lalu dengan 0 (artinya bulan lalu tidak ada penjualan)
    aggregated['penjualan_bulan_lalu'] = aggregated['penjualan_bulan_lalu'].fillna(0)

    # Urutkan data berdasarkan waktu agar logis
    aggregated = aggregated.sort_values(by=['tahun', 'bulan', 'minggu_ke', 'barang_id']).reset_index(drop=True)

    features = ['barang_id', 'harga_jual', 'bulan', 'minggu_ke', 'penjualan_bulan_lalu']
    return aggregated, features

def train_decision_tree():
    """
    Melatih model Decision Tree Regressor jika data cukup.
    Menghitung metrik performa K-Fold CV dan MAE.
    Menyimpan model ke disk menggunakan Joblib.
    """
    df = load_data_from_db()
    
    # Kita butuh minimal data tertentu agar bisa ditraining
    # Katakanlah minimal ada 15 transaksi tercatat di database secara total
    if len(df) < 15:
        return {
            "success": False,
            "message": f"Data historis tidak cukup untuk training. Butuh minimal 15 baris transaksi, saat ini baru ada {len(df)}."
        }

    dataset, features = preprocess_and_feature_engineering(df)
    
    if dataset.empty or len(dataset) < 5:
        return {
            "success": False,
            "message": "Data historis setelah agregasi terlalu sedikit untuk melatih model."
        }

    X = dataset[features].values
    y = dataset['jumlah_terjual'].values

    # 1. Evaluasi model menggunakan K-Fold Cross Validation
    n_splits = min(5, len(dataset))
    if n_splits >= 2:
        kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
        mae_scores = []
        for train_idx, test_idx in kf.split(X):
            X_tr, X_te = X[train_idx], X[test_idx]
            y_tr, y_te = y[train_idx], y[test_idx]
            
            # Batasi kedalaman pohon (max_depth=4) untuk mencegah overfitting
            fold_model = DecisionTreeRegressor(max_depth=4, random_state=42)
            fold_model.fit(X_tr, y_tr)
            preds = fold_model.predict(X_te)
            mae_scores.append(mean_absolute_error(y_te, preds))
        
        mean_mae = float(np.mean(mae_scores))
    else:
        mean_mae = 0.0

    # 2. Train model akhir pada seluruh dataset
    final_model = DecisionTreeRegressor(max_depth=4, random_state=42)
    final_model.fit(X, y)

    # Simpan model beserta daftar fitur
    model_data = {
        "model": final_model,
        "features": features,
        "mean_mae": mean_mae,
        "data_count": len(dataset)
    }
    
    joblib.dump(model_data, MODEL_PATH)
    
    return {
        "success": True,
        "mean_mae": mean_mae,
        "data_count": len(dataset),
        "message": "Model Decision Tree berhasil dilatih dan disimpan."
    }

def get_trained_model():
    """
    Memuat model Decision Tree dari disk. Jika belum ada, lakukan training.
    """
    if not os.path.exists(MODEL_PATH):
        # Lakukan training jika berkas model belum dibuat
        res = train_decision_tree()
        if not res["success"]:
            return None, res["message"]
            
    try:
        model_data = joblib.load(MODEL_PATH)
        return model_data, None
    except Exception as e:
        return None, str(e)

def predict_sales_for_period(barang_id, target_year, target_month):
    """
    Memprediksi penjualan barang pada tahun & bulan target.
    Metode: memprediksi penjualan untuk minggu 1 s/d 5 pada bulan target,
    kemudian menjumlahkannya untuk mendapatkan total bulanan.
    """
    # 1. Ambil data model
    model_data, err = get_trained_model()
    if err:
        return {"success": False, "message": err}
        
    model = model_data["model"]
    
    # 2. Ambil informasi harga jual barang saat ini dan sisa stok
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT harga_jual, stok, nama_barang FROM barang WHERE id = %s", (barang_id,))
    barang = cursor.fetchone()
    
    if not barang:
        conn.close()
        return {"success": False, "message": f"Barang dengan ID {barang_id} tidak ditemukan."}
        
    harga_jual = barang["harga_jual"]
    sisa_stok = barang["stok"]
    nama_barang = barang["nama_barang"]

    # 3. Hitung Lag Feature: penjualan_bulan_lalu (penjualan pada bulan sebelum target)
    # Bulan sebelum target:
    lag_year = target_year
    lag_month = target_month - 1
    if lag_month == 0:
        lag_month = 12
        lag_year = target_year - 1
        
    # Cari total penjualan produk pada bulan lag tersebut dari transaksi
    query_lag = """
    SELECT SUM(d.jumlah) as total_terjual
    FROM detail_transaksi d
    JOIN transaksi t ON d.transaksi_id = t.id
    WHERE d.barang_id = %s 
      AND YEAR(t.tanggal) = %s 
      AND MONTH(t.tanggal) = %s
    """
    cursor.execute(query_lag, (barang_id, lag_year, lag_month))
    res_lag = cursor.fetchone()
    penjualan_bulan_lalu = res_lag["total_terjual"] if res_lag["total_terjual"] else 0
    conn.close()

    # 4. Lakukan prediksi mingguan (minggu 1 s/d 5)
    weekly_predictions = []
    for week in range(1, 6):
        # Format input: ['barang_id', 'harga_jual', 'bulan', 'minggu_ke', 'penjualan_bulan_lalu']
        input_features = np.array([[
            barang_id,
            harga_jual,
            target_month,
            week,
            penjualan_bulan_lalu
        ]])
        
        pred = model.predict(input_features)[0]
        # Penjualan tidak boleh negatif, jadi kita clip di 0
        weekly_predictions.append(max(0.0, round(float(pred), 2)))
        
    total_prediksi = round(sum(weekly_predictions), 2)
    
    return {
        "success": True,
        "barang_id": barang_id,
        "nama_barang": nama_barang,
        "periode_target": f"{target_year}-{target_month:02d}",
        "weekly_predictions": weekly_predictions,
        "jumlah_prediksi": total_prediksi,
        "sisa_stok": sisa_stok,
        "mean_mae": model_data["mean_mae"]
    }
