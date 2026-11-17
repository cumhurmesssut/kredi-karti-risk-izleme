"""Günlük kredi kartı risk raporu: SQL'leri çalıştırır, Excel + HTML mail üretir.
Varsayılan DRY-RUN'dır (mail göndermez). Göndermek için --send ve SMTP_* ortam değişkenleri gerekir.
"""
import argparse
import os
import smtplib
import sqlite3
from email.message import EmailMessage
from pathlib import Path

import pandas as pd

BASE = Path(__file__).parent
SQL_DIR = BASE / "sql"
OUT_DIR = BASE / "output"


def run_sql(con, filename, params=None):
    sql = (SQL_DIR / filename).read_text(encoding="utf-8")
    return pd.read_sql_query(sql, con, params=params or {})


def build_html(limit_df, dpd_df, dq_df, as_of, esik):
    kritik = limit_df[limit_df.risk_seviyesi != "UYARI"]
    ozet = (f"<p><b>{as_of}</b> itibarıyla limit kullanımı %{int(esik*100)} ve üzeri olan "
            f"<b>{len(limit_df)}</b> kart var; bunların <b>{len(kritik)}</b> tanesi kritik/limit aşımı.</p>")
    return f"""<html><body style="font-family:Arial,sans-serif">
<h2>Kredi Kartı Risk İzleme - Günlük Rapor</h2>{ozet}
<h3>En yüksek riskli 10 kart</h3>{limit_df.head(10).to_html(index=False, border=0)}
<h3>Gecikme (DPD) dağılımı</h3>{dpd_df.to_html(index=False, border=0)}
<h3>Veri kalitesi kontrolleri</h3>{dq_df.to_html(index=False, border=0)}
<p style="color:#888">Bu rapor sentetik veri ile üretilmiştir.</p></body></html>"""


def send_mail(html, xlsx_path, subject):
    msg = EmailMessage()
    msg["Subject"], msg["From"], msg["To"] = subject, os.environ["MAIL_FROM"], os.environ["MAIL_TO"]
    msg.set_content("HTML görüntüleyen bir mail istemcisi gerekir.")
    msg.add_alternative(html, subtype="html")
    msg.add_attachment(xlsx_path.read_bytes(), maintype="application",
                       subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       filename=xlsx_path.name)
    with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.environ.get("SMTP_PORT", 587))) as s:
        s.starttls()
        s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
        s.send_message(msg)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--as-of", default="2025-06-30")
    ap.add_argument("--esik", type=float, default=0.80)
    ap.add_argument("--send", action="store_true", help="Maili gerçekten gönder")
    args = ap.parse_args()

    OUT_DIR.mkdir(exist_ok=True)
    with sqlite3.connect(BASE / "banka_demo.db") as con:
        limit_df = run_sql(con, "01_limit_kullanim_uyarisi.sql", {"esik": args.esik})
        dpd_df = run_sql(con, "02_gecikme_dpd_analizi.sql", {"as_of": args.as_of})
        dq_df = run_sql(con, "03_veri_kalitesi_kontrolleri.sql")
        sus_df = run_sql(con, "04_supheli_islem_kurali.sql")

    xlsx = OUT_DIR / f"risk_raporu_{args.as_of}.xlsx"
    with pd.ExcelWriter(xlsx, engine="openpyxl") as w:
        limit_df.to_excel(w, sheet_name="Limit Uyarilari", index=False)
        dpd_df.to_excel(w, sheet_name="DPD Dagilimi", index=False)
        dq_df.to_excel(w, sheet_name="Veri Kalitesi", index=False)
        sus_df.to_excel(w, sheet_name="Supheli Islemler", index=False)

    html = build_html(limit_df, dpd_df, dq_df, args.as_of, args.esik)
    (OUT_DIR / "email_onizleme.html").write_text(html, encoding="utf-8")
    print(f"Excel: {xlsx.name} | Limit uyarısı: {len(limit_df)} kart | Şüpheli işlem: {len(sus_df)}")
    print(dpd_df.to_string(index=False))
    print(dq_df.to_string(index=False))

    if args.send:
        send_mail(html, xlsx, f"Kredi Kartı Risk Raporu - {args.as_of}")
        print("Mail gönderildi.")
    else:
        print("DRY-RUN: mail gönderilmedi (--send ile gönderilir). Önizleme: output/email_onizleme.html")


if __name__ == "__main__":
    main()
