import pyodbc
import pandas as pd

def get_data_from_bdd_msql(server, database, sl) -> pd.DataFrame :

    server = "10.24.10.114,1433"   # IMPORTANT : virgule et non ":"
    database = "FOURNIER-HUB"

    conn = None

    sl = sl
    
    try:
        # Connexion SQL Server (authentification Windows)
        conn = pyodbc.connect(
            'DRIVER={SQL Server Native Client 11.0};'
            f'SERVER={server};'
            f'DATABASE={database};'
            'Trusted_Connection=yes;'
            'Connection Timeout=5;'
        )

        print("✅ Connexion réussie")

        # Test requête
        cursor = conn.cursor()
        cursor.execute("SELECT GETDATE()")

        result = cursor.fetchone()
        print("Date serveur :", result[0])

    except Exception as e:
        print("❌ Connexion refusée")
        print("Erreur:", e)

    finally:
        if conn:
            conn.close()
            print("🔌 Déconnexion effectuée")
