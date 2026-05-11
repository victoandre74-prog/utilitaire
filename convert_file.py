import pandas as pd
import os.path

#=== CHEMIN ===
input_folder = r"input"
output_folder= r"output"

DEFAULT_WEIGHT = 1.0
nb_empty = 0
nb_valid = 0

list = os.listdir(input_folder)
nb_files = len(list)
print(f"Nombre de fichiers dans le dossier : {nb_files}")

# === MATRICE DES ORIENTATIONS ===
ORIENTATION_MAP = {
    "HxL,LxH":"HLW,LHW",
    "HxW,WxH":"HWL,WHL",
    "WxL,LxW":"WLH,LWH",
    "HxW,WxH,HxL,LxH":"HWL,WHL,HLW,LHW",
    "HxL,LxH,HxW,WxH":"HWL,WHL,HLW,LHW",
    "HxW,WxH,WxL,LxW":"HWL,WHL,WLH,LWH",
    "WxL,LxW,HxW,WxH":"HWL,WHL,WLH,LWH",
    "WxL,LxW,HxL,LxH":"WLH,LWH,HLW,LHW",
    "HxL,LxH,WxL,LxW":"WLH,LWH,HLW,LHW",
    "HxW,WxH,HxL,LxH,WxL,LxW":"all",
    "HxW,WxH,WxL,LxW,HxL,LxH":"all",
    "HxL,LxH,WxL,LxW,HxW,WxH":"all",
    "HxL,LxH,HxW,WxH,WxL,LxW":"all",
    "WxL,LxW,HxW,WxH,HxL,LxH":"all",
    "WxL,LxW,HxL,LxH,HxW,WxH":"all",
}

# === DICTIONNAIRE DE MATCH PRIORITE ===
p_matrice = pd.read_csv("matrice_priority.csv",sep=";",header=None)
priority_map = dict(zip(p_matrice[0], p_matrice[1]))
                    

for i in range(0,nb_files):
    # === FICHIERS ===
    INPUT_FILE = list[i]
    OUTPUT_FILE = INPUT_FILE

    # === LECTURE DU FICHIER ===
    full_path_in = os.path.join(input_folder, INPUT_FILE)
    
    # === GESTION DES FICHIERS VIDE ===
    if os.path.getsize(full_path_in) == 0:
        print (f"Fichier vide ignorée : {INPUT_FILE}")
        nb_empty += 1 
        continue
    
    df = pd.read_csv(full_path_in, sep=";", header=None)

 
    # === CONSTRUCTION DU FICHIER===
    df_out = pd.DataFrame({
        "id": df[1],
        "priority": df[1].map(priority_map).fillna("error"),
        "length": df[5] / 10,
        "width": df[6] / 10,
        "height": df[7] / 10,
        "weight": df[8].where(df[8] > 0, DEFAULT_WEIGHT),
        "allowed_orientations": df[4].map(ORIENTATION_MAP).fillna("error"),
        "client_id": df[0],
        "stackable": df[10].apply(lambda x: True if x == 1 else False)
    })

    # Colonnes optionnelles 
    df_out["designation"] = ""
    df_out["location"] = ""

    # === EXPORT ===
    full_path_out = os.path.join(output_folder, OUTPUT_FILE)
    df_out.to_csv(full_path_out, sep=";", index=False)


    if (df_out["priority"] == "error").any():
        print(f"ERROR priority manquante dans le fichier : {INPUT_FILE}")

    if (df_out["allowed_orientations"] == "error").any():
        print(f"ERROR orientation manquante dans le fichier : {INPUT_FILE}")

    nb_valid +=1
    #print(f"✅ Fichier généré : {OUTPUT_FILE}")
print(f"Nombre de fichiers vides : {nb_empty}")
print(f"Nombre de fichiers crées : {nb_valid}")