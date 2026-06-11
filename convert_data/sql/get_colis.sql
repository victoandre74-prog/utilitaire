SELECT DISTINCT
    CodeNoeud, 
    CONCAT(
        NumeroAR,
        '009',
        RIGHT('0000' + CAST(NumeroLigneAR AS VARCHAR), 4),
        RIGHT('0000' + CAST(SequenceAR AS VARCHAR), 2)
    ) AS Id,
    GroupeProduit,
    Dimension1Emballe, 
    Dimension2Emballe, 
    Dimension3Emballe,
    Poids,
    Orientations, 
    NumeroAR,
    DESSOUS,
    DESSUS,
    Designation,
    SemaineLivraison 
FROM [FOURNIER-DWH].u9.Fait_BDD_U9_SL_2024S17_2024S22
WHERE GroupeProduit IN ({gp_sql})
    AND CodeNoeud IN ({cn_sql})
ORDER BY CodeNoeud ASC