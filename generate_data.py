"""Sentetik kredi kartı veri seti üretir (SQLite). Gerçek müşteri verisi İÇERMEZ."""
import sqlite3
import numpy as np
import pandas as pd
from pathlib import Path

SEED = 42
N_CUSTOMERS = 2000
AS_OF = pd.Timestamp("2025-06-30")
DB_PATH = Path(__file__).parent / "banka_demo.db"

rng = np.random.default_rng(SEED)

ADLAR = ["Ahmet", "Mehmet", "Ayşe", "Fatma", "Mustafa", "Elif", "Zeynep", "Ali", "Emre", "Burak",
         "Selin", "Deniz", "Cem", "Esra", "Hakan", "Merve", "Can", "Özge", "Kerem", "Büşra"]
SOYADLAR = ["Yılmaz", "Kaya", "Demir", "Şahin", "Çelik", "Yıldız", "Aydın", "Özdemir", "Arslan",
            "Doğan", "Kılıç", "Aslan", "Çetin", "Koç", "Kurt", "Özkan", "Şimşek", "Polat"]
SEHIRLER = ["İstanbul", "Ankara", "İzmir", "Bursa", "Antalya", "Adana", "Konya", "Gaziantep"]
SEGMENTLER = ["Bireysel", "Premium", "Ticari"]
KATEGORILER = ["Market", "Akaryakıt", "Giyim", "Elektronik", "Restoran", "Seyahat", "Fatura", "Online"]


def build_customers():
    df = pd.DataFrame({
        "customer_id": np.arange(1, N_CUSTOMERS + 1),
        "ad_soyad": [f"{rng.choice(ADLAR)} {rng.choice(SOYADLAR)}" for _ in range(N_CUSTOMERS)],
        "segment": rng.choice(SEGMENTLER, N_CUSTOMERS, p=[0.7, 0.2, 0.1]),
        "sehir": rng.choice(SEHIRLER, N_CUSTOMERS),
        "kayit_tarihi": (AS_OF - pd.to_timedelta(rng.integers(90, 2500, N_CUSTOMERS), unit="D")).strftime("%Y-%m-%d"),
    })
    # Bilinçli kirli veri: veri kalitesi sorgularını göstermek için
    df.loc[rng.choice(df.index, 25, replace=False), "sehir"] = None
    dup = df.sample(15, random_state=SEED).copy()
    dup["customer_id"] = np.arange(N_CUSTOMERS + 1, N_CUSTOMERS + 1 + len(dup))
    return pd.concat([df, dup], ignore_index=True)


def build_cards(customers):
    n = len(customers)
    limit = rng.choice([10000, 25000, 50000, 100000, 250000], n, p=[0.2, 0.3, 0.3, 0.15, 0.05])
    usage = np.clip(rng.beta(2, 3.2, n) * 1.15, 0, 1.12)
    borc = (limit * usage).round(2)
    cards = pd.DataFrame({
        "card_id": np.arange(1, n + 1),
        "customer_id": customers["customer_id"].values,
        "limit_tl": limit.astype(float),
        "guncel_borc_tl": borc,
    })
    # Kirli veri: limiti sıfır/negatif kartlar
    cards.loc[rng.choice(cards.index, 6, replace=False), "limit_tl"] = 0
    return cards


def build_statements(cards):
    rows, sid = [], 1
    for _, c in cards.iterrows():
        for m in range(4):  # son 4 ekstre
            ekstre = AS_OF - pd.Timedelta(days=30 * m + int(rng.integers(5, 25)))
            son_odeme = ekstre + pd.Timedelta(days=10)
            borc = round(float(c.guncel_borc_tl) * rng.uniform(0.4, 1.0), 2)
            asgari = round(borc * 0.20, 2)
            # Çoğu müşteri öder; küçük bir kısmı asgariyi bile ödemez
            if rng.random() < 0.07 and son_odeme < AS_OF:
                odenen = round(asgari * rng.uniform(0, 0.8), 2)
            else:
                odenen = round(rng.uniform(asgari, borc), 2)
            rows.append((sid, int(c.card_id), ekstre.strftime("%Y-%m-%d"),
                         son_odeme.strftime("%Y-%m-%d"), borc, asgari, odenen))
            sid += 1
    return pd.DataFrame(rows, columns=["ekstre_id", "card_id", "ekstre_tarihi",
                                       "son_odeme_tarihi", "ekstre_borcu_tl", "asgari_odeme_tl", "odenen_tl"])


def build_transactions(cards, n_txn=40000):
    card_ids = rng.choice(cards["card_id"], n_txn)
    tutar = np.round(rng.lognormal(mean=5.3, sigma=0.9, size=n_txn), 2)
    # Birkaç aykırı (anomali) işlem enjekte et
    idx = rng.choice(n_txn, 40, replace=False)
    tutar[idx] = np.round(tutar[idx] * rng.uniform(15, 40, 40), 2)
    # Kirli veri: negatif tutar
    tutar[rng.choice(n_txn, 5, replace=False)] *= -1
    tarih = (AS_OF - pd.to_timedelta(rng.integers(0, 90, n_txn), unit="D")).strftime("%Y-%m-%d")
    return pd.DataFrame({
        "txn_id": np.arange(1, n_txn + 1), "card_id": card_ids, "txn_tarihi": tarih,
        "tutar_tl": tutar, "kategori": rng.choice(KATEGORILER, n_txn),
    })


def main():
    customers = build_customers()
    cards = build_cards(customers)
    statements = build_statements(cards)
    txns = build_transactions(cards)
    if DB_PATH.exists():
        DB_PATH.unlink()
    with sqlite3.connect(DB_PATH) as con:
        customers.to_sql("customers", con, index=False)
        cards.to_sql("cards", con, index=False)
        statements.to_sql("ekstreler", con, index=False)
        txns.to_sql("transactions", con, index=False)
    print(f"{DB_PATH.name} oluşturuldu: {len(customers)} müşteri, {len(cards)} kart, "
          f"{len(statements)} ekstre, {len(txns)} işlem")


if __name__ == "__main__":
    main()
