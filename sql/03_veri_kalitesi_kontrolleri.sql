-- Veri kalitesi özet kontrolleri
-- Her satır bir kural; adet > 0 ise inceleme gerekir

SELECT
    'Mukerrer musteri (ad + kayit tarihi ayni)' AS kontrol,
    COUNT(*) AS adet
FROM (
    SELECT
        ROW_NUMBER() OVER (
            PARTITION BY ad_soyad, kayit_tarihi
            ORDER BY customer_id
        ) AS sn
    FROM customers
) AS tekrarlar
WHERE tekrarlar.sn > 1

UNION ALL

SELECT 'Sehir bilgisi eksik musteri', COUNT(*)
FROM customers
WHERE sehir IS NULL

UNION ALL

SELECT 'Limiti 0 veya negatif kart', COUNT(*)
FROM cards
WHERE limit_tl <= 0

UNION ALL

SELECT 'Negatif tutarli islem', COUNT(*)
FROM transactions
WHERE tutar_tl < 0

UNION ALL

SELECT 'Musterisi bulunmayan kart (orphan)', COUNT(*)
FROM cards c
LEFT JOIN customers m
    ON m.customer_id = c.customer_id
WHERE m.customer_id IS NULL;