# Kredi Kartı Risk İzleme (Demo Proje)

Bir bankanın kredi kartı portföyü için **limit kullanım uyarısı, gecikme (DPD) analizi, veri kalitesi kontrolü
ve basit şüpheli işlem kuralı** üreten, günlük otomatik rapor/mail akışı.

> **Not:** Tüm veriler `generate_data.py` ile üretilmiş **sentetik** veridir. Gerçek müşteri veya kurum verisi içermez.

## Problem
Risk ve operasyon ekipleri, limitine yaklaşan veya ödemesini geciktiren müşterileri her gün manuel kontrol etmek zorunda kalır.
Bu proje, kontrolü SQL tabanlı bir job ile otomatikleştirir ve sonucu Excel + HTML mail olarak iletir.

## Ne yapıyor?
| Modül | Dosya | Teknik |
|---|---|---|
| Limit kullanım uyarısı (%80 / %90 / aşım) | `sql/01_...sql` | CTE, JOIN, CASE, `RANK() OVER (PARTITION BY ...)` |
| Gecikme (DPD) dilimleri: 1-29 / 30-59 / 60-89 / 90+ | `sql/02_...sql` | Tarih farkı, koşullu gruplama, pencere fonksiyonu ile pay hesabı |
| Veri kalitesi kontrolleri | `sql/03_...sql` | Mükerrer tespiti (`ROW_NUMBER`), NULL / orphan / negatif değer kontrolleri |
| Şüpheli işlem kuralı (kart ortalamasının 8 katı) | `sql/04_...sql` | `AVG() OVER (PARTITION BY card_id)` |
| Otomasyon | `run_report.py` | pandas, openpyxl, smtplib (varsayılan dry-run) |

## Çalıştırma
```bash
pip install -r requirements.txt
python generate_data.py        # sentetik veritabanını üretir (banka_demo.db)
python run_report.py           # Excel + HTML mail önizlemesi üretir (output/)
python run_report.py --send    # SMTP_HOST, SMTP_USER, SMTP_PASS, MAIL_FROM, MAIL_TO tanımlıysa maili gönderir
```
Parametreler: `--as-of 2025-06-30` (rapor tarihi), `--esik 0.80` (limit uyarı eşiği).

## Örnek çıktı
`output/risk_raporu_*.xlsx` (4 sayfa) ve `output/email_onizleme.html`.

## Varsayımlar
- Asgari ödeme, ekstre borcunun %20'si kabul edilmiştir.
- DPD, son ödeme tarihi ile rapor tarihi arasındaki gün farkıdır.
- Demo SQLite ile çalışır; sorgular Oracle / SQL Server / Teradata'ya küçük sözdizimi değişiklikleriyle taşınabilir
  (örn. `julianday` farkı yerine `DATEDIFF` veya `tarih - tarih`).

## Geliştirme fikirleri
Power BI dashboard, RFM segmentasyonu, Airflow/Cron ile zamanlama, birim testleri.
