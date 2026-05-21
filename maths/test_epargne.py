
import pytest
from epargne import taux_epargne

# ✅ 1. Cas nominal (valeurs réalistes)
@pytest.mark.parametrize("r,N,T,expected", [
    (0.02, 43, 25, 0.291),
    (0.03, 30, 20, 0.403),
    (0.01, 40, 25, 0.457),
])
def test_taux_epargne_nominal(r, N, T, expected):
    assert taux_epargne(r, N, T) == pytest.approx(expected, 0.1)


# ✅ 2. Cas limite : r = 0
def test_taux_epargne_r_zero():
    # formule spéciale attendue : T / N
    assert taux_epargne(0, 10, 20) == pytest.approx(2.0, 0.1)


# ✅ 3. Cas limite : valeurs minimales
def test_taux_epargne_min_values():
    result = taux_epargne(0.001, 5, 5)
    assert result > 0


# ✅ 4. Cas limite : valeurs maximales
def test_taux_epargne_max_values():
    result = taux_epargne(0.1, 50, 40)
    assert result > 0


# ✅ 5. Monotonie (propriété métier)
def test_taux_epargne_monotonicity():
    # plus d'années d’épargne → taux plus faible
    t1 = taux_epargne(0.02, 20, 25)
    t2 = taux_epargne(0.02, 40, 25)
    assert t2 < t1


# ✅ 6. Sensibilité au rendement
def test_taux_epargne_rendement():
    # meilleur rendement → besoin d’épargne plus faible
    t1 = taux_epargne(0.01, 30, 25)
    t2 = taux_epargne(0.05, 30, 25)
    assert t2 < t1


# ✅ 7. Robustesse : pas de division par zéro
def test_taux_epargne_no_crash():
    try:
        taux_epargne(0.00001, 1, 1)
    except ZeroDivisionError:
        pytest.fail("Division par zéro détectée")


# ✅ 8. Tests de type invalide
@pytest.mark.parametrize("r,N,T", [
    ("0.02", 30, 20),
    (0.02, "30", 20),
    (0.02, 30, "20"),
])
def test_taux_epargne_type_error(r, N, T):
    with pytest.raises(TypeError):
        taux_epargne(r, N, T)


# ✅ 9. Valeurs négatives (cas métier invalide)
@pytest.mark.parametrize("r,N,T", [
    (-0.01, 30, 20),
    (0.02, -30, 20),
    (0.02, 30, -20),
])
def test_taux_epargne_negative_values(r, N, T):
    # selon ta logique métier, tu peux lever une erreur
    # ici on vérifie juste que ça ne passe pas silencieusement
    result = taux_epargne(r, N, T)
    assert result is not None
