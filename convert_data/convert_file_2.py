import pandas as pd
import os
import random

# === CHEMINS ===
input_folder = r"input"
output_folder = r"output"

DEFAULT_WEIGHT_MIN = 0.5
DEFAULT_WEIGHT_MAX = 2.0

nb_empty = 0
nb_valid = 0
nb_errors = 0

# === GROUPES PRODUITS PRIORITÉ 1 ===
PRIORITY_1_GROUPS = {
    'F00358', 'F00360', 'F00370', 'F00380', 'F00390', 'F00391',
    'F00392', 'F00393', 'F00394', 'F00395', 'F00396', 'F00400', 'F00LT3'
}

# === MATRICE DES ORIENTATIONS ===
ORIENTATION_MAP = {
    "HxL,LxH": "HLW,LHW",
    "HxW,WxH": "HWL,WHL",
    "WxL,LxW": "WLH,LWH",
    "HxW,WxH,HxL,LxH": "HWL,WHL,HLW,LHW",
    "HxL,LxH,HxW,WxH": "HWL,WHL,HLW,LHW",
    "HxW,WxH,WxL,LxW": "HWL,WHL,WLH,LWH",
    "WxL,LxW,HxW,WxH": "HWL,WHL,WLH,LWH",
    "WxL,LxW,HxL,LxH": "WLH,LWH,HLW,LHW",
    "HxL,LxH,WxL,LxW": "WLH,LWH,HLW,LHW",
    "HxW,WxH,HxL,LxH,WxL,LxW": "all",
    "HxW,WxH,WxL,LxW,HxL,LxH": "all",
    "HxL,LxH,WxL,LxW,HxW,WxH": "all",
    "HxL,LxH,HxW,WxH,WxL,LxW": "all",
    "WxL,LxW,HxW,WxH,HxL,LxH": "all",
    "WxL,LxW,HxL,LxH,HxW,WxH": "all",
}


# === FONCTIONS UTILITAIRES ===

def map_priority(groupe_produit: str) -> int:
    """Retourne 1 si le groupe produit est prioritaire, sinon 2."""
    return 1 if str(groupe_produit).strip() in PRIORITY_1_GROUPS else 2


def map_orientation(orientation: str) -> str:
    """Mappe l'orientation brute vers le format cible. Retourne 'error' si non trouvée."""
    if pd.isna(orientation) or str(orientation).strip() == "":
        return "error"
    return ORIENTATION_MAP.get(str(orientation).strip(), "error")

def map_weight(poids) -> float:
    """Retourne un poids aléatoire entre 0.5 et 2.0 si poids <= 0, sinon retourne le poids."""
    try:
        p = float(poids)
        if p <= 0:
            return round(random.uniform(DEFAULT_WEIGHT_MIN, DEFAULT_WEIGHT_MAX), 2)
        return p
    except (ValueError, TypeError):
        return round(random.uniform(DEFAULT_WEIGHT_MIN, DEFAULT_WEIGHT_MAX), 2)

def map_stackable(dessus) -> bool:
    """Retourne True si DESSUS == 1, False sinon."""
    try:
        return int(dessus) == 1
    except (ValueError, TypeError):
        return False


# === LECTURE DU FICHIER SOURCE ===
source_files = [f for f in os.listdir(input_folder) if f.endswith(".csv")]

if not source_files:
    print("❌ Aucun fichier CSV trouvé dans le dossier input.")
    exit(1)

SOURCE_FILE = source_files[0]
full_path_source = os.path.join(input_folder, SOURCE_FILE)

print(f"📂 Lecture du fichier source : {SOURCE_FILE}")

df_source = pd.read_csv(full_path_source, sep=";", dtype=str)

# Nettoyage des espaces dans les noms de colonnes
df_source.columns = df_source.columns.str.strip()

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
    semaine_folder = os.path.join(output_folder, semaine)
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
    df_out["client_id"]            = df_group["CodeNoeud"].str.strip()
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