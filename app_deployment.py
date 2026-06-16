import streamlit as st
import pandas as pd
import numpy as np
import os
import joblib
from datetime import datetime

# Import mlxtend for Apriori association rules
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, association_rules

# 1. Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Deployment - Toko Setia Ciawi",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Custom CSS Styling (Premium Design)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Card design */
    .premium-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e9ecef;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.02);
        margin-bottom: 1rem;
    }
    
    /* Header styling */
    h1, h2, h3 {
        color: #0f4c81;
    }
    
    /* Badge styling */
    .badge-ml {
        background-color: #e3faf2;
        color: #0ca678;
        padding: 0.3rem 0.6rem;
        border-radius: 6px;
        font-weight: 600;
        font-size: 12px;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# 3. Load Data & Preprocessing Setup
@st.cache_data
def load_data():
    if not os.path.exists("data.csv"):
        return None
    df = pd.read_csv("data.csv")
    df['Jumlah'] = pd.to_numeric(df['Jumlah'], errors='coerce').fillna(0.0)
    df['tanggal_parsed'] = pd.to_datetime(df['Tanggal'])
    df['tahun'] = df['tanggal_parsed'].dt.year
    df['bulan'] = df['tanggal_parsed'].dt.month
    return df

df = load_data()

# 4. Load Model .joblib
@st.cache_resource
def load_model():
    model_path = "model.joblib"
    if os.path.exists(model_path):
        return joblib.load(model_path)
    return None

model_data = load_model()

# --- Sidebar Navigasi ---
st.sidebar.markdown("<h2 style='text-align: center; color: #0f4c81;'>🏪 Toko Setia Ciawi</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='text-align: center; color: #666;'>Sistem Pendukung Keputusan Penjualan</p>", unsafe_allow_html=True)
st.sidebar.write("---")

menu = st.sidebar.radio(
    "Navigasi Menu",
    ["Dashboard & Dataset", "Prediksi Restock (Decision Tree)", "Rekomendasi Cross-Selling (Apriori)"]
)


if df is None:
    st.error("File `data.csv` tidak ditemukan di root direktori. Silakan letakkan file data terlebih dahulu.")
else:
    # Buat mapping barang_id yang sama persis dengan saat training
    unique_products = df['Nama_barang'].unique()
    product_to_id = {name: idx + 1 for idx, name in enumerate(unique_products)}

    # --- MENU 1: DASHBOARD & DATASET ---
    if menu == "Dashboard & Dataset":
        st.title("Ringkasan Dataset Transaksi")
        st.markdown("Analisis deskriptif dataset historis penjualan Toko Setia Ciawi.")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class="premium-card" style="text-align: center;">
                <span style="color: #666; font-size: 14px;">Total Baris Transaksi</span>
                <h2 style="margin: 0.5rem 0; color: #0f4c81;">{len(df):,} Baris</h2>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="premium-card" style="text-align: center;">
                <span style="color: #666; font-size: 14px;">Variasi Produk</span>
                <h2 style="margin: 0.5rem 0; color: #0f4c81;">{len(unique_products)} Jenis</h2>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="premium-card" style="text-align: center;">
                <span style="color: #666; font-size: 14px;">Total Nota Transaksi</span>
                <h2 style="margin: 0.5rem 0; color: #0f4c81;">{df['ID_Transaksi'].nunique():,} Nota</h2>
            </div>
            """, unsafe_allow_html=True)
            
        st.write("")
        st.markdown("### Preview Data Transaksi (`data.csv`)")
        st.dataframe(df[['ID_Transaksi', 'Tanggal', 'Nama_barang', 'Jumlah', 'Satuan']].head(100), use_container_width=True)

    # --- MENU 2: PREDIKSI RESTOCK (DECISION TREE) ---
    elif menu == "Prediksi Restock (Decision Tree)":
        st.title("Prediksi Penjualan & Rekomendasi Restock")
        st.markdown("Gunakan model **Decision Tree Regressor** dari file `.joblib` untuk memprediksi penjualan barang bulan depan.")
        
        if model_data is None:
            st.warning("Model biner `model.joblib` belum ada. Silakan jalankan file `Tugas_Besar_ML.ipynb` terlebih dahulu untuk menghasilkan file model.")
        else:
            col_in1, col_in2 = st.columns([1.5, 1])
            
            with col_in1:
                with st.container(border=True):
                    st.markdown("### Input Parameter Prediksi")
                    
                    # 1. Pilih Produk
                    selected_product = st.selectbox("Pilih Produk", unique_products)
                    
                    # 2. Target Waktu
                    col_m, col_y = st.columns(2)
                    with col_m:
                        months = {
                            1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
                            7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember"
                        }
                        target_month = st.selectbox("Bulan Target", list(months.keys()), format_func=lambda x: months[x], index=datetime.now().month % 12)
                    with col_y:
                        target_year = st.selectbox("Tahun Target", [2026, 2027])
                        
                    # 3. Parameter Stok
                    col_s1, col_s2 = st.columns(2)
                    with col_s1:
                        sisa_stok = st.number_input("Sisa Stok Saat Ini (Fisik)", min_value=0.0, step=1.0, value=10.0)
                    with col_s2:
                        safety_stock = st.number_input("Batas Stok Aman (Safety Stock)", min_value=0.0, step=5.0, value=20.0)
                        
                    predict_btn = st.button("Hitung Estimasi & Rekomendasi Restock", use_container_width=True)
                    
            with col_in2:
                with st.container(border=True):
                    st.markdown("### Informasi Model Terbaca (.joblib)")
                    st.write(f"- **Metrik Rata-rata Error (MAE):** `{model_data['mean_mae']:.4f} unit`")
                    st.write(f"- **Jumlah Data Latih:** `{model_data['data_count']} baris`")
                    st.write("- **Preprocessing:** `StandardScaler()` (Aktif)")
                    st.write("- **Estimator:** `DecisionTreeRegressor(max_depth=4)`")
                    st.write("- **Sumber Model:** `model.joblib`")
                    
            if predict_btn:
                # 1. Hitung Lag Feature: penjualan_bulan_lalu dari data.csv
                prev_month = target_month - 1
                prev_year = target_year
                if prev_month == 0:
                    prev_month = 12
                    prev_year = target_year - 1
                    
                # Cari total penjualan produk pada bulan lag dari data.csv
                product_sales = df[df['Nama_barang'] == selected_product]
                penjualan_bulan_lalu = product_sales[
                    (product_sales['tahun'] == prev_year) & 
                    (product_sales['bulan'] == prev_month)
                ]['Jumlah'].sum()
                
                # 2. Dapatkan barang_id untuk input model
                barang_id = product_to_id[selected_product]
                
                # 3. Lakukan prediksi mingguan (minggu 1 s/d 5)
                pipeline = model_data['pipeline']
                weekly_predictions = []
                
                for week in range(1, 6):
                    # Format input fitur: ['barang_id', 'bulan', 'minggu_ke', 'penjualan_bulan_lalu']
                    input_features = np.array([[
                        barang_id,
                        target_month,
                        week,
                        penjualan_bulan_lalu
                    ]])
                    
                    pred = pipeline.predict(input_features)[0]
                    weekly_predictions.append(max(0.0, round(float(pred), 2)))
                    
                total_prediksi = round(sum(weekly_predictions), 2)
                
                # 4. Hitung Rekomendasi Beli
                rekomendasi_beli = max(0.0, total_prediksi + safety_stock - sisa_stok)
                
                # 5. Tampilkan Output ke UI
                st.write("---")
                st.markdown(f"## Hasil Analisis: **{selected_product}**")
                
                col_c1, col_c2, col_c3 = st.columns(3)
                with col_c1:
                    st.metric("Estimasi Produk Laku (1 Bulan)", f"{total_prediksi} unit")
                with col_c2:
                    st.metric("Sisa Stok Fisik Saat Ini", f"{sisa_stok} unit")
                with col_c3:
                    st.metric("Safety Stock Diterapkan", f"{safety_stock} unit")
                    
                st.write("")
                st.markdown("#### Detailing Prediksi Mingguan:")
                df_weekly = pd.DataFrame({
                    "Minggu": [f"Minggu {i}" for i in range(1, 6)],
                    "Estimasi Jumlah Penjualan (Unit)": weekly_predictions
                })
                st.dataframe(df_weekly, use_container_width=True, hide_index=True)
                
                if rekomendasi_beli > 0:
                    st.markdown(f"""
                    <div style="background-color: #e3faf2; border-left: 6px solid #12b886; padding: 1.5rem; border-radius: 8px; margin-top: 1.5rem;">
                        <h3 style="color: #0ca678; margin-top: 0;">Rekomendasi Tindakan: PERLU PEMBELIAN STOK</h3>
                        <p style="font-size: 16px; margin-bottom: 0;">
                            Berdasarkan estimasi penjualan sebesar <strong>{total_prediksi} unit</strong> dan batas safety stock 
                            <strong>{safety_stock} unit</strong>, dengan sisa stok fisik saat ini <strong>{sisa_stok} unit</strong>.<br>
                            Anda direkomendasikan untuk memesan ulang stok sebanyak:
                            <span style="font-size: 24px; font-weight: bold; color: #0ca678;"><br>BELI LAGI SEBANYAK: {rekomendasi_beli:.1f} UNIT</span>
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="background-color: #e8f4fd; border-left: 6px solid #1971c2; padding: 1.5rem; border-radius: 8px; margin-top: 1.5rem;">
                        <h3 style="color: #1971c2; margin-top: 0;">Rekomendasi Tindakan: STOK MASIH AMAN</h3>
                        <p style="font-size: 16px; margin-bottom: 0;">
                            Sisa stok fisik saat ini (<strong>{sisa_stok} unit</strong>) masih mencukupi untuk memenuhi perkiraan penjualan 
                            <strong>{total_prediksi} unit</strong> ditambah cadangan stok aman (<strong>{safety_stock} unit</strong>).<br>
                            <span style="font-weight: bold; color: #1971c2;">Anda tidak perlu melakukan pemesanan stok barang untuk bulan depan.</span>
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

    # --- MENU 3: REKOMENDASI CROSS-SELLING (APRIORI) ---
    elif menu == "Rekomendasi Cross-Selling (Apriori)":
        st.title("Rekomendasi Cross-Selling & Keranjang Belanja")
        st.markdown("Menjalankan algoritma **Apriori** menggunakan library **`mlxtend`** untuk melihat asosiasi produk.")
        
        # Pengaturan parameter Apriori via Sidebar / Kolom
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            min_support = st.slider("Batas Minimal Support", min_value=0.01, max_value=0.10, value=0.02, step=0.01, help="Frekuensi minimal kemunculan kombinasi produk dalam seluruh transaksi.")
        with col_p2:
            min_confidence = st.slider("Batas Minimal Confidence", min_value=0.10, max_value=1.00, value=0.30, step=0.05, help="Tingkat akurasi aturan asosiasi (jika beli A, berapa peluang beli B).")
            
        with st.spinner("Menghitung aturan asosiasi Apriori..."):
            # 1. Kelompokkan produk berdasarkan transaksi
            transactions_df = df.groupby('ID_Transaksi')['Nama_barang'].apply(list).reset_index()
            transactions = transactions_df['Nama_barang'].tolist()
            
            # 2. One-Hot Encoding
            te = TransactionEncoder()
            te_ary = te.fit(transactions).transform(transactions)
            df_encoded = pd.DataFrame(te_ary, columns=te.columns_)
            
            # 3. Hitung Apriori
            frequent_itemsets = apriori(df_encoded, min_support=min_support, use_colnames=True)
            
            if frequent_itemsets.empty:
                st.warning("Tidak ada aturan asosiasi yang terbentuk dengan batas Support dan Confidence saat ini. Silakan turunkan nilainya.")
            else:
                # 4. Bangun Aturan Asosiasi
                rules_df = association_rules(frequent_itemsets, metric="confidence", min_threshold=min_confidence)
                
                if rules_df.empty:
                    st.warning("Tidak ada aturan asosiasi yang memenuhi batas Confidence saat ini.")
                else:
                    rules_df = rules_df.sort_values(by='confidence', ascending=False).reset_index(drop=True)
                    
                    # Format kolom set ke list agar rapi
                    rules_df['antecedents'] = rules_df['antecedents'].apply(lambda x: ", ".join(list(x)))
                    rules_df['consequents'] = rules_df['consequents'].apply(lambda x: ", ".join(list(x)))
                    
                    st.write("")
                    st.markdown(f"### Aturan Asosiasi Terbentuk ({len(rules_df)} Rules)")
                    
                    # Rename kolom agar user-friendly
                    display_df = rules_df[['antecedents', 'consequents', 'support', 'confidence', 'lift']].copy()
                    display_df.columns = ["Jika Pelanggan Membeli (Antecedent)", "Maka Juga Membeli (Consequent)", "Nilai Support", "Nilai Confidence", "Lift Ratio"]
                    
                    # Format angka desimal
                    display_df['Nilai Support'] = display_df['Nilai Support'].apply(lambda x: f"{x*100:.1f}%")
                    display_df['Nilai Confidence'] = display_df['Nilai Confidence'].apply(lambda x: f"{x*100:.1f}%")
                    display_df['Lift Ratio'] = display_df['Lift Ratio'].apply(lambda x: f"{x:.2f}")
                    
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                    
                    # --- SIMULASI KASIR ---
                    st.write("")
                    st.markdown("### Simulasi Rekomendasi Kasir (Cross-Selling)")
                    st.markdown("Pilih produk yang sedang dibeli oleh pelanggan untuk memicu rekomendasi item tambahan:")
                    
                    input_product = st.selectbox("Produk yang Dibeli Pelanggan", unique_products)
                    
                    # Filter aturan berdasarkan antecedent
                    recs = rules_df[rules_df['antecedents'] == input_product]
                    
                    if not recs.empty:
                        st.markdown(f"##### **Rekomendasi Produk Pelengkap untuk '{input_product}':**")
                        for _, r in recs.iterrows():
                            confidence_pct = r['confidence'] * 100
                            st.info(f"Rekomendasikan: **{r['consequents']}** (Tingkat Keyakinan/Confidence: **{confidence_pct:.1f}%** | Lift: **{r['lift']:.2f}**)")
                    else:
                        st.warning(f"Tidak ada rekomendasi pelengkap yang kuat untuk '{input_product}' pada konfigurasi support/confidence saat ini.")
