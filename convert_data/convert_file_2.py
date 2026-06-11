import pandas as pd
import os
import random
import param 
import query

nb_valid = 0
nb_errors = 0

# === CHARGEMENT DE LA SOURCE ===

def load_data() -> pd.DataFrame:
    """Charge les données selon le mode défini dans param.DATA_SOURCE."""

    if param.DATA_SOURCE == "sql":
        print("🔌 Mode SQL activé")
        gp_sql    = ", ".join(f"'{v}'" for v in param.GroupeProduit)
        cn_sql    = ", ".join(f"'{v}'" for v in param.CodeNoeud)
        sql_query = query.load_sql_file(
            param.SQL_FILE_PATH,
            gp_sql=gp_sql,
            cn_sql=cn_sql
        )
        return query.get_data_from_bdd_msql(param.SQL_SERVER, param.SQL_DATABASE, sql_query)

    elif param.DATA_SOURCE == "csv":
        print("📄 Mode CSV activé")
        return query.get_data_from_csv(param.CSV_SOURCE_PATH)

    else:
        print(f"❌ DATA_SOURCE invalide : '{param.DATA_SOURCE}' (attendu : 'sql' ou 'csv')")
        return pd.DataFrame()


# === FONCTIONS UTILITAIRES ===

def map_priority(groupe_produit: str) -> int:
    """Retourne 1 si le groupe produit est prioritaire, sinon 2."""
    return 1 if str(groupe_produit).strip() in param.PRIORITY_1_GROUPS else 2


def map_orientation(orientation: str) -> str:
    """Mappe l'orientation brute vers le format cible. Retourne 'error' si non trouvée."""
    if pd.isna(orientation) or str(orientation).strip() == "":
        return "error"
    return param.ORIENTATION_MAP.get(str(orientation).strip(), "error")

def map_weight(poids) -> float:
    """Retourne un poids aléatoire entre 0.5 et 2.0 si poids <= 0, sinon retourne le poids."""
    try:
        p = float(poids)
        if p <= 0:
            return round(random.uniform(param.DEFAULT_WEIGHT_MIN, param.DEFAULT_WEIGHT_MAX), 2)
        return p
    except (ValueError, TypeError):
        return round(random.uniform(param.DEFAULT_WEIGHT_MIN, param.DEFAULT_WEIGHT_MAX), 2)

def map_stackable(dessus) -> bool:
    """Retourne True si DESSUS == 1, False sinon."""
    try:
        return int(dessus) == 1
    except (ValueError, TypeError):
        return False

df_source = load_data()
print(df_source.dtypes)

if df_source.empty:
    print("❌ Données vides, arrêt du programme.")
    exit(1)

# Vérification des colonnes attendues
expected_cols = [
    "CodeNoeud", "Id", "GroupeProduit",
    "Dimension1Emballe", "Dimension2Emballe", "Dimension3Emballe",
    "Poids", "Orientations", "NumeroAR",
    "DESSOUS", "DESSUS", "Designation", "SemaineLivraison"
]
missing_cols = [c for c in expected_cols if c not in df_source.columns]
if missing_cols:
    print(f"❌ Colonnes manquantes dans le fichier source : {missing_cols}")
    exit(1)

print(f"✅ {len(df_source)} lignes lues.")

# === GROUPEMENT PAR SEMAINE ET CODENOEUD ===
groups = df_source.groupby(["SemaineLivraison", "CodeNoeud"])

for (semaine, code_noeud), df_group in groups:

    semaine    = str(semaine).strip()
    code_noeud = str(code_noeud).strip()

    # --- Dossier de sortie par semaine ---
    semaine_folder = os.path.join(param.OUTPUT_FOLDER, semaine)
    os.makedirs(semaine_folder, exist_ok=True)

    # --- Nom du fichier de sortie ---
    output_filename = f"{semaine}_{code_noeud}_1_colis.csv"
    full_path_out   = os.path.join(semaine_folder, output_filename)

    # --- Construction du DataFrame de sortie ---
    df_out = pd.DataFrame()

    df_out["id"]                   = df_group["Id"].str.strip()
    df_out["priority"]             = df_group["GroupeProduit"].apply(map_priority)
    df_out["length"]               = pd.to_numeric(df_group["Dimension1Emballe"], errors="coerce") / 10
    df_out["width"]                = pd.to_numeric(df_group["Dimension2Emballe"], errors="coerce") / 10
    df_out["height"]               = pd.to_numeric(df_group["Dimension3Emballe"], errors="coerce") / 10
    df_out["weight"]               = df_group["Poids"].apply(map_weight)
    df_out["allowed_orientations"] = df_group["Orientations"].apply(map_orientation)
    df_out["client_id"]            = df_group["NumeroAR"].str.strip()
    df_out["stackable"]            = df_group["DESSUS"].apply(map_stackable)
    df_out["designation"]          = df_group["Designation"].fillna("").str.strip()
    df_out["location"]             = ""

    # --- Export CSV ---
    df_out.to_csv(full_path_out, sep=";", index=False)
    nb_valid += 1

    # --- Logs d'erreurs ---
    has_error = False

    if (df_out["allowed_orientations"] == "error").any():
        nb_errors += 1
        has_error = True
        print(f"⚠️  ORIENTATION manquante dans : {output_filename}")

    if df_out[["length", "width", "height"]].isnull().any().any():
        nb_errors += 1
        has_error = True
        print(f"⚠️  DIMENSION nulle/invalide dans : {output_filename}")

    if not has_error:
        print(f"✅ Fichier généré : {semaine}/{output_filename}")

# === RÉSUMÉ ===
print()
print("=" * 50)
print(f"📁 Fichiers générés  : {nb_valid}")
print(f"⚠️  Erreurs détectées : {nb_errors}")
print("=" * 50)