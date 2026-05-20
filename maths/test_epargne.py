from epargne import taux_epargne

def test_taux_epargne ():
    t = taux_epargne (0.02,43,25)
    assert t == 0.291