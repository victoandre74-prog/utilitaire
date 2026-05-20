# =============================================================================
# CALCUL DES DIMENSIONS DE CARTON D'EMBALLAGE - MEUBLES FOURNIER
# =============================================================================
# Ce script reproduit la logique métier de la procédure stockée SQL Server
# [dlc].[usp_traiter_donnees_interface_n3_n2].
#
# Principe général :
#   - On part des dimensions BRUTES du meuble (en dixièmes de mm)
#   - On applique une série d'ajustements selon le TYPE de meuble,
#     ses OPTIONS, et son MODE de fabrication (KIT ou normal)
#   - On retourne les dimensions finales du CARTON en mm
#
# Deux grandes branches de traitement :
#   1. Meuble NORMAL  → ajustements complexes H/L/P
#   2. Meuble KIT     → dimensions lues depuis la fiche article
# =============================================================================

from dataclasses import dataclass


# =============================================================================
# CONSTANTES MÉTIER
# =============================================================================

LARGEUR_LAIZE_MAX = 1860
# Largeur maximale de la laize (rouleau de carton) en mm.
# Au-delà, la machine Biele ne peut pas produire le carton.

RABAT_ENCOLLAGE = 50
# Dimension fixe du rabat d'encollage en mm (constante métier).

SURCOTE_CONFORT_H = 10
# Surcote de confort appliquée sur la hauteur du carton (mm).
# Référence : mail Mathieu du jeudi 18/02. [1]

SURCOTE_CONFORT_L = 15
# Surcote de confort appliquée sur la largeur du carton (+10mm + 5mm). [1]

SURCOTE_CONFORT_P = 10
# Surcote de confort appliquée sur la profondeur du carton (mm). [1]

SURCOTE_PIED = 25
# Hauteur ajoutée au carton pour les meubles équipés de pieds (mm). [1]

SURCOTE_RENFORT_ARMOIRE = 4
# Hauteur ajoutée pour les renforts des grandes armoires (H >= 1380mm). [1]

SURCOTE_ISOGYL = 3
# Protection isogyl ajoutée sous certains meubles (rideau, plan, LFE...) en mm. [1]


# =============================================================================
# MODÈLE DE DONNÉES
# =============================================================================

@dataclass
class Meuble:
    """
    Représente un meuble tel qu'il arrive depuis la table INTERFACE_N3_N2.
    Chaque champ correspond à une colonne du CSV / de la table SQL.

    Nommage : les champs Lxxx reprennent exactement les noms de colonnes SQL
    pour faciliter la traçabilité avec le script d'origine.
    """
    L013: str   # Identifiant unique de la ligne (clé de traitement)
    L024: str   # Dim 1 du carton (renseignée uniquement pour les KITs)
    L025: str   # Dim 2 du carton (renseignée uniquement pour les KITs)
    L026: str   # Dim 3 du carton (renseignée uniquement pour les KITs)
    L042: str   # Code poignée (ex: '560' = poignée contour)
    L125: str   # Modèle technique de la façade (ex: 'ME13', 'SP', 'SAV'...)
    L135: str   # Code option 1 (ex: 'CH' = cheminée hotte, 'CF' = filtre...)
    L137: str   # Code option 2
    L139: str   # Code option 3
    L141: str   # Code option 4
    L170: str   # Type de meuble  (ex: 'BA'=bas, 'AR'=armoire, 'RI'=rideau...)
    L171: str   # Sous-type de meuble (ex: 'LIN'=linéaire, 'ANG'=angle...)
    L172: str   # Ligne déco (ex: 'SP4', 'S9V'...)
    L173: str   # Flag KIT : 'O' = oui, 'N' = non
    L271: str   # Code descripteur (contient des infos fonctionnelles encodées)
    L317: int   # Hauteur du meuble en DIXIÈMES de mm  (ex: 7200 = 720mm)
    L318: int   # Largeur du meuble en DIXIÈMES de mm  (ex: 6000 = 600mm)
    L319: int   # Profondeur du meuble en DIXIÈMES de mm (ex: 5800 = 580mm)


@dataclass
class DimensionsCarton:
    """
    Résultat du calcul : dimensions finales du carton d'emballage en mm.
    Ces valeurs sont transmises à la machine Biele sous les paramètres H, L, B.
    """
    hauteur:    int     # Paramètre H (hauteur du carton en mm)
    largeur:    int     # Paramètre L (largeur du carton en mm)
    profondeur: int     # Paramètre B (profondeur/épaisseur du carton en mm)


# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def correction_ligne_deco(ligne_deco: str) -> str:
    """
    Corrige la ligne déco avant traitement.
    'S9V' est un alias obsolète de 'SP4' et doit être remplacé
    pour que les conditions métier fonctionnent correctement. [1]
    """
    return "SP4" if ligne_deco == "S9V" else ligne_deco


def est_kit(meuble: Meuble) -> bool:
    """
    Détermine si un meuble est en mode KIT.
    Un meuble est KIT si :
      - Son code descripteur L271 vaut '51043' (code article KIT spécifique)
      - OU si le flag L173 est explicitement à 'O' (Oui)

    Les meubles KIT ont leurs dimensions carton pré-définies dans la fiche
    article (L024/L025/L026) et ne suivent pas les calculs standards. [1]
    """
    return meuble.L271 in ("51043",) or meuble.L173 == "O"


def epaisseur_facade(meuble: Meuble) -> int:
    """
    Calcule l'épaisseur totale de la façade en mm selon le modèle technique (L125).

    Cette valeur est AJOUTÉE à la profondeur du carton car la façade dépasse
    la caisse du meuble et doit être protégée dans l'emballage.

    Composition de l'épaisseur :
      - Épaisseur physique de la façade (varie selon le modèle)
      - + 2mm de butée de façade (jeu mécanique)
      - + 3mm de protection (film isogyl) pour certains modèles alu

    Référence modèles :
      ME13 / ME04 → cadre aluminium 22mm  → total 27mm [1]
      ME11        → cadre aluminium 20mm  → total 25mm [1]
      RC12 / BC27 → façade panneaux 20mm  → total 22mm [1]
      BC26 / LA00 / LA34 / LA13 / PF50 → façade 19mm → total 21mm [1]
      SP / SAV / '' → sans porte          → total  0mm [1]
      Autre (STD)   → façade standard 18mm → total 20mm [1]
    """
    m = meuble.L125

    if m in ("ME13", "ME04"):
        # Façade à cadre alu épaisseur 22mm + 3mm protection iso + 2mm butée
        return 22 + 3 + 2

    elif m == "ME11":
        # Façade à cadre alu épaisseur 20mm + 3mm protection iso + 2mm butée
        return 20 + 3 + 2

    elif m in ("RC12", "BC27"):
        # Façade panneau 20mm + 2mm butée (pas de protection iso)
        return 20 + 2

    elif m in ("BC26", "LA00", "LA34", "LA13", "PF50"):
        # Façade panneau 19mm + 2mm butée
        return 19 + 2

    elif m in ("SP", "SAV", "") and meuble.L170 in ("HA", "BA") and meuble.L171 == "ANG":
        # Meuble d'angle (HA ou BA) déclaré sans porte :
        # on applique quand même l'épaisseur STD car il y a une partie fixe
        return 18 + 2

    elif m in ("SP", "SAV", ""):
        # Sans porte (SP) ou SAV : aucune façade → épaisseur nulle
        return 0

    else:
        # Façade standard (modèle non listé) + 2mm butée
        return 18 + 2


def est_poignee_contour(code_poignee: str) -> bool:
    """
    Détecte si le meuble est équipé d'une poignée de type 'contour'.
    Les poignées contour ont un profil qui enveloppe la façade, ce qui modifie
    le calcul de profondeur du carton (on ne compte plus l'épaisseur de façade
    mais on ajoute 30mm spécifiques à ce type de poignée). [1]

    Codes poignées contour : '560', '168', '255', '134'
    """
    return code_poignee in ("560", "168", "255", "134")


# =============================================================================
# CALCUL PRINCIPAL DES DIMENSIONS
# =============================================================================

def calculer_dimensions_carton(meuble: Meuble) -> DimensionsCarton:
    """
    Calcule les dimensions finales (H/L/P) du carton d'emballage pour un meuble.

    Logique générale :
      1. Conversion des dimensions brutes (dixièmes mm → mm)
      2. Détermination du mode de traitement (KIT ou normal)
      3. Application des ajustements métier selon le type de meuble
      4. Retour des dimensions finales

    Paramètre  : meuble (Meuble) → données brutes du meuble
    Retour     : DimensionsCarton → hauteur / largeur / profondeur en mm
    """

    # ── Correction de la ligne déco avant tout traitement ────────────────────
    meuble.L172 = correction_ligne_deco(meuble.L172)

    # ── Conversion des dimensions brutes : dixièmes de mm → mm ───────────────
    # Les dimensions stockées en base sont en dixièmes de mm (format U4/PLM).
    # Ex : L317 = 7200 → 720mm de hauteur [1]
    H = meuble.L317 // 10
    L = meuble.L318 // 10
    P = meuble.L319 // 10

    # ── Pré-calculs des flags ─────────────────────────────────────────────────

    kit = est_kit(meuble)
    # Indique si le meuble suit la logique KIT (dims depuis fiche article)

    ep_facade = epaisseur_facade(meuble)
    # Épaisseur de façade à ajouter à la profondeur du carton

    table_extra = len(meuble.L271) >= 9 and meuble.L271[6:9] == "103"
    # Détecte les meubles 'table extractible' via la fonction ext 103
    # encodée en position 7-9 du code descripteur L271.
    # Ces meubles n'ont pas d'embase de pied montée → pas de surcote pied. [1]

    options = {meuble.L135, meuble.L137, meuble.L139, meuble.L141}
    # Ensemble des 4 codes options du meuble, permet de tester
    # rapidement la présence d'une option (ex: "CH" in options)

    pgncontour = est_poignee_contour(meuble.L042)
    # True si le meuble a une poignée contour → modifie le calcul profondeur


    # =========================================================================
    # BRANCHE 1 : MEUBLE NORMAL (non KIT)
    # =========================================================================
    if not kit:

        # ── AJUSTEMENTS DE HAUTEUR ────────────────────────────────────────────
        #
        # La hauteur du carton est la dimension la plus impactée car elle dépend
        # fortement de la présence ou non de pieds, de protections spéciales,
        # ou de composants supplémentaires (bac SULV, hotte, etc.).

        # CAS 1 : Meubles bas avec pieds (types BA / BN / BS / BE)
        # On ajoute 25mm pour l'embase des pieds sous le meuble. [1]
        # Exclusions :
        #   - Sous-types PON/PCO/TED/TEG → pas de pieds
        #   - Largeur ≤ 150mm            → trop étroit pour des pieds
        #   - Table extractible (ext103)  → embase pied non montée
        #   - BA ANG SP4                 → angle sans pied (cas particulier)
        if (meuble.L170 in ("BA", "BN", "BS", "BE")
                and meuble.L171 not in ("PON", "PCO", "TED", "TEG")
                and L > 150
                and not table_extra
                and not (meuble.L170 == "BA"
                         and meuble.L171 == "ANG"
                         and meuble.L172 == "SP4")):
            H += SURCOTE_PIED

        # CAS 2 : Armoires avec pieds (types AR / AI)
        # Condition de présence de pieds : prof > 340mm ET largeur ≥ 400mm. [1]
        # Les armoires étroites ou peu profondes n'ont pas de pieds.
        elif (meuble.L170 in ("AR", "AI")
              and meuble.L171 not in ("SLV",)
              and P > 340 and L >= 400):
            H += SURCOTE_PIED

            # Renforts supplémentaires pour les très grandes armoires (H ≥ 1380mm)
            if meuble.L317 // 10 >= 1380:
                H += SURCOTE_RENFORT_ARMOIRE

        # CAS 3 : Meubles rideau (RI) et meubles sur plan (PT)
        # Une protection isogyl de 3mm est ajoutée sous le meuble. [1]
        # EXCEPTION : les "grands meubles" (très hauts ET très profonds)
        # ont un traitement différent (rabat spécifique) → pas de +3mm ici.
        elif meuble.L170 in ("RI", "PT"):
            grand_meuble = (
                # Grand meuble rideau : H ≥ 1351mm ET profondeur 400-499mm
                (meuble.L317 >= 13510 and 4000 <= meuble.L319 < 5000)
                # Grand meuble sur plan prof 580 : H ≥ 1213mm ET prof ≥ 500mm
                or (meuble.L317 >= 12130 and meuble.L319 >= 5000)
            )
            if not grand_meuble:
                H += SURCOTE_ISOGYL

        # CAS 4 : Meubles hauts sur plan (HP)
        # Même logique que RI/PT pour les grands meubles. [1]
        elif meuble.L170 == "HP":
            grand_meuble = (meuble.L317 >= 12290 and meuble.L319 >= 5000)
            if not grand_meuble:
                H += SURCOTE_ISOGYL

        # ── CAS SPÉCIAL : SULV (bac de rétention liquide) ────────────────────
        # Les armoires SULV (AR + SUP) intègrent un bac de rétention.
        # Selon la hauteur du meuble, le bac est soit POSÉ SUR le meuble
        # (H ≤ 2760), soit INTÉGRÉ DANS le meuble (H > 2760). [1]
        # Dans les deux cas on retire 138mm (1 pas de hauteur) et on rajoute
        # les compensations nécessaires.
        if meuble.L170 == "AR" and meuble.L171 == "SUP":

            if 1380 < meuble.L317 <= 2760:
                # Bac posé sur le meuble → retrait 1 pas + surcote bac + isogyl
                if meuble.L125 != "SAV":
                    # Avec façade : +70mm (surcote bac) + 3mm protection isogyl
                    H = H - 138 + 70 + 3
                else:
                    # SAV = sans façade, sans bac → seulement le retrait du pas
                    H -= 138

            elif meuble.L317 > 2760:
                # Bac intégré dans le meuble → retrait 1 pas
                # + épaisseur façade + crochet 15mm + isogyl [1]
                if meuble.L125 != "SAV":
                    H = H - 138 + ep_facade + 15 + 3
                else:
                    H -= 138

        # ── CAS SPÉCIAL : Hottes intégrées (HA + HIN) ────────────────────────
        # Les hottes intégrées nécessitent des protections supplémentaires
        # selon les options montées. [1]
        if meuble.L170 == "HA" and meuble.L171 == "HIN":
            if "CH" in options:
                # Option cheminée (CH) : polystyrène 40mm + isogyl 3mm
                H += 40 + 3
            if "CF" in options:
                # Option filtre (CF) : isogyl 3mm uniquement
                H += SURCOTE_ISOGYL

        # ── CAS SPÉCIAL : Hottes standard (HA + HOT) ─────────────────────────
        # Options CA / C4 / C5 = hotte avec cheminée → +40mm + isogyl. [1]
        if meuble.L170 == "HA" and meuble.L171 == "HOT":
            if options & {"CA", "C4", "C5"}:
                H += 40 + 3

        # ── CAS SPÉCIAL : Fonds éclairants (LFE) ─────────────────────────────
        # Protection isogyl systématique de 3mm pour les fonds éclairants. [1]
        if meuble.L171 == "LFE":
            H += SURCOTE_ISOGYL


        # ── AJUSTEMENTS DE PROFONDEUR ─────────────────────────────────────────
        #
        # La profondeur du carton doit intégrer l'épaisseur de la façade
        # qui dépasse de la caisse du meuble.

        # Ajout de l'épaisseur façade (sauf pour les angles APC et ARE
        # qui ont une géométrie particulière et pas de façade frontale). [1]
        if meuble.L171 not in ("APC", "ARE"):
            P += ep_facade

            # CAS POIGNÉE CONTOUR : la poignée enveloppe la façade,
            # on annule l'épaisseur façade et on applique 30mm fixes
            # (20mm std + 10mm spécifique poignée contour). [1]
            if pgncontour:
                P = P - ep_facade + 20 + 10

        # CAS SPÉCIAL : Bas d'angle (BA + ANG) avec retour de partie fixe
        # Certaines configurations d'angle nécessitent une cale de 80mm
        # pour le retour de la partie fixe. [1]
        # Poignées concernées : P28 (087), Mercure (167), 264, 265, 880
        # Modèles concernés  : PF11, SF03, ou ligne déco SP4
        if meuble.L170 == "BA" and meuble.L171 == "ANG":
            poignees_speciales = {"087", "167", "264", "265", "880"}
            if (meuble.L042 in poignees_speciales
                    or meuble.L125 in ("PF11", "SF03")
                    or meuble.L172 == "SP4"):

                # Exclusion de la partie fixe assortie e629
                # (FFI de largeur 646mm → code descripteur commence par '629') [1]
                if meuble.L271[:3] != "629":
                    P += 80     # ajout épaisseur cale retour partie fixe

                    # Plafond à 650mm pour contrainte d'expédition [1]
                    P = min(P, 650)


        # ── SURCOTES DE CONFORT FINALES ───────────────────────────────────────
        # Appliquées en dernier, sur toutes les dimensions,
        # pour garantir un jeu suffisant autour du meuble dans le carton.
        # Référence : mail Mathieu du 18/02. [1]
        # Note : ces surcotes ne s'appliquent PAS aux meubles KIT.
        H += SURCOTE_CONFORT_H      # +10mm en hauteur
        L += SURCOTE_CONFORT_L      # +15mm en largeur (+10 + 5)
        P += SURCOTE_CONFORT_P      # +10mm en profondeur


    # =========================================================================
    # BRANCHE 2 : MEUBLE KIT
    # =========================================================================
    else:
        # Pour les meubles KIT, les dimensions du carton sont définies
        # directement dans la fiche article (champs L024 / L025 / L026).
        # Ces valeurs sont aussi en dixièmes de mm. [1]

        d1 = int(meuble.L024 or 0)  # Dim 1 (hauteur carton KIT)
        d2 = int(meuble.L025 or 0)  # Dim 2 (largeur carton KIT)
        d3 = int(meuble.L026 or 0)  # Dim 3 (profondeur carton KIT)

        if d1 and d2 and d3:
            # Les 3 dimensions sont renseignées → on les utilise directement
            H, L, P = d1 // 10, d2 // 10, d3 // 10

        else:
            # Dimensions non renseignées → valeurs par défaut selon le sous-type
            if meuble.L170 == "BA" and meuble.L171 in ("ARE", "APC"):
                # KIT bas d'angle : dimensions fixes connues
                H, L, P = 880, 880, 375
            else:
                # Cas non géré / données manquantes → valeurs minimales
                # ⚠ Ces valeurs (50mm) sont des placeholders à ajuster
                H, L, P = 50, 50, 50


    # =========================================================================
    # RETOUR DU RÉSULTAT
    # =========================================================================
    return DimensionsCarton(hauteur=H, largeur=L, profondeur=P)


# =============================================================================
# EXEMPLE D'UTILISATION
# =============================================================================

if __name__ == "__main__":

    # Exemple : meuble bas linéaire de 720mm de haut, 600mm de large, 580mm de prof
    meuble_test = Meuble(
        L013 = "ID001",
        L024 = "0", L025 = "0", L026 = "0",  # pas de dims KIT
        L042 = "000",                          # pas de poignée contour
        L125 = "",                             # façade standard STD (→ 20mm)
        L135 = "", L137 = "", L139 = "", L141 = "",  # pas d'options
        L170 = "BA",    # meuble bas
        L171 = "LIN",   # linéaire
        L172 = "SP4",
        L173 = "N",     # pas un KIT
        L271 = "000000000",
        L317 = 7200,    # 720mm de hauteur
        L318 = 6000,    # 600mm de largeur
        L319 = 5800,    # 580mm de profondeur
    )

    dims = calculer_dimensions_carton(meuble_test)

    print("=" * 40)
    print("  DIMENSIONS DU CARTON D'EMBALLAGE")
    print("=" * 40)
    print(f"  Hauteur    (H) : {dims.hauteur} mm")
    print(f"  Largeur    (L) : {dims.largeur} mm")
    print(f"  Profondeur (P) : {dims.profondeur} mm")
    print("=" * 40)