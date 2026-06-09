import pyodbc
import pandas as pd

def get_data_from_bdd_msql(server, database, query) -> pd.DataFrame :

    conn = None

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

        df= pd.read_sql_query(query, conn)
        df.columns = df.columns.str.strip().str.lower()
        
        return df
    
    except Exception as e:
        print("❌ Connexion refusée")
        print("Erreur:", e)


if __name__ == "__main__":
    server = "10.24.10.114,1433"   # IMPORTANT : virgule et non ":"
    database = "FOURNIER-HUB"
    query = "SELECT * FROM your_table"

    df = get_data_from_bdd_msql(server, database, query)
    print(df)   