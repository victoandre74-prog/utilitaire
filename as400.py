
import pyodbc
import pandas as pd

# 🔐 Connexion
conn = pyodbc.connect(
    "DSN=Commercial;"
    "UID=vandre;"
    "PWD=Fournier01"
)

cursor = conn.cursor()

# 🎯 paramètres
#groupes = ('F00390','F00380')

# ✅ requête (identique)
query = f"""
WITH CombinedData AS (
    SELECT LCCSTE, LCNRAR, LCNRLI, LCREFC, LCRTEC, LCQUTE
	FROM MOBGC.LIGCO2
	UNION ALL
	SELECT LCCSTE, LCNRAR, LCNRLI, LCREFC, LCRTEC, LCQUTE
	FROM MOBGC.HSTLG2
)
SELECT DISTINCT
	cd.LCCSTE CodeSociete,
	cd.LCNRAR NumeroAR,
	cd.LCNRLI NumeroLigne,
	j.HLNSEQ NumeroSequ,
	cd.LCREFC RefCom, 
	cd.LCRTEC RefTech,
	gpp.ARGRFS GroupeProduit,
	cd.LCQUTE Quantite,
	en.GCSL SLCommande,
	j.HLSELI SLjalonne,
	gpp.ARHAUT Hauteur, 
	gpp.ARLARG Largeur,
	gpp.ARPROF Profondeur,
	gpp.ARPOID Poids,
	gpp.ARTYPM Type, 
	gpp.ARSTYP SousType
FROM 
CombinedData cd
LEFT JOIN MOGPIF.GPPF11 Gpp ON gpp.ARRTEC=cd.LCRTEC
LEFT JOIN MOLOIF.JALHISP j ON cd.LCCSTE=j.HLCSTE and cd.LCNRAR=j.HLNRAR and cd.LCNRLI=j.HLNRLI
LEFT JOIN
	(
	SELECT GCCSTE, GCNRAR, GCCINS, GCSL
	FROM MOBGC.GDECOM
	UNION ALL
	SELECT GCCSTE, GCNRAR, GCCINS, GCSL
	FROM MOBGC.HSTGDE
	) en ON  en.GCCSTE=cd.LCCSTE AND en.GCNRAR =cd.LCNRAR
WHERE gpp.ARGRFS IN ('EXPCOL', 'F00358', 'F00360', 'F00370','F00380', 'F00390', 'F00391', 'F00392', 'F00393', 'F00394', 'F00395',
'F00396', 'F00400', 'F0040P', 'F00LT3', 'F01294', 'F01297', 'F02100', 'F02101', 'F02120', 'F09400',
'FSR133', 'P00021', 'P00022', 'P00023', 'P00024', 'P00025', 'P00026', 'P09410', 'P09450') AND en.GCSL = '202605' AND cd.LCCSTE = '1'
"""

# ✅ RECUP DATA
df= pd.read_sql_query(query, conn)
df.columns = df.columns.str.strip().str.lower()

df["volume m3"] = (df["hauteur"]*df["largeur"]*df["profondeur"])/1e6
# ✅ EXPORT
df.to_excel("export.xlsx", index=False)

# ✅ FERMETURE
cursor.close()
conn.close()

print("✅ Export OK")
