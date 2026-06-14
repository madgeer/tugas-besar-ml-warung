import sqlite3
from collections import defaultdict
from backend.database import get_connection

def get_association_rules(min_support=0.02, min_confidence=0.3):
    """
    Menjalankan algoritma Apriori secara manual (zero-dependency) pada data detail_transaksi.
    Mengembalikan aturan asosiasi A -> B yang memenuhi min_support dan min_confidence.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Ambil data barang untuk mapping ID ke Nama
    cursor.execute("SELECT id, nama_barang, kode_barang FROM barang")
    products = {row["id"]: {"nama": row["nama_barang"], "kode": row["kode_barang"]} for row in cursor.fetchall()}
    
    # 2. Ambil data keranjang transaksi
    # Kelompokkan barang_id berdasarkan transaksi_id
    cursor.execute("SELECT transaksi_id, barang_id FROM detail_transaksi")
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return []
        
    transactions = defaultdict(set)
    for row in rows:
        transactions[row["transaksi_id"]].add(row["barang_id"])
        
    N = len(transactions)
    if N == 0:
        return []
        
    # 3. Hitung frekuensi barang tunggal (C1 -> L1)
    item_counts = defaultdict(int)
    for t_items in transactions.values():
        for item in t_items:
            item_counts[item] += 1
            
    # L1: Itemset ukuran 1 yang memenuhi min_support
    frequent_items = {}
    for item, count in item_counts.items():
        support = count / N
        if support >= min_support:
            frequent_items[item] = support
            
    # 4. Hitung frekuensi pasangan barang (C2 -> L2)
    pair_counts = defaultdict(int)
    for t_items in transactions.values():
        # Dapatkan semua kombinasi pasangan unik dalam transaksi yang ada di L1
        items_in_l1 = [item for item in t_items if item in frequent_items]
        for i in range(len(items_in_l1)):
            for j in range(i + 1, len(items_in_l1)):
                pair = tuple(sorted((items_in_l1[i], items_in_l1[j])))
                pair_counts[pair] += 1
                
    # L2: Itemset ukuran 2 yang memenuhi min_support
    frequent_pairs = {}
    for pair, count in pair_counts.items():
        support = count / N
        if support >= min_support:
            frequent_pairs[pair] = support
            
    # 5. Bangun Aturan Asosiasi (Rules) dari L2: A -> B dan B -> A
    rules = []
    for pair, pair_support in frequent_pairs.items():
        item_A, item_B = pair
        
        # Aturan 1: A -> B
        count_A = item_counts[item_A]
        confidence_A_B = pair_support / (count_A / N)
        support_B = frequent_items[item_B]
        lift_A_B = confidence_A_B / support_B
        
        if confidence_A_B >= min_confidence:
            rules.append({
                "antecedent_id": item_A,
                "antecedent_name": products[item_A]["nama"],
                "antecedent_code": products[item_A]["kode"],
                "consequent_id": item_B,
                "consequent_name": products[item_B]["nama"],
                "consequent_code": products[item_B]["kode"],
                "support": float(pair_support),
                "confidence": float(confidence_A_B),
                "lift": float(lift_A_B)
            })
            
        # Aturan 2: B -> A
        count_B = item_counts[item_B]
        confidence_B_A = pair_support / (count_B / N)
        support_A = frequent_items[item_A]
        lift_B_A = confidence_B_A / support_A
        
        if confidence_B_A >= min_confidence:
            rules.append({
                "antecedent_id": item_B,
                "antecedent_name": products[item_B]["nama"],
                "antecedent_code": products[item_B]["kode"],
                "consequent_id": item_A,
                "consequent_name": products[item_A]["nama"],
                "consequent_code": products[item_A]["kode"],
                "support": float(pair_support),
                "confidence": float(confidence_B_A),
                "lift": float(lift_B_A)
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
