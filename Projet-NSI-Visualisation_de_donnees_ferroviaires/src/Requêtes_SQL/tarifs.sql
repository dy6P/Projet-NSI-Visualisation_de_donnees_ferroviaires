SELECT (ta.prix_minimum + ta.prix_maximum) / 2 AS "prix moyen", g_o.nom AS "origine", g_d.nom AS "destination", ta.transporteur
FROM tarifs ta
JOIN trigrammes tr_o ON tr_o.uic_code = ta.uic_origine
JOIN trigrammes tr_d ON tr_d.uic_code = ta.uic_destination
JOIN gares g_o ON g_o.trigramme = tr_o.trigramme
JOIN gares g_d ON g_d.trigramme = tr_d.trigramme;