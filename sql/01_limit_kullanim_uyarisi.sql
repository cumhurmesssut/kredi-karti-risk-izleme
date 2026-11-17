-- Limit kullanım oranı eşik ve üzeri olan kartlar + segment içi sıralama
-- Parametre: :esik (örn. 0.80)
WITH kart_durumu AS (
    SELECT
        c.card_id,
        m.customer_id,
        m.ad_soyad,
        m.segment,
        c.limit_tl,
        c.guncel_borc_tl,
        ROUND(c.guncel_borc_tl * 1.0 / c.limit_tl, 4) AS kullanim_orani
    FROM cards c
    JOIN customers m ON m.customer_id = c.customer_id
    WHERE c.limit_tl > 0                      -- bozuk limit kayıtları veri kalitesi raporunda
)
SELECT
    card_id, customer_id, ad_soyad, segment, limit_tl, guncel_borc_tl,
    ROUND(kullanim_orani * 100, 1)            AS kullanim_yuzde,
    ROUND(limit_tl - guncel_borc_tl, 2)       AS kalan_limit_tl,
    CASE
        WHEN kullanim_orani >= 1.00 THEN 'LIMIT ASIMI'
        WHEN kullanim_orani >= 0.90 THEN 'KRITIK'
        ELSE 'UYARI'
    END                                       AS risk_seviyesi,
    RANK() OVER (PARTITION BY segment ORDER BY kullanim_orani DESC) AS segment_ici_sira
FROM kart_durumu
WHERE kullanim_orani >= 0.80
ORDER BY kullanim_orani DESC;
