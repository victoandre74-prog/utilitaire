
import pyodbc

try:
    conn = pyodbc.connect(
        'DRIVER={SQL Server Native Client 11.0};'
        'SERVER=10.24.10.114,1433;'
        'Trusted_Connection=yes;'
    )

    print("✅ Connexion réussie (sans DB)")

    conn.close()

except Exception as e:
    print("❌ Connexion refusée")
    print(e)
