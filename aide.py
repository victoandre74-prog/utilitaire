import pandas as pd
import os.path


#=== CHEMIN ===
input_folder = r"utilitaire\input"
output_folder= r"utilitaire\output"

list = os.listdir(input_folder)
nb_files = len(list)
print(list[1])

.where(df[8] > 0, DEFAULT_WEIGHT)