import math

a = input("Entrez rendement réelle (entre 0 et 0.08) : ")
b = input("Entrez année de travail/épargne (entre 5 et 60) : ")
c = input("Entrez année à la retraite : ")

def taux_epargne (r, N, T):
    """
    r : rendement réelle 
    N : années d'épargne
    T : années de retraite

    """
    numerateur = 1 - (1+float(r))**(-float(T))
    denominateur = (1+float(r))**float(N) - 1
    return round(numerateur/denominateur,3)


print(taux_epargne (a,b,c))



