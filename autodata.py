import pandas as pd
import sqlite3
import json

df = pd.read_csv("TieliikenneAvoinData_31_12_2025.csv", encoding='ANSI', sep=";", decimal=",")
df.columns = df.columns.str.strip()
conn = sqlite3.connect("autodata.db")
df.to_sql('autodata_all', conn, if_exists='replace')


cur = conn.cursor()

cur.execute("""DELETE FROM autodata_all WHERE ajoneuvoluokka NOT IN ('M1','M1G')""")
conn.commit()
cur.execute("""DELETE FROM autodata_all WHERE ajoneuvonkaytto NOT IN (1.0)""")
conn.commit()
cur.execute("""DELETE FROM autodata_all WHERE korityyppi NOT IN ('AA', 'AB', 'AC', 'AD', 'AE', '1.7')""")
conn.commit()
cur.execute("""DELETE FROM autodata_all WHERE kayttovoima IS NULL""")
conn.commit()

cur.execute("""DROP TABLE IF EXISTS autodata""")
cur.execute("""CREATE TABLE autodata AS SELECT ensirekisterointipvm, kayttoonottopvm, vari, omamassa, ajonKokPituus, ajonLeveys, kayttovoima, merkkiSelvakielinen, mallimerkinta, kaupallinenNimi, kunta, NEDC_Co2, matkamittarilukema FROM autodata_all""")
conn.commit()

with open("kuntarajat2.json", "r", encoding="utf-8") as f:
    kunnat_json = json.load(f)

kuntien_nimet = []

for feature in kunnat_json["features"]:
    kunta = feature["properties"]

    kunta_id = int(kunta["NATCODE"])
    kunta_name = kunta["NAMEFIN"]

    kuntien_nimet.append((kunta_name, kunta_id))

cur.executemany("""UPDATE autodata SET kunta = ? WHERE CAST(kunta as INTEGER) = ?""", kuntien_nimet)
cur.execute("DELETE FROM autodata WHERE kunta IS NULL")
conn.commit()
cur.execute("DELETE FROM autodata WHERE kunta NOT GLOB '[^0-9]*'")
conn.commit()

cur.execute("""UPDATE autodata SET kayttoonottopvm = CAST(REPLACE(CAST(kayttoonottopvm AS TEXT), '0000', '0101') AS INTEGER) WHERE CAST(kayttoonottopvm AS TEXT) LIKE '%0000'""")
conn.commit()
cur.execute("""UPDATE autodata SET ensirekisterointipvm = substr(ensirekisterointipvm, 7, 4) ||'-'|| substr(ensirekisterointipvm, 4, 2) ||'-'||substr(ensirekisterointipvm, 1, 2) WHERE ensirekisterointipvm LIKE '__.__.____'""")
conn.commit()
cur.execute("""UPDATE autodata SET kayttoonottopvm = substr(CAST(kayttoonottopvm AS TEXT), 1, 4) ||'-'|| substr(CAST(kayttoonottopvm AS TEXT), 5, 2) ||'-'|| substr(CAST(kayttoonottopvm AS TEXT), 7, 2) WHERE CAST(kayttoonottopvm AS TEXT) GLOB '[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]'""")
conn.commit()
cur.execute("""DELETE FROM autodata WHERE date(kayttoonottopvm) IS NULL OR date(ensirekisterointipvm) IS NULL""")
conn.commit()
cur.execute("""UPDATE autodata SET ensirekisterointipvm = ensirekisterointipvm WHERE length(ensirekisterointipvm) = 10 AND date(ensirekisterointipvm) IS NOT NULL""")
conn.commit()

cur.execute("""UPDATE autodata SET NEDC_Co2 = 0 WHERE kayttovoima = '4.0'""")
conn.commit()

cur.execute("""UPDATE autodata SET vari = 'pd.NA' WHERE vari = '-1'""")
conn.commit()


cur.execute("""UPDATE autodata SET merkkiSelvakielinen = 'Chrysler' WHERE kaupallinenNimi IN ('SEBRING', 'CROSSFIRE')""")
conn.commit()
cur.execute("""UPDATE autodata SET merkkiSelvakielinen = 'Jaguar' WHERE kaupallinenNimi IN ('XJ') OR merkkiSelvakielinen IN ('Daimler')""")
conn.commit()

name_changes  = {
    "QUATTRO": "Audi",
    "Quattro": "Audi",

    "ALPINA": "BMW",
    "Alpina": "BMW",
    "BMW Alpina": "BMW",
    "BMW i": "BMW",
    "BWW": "BMW",

    "GM Daewoo": "Daewoo",

    "FORD-CNG-TECHNIK": "Ford",
    "Ford-TEC": "Ford",

    "Hundai": "Hyundai",

    "Jaguar Land Rover Limited": "Jaguar",

    "Lada-Vaz": "Lada",

    "DaimlerChrysler": "Mercedes-Benz", 
    "Daimler": "Mercedes-benz",
    "MERCEDES-AMG": "Mercedes-Benz",
    "Mercedes-Benz-CI": "Mercedes-Benz",

    "BMW MINI": "BMW",

    "POLESTAR": "Polestar",

    "SALEEN": "Saleen",

    "SKD": "Skoda",
    "Skida": "Skoda",

    "TESLA MOTORS": "Tesla",
    "Tesla Motors": "Tesla",

    "THINK": "Think",

    "TOYOTA": "Toyota",

    "VOLKSWAGEN": "Volkswagen",
    "VW": "Volkswagen",
    "Volkswagen, VW": "Volkswagen"
}

for old, new in name_changes.items():
    cur.execute("""UPDATE autodata SET merkkiSelvakielinen =? WHERE TRIM(merkkiSelvakielinen) =?""", (new, old))
conn.commit()

cur.execute("""SELECT merkkiSelvakielinen, COUNT(*) AS count FROM autodata GROUP BY merkkiSelvakielinen ORDER BY merkkiSelvakielinen""")
for brand, count in cur.fetchall():
    print(brand, count)
#Tarvittaessa voi lisätä sanakirjaan lisää

kayttovoima_changes = [
    ("01", "1.0"),
    ("02", "2.0"),
    ("04", "4.0"),
    ("05", "5.0"),
    ("06", "6.0"),
    ("13", "13.0"),
    ("33", "33.0"),
    ("34", "34.0"),
    ("37", "37.0"),
    ("38", "38.0"),
    ("39", "39.0"),
    ("40", "40.0"),
    ("41", "41.0"),
    ("42", "42.0"),
    ("43", "43.0"),
    ("44", "44.0"),
    ("48", "48.0"),
    ("49", "49.0"),
    ("61", "61.0"),
    ("63", "63.0"),
]
cur.executemany("""
    UPDATE autodata
    SET kayttovoima = ?
    WHERE kayttovoima = ?
""", kayttovoima_changes) 
conn.commit()

cur.execute("""DROP TABLE IF EXISTS autodata_all""")
conn.commit()

conn.close()

