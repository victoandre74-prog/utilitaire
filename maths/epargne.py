import math

# while True:
#     ├── try:
#     │     ├── input
#     │     ├── conversion
#     │     └── test intervalle
#     │         ├── OK → return → FIN
#     │         └── KO → print → REBOUCLE
#     │
#     └── except:
#           print → REBOUCLE

def demander_valeur(message, min_valeur, max_valeur, type_val=float):
    
    while True:
        try: 
            val = type_val(input(message))
            if min_valeur <= val <= max_valeur:
                return val
            else:
                print("Valeur non accepteé")
        except ValueError:
            print(f"Saisisez un nombre de type {type_val.__name__} ")

if __name__=="__main__":
    rendement = demander_valeur("Entrez rendement rélle (nombre décimal entre 0.001 et 0.1) : ", 0.001, 0.1, float)
    annees_epargne = demander_valeur("Entrez nombre d'années de travail (nombre entier entre 5 et 50) : ", 5, 50, int)
    annees_retraites = demander_valeur("Entrez nombre années passées à la retraite (nombre entier entre 5 et  40) ",5 , 40, int)

def taux_epargne (r, N, T):
    """
    r : rendement réelle 
    N : années d'épargne
    T : années de retraite

    """
    numerateur = 1 - (1+r)**(-T)
    denominateur = (1+r)**N - 1
    return round(numerateur/denominateur,8)

if __name__=="__main__":
    print(taux_epargne (rendement, annees_epargne, annees_retraites))

