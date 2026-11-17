
-- Asgari ödemesi yapılmamış ekstreler için DPD analizi

DECLARE @as_of DATE = '2026-01-07';

WITH geciken AS (
    SELECT
        e.card_id,
        e.ekstre_id,
        e.asgari_odeme_tl - e.odenen_tl AS eksik_odeme_tl,
        DATEDIFF(DAY, e.son_odeme_tarihi, @as_of) AS dpd
    FROM ekstreler e
    WHERE e.odenen_tl < e.asgari_odeme_tl
      AND e.son_odeme_tarihi < @as_of
),
dpd_gruplari AS (
    SELECT
        CASE
            WHEN dpd BETWEEN 1 AND 29 THEN '1) 1-29 gun'
            WHEN dpd BETWEEN 30 AND 59 THEN '2) 30-59 gun'
            WHEN dpd BETWEEN 60 AND 89 THEN '3) 60-89 gun'
            ELSE '4) 90+ gun'
        END AS dpd_dilimi,
        card_id,
        ekstre_id,
        eksik_odeme_tl
    FROM geciken
    WHERE dpd >= 1
)
SELECT
    dpd_dilimi,
    COUNT(DISTINCT card_id) AS kart_sayisi,
    COUNT(*) AS geciken_ekstre,
    ROUND(SUM(eksik_odeme_tl), 2) AS toplam_eksik_odeme_tl,
    ROUND(
        100.0 * SUM(eksik_odeme_tl)
        / NULLIF(SUM(SUM(eksik_odeme_tl)) OVER (), 0),
        1
    ) AS pay_yuzde
FROM dpd_gruplari
GROUP BY dpd_dilimi
ORDER BY dpd_dilimi;
