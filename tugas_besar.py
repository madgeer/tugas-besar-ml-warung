# %%
# === CELL 1: CODE ===
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.tree import DecisionTreeRegressor, plot_tree
from sklearn.model_selection import KFold
from sklearn.metrics import mean_absolute_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import joblib
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, association_rules

# %% [markdown]
# === CELL 2: MARKDOWN ===
# ## 1. Load Data
# Membaca file dataset `data.csv` yang berisi riwayat penjualan toko.

# %%
# === CELL 3: CODE ===
# Membaca dataset
df = pd.read_csv('data.csv')

# === PROSES DATA CLEANING ===
# 1. Bersihkan pemisah desimal koma menjadi titik pada kolom Jumlah
df['Jumlah'] = df['Jumlah'].astype(str).str.replace(',', '.').astype(float)

# 2. Standarisasi nama produk yang typo / duplikat
mapping_typo = {
    'Rokok Jarum Cokelat': 'Rokok Jarum Coklat',
    'Rokok Jarim Coklat': 'Rokok Jarum Coklat',
    'Jarum Super': 'Rokok Jarum Super',
    'Rokok Super': 'Rokok Jarum Super',
    'Rokok GGM': 'Rokok Garam Merah',
    'Garam': 'Rokok Garam Merah',
    'Gula Pasir Pasir': 'Gula Pasir',
}
df['Nama_barang'] = df['Nama_barang'].replace(mapping_typo)
df.loc[df['Satuan'] == 'Batang', 'Nama_barang'] = df.loc[df['Satuan'] == 'Batang', 'Nama_barang'] + ' (batang)'

print(f"Dataset berhasil dimuat dan dibersihkan. Total data: {df.shape[0]} baris, {df['Nama_barang'].nunique()} jenis barang.")
df.head()

# %% [markdown]
# === CELL 4: MARKDOWN ===
# ## 2. Preprocessing & Feature Engineering (Model Regresi)
# Mengubah data transaksi mentah menjadi fitur input untuk model prediksi stok.

# %%
# === CELL 5: CODE ===
df_prep = df.copy()

df_prep['Jumlah'] = pd.to_numeric(df_prep['Jumlah'], errors='coerce').fillna(0.0) # Mengonversi kolom 'Jumlah' ke tipe numerik, menggantikan nilai yang tidak dapat dikonversi dengan 0.0

# Ekstraksi fitur tanggal
df_prep['tanggal'] = pd.to_datetime(df_prep['Tanggal'])
df_prep['tahun'] = df_prep['tanggal'].dt.year
df_prep['bulan'] = df_prep['tanggal'].dt.month
df_prep['hari'] = df_prep['tanggal'].dt.day

# Menentukan minggu ke berapa dalam bulan
df_prep['minggu_ke'] = ((df_prep['hari'] - 1) // 7) + 1
df_prep['minggu_ke'] = df_prep['minggu_ke'].clip(1, 5)

# Encoding nama barang menjadi ID numerik
unique_items = df_prep['Nama_barang'].unique()
item_to_id = {name: idx + 1 for idx, name in enumerate(unique_items)}
df_prep['barang_id'] = df_prep['Nama_barang'].map(item_to_id)

# Menambahkan kolom harga jual dengan nilai tetap (misalnya 5000)

dataset = df_prep.groupby(['tahun', 'bulan', 'minggu_ke', 'barang_id']).agg(
    jumlah_terjual=('Jumlah', 'sum')
).reset_index()

monthly_sales = df_prep.groupby(['tahun', 'bulan', 'barang_id'])['Jumlah'].sum().reset_index()
monthly_sales.rename(columns={'Jumlah': 'penjualan_bulan_lalu'}, inplace=True)

dataset['tahun_lalu'] = dataset['tahun']
dataset['bulan_lalu'] = dataset['bulan'] - 1

jan_mask = dataset['bulan'] == 1
dataset.loc[jan_mask, 'tahun_lalu'] = dataset['tahun'] - 1
dataset.loc[jan_mask, 'bulan_lalu'] = 12

dataset = pd.merge(
    dataset,
    monthly_sales,
    left_on=['tahun_lalu', 'bulan_lalu', 'barang_id'],
    right_on=['tahun', 'bulan', 'barang_id'],
    how='left',
    suffixes=('', '_temp')
)

dataset.drop(columns=['tahun_temp', 'bulan_temp', 'tahun_lalu', 'bulan_lalu'], errors='ignore', inplace=True)
dataset['penjualan_bulan_lalu'] = dataset['penjualan_bulan_lalu'].fillna(0)
dataset = dataset.sort_values(by=['tahun', 'bulan', 'minggu_ke', 'barang_id']).reset_index(drop=True)

features = ['barang_id', 'bulan', 'minggu_ke', 'penjualan_bulan_lalu']

print(f"Data berhasil dipreproses. Jumlah dataset teragregasi: {dataset.shape[0]} baris.")
print(f"Fitur input yang digunakan: {features}")
dataset.head()

# %% [markdown]
# === CELL 6: MARKDOWN ===
# ## 3. Pembangunan Pipeline & Evaluasi Model
# Membangun pipeline model ML dan mengevaluasi performa menggunakan 5-Fold Cross Validation.

# %%
# === CELL 7: CODE ===
X = dataset[features].values
y = dataset['jumlah_terjual'].values

kf = KFold(n_splits=5, shuffle=True, random_state=42)
mae_scores = []

for fold, (train_idx, test_idx) in enumerate(kf.split(X), 1):
    X_tr, X_te = X[train_idx], X[test_idx]
    y_tr, y_te = y[train_idx], y[test_idx]
    
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('regressor', DecisionTreeRegressor(max_depth=3, min_samples_split=20, random_state=42))
    ])
    
    pipeline.fit(X_tr, y_tr)
    
    preds = pipeline.predict(X_te)
    mae = mean_absolute_error(y_te, preds)
    mae_scores.append(mae)
    print(f"Fold {fold} - MAE: {mae:.4f} unit laku")

mean_mae = np.mean(mae_scores)
print(f"\nRata-rata MAE Keseluruhan: {mean_mae:.4f} unit laku")

# %% [markdown]
# === CELL 8: MARKDOWN ===
# ## 4. Final Model Training & Visualisasi
# Melatih pipeline model pada seluruh data yang tersedia dan melakukan visualisasi pohon keputusan (*decision tree*).

# %%
# === CELL 9: CODE ===
final_pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('regressor', DecisionTreeRegressor(max_depth=3, min_samples_split=20, random_state=42))
])
final_pipeline.fit(X, y)

print("Model Pipeline akhir berhasil dilatih pada seluruh data.")

regressor_model = final_pipeline.named_steps['regressor']
plt.figure(figsize=(20, 10))
plot_tree(
    regressor_model, 
    feature_names=features, 
    filled=True, 
    rounded=True, 
    fontsize=10
)
plt.title("Visualisasi Struktur Pohon Keputusan (Decision Tree)", fontsize=16)
plt.show()

# %% [markdown]
# === CELL 10: MARKDOWN ===
# ## 5. Simpan Pipeline ke File `.joblib`
# Menyimpan objek pipeline terlatih beserta daftar fitur dan skor evaluasi menggunakan format `.joblib`

# %%
# === CELL 11: CODE ===
model_save_path = 'model.joblib'

model_data = {
    "pipeline": final_pipeline,
    "features": features,
    "mean_mae": mean_mae,
    "data_count": len(dataset)
}

joblib.dump(model_data, model_save_path)
print(f"Sukses! Model Pipeline berhasil disimpan di: {model_save_path}")

# %% [markdown]
# === CELL 12: MARKDOWN ===
# ## 6. Analisis Asosiasi (Apriori)
# Menggunakan algoritma **Apriori** dari library **`mlxtend`** untuk menganalisis keterkaitan antar produk dalam transaksi (Market Basket Analysis).

# %%
# === CELL 13: CODE ===
transactions_df = df.groupby('ID_Transaksi')['Nama_barang'].apply(list).reset_index()
transactions = transactions_df['Nama_barang'].tolist()

print(f"Total transaksi kasir terdeteksi: {len(transactions)} keranjang.")
print("Contoh 5 keranjang transaksi pertama:")
for i, t in enumerate(transactions[:5], 1):
    print(f"  Keranjang {i}: {t}")

te = TransactionEncoder()
te_ary = te.fit(transactions).transform(transactions)
df_encoded = pd.DataFrame(te_ary, columns=te.columns_)

print(f"\nDimensi matriks biner transaksi: {df_encoded.shape[0]} baris x {df_encoded.shape[1]} produk.")
df_encoded.head()

# %%
# === CELL 14: CODE ===
min_support = 0.02
frequent_itemsets = apriori(df_encoded, min_support=min_support, use_colnames=True)

frequent_itemsets['Itemset Size'] = frequent_itemsets['itemsets'].apply(lambda x: len(x))
frequent_itemsets['Frequency'] = (frequent_itemsets['support'] * len(df_encoded)).round(0)

frequent_itemsets_display = frequent_itemsets[frequent_itemsets['Itemset Size'] >= 2].copy()
frequent_itemsets_display = frequent_itemsets_display[['support', 'itemsets', 'Itemset Size', 'Frequency']]
frequent_itemsets_display.columns = ['Support', 'Itemsets', 'Itemset Size', 'Frequency']

print(f"Berhasil menemukan {len(frequent_itemsets)} frequent itemsets total (tunggal + kombinasi).")
print(f"Jumlah kombinasi itemset (jumlah barang >= 2): {len(frequent_itemsets_display)}.")

frequent_itemsets_display.head(10)

# %%
# === CELL 15: CODE ===
min_confidence = 0.3
rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=min_confidence)

rules['Rule'] = rules['antecedents'].apply(lambda x: ', '.join(list(x))) + ' -> ' + rules['consequents'].apply(lambda x: ', '.join(list(x)))

rules_display = rules.sort_values(by=['confidence', 'lift'], ascending=[False, False]).reset_index(drop=True)

rules_display = rules_display[['Rule', 'antecedent support', 'consequent support', 'support', 'confidence', 'lift']]
rules_display.columns = ['Rule', 'Antecedent Support', 'Consequent Support', 'Support', 'Confidence', 'Lift']

print(f"Berhasil menghasilkan {len(rules_display)} aturan asosiasi.")

rules_display.head(10)

