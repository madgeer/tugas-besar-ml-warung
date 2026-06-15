import pandas as pd
from collections import defaultdict
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, association_rules
from backend.database import get_connection

def get_association_rules(min_support=0.02, min_confidence=0.3):
    """
    Menjalankan algoritma Apriori menggunakan library mlxtend pada data detail_transaksi.
    Mengembalikan aturan asosiasi A -> B yang memenuhi min_support dan min_confidence.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Ambil data barang untuk mapping ID ke Nama dan Kode
    cursor.execute("SELECT id, nama_barang, kode_barang FROM barang")
    products = {row["id"]: {"nama": row["nama_barang"], "kode": row["kode_barang"]} for row in cursor.fetchall()}
    
    # 2. Ambil data keranjang transaksi
    cursor.execute("SELECT transaksi_id, barang_id FROM detail_transaksi")
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return []
        
    # Kelompokkan barang_id berdasarkan transaksi_id (keranjang belanja)
    transactions_dict = defaultdict(list)
    for row in rows:
        transactions_dict[row["transaksi_id"]].append(row["barang_id"])
        
    transactions = list(transactions_dict.values())
    N = len(transactions)
    if N == 0:
        return []
        
    # 3. Transformasi transaksi ke bentuk One-Hot Encoded DataFrame menggunakan mlxtend
    te = TransactionEncoder()
    te_ary = te.fit(transactions).transform(transactions)
    df_encoded = pd.DataFrame(te_ary, columns=te.columns_)
    
    # 4. Cari frequent itemsets menggunakan mlxtend apriori
    frequent_itemsets = apriori(df_encoded, min_support=min_support, use_colnames=True)
    
    if frequent_itemsets.empty:
        return []
        
    # 5. Bangun Aturan Asosiasi (Association Rules) menggunakan mlxtend
    rules_df = association_rules(frequent_itemsets, metric="confidence", min_threshold=min_confidence)
    
    if rules_df.empty:
        return []
        
    # 6. Format rules agar sesuai dengan struktur data yang digunakan oleh frontend
    rules = []
    for _, row in rules_df.iterrows():
        antecedents_ids = list(row["antecedents"])
        consequents_ids = list(row["consequents"])
        
        # Fokus pada aturan single antecedent -> single consequent untuk modul kasir / cross-selling
        if len(antecedents_ids) == 1 and len(consequents_ids) == 1:
            item_A = antecedents_ids[0]
            item_B = consequents_ids[0]
            
            if item_A in products and item_B in products:
                rules.append({
                    "antecedent_id": int(item_A),
                    "antecedent_name": products[item_A]["nama"],
                    "antecedent_code": products[item_A]["kode"],
                    "consequent_id": int(item_B),
                    "consequent_name": products[item_B]["nama"],
                    "consequent_code": products[item_B]["kode"],
                    "support": float(row["support"]),
                    "confidence": float(row["confidence"]),
                    "lift": float(row["lift"])
                })
                
    # Urutkan aturan berdasarkan confidence tertinggi, lalu lift
    rules = sorted(rules, key=lambda x: (-x["confidence"], -x["lift"]))
    return rules

def get_recommendations_for_item(barang_id, min_support=0.02, min_confidence=0.3):
    """
    Mengambil daftar produk rekomendasi pendamping untuk barang tertentu
    berdasarkan aturan asosiasi Apriori yang terbentuk.
    """
    all_rules = get_association_rules(min_support, min_confidence)
    # Filter aturan yang antecedent-nya cocok dengan barang_id
    recs = [rule for rule in all_rules if rule["antecedent_id"] == barang_id]
    return recs
