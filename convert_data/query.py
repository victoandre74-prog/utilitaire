import pyodbc
import pandas as pd
import os

def get_data_from_bdd_msql(server, database, query) -> pd.DataFrame:
    conn = None

    try:
        conn = pyodbc.connect(
            'DRIVER={SQL Server Native Client 11.0};'
            f'SERVER={server};'
            f'DATABASE={database};'
            'Trusted_Connection=yes;'
            'Connection Timeout=5;'
        )

        df = pd.read_sql(query, conn)

        # Nettoyage colonnes
        df.columns = df.columns.str.strip()

        print("✅ Connexion réussie")

        return df

    except Exception as e:
        print("❌ Connexion refusée")
        print("Erreur:", e)
        return pd.DataFrame()  # ✅ éviter crash après

    finally:
        # ✅ fermeture sécurisée même si erreur
        if conn:
            conn.close()


if __name__ == "__main__":
    server = "10.24.10.114,1433"
    database = "FOURNIER-HUB"

    query = """
    SELECT DISTINCT TOP 100
        CodeNoeud, 
        CONCAT(
            NumeroAR,
            '009',
            RIGHT('0000' + CAST(NumeroLigneAR AS VARCHAR), 4),
            RIGHT('0000' + CAST(SequenceAR AS VARCHAR), 2)
        ) AS Id,
        GroupeProduit,
        Dimension1Emballe, 
        Dimension2Emballe, 
        Dimension3Emballe,
        Poids,
        Orientations, 
        NumeroAR,
        DESSOUS,
        DESSUS,
        Designation,
        SemaineLivraison 
    FROM [FOURNIER-DWH].u9.Fait_BDD_U9_SL_2024S17_2024S22
    WHERE GroupeProduit IN (
        'EXPCOL', 'F00358', 'F00360', 'F00370','F00380', 'F00390', 'F00391', 
        'F00392', 'F00393', 'F00394', 'F00395','F00396', 'F00400', 'F0040P', 
        'F00LT3', 'F01294', 'F01297', 'F02100', 'F02101', 'F02120', 'F09400',
        'FSR133', 'P00021', 'P00022', 'P00023', 'P00024', 'P00025', 'P00026', 
        'P09410', 'P09450')
        AND CodeNoeud IN ('00092817', '00099900')
    ORDER BY CodeNoeud ASC
    """

    df = get_data_from_bdd_msql(server, database, query)

    if not df.empty:
        #print(df)
        #print(df.shape)
        output_path = os.path.join(os.getcwd(), "test_export.csv")
        df.to_csv(output_path, sep=";", index=False, encoding="utf-8")
        print(f"✅ Export CSV réussi : {output_path}")
    else:
        print("⚠️ Aucun fichier exporté (DataFrame vide)")