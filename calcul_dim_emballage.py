# ─── Constantes ───────────────────────────────────────────────────────────────

LARGEUR_LAIZE_MAX = 1860

# ─── Modèle de données ────────────────────────────────────────────────────────

from dataclasses import dataclass

@dataclass
class Meuble:
    L013: str   # ID
    L024: str   # Dim 1 carton si spécifiée (KIT)
    L025: str   # Dim 2 carton si spécifiée (KIT)
    L026: str   # Dim 3 carton si spécifiée (KIT)
    L042: str   # Code Poignée
    L125: str   # Modèle Technique façade
    L135: str   # Code Option 1
    L137: str   # Code Option 2
    L139: str   # Code Option 3
    L141: str   # Code Option 4
    L170: str   # Type Meuble
    L171: str   # Sous-Type Meuble
    L172: str   # Ligne Deco
    L173: str   # Flag Kit
    L271: str   # Code Descripteur
    L317: int   # Hauteur meuble (dixièmes de mm)
    L318: int   # Largeur meuble (dixièmes de mm)
    L319: int   # Profondeur meuble (dixièmes de mm)

@dataclass
class DimensionsCarton:
    hauteur:    int
    largeur:    int
    profondeur: int

# ─── Fonctions utilitaires ────────────────────────────────────────────────────

def correction_ligne_deco(ligne_deco: str) -> str:
    """S9V est un alias de SP4."""
    return "SP4" if ligne_deco == "S9V" else ligne_deco

def est_kit(meuble: Meuble) -> bool:
    """Un meuble est en KIT si L271='51043' ou L173='O'."""
    return meuble.L271 in ("51043",) or meuble.L173 == "O"

def epaisseur_facade(meuble: Meuble) -> int:
    """
    Calcule l'épaisseur de façade (mm) selon le modèle technique (L125).
    Cette épaisseur est ensuite ajoutée à la profondeur du carton. [1]
    """
    m = meuble.L125
    if m in ("ME13", "ME04"):
        return 22 + 3 + 2       # cadre alu 22mm + 3mm protection + 2mm butée
    elif m == "ME11":
        return 20 + 3 + 2       # cadre alu 20mm + 3mm protection + 2mm butée
    elif m in ("RC12", "BC27"):
        return 20 + 2           # façade 20mm + 2mm butée
    elif m in ("BC26", "LA00", "LA34", "LA13", "PF50"):
        return 19 + 2           # façade 19mm + 2mm butée
    elif m in ("SP", "SAV", "") and meuble.L170 in ("HA", "BA") and meuble.L171 == "ANG":
        return 18 + 2           # meuble d'angle sans porte → épaisseur std
    elif m in ("SP", "SAV", ""):
        return 0                # sans porte → pas de façade
    else:
        return 18 + 2           # façade STD + 2mm butée

def est_poignee_contour(code_poignee: str) -> bool:
    """Détecte si le meuble a une poignée contour."""
    return code_poignee in ("560", "168", "255", "134")

# ─── Calcul principal ─────────────────────────────────────────────────────────

def calculer_dimensions_carton(meuble: Meuble) -> DimensionsCarton:
    """
    Calcule les dimensions du carton (Hauteur / Largeur / Profondeur) en mm
    à partir des données du meuble. [1]
    """

    # Correction ligne déco
    meuble.L172 = correction_ligne_deco(meuble.L172)

    # Dimensions brutes : dixièmes de mm → mm [1]
    H = meuble.L317 // 10
    L = meuble.L318 // 10
    P = meuble.L319 // 10

    kit        = est_kit(meuble)
    ep_facade  = epaisseur_facade(meuble)
    table_extra = len(meuble.L271) >= 9 and meuble.L271[6:9] == "103"
    options    = {meuble.L135, meuble.L137, meuble.L139, meuble.L141}
    pgncontour = est_poignee_contour(meuble.L042)

    # ── Meuble NON KIT ────────────────────────────────────────────────────────
    if not kit:

        # ── Ajustements Hauteur ───────────────────────────────────────────────

        # Meubles bas avec pieds (BA/BN/BS/BE) [1]
        if (meuble.L170 in ("BA", "BN", "BS", "BE")
                and meuble.L171 not in ("PON", "PCO", "TED", "TEG")
                and L > 150
                and not table_extra
                and not (meuble.L170 == "BA"
                         and meuble.L171 == "ANG"
                         and meuble.L172 == "SP4")):
            H += 25

        # Armoires avec pieds (AR/AI) [1]
        elif (meuble.L170 in ("AR", "AI")
              and meuble.L171 not in ("SLV",)
              and P > 340 and L >= 400):
            H += 25
            if meuble.L317 // 10 >= 1380:   # renforts pour grandes armoires
                H += 4

        # Meubles rideau / sur plan (RI/PT) [1]
        elif meuble.L170 in ("RI", "PT"):
            grand_meuble = (
                (meuble.L317 >= 13510 and 4000 <= meuble.L319 < 5000)
                or (meuble.L317 >= 12130 and meuble.L319 >= 5000)
            )
            if not grand_meuble:
                H += 3      # protection isogyl

        # Meubles hauts sur plan (HP) [1]
        elif meuble.L170 == "HP":
            if not (meuble.L317 >= 12290 and meuble.L319 >= 5000):
                H += 3

        # SULV : bac de rétention [1]
        if meuble.L170 == "AR" and meuble.L171 == "SUP":
            if 1380 < meuble.L317 <= 2760:
                if meuble.L125 != "SAV":
                    H = H - 138 + 70 + 3
                else:
                    H -= 138
            elif meuble.L317 > 2760:
                if meuble.L125 != "SAV":
                    H = H - 138 + ep_facade + 15 + 3
                else:
                    H -= 138

        # Hottes intégrées HIN [1]
        if meuble.L170 == "HA" and meuble.L171 == "HIN":
            if "CH" in options:
                H += 40 + 3     # polystyrène + isogyl
            if "CF" in options:
                H += 3          # isogyl seul

        # Hottes standard HOT [1]
        if meuble.L170 == "HA" and meuble.L171 == "HOT":
            if options & {"CA", "C4", "C5"}:
                H += 40 + 3

        # Fonds éclairants LFE [1]
        if meuble.L171 == "LFE":
            H += 3

        # ── Ajustements Profondeur ────────────────────────────────────────────

        if meuble.L171 not in ("APC", "ARE"):
            P += ep_facade
            if pgncontour:
                # Poignée contour : on annule l'épaisseur façade et on ajoute 30mm [1]
                P = P - ep_facade + 20 + 10

        # Bas d'angle : cale retour partie fixe (+80mm) [1]
        if meuble.L170 == "BA" and meuble.L171 == "ANG":
            poignees_speciales = {"087", "167", "264", "265", "880"}
            if (meuble.L042 in poignees_speciales
                    or meuble.L125 in ("PF11", "SF03")
                    or meuble.L172 == "SP4"):
                if meuble.L271[:3] != "629":    # exclure partie fixe assortie e629
                    P += 80
                    P = min(P, 650)             # plafond expédition

        # ── Surcotes de confort (+10mm partout, +5mm sur largeur) [1] ────────
        H += 10
        L += 10 + 5
        P += 10

    # ── Meuble KIT ────────────────────────────────────────────────────────────
    else:
        d1 = int(meuble.L024 or 0)
        d2 = int(meuble.L025 or 0)
        d3 = int(meuble.L026 or 0)

        if d1 and d2 and d3:
            # Dimensions fournies dans la fiche article [1]
            H, L, P = d1 // 10, d2 // 10, d3 // 10
        else:
            # Valeurs par défaut selon le sous-type [1]
            if meuble.L170 == "BA" and meuble.L171 in ("ARE", "APC"):
                H, L, P = 880, 880, 375
            else:
                H, L, P = 50, 50, 50   # valeurs à ajuster

    return DimensionsCarton(hauteur=H, largeur=L, profondeur=P)


# ─── Exemple d'utilisation ────────────────────────────────────────────────────

if __name__ == "__main__":
    meuble_test = Meuble(
        L013="ID001",
        L024="0", L025="0", L026="0",
        L042="000",
        L125="",            # façade STD
        L135="", L137="", L139="", L141="",
        L170="BA",          # meuble bas
        L171="LIN",         # linéaire
        L172="SP4",
        L173="N",           # pas un KIT
        L271="000000000",
        L317=7200,          # 720mm de haut (en dixièmes)
        L318=6000,          # 600mm de large
        L319=5800,          # 580mm de profond
    )

    dims = calculer_dimensions_carton(meuble_test)
    print(f"Hauteur carton    : {dims.hauteur} mm")
    print(f"Largeur carton    : {dims.largeur} mm")
    print(f"Profondeur carton : {dims.profondeur} mm")