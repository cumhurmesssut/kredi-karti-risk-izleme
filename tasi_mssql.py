import sqlite3
import urllib.parse
import pandas as pd
from sqlalchemy import create_engine

SUNUCU = r".\SQLEXPRESS"          # Express kullanıyorsan: "localhost\\SQLEXPRESS"
VERITABANI = "BankaDemo"

baglanti = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    f"SERVER={SUNUCU};"
    f"DATABASE={VERITABANI};"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)
engine = create_engine(
    "mssql+pyodbc:///?odbc_connect=" + urllib.parse.quote_plus(baglanti),
    fast_executemany=True,
)

src = sqlite3.connect("banka_demo.db")
for tablo in ["customers", "cards", "ekstreler", "transactions"]:
    df = pd.read_sql_query(f"SELECT * FROM {tablo}", src)
    for kolon in df.columns:
        if kolon.endswith("tarihi"):
            df[kolon] = pd.to_datetime(df[kolon])
    df.to_sql(tablo, engine, if_exists="replace", index=False)
    print(tablo, len(df), "satır yüklendi")