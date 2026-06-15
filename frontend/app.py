import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time

# Konfigurasi halaman Streamlit
st.set_page_config(
    page_title="Sistem Prediksi Stok Warung",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Backend API URL
API_URL = "http://127.0.0.1:8001"

# --- Styling CSS Custom ---
st.markdown("""
<style>
    /* Mengubah font dan warna utama */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Tombol premium */
    div.stButton > button:first-child {
        background-color: #0f4c81;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover {
        background-color: #1a629f;
        box-shadow: 0 4px 12px rgba(15, 76, 129, 0.3);
        transform: translateY(-1px);
    }
    
    /* Box metrik */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #eef2f5;
        text-align: center;
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
    }
    
    /* Peringatan stok */
    .stock-alert {
        background-color: #fff9db;
        border-left: 5px solid #fcc419;
        padding: 1rem;
        border-radius: 4px;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Inisialisasi state sesi
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = None
if "temp_items" not in st.session_state:
    st.session_state["temp_items"] = []
if "nota_transaksi" not in st.session_state:
    st.session_state["nota_transaksi"] = ""

def format_rupiah(val):
    return f"Rp {val:,.0f}".replace(",", ".")

# --- Halaman Login ---
def show_login():
    st.write("")
    st.write("")
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center; color: #0f4c81;'>🏪 Sistem Prediksi Stok</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #666;'>Optimalkan manajemen stok warung Anda dengan Decision Tree</p>", unsafe_allow_html=True)
        
        with st.container(border=True):
            st.markdown("<h3 style='margin-top:0; color: #333;'>Masuk Akun Pemilik</h3>", unsafe_allow_html=True)
            username = st.text_input("Username", placeholder="Masukkan username")
            password = st.text_input("Password", type="password", placeholder="Masukkan password")
            
            login_btn = st.button("Masuk", use_container_width=True)
            
            if login_btn:
                if not username or not password:
                    st.error("Username dan password harus diisi.")
                else:
                    try:
                        res = requests.post(f"{API_URL}/api/login", json={
                            "username": username,
                            "password": password
                        })
                        if res.status_code == 200:
                            st.session_state["logged_in"] = True
                            st.session_state["username"] = username
                            st.success("Login Berhasil!")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error(res.json().get("detail", "Gagal login."))
                    except requests.exceptions.ConnectionError:
                        st.error("Gagal terhubung ke Backend API. Pastikan server FastAPI telah dijalankan di port 8000.")

# --- Halaman Dashboard ---
def show_dashboard():
    st.title("📊 Dashboard Utama")
    st.markdown("Ringkasan kondisi penjualan dan inventaris warung Anda saat ini.")
    
    try:
        res = requests.get(f"{API_URL}/api/dashboard")
        if res.status_code == 200:
            data = res.json()
            
            # Baris Metrik Utama
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <span style="color: #666; font-size: 14px; font-weight: 500;">Total Omzet Penjualan</span>
                    <h2 style="color: #0f4c81; margin: 0.5rem 0;">{format_rupiah(data['total_omzet'])}</h2>
                    <span style="color: green; font-size: 12px;">★ Akumulasi keseluruhan</span>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div class="metric-card">
                    <span style="color: #666; font-size: 14px; font-weight: 500;">Variasi Barang Terdaftar</span>
                    <h2 style="color: #0f4c81; margin: 0.5rem 0;">{data['jenis_barang']} Jenis</h2>
                    <span style="color: #666; font-size: 12px;">Unit barang master</span>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                <div class="metric-card">
                    <span style="color: #666; font-size: 14px; font-weight: 500;">Total Kuantitas Stok Fisik</span>
                    <h2 style="color: #0f4c81; margin: 0.5rem 0;">{data['total_stok'] if data['total_stok'] else 0} Unit</h2>
                    <span style="color: #666; font-size: 12px;">Total sisa stok gudang</span>
                </div>
                """, unsafe_allow_html=True)
                
            st.write("")
            st.write("")
            
            # Baris Informasi Detail
            det_col1, det_col2 = st.columns([1, 1.2])
            
            with det_col1:
                st.markdown("### Peringatan Stok Menipis")
                st.markdown("Produk dengan stok di bawah batas minimal (10 unit) yang perlu segera di-restock:")
                
                low_stock = data.get("low_stock_alerts", [])
                if low_stock:
                    for item in low_stock:
                        st.markdown(f"""
                        <div class="stock-alert">
                            <strong>{item['nama_barang']}</strong> ({item['kode_barang']})<br>
                            Kategori: {item['kategori']} | Sisa Stok: <span style="color: red; font-weight: bold;">{item['stok']} unit</span>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.success("✅ Semua stok aman. Tidak ada produk yang menipis.")
                    
            with det_col2:
                st.markdown("### 📝 Transaksi Penjualan Terbaru")
                st.markdown("Daftar 5 nota transaksi penjualan terakhir:")
                recent_trx = data.get("recent_transactions", [])
                if recent_trx:
                    df_trx = pd.DataFrame(recent_trx)
                    df_trx.columns = ["ID", "Nomor Nota", "Waktu Transaksi", "Total Bayar"]
                    df_trx["Total Bayar"] = df_trx["Total Bayar"].apply(format_rupiah)
                    st.dataframe(df_trx[["Nomor Nota", "Waktu Transaksi", "Total Bayar"]], use_container_width=True, hide_index=True)
                else:
                    st.info("Belum ada transaksi penjualan tercatat.")
        else:
            st.error("Gagal memuat data dashboard dari backend.")
    except Exception as e:
        st.error(f"Koneksi ke backend gagal: {str(e)}")

# --- Halaman Kelola Barang ---
def show_kelola_barang():
    st.title("Kelola Master Data Barang")
    st.markdown("Tambah, edit, atau hapus data barang dagangan warung.")
    
    try:
        res = requests.get(f"{API_URL}/api/barang")
        if res.status_code == 200:
            barang_list = res.json()
            df_barang = pd.DataFrame(barang_list)
            
            # Layout Tab
            tab1, tab2 = st.tabs(["📋 Daftar Barang", "🔧 Aksi CRUD"])
            
            with tab1:
                if not df_barang.empty:
                    df_show = df_barang.copy()
                    df_show.columns = ["ID", "Kode Barang", "Nama Barang", "Kategori", "Harga Jual", "Stok Fisik"]
                    df_show["Harga Jual"] = df_show["Harga Jual"].apply(format_rupiah)
                    st.dataframe(df_show[["Kode Barang", "Nama Barang", "Kategori", "Harga Jual", "Stok Fisik"]], use_container_width=True, hide_index=True)
                else:
                    st.info("Belum ada data barang terdaftar.")
                    
            with tab2:
                action = st.radio("Pilih Tindakan", ["Tambah Barang Baru", "Edit / Hapus Barang"], horizontal=True)
                
                if action == "Tambah Barang Baru":
                    with st.form("tambah_barang"):
                        col1, col2 = st.columns(2)
                        with col1:
                            kode = st.text_input("Kode Barang (Unique)", placeholder="Contoh: BRG-011")
                            nama = st.text_input("Nama Barang", placeholder="Contoh: Indomie Soto")
                            kategori = st.selectbox("Kategori", ["Mie Instan", "Minuman", "Sembako", "Sabun & Deterjen", "Bumbu Dapur", "Alat Tulis", "Perlengkapan Rumah", "Makanan Ringan", "Obat-obatan", "Perlengkapan Mandi", "Rokok", "Kebutuhan Bayi", "Lainnya"])
                        with col2:
                            harga = st.number_input("Harga Jual (Rp)", min_value=1, step=500, value=5000)
                            stok = st.number_input("Jumlah Stok Awal", min_value=0.0, step=0.1, value=50.0)
                            
                        submit = st.form_submit_button("Simpan Barang")
                        if submit:
                            if not kode or not nama:
                                st.error("Kode dan Nama barang wajib diisi!")
                            else:
                                post_res = requests.post(f"{API_URL}/api/barang", json={
                                     "kode_barang": kode,
                                     "nama_barang": nama,
                                     "kategori": kategori,
                                     "harga_jual": int(harga),
                                     "stok": float(stok)
                                })
                                if post_res.status_code == 200:
                                    st.success("Barang berhasil ditambahkan!")
                                    time.sleep(0.5)
                                    st.rerun()
                                else:
                                    st.error(post_res.json().get("detail", "Gagal menyimpan barang."))
                                    
                elif action == "Edit / Hapus Barang":
                    if not df_barang.empty:
                        # Pilih barang yang akan diubah
                        barang_options = {row["id"]: f"{row['nama_barang']} ({row['kode_barang']})" for row in barang_list}
                        selected_id = st.selectbox("Pilih Barang yang akan diubah/dihapus", list(barang_options.keys()), format_func=lambda x: barang_options[x])
                        
                        # Ambil detail barang terpilih
                        curr_barang = next(item for item in barang_list if item["id"] == selected_id)
                        
                        with st.form("edit_barang"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.text_input("Kode Barang (Tidak dapat diubah)", value=curr_barang["kode_barang"], disabled=True)
                                edit_nama = st.text_input("Nama Barang", value=curr_barang["nama_barang"])
                                categories = ["Mie Instan", "Minuman", "Sembako", "Sabun & Deterjen", "Bumbu Dapur", "Alat Tulis", "Perlengkapan Rumah", "Makanan Ringan", "Obat-obatan", "Perlengkapan Mandi", "Rokok", "Kebutuhan Bayi", "Lainnya"]
                                default_idx = categories.index(curr_barang["kategori"]) if curr_barang["kategori"] in categories else 0
                                edit_kategori = st.selectbox("Kategori", categories, index=default_idx)
                            with col2:
                                edit_harga = st.number_input("Harga Jual (Rp)", min_value=1, step=500, value=int(curr_barang["harga_jual"]))
                                edit_stok = st.number_input("Jumlah Stok Saat Ini", min_value=0.0, step=0.1, value=float(curr_barang["stok"]))
                                
                            col_btn1, col_btn2 = st.columns(2)
                            with col_btn1:
                                update_btn = st.form_submit_button("Simpan Perubahan")
                            with col_btn2:
                                delete_btn = st.form_submit_button("Hapus Barang 🔴")
                                
                            if update_btn:
                                put_res = requests.put(f"{API_URL}/api/barang/{selected_id}", json={
                                    "nama_barang": edit_nama,
                                    "kategori": edit_kategori,
                                    "harga_jual": int(edit_harga),
                                    "stok": float(edit_stok)
                                })
                                if put_res.status_code == 200:
                                    st.success("Barang berhasil diperbarui!")
                                    time.sleep(0.5)
                                    st.rerun()
                                else:
                                    st.error(put_res.json().get("detail", "Gagal memperbarui barang."))
                                    
                            if delete_btn:
                                del_res = requests.delete(f"{API_URL}/api/barang/{selected_id}")
                                if del_res.status_code == 200:
                                    st.success("Barang berhasil dihapus!")
                                    time.sleep(0.5)
                                    st.rerun()
                                else:
                                    st.error(del_res.json().get("detail", "Gagal menghapus barang (barang kemungkinan memiliki riwayat transaksi)."))
                    else:
                        st.info("Tidak ada barang untuk diubah.")
        else:
            st.error("Gagal memuat barang dari backend.")
    except Exception as e:
        st.error(f"Koneksi backend gagal: {str(e)}")

# --- Halaman Input Transaksi ---
def show_input_transaksi():
    st.title("🛒 Input Transaksi Penjualan")
    st.markdown("Catat transaksi keluar barang. Stok fisik akan berkurang secara otomatis.")
    
    # Inisialisasi nomor nota acak unik jika belum ada
    if not st.session_state["nota_transaksi"]:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        st.session_state["nota_transaksi"] = f"NT-{timestamp}"
        
    try:
        res = requests.get(f"{API_URL}/api/barang")
        if res.status_code == 200:
            barang_list = res.json()
            
            # Tampilkan Nomor Nota
            st.markdown(f"**Nomor Nota Baru:** `{st.session_state['nota_transaksi']}`")
            
            col_form, col_summary = st.columns([1.1, 1])
            
            with col_form:
                st.markdown("### Tambah Item Penjualan")
                # Dropdown barang
                barang_options = {item["id"]: f"{item['nama_barang']} ({format_rupiah(item['harga_jual'])}) | Stok: {item['stok']}" for item in barang_list}
                chosen_id = st.selectbox("Pilih Produk", list(barang_options.keys()), format_func=lambda x: barang_options[x])
                
                qty = st.number_input("Jumlah Kuantitas", min_value=0.01, step=0.01, value=1.0)
                
                add_item_btn = st.button("Tambah ke Nota")
                if add_item_btn:
                    chosen_item = next(item for item in barang_list if item["id"] == chosen_id)
                    # Cek jika stok cukup
                    if chosen_item["stok"] < qty:
                        st.error(f"Gagal! Stok '{chosen_item['nama_barang']}' tidak cukup. Sisa stok: {chosen_item['stok']}.")
                    else:
                        # Cek jika sudah dimasukkan ke keranjang, tinggal ditambahkan jumlahnya
                        existing = next((item for item in st.session_state["temp_items"] if item["barang_id"] == chosen_id), None)
                        if existing:
                            if chosen_item["stok"] < (existing["jumlah"] + qty):
                                st.error(f"Gagal! Total jumlah di nota ({existing['jumlah'] + qty}) melebihi stok ({chosen_item['stok']}).")
                            else:
                                existing["jumlah"] = round(existing["jumlah"] + qty, 2)
                                existing["subtotal"] = int(round(existing["jumlah"] * chosen_item["harga_jual"]))
                                st.success("Item diperbarui di nota.")
                                time.sleep(0.5)
                                st.rerun()
                        else:
                            st.session_state["temp_items"].append({
                                "barang_id": chosen_id,
                                "kode_barang": chosen_item["kode_barang"],
                                "nama_barang": chosen_item["nama_barang"],
                                "harga_jual": chosen_item["harga_jual"],
                                "jumlah": float(qty),
                                "subtotal": int(round(qty * chosen_item["harga_jual"]))
                            })
                            st.success(f"Berhasil menambahkan {qty} {chosen_item['nama_barang']} ke nota.")
                            time.sleep(0.5)
                            st.rerun()
                            
                # Tampilkan rekomendasi silang Apriori
                st.write("")
                try:
                    rec_res = requests.get(f"{API_URL}/api/rekomendasi/{chosen_id}")
                    if rec_res.status_code == 200:
                        recs = rec_res.json()
                        if recs:
                            st.markdown("💡 **Sering Dibeli Bersama (Rekomendasi Asosiasi):**")
                            for r in recs[:2]: # Tampilkan max 2 rekomendasi terkuat
                                r_id = r["consequent_id"]
                                r_name = r["consequent_name"]
                                r_conf = r["confidence"] * 100
                                
                                # Cek ketersediaan produk rekomendasi
                                r_item = next((item for item in barang_list if item["id"] == r_id), None)
                                if r_item and r_item["stok"] > 0:
                                    col_rec_txt, col_rec_btn = st.columns([2.5, 1])
                                    with col_rec_txt:
                                        st.markdown(f"- **{r_name}** ({format_rupiah(r_item['harga_jual'])})<br><span style='color: #666; font-size:12px;'>Keyakinan: {r_conf:.1f}%</span>", unsafe_allow_html=True)
                                    with col_rec_btn:
                                        if st.button(f"➕ Tambah", key=f"rec_{r_id}"):
                                            existing = next((item for item in st.session_state["temp_items"] if item["barang_id"] == r_id), None)
                                            if existing:
                                                if r_item["stok"] < (existing["jumlah"] + 1.0):
                                                    st.error("Stok produk rekomendasi habis.")
                                                else:
                                                    existing["jumlah"] = round(existing["jumlah"] + 1.0, 2)
                                                    existing["subtotal"] = int(round(existing["jumlah"] * r_item["harga_jual"]))
                                                    st.success(f"Kuantitas {r_name} ditambah.")
                                                    time.sleep(0.5)
                                                    st.rerun()
                                            else:
                                                st.session_state["temp_items"].append({
                                                    "barang_id": r_id,
                                                    "kode_barang": r_item["kode_barang"],
                                                    "nama_barang": r_name,
                                                    "harga_jual": r_item["harga_jual"],
                                                    "jumlah": 1.0,
                                                    "subtotal": int(r_item["harga_jual"])
                                                })
                                                st.success(f"'{r_name}' ditambahkan.")
                                                time.sleep(0.5)
                                                st.rerun()
                except Exception:
                    pass
                            
            with col_summary:
                st.markdown("### Rincian Nota Penjualan")
                if st.session_state["temp_items"]:
                    df_temp = pd.DataFrame(st.session_state["temp_items"])
                    df_show = df_temp.copy()
                    df_show["harga_jual"] = df_show["harga_jual"].apply(format_rupiah)
                    df_show["subtotal"] = df_show["subtotal"].apply(format_rupiah)
                    df_show.columns = ["Barang ID", "Kode", "Nama Produk", "Harga Satuan", "Jumlah", "Subtotal"]
                    st.dataframe(df_show[["Kode", "Nama Produk", "Harga Satuan", "Jumlah", "Subtotal"]], use_container_width=True, hide_index=True)
                    
                    total_bayar = sum(item["subtotal"] for item in st.session_state["temp_items"])
                    st.markdown(f"### **Total Bayar:** <span style='color: #0f4c81;'>{format_rupiah(total_bayar)}</span>", unsafe_allow_html=True)
                    
                    col_act1, col_act2 = st.columns(2)
                    with col_act1:
                        clear_btn = st.button("Batalkan Transaksi")
                        if clear_btn:
                            st.session_state["temp_items"] = []
                            st.session_state["nota_transaksi"] = ""
                            st.warning("Keranjang transaksi dibersihkan.")
                            time.sleep(0.5)
                            st.rerun()
                            
                    with col_act2:
                        save_btn = st.button("Simpan & Konfirmasi")
                        if save_btn:
                            # Kirim ke backend
                            payload = {
                                "nomor_nota": st.session_state["nota_transaksi"],
                                "total_bayar": total_bayar,
                                "items": [
                                    {
                                        "barang_id": item["barang_id"],
                                        "jumlah": item["jumlah"],
                                        "subtotal": item["subtotal"]
                                    } for item in st.session_state["temp_items"]
                                ]
                            }
                            post_res = requests.post(f"{API_URL}/api/transaksi", json=payload)
                            if post_res.status_code == 200:
                                st.success("Transaksi berhasil disimpan dan stok otomatis terpotong!")
                                # Reset state transaksi
                                st.session_state["temp_items"] = []
                                st.session_state["nota_transaksi"] = ""
                                time.sleep(1.0)
                                st.rerun()
                            else:
                                st.error(post_res.json().get("detail", "Gagal menyimpan transaksi."))
                else:
                    st.info("Nota kosong. Silakan pilih produk di sebelah kiri.")
        else:
            st.error("Gagal mengambil daftar barang.")
    except Exception as e:
        st.error(f"Koneksi backend gagal: {str(e)}")

# --- Halaman Laporan ---
def show_laporan():
    st.title("📋 Laporan & Riwayat Penjualan")
    st.markdown("Lihat rekapitulasi data transaksi penjualan harian.")
    
    col1, col2 = st.columns(2)
    with col1:
        start_d = st.date_input("Tanggal Mulai", datetime.now() - pd.Timedelta(days=30))
    with col2:
        end_d = st.date_input("Tanggal Akhir", datetime.now())
        
    fetch_btn = st.button("Tampilkan Laporan")
    
    if fetch_btn:
        try:
            params = {
                "start_date": start_d.strftime("%Y-%m-%d"),
                "end_date": end_d.strftime("%Y-%m-%d")
            }
            res = requests.get(f"{API_URL}/api/laporan", params=params)
            if res.status_code == 200:
                data = res.json()
                if data:
                    df = pd.DataFrame(data)
                    
                    # Hitung Summary
                    total_omzet = sum(df["subtotal"])
                    total_qty = sum(df["jumlah"])
                    
                    # Tampilkan metrik ringkasan laporan
                    col_m1, col_m2 = st.columns(2)
                    with col_m1:
                        st.metric("Total Omzet Periode Ini", format_rupiah(total_omzet))
                    with col_m2:
                        st.metric("Total Kuantitas Barang Terjual", f"{total_qty} Unit")
                        
                    # Format tabel agar ramah dibaca
                    df_show = df.copy()
                    df_show.columns = ["Nomor Nota", "Waktu Transaksi", "Nama Produk", "Jumlah", "Subtotal"]
                    df_show["Subtotal"] = df_show["Subtotal"].apply(format_rupiah)
                    
                    st.dataframe(df_show, use_container_width=True, hide_index=True)
                    
                    # Tombol unduh CSV
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Unduh Laporan (CSV)",
                        data=csv,
                        file_name=f"laporan_penjualan_{params['start_date']}_ke_{params['end_date']}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("Tidak ada riwayat transaksi penjualan dalam periode terpilih.")
            else:
                st.error("Gagal menarik data laporan.")
        except Exception as e:
            st.error(f"Koneksi backend gagal: {str(e)}")

# --- Halaman Prediksi ---
def show_prediksi():
    st.title("🔮 Analisis Prediksi & Rekomendasi Restock")
    st.markdown("Gunakan model Machine Learning Decision Tree Regression untuk menentukan persediaan stok barang bulan depan.")
    
    try:
        # Ambil daftar barang
        res_barang = requests.get(f"{API_URL}/api/barang")
        if res_barang.status_code == 200:
            barang_list = res_barang.json()
            
            col_in1, col_in2 = st.columns([1.2, 1])
            
            with col_in1:
                with st.container(border=True):
                    st.markdown("### Konfigurasi Target Analisis")
                    # Pilih barang
                    barang_options = {item["id"]: f"{item['nama_barang']} ({item['kode_barang']}) | Sisa Stok: {item['stok']}" for item in barang_list}
                    chosen_id = st.selectbox("Pilih Produk", list(barang_options.keys()), format_func=lambda x: barang_options[x])
                    
                    # Target Bulan
                    current_year = datetime.now().year
                    months = {
                        1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
                        7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember"
                    }
                    col_m, col_y = st.columns(2)
                    with col_m:
                        target_month = st.selectbox("Bulan Target", list(months.keys()), format_func=lambda x: months[x], index=datetime.now().month % 12)
                    with col_y:
                        target_year = st.selectbox("Tahun Target", [current_year, current_year + 1])
                        
                    # Safety Stock
                    safety_stock = st.number_input("Batas Aman Stok (Safety Stock)", min_value=0, step=5, value=20, help="Cadangan stok minimal untuk mencegah kehabisan barang akibat keterlambatan pasokan.")
                    
                    predict_btn = st.button("Hitung Prediksi Penjualan")
                    
            with col_in2:
                with st.container(border=True):
                    st.markdown("### Performa Model ML")
                    st.markdown("Informasi status pelatihan model kecerdasan buatan warung saat ini.")
                    
                    # Tombol latih ulang model
                    retrain_btn = st.button("Latih Ulang Model ML 🔄")
                    if retrain_btn:
                        with st.spinner("Melatih ulang model Decision Tree di server backend..."):
                            train_res = requests.post(f"{API_URL}/api/train")
                            if train_res.status_code == 200:
                                t_data = train_res.json()
                                st.success("Model berhasil dilatih ulang!")
                                st.write(f"- Jumlah baris data latih: **{t_data['data_count']} baris**")
                                st.write(f"- Rata-rata error (MAE): **{t_data['mean_mae']:.2f} unit**")
                            else:
                                st.error("Gagal melatih ulang model (Data transaksi di database kemungkinan kurang).")
                    
                    st.markdown("---")
                    st.markdown("""
                    **Arsitektur & Alur Deployment (Slide 10-11 PDF):**
                    *   **Pipeline:** `sklearn.pipeline.Pipeline` (Aktif)
                    *   **Preprocessing:** `StandardScaler()` (Penyamaan Skala)
                    *   **Estimator:** `DecisionTreeRegressor(max_depth=4)`
                    *   **Format Simpan:** `Joblib (Compressed)`
                    """)
                                
            # Tombol prediksi ditekan
            if predict_btn:
                try:
                    params = {
                        "barang_id": chosen_id,
                        "periode": f"{target_year}-{target_month:02d}",
                        "safety_stock": safety_stock
                    }
                    pred_res = requests.get(f"{API_URL}/api/prediksi", params=params)
                    if pred_res.status_code == 200:
                        pred_data = pred_res.json()
                        
                        st.write("---")
                        st.markdown(f"## Hasil Analisis: **{pred_data['nama_barang']}**")
                        st.caption(f"Status Data: {'Dari Cache Database' if pred_data.get('cached') else 'Inferensi Model Baru'}")
                        
                        # Baris Visualisasi Kartu
                        col_c1, col_c2, col_c3 = st.columns(3)
                        with col_c1:
                            st.metric("Estimasi Produk Laku (1 Bulan)", f"{pred_data['jumlah_prediksi']} unit")
                        with col_c2:
                            st.metric("Sisa Stok Fisik Saat Ini", f"{pred_data['sisa_stok']} unit")
                        with col_c3:
                            st.metric("Safety Stock Diterapkan", f"{safety_stock} unit")
                            
                        # Hasil Rekomendasi Restock
                        rekomendasi = pred_data["rekomendasi_stok"]
                        
                        if rekomendasi > 0:
                            st.markdown(f"""
                            <div style="background-color: #e3faf2; border-left: 6px solid #12b886; padding: 1.5rem; border-radius: 8px; margin-top: 1.5rem;">
                                <h3 style="color: #0ca678; margin-top: 0;">💡 Rekomendasi Tindakan: PERLU PEMBELIAN STOK</h3>
                                <p style="font-size: 16px; margin-bottom: 0;">
                                    Berdasarkan prediksi penjualan sebesar <strong>{pred_data['jumlah_prediksi']} unit</strong> dan batas safety stock 
                                    <strong>{safety_stock} unit</strong>, dengan sisa stok fisik saat ini <strong>{pred_data['sisa_stok']} unit</strong>.<br>
                                    Anda direkomendasikan untuk memesan ulang stok sebanyak:
                                    <span style="font-size: 24px; font-weight: bold; color: #0ca678;"><br>🛒 BELI LAGI SEBANYAK: {rekomendasi} UNIT</span>
                                </p>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            <div style="background-color: #e8f4fd; border-left: 6px solid #1c7ed6; padding: 1.5rem; border-radius: 8px; margin-top: 1.5rem;">
                                <h3 style="color: #1971c2; margin-top: 0;">✅ Rekomendasi Tindakan: STOK MASIH AMAN</h3>
                                <p style="font-size: 16px; margin-bottom: 0;">
                                    Sisa stok fisik Anda saat ini sebesar <strong>{pred_data['sisa_stok']} unit</strong> dinilai masih aman untuk memenuhi 
                                    proyeksi kebutuhan bulan depan (<strong>{pred_data['jumlah_prediksi']} unit</strong>) ditambah safety stock.<br>
                                    <span style="font-size: 20px; font-weight: bold; color: #1971c2;"><br>Anda tidak perlu memesan barang untuk periode ini.</span>
                                </p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                        # Grafik Prediksi Mingguan (jika ada weekly_predictions dari backend)
                        weekly_preds = pred_data.get("weekly_predictions")
                        if weekly_preds:
                            st.markdown("### 📈 Pola Tren Penjualan Mingguan (Target Bulan)")
                            st.markdown("Grafik proyeksi kuantitas produk laku per minggu (Minggu 1 s/d Minggu 5) untuk mendeteksi siklus belanja:")
                            
                            df_chart = pd.DataFrame({
                                "Minggu": [f"Minggu {i}" for i in range(1, 6)],
                                "Proyeksi Kuantitas Laku": weekly_preds
                            })
                            st.line_chart(df_chart.set_index("Minggu"), color="#0f4c81")
                    else:
                        st.error(pred_res.json().get("detail", "Gagal menghitung prediksi."))
                except Exception as e:
                    st.error(f"Terjadi kesalahan saat memproses prediksi: {str(e)}")
        else:
            st.error("Gagal mengambil master data barang.")
    except Exception as e:
        st.error(f"Koneksi backend gagal: {str(e)}")

# --- Halaman Analisis Asosiasi (Apriori) ---
def show_apriori():
    st.title("🛒 Analisis Asosiasi Produk (Market Basket Analysis)")
    st.markdown("Temukan pola kombinasi barang yang paling sering dibeli secara bersamaan oleh pelanggan menggunakan Algoritma Apriori.")
    
    col1, col2 = st.columns([1, 2.5])
    
    with col1:
        with st.container(border=True):
            st.markdown("### Konfigurasi Batas Apriori")
            min_support = st.slider("Support Minimal (min_support)", min_value=0.01, max_value=0.20, value=0.02, step=0.01, help="Kekerapan barang/kombinasi barang dibeli dalam seluruh transaksi.")
            min_confidence = st.slider("Confidence Minimal (min_confidence)", min_value=0.10, max_value=1.00, value=0.30, step=0.05, help="Keyakinan seberapa sering barang B dibeli jika barang A dibeli.")
            
            run_btn = st.button("Jalankan Analisis Apriori")
            
    with col2:
        with st.container(border=True):
            st.markdown("### Mengapa Menggunakan Apriori?")
            st.markdown("""
            * **Cross-Selling**: Membantu memajang produk pendamping secara berdekatan (misalnya, menempatkan minuman dingin dekat rak mie instan).
            * **Paket Promosi (Bundling)**: Mempermudah perancangan diskon paket hemat (misalnya, Paket Beras + Minyak Goreng).
            * **Rekomendasi Pintar**: Secara otomatis memberikan rekomendasi produk tambahan pada halaman kasir ketika pembeli memilih barang tertentu.
            """)
            
    # Menampilkan hasil analisis
    try:
        params = {
            "min_support": min_support,
            "min_confidence": min_confidence
        }
        res = requests.get(f"{API_URL}/api/apriori", params=params)
        if res.status_code == 200:
            rules = res.json()
            
            st.write("---")
            st.markdown(f"### 📊 Hasil Aturan Asosiasi Terbentuk ({len(rules)} Aturan)")
            
            if rules:
                df_rules = pd.DataFrame(rules)
                
                # Rapiin kolom untuk user
                df_show = pd.DataFrame({
                    "Jika Membeli (Antecedent)": df_rules["antecedent_name"] + " (" + df_rules["antecedent_code"] + ")",
                    "Maka Membeli (Consequent)": df_rules["consequent_name"] + " (" + df_rules["consequent_code"] + ")",
                    "Support": df_rules["support"].apply(lambda x: f"{x*100:.1f}%"),
                    "Confidence": df_rules["confidence"].apply(lambda x: f"{x*100:.1f}%"),
                    "Lift Score": df_rules["lift"].apply(lambda x: f"{x:.2f}")
                })
                
                st.dataframe(df_show, use_container_width=True, hide_index=True)
                
                st.info("""
                💡 **Tips Membaca Lift Score:** 
                - **Lift > 1**: Menunjukkan hubungan positif yang kuat (barang B *sangat dipengaruhi* oleh pembelian barang A).
                - **Lift = 1**: Tidak ada asosiasi (kedua barang dibeli secara independen).
                - **Lift < 1**: Menunjukkan hubungan negatif (pelanggan yang membeli barang A cenderung *tidak* membeli barang B).
                """)
            else:
                st.warning("⚠️ Tidak ada aturan asosiasi yang terbentuk dengan batas Support dan Confidence saat ini. Silakan turunkan nilainya.")
        else:
            st.error("Gagal menjalankan analisis Apriori dari backend.")
    except Exception as e:
        st.error(f"Koneksi backend gagal: {str(e)}")

# --- Alur Tampilan Aplikasi ---
if not st.session_state["logged_in"]:
    show_login()
else:
    # Sidebar Navigasi
    st.sidebar.markdown(f"<h2 style='color: #0f4c81;'>🏪 Warung Stok</h2>", unsafe_allow_html=True)
    st.sidebar.markdown(f"👤 Login sebagai: **{st.session_state['username']}**")
    
    menu = st.sidebar.radio(
        "Navigasi Menu",
        ["Dashboard Utama", "Kelola Data Barang", "Input Transaksi Penjualan", "Laporan & Riwayat Penjualan", "Analisis Prediksi (Modul ML)", "Analisis Asosiasi (Apriori)"]
    )
    
    st.sidebar.write("---")
    logout_btn = st.sidebar.button("Keluar Akun (Logout)")
    if logout_btn:
        st.session_state["logged_in"] = False
        st.session_state["username"] = None
        st.session_state["temp_items"] = []
        st.success("Logout Berhasil.")
        time.sleep(0.5)
        st.rerun()
        
    # Router Halaman
    if menu == "Dashboard Utama":
        show_dashboard()
    elif menu == "Kelola Data Barang":
        show_kelola_barang()
    elif menu == "Input Transaksi Penjualan":
        show_input_transaksi()
    elif menu == "Laporan & Riwayat Penjualan":
        show_laporan()
    elif menu == "Analisis Prediksi (Modul ML)":
        show_prediksi()
    elif menu == "Analisis Asosiasi (Apriori)":
        show_apriori()
