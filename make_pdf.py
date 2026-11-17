import sqlite3
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image

pdfmetrics.registerFont(TTFont("DV", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DVB", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
from reportlab.pdfbase.pdfmetrics import registerFontFamily
registerFontFamily("DV", normal="DV", bold="DVB", italic="DV", boldItalic="DVB")

con = sqlite3.connect("banka_demo.db")
q = lambda f, p=None: pd.read_sql_query(open(f"sql/{f}").read(), con, params=p or {})
limit = q("01_limit_kullanim_uyarisi.sql", {"esik": 0.80})
dpd = q("02_gecikme_dpd_analizi.sql", {"as_of": "2025-06-30"})
dq = q("03_veri_kalitesi_kontrolleri.sql")

# Grafik
fig, ax = plt.subplots(1, 2, figsize=(9, 3.2))
risk = limit.risk_seviyesi.value_counts().reindex(["UYARI", "KRITIK", "LIMIT ASIMI"]).fillna(0)
ax[0].bar(["Uyarı\n(%80-90)", "Kritik\n(%90-100)", "Limit aşımı"], risk.values, color=["#E8B84B", "#E07B39", "#B23A3A"])
ax[0].set_title("Limit kullanım riski (kart adedi)", fontsize=10)
ax[1].bar([s.split(") ")[1].replace(" gun", " gün") for s in dpd.dpd_dilimi], dpd.toplam_eksik_odeme_tl / 1000, color="#3B6EA8")
ax[1].set_title("DPD dilimlerine göre eksik ödeme (bin TL)", fontsize=10)
for a in ax:
    a.spines[["top", "right"]].set_visible(False)
plt.tight_layout(); plt.savefig("output/grafik.png", dpi=170); plt.close()

H = ParagraphStyle("H", fontName="DVB", fontSize=11, spaceBefore=10, spaceAfter=4, textColor=colors.HexColor("#1F3A5F"))
B = ParagraphStyle("B", fontName="DV", fontSize=9, leading=13)
T = ParagraphStyle("T", fontName="DVB", fontSize=16, leading=22, spaceAfter=4, textColor=colors.HexColor("#1F3A5F"))
S = ParagraphStyle("S", fontName="DV", fontSize=9, textColor=colors.grey, spaceAfter=6)

kritik = int((limit.risk_seviyesi != "UYARI").sum())
story = [
    Paragraph("Kredi Kartı Risk İzleme – Proje Özeti", T),
    Paragraph("Sentetik veri ile hazırlanmış demo proje | SQL · Python · Otomatik raporlama", S),
    Paragraph("Problem", H),
    Paragraph("Risk ve operasyon ekipleri limitine yaklaşan veya ödemesini geciktiren müşterileri manuel kontrol etmek zorunda kalır. "
              "Bu proje kontrolü SQL tabanlı bir job ile otomatikleştirir; sonucu Excel ve HTML mail olarak iletir.", B),
    Paragraph("Yaklaşım", H),
    Paragraph("• <b>Limit uyarısı:</b> Kullanım oranı %80+ kartlar; uyarı / kritik / limit aşımı sınıflaması, segment içi sıralama (RANK).<br/>"
              "• <b>Gecikme (DPD):</b> Asgari ödemesi yapılmamış ekstreler 1-29 / 30-59 / 60-89 / 90+ gün dilimlerinde.<br/>"
              "• <b>Veri kalitesi:</b> Mükerrer, eksik, negatif ve geçersiz limit kayıtlarının tespiti.<br/>"
              "• <b>Şüpheli işlem:</b> Kart ortalamasının 8 katını aşan işlemler (pencere fonksiyonu).<br/>"
              "• <b>Otomasyon:</b> Python + pandas ile Excel (4 sayfa) ve HTML mail üretimi, SMTP ile gönderim.", B),
    Paragraph("Sonuçlar (sentetik veri, 2.015 kart)", H),
    Paragraph(f"%80 ve üzeri limit kullanan <b>{len(limit)}</b> kart tespit edildi; bunların <b>{kritik}</b> tanesi kritik veya limit aşımında. "
              f"Gecikmeli ekstrelerde toplam eksik ödeme <b>{dpd.toplam_eksik_odeme_tl.sum():,.0f} TL</b>.".replace(",", "."), B),
    Spacer(1, 6),
    Image("output/grafik.png", width=17 * cm, height=6 * cm),
]

rows = [["Veri kalitesi kontrolü", "Adet"]] + [[r.kontrol, str(r.adet)] for r in dq.itertuples()]
t = Table(rows, colWidths=[12 * cm, 3 * cm])
t.setStyle(TableStyle([("FONT", (0, 0), (-1, 0), "DVB", 8.5), ("FONT", (0, 1), (-1, -1), "DV", 8.5),
                       ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E6ECF4")),
                       ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey), ("ALIGN", (1, 0), (1, -1), "RIGHT")]))
story += [Paragraph("Veri kalitesi kontrol özeti", H), t,
          Paragraph("Teknik detaylar, kod ve çalıştırma adımları için GitHub deposuna bakınız: <b>[GITHUB-LINKINIZ]</b>", 
                    ParagraphStyle("F", parent=B, spaceBefore=10))]
SimpleDocTemplate("Proje_Ozeti.pdf", pagesize=A4, leftMargin=2*cm, rightMargin=2*cm, topMargin=1.8*cm, bottomMargin=1.5*cm).build(story)
print("ok")
