import pyodbc
import pandas as pd
import os

def load_sql_file(filepath: str, **kwargs) -> str:
    """
    Lit un fichier .sql et remplace les placeholders par les valeurs fournies.
    Exemple : load_sql_file("sql/get_colis.sql", gp_sql="'A','B'", cn_sql="'C'")
    """
    try:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Fichier SQL introuvable : {filepath}")

        with open(filepath, "r", encoding="utf-8") as f:
            sql = f.read()

        # Remplacement des placeholders {gp_sql}, {cn_sql}, etc.
        sql = sql.format(**kwargs)

        return sql

    except KeyError as e:
        raise ValueError(f"Placeholder manquant dans le fichier SQL : {e}")
    except Exception as e:
        raise RuntimeError(f"Erreur lors du chargement du fichier SQL : {e}")


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
        df.columns = df.columns.str.strip()

        # === Normalisation des types SQL → Python ===
        
        # Colonnes entières lues en float → str (identifiants)
        cols_int_to_str = ["NumeroAR", "DESSOUS", "DESSUS"]
        for col in cols_int_to_str:
            if col in df.columns:
                df[col] = df[col].apply(
                    lambda x: str(int(x)) if pd.notna(x) else ""
                )

        # Colonnes entières → int (dimensions, semaine)
        cols_to_int = ["Dimension1Emballe", "Dimension2Emballe", "Dimension3Emballe", "SemaineLivraison"]
        for col in cols_to_int:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

        print("✅ Connexion réussie")
        return df

    except Exception as e:
        print("❌ Connexion refusée")
        print("Erreur:", e)
        return pd.DataFrame()

    finally:
        if conn:
            conn.close()

def get_data_from_csv(filepath: str) -> pd.DataFrame:
    """Charge un fichier CSV depuis le chemin donné."""
    try:
        if not os.path.exists(filepath):
            print(f"❌ Fichier introuvable : {filepath}")
            return pd.DataFrame()

        df = pd.read_csv(filepath, sep=";", encoding="utf-8", dtype=str)
        df.columns = df.columns.str.strip()
        print(f"✅ Fichier CSV chargé : {filepath}")
        return df

    except Exception as e:
        print(f"❌ Erreur lors de la lecture du CSV : {e}")
        return pd.DataFrame()
