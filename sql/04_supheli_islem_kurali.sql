-- Basit anomali kuralı:
-- İşlem tutarı, kartın kendi ortalamasının 8 katından büyükse işaretle

WITH islem AS (
    SELECT
        t.txn_id,
        t.card_id,
        t.txn_tarihi,
        t.kategori,
        t.tutar_tl,
        AVG(t.tutar_tl) OVER (PARTITION BY t.card_id) AS kart_ortalama_tl,
        COUNT(*) OVER (PARTITION BY t.card_id) AS kart_islem_adedi
    FROM transactions t
    WHERE t.tutar_tl > 0
)
SELECT TOP 50
    txn_id,
    card_id,
    txn_tarihi,
    kategori,
    tutar_tl,
    ROUND(kart_ortalama_tl, 2) AS kart_ortalama_tl,
    ROUND(tutar_tl / NULLIF(kart_ortalama_tl, 0), 1) AS kat_orani
FROM islem
WHERE kart_islem_adedi >= 5
  AND tutar_tl > 8 * kart_ortalama_tl
ORDER BY kat_orani DESC;