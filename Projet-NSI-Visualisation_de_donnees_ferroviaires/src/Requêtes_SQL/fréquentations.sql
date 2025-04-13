SELECT g.nom AS "gare", f.fréquentation / 365 AS "fréquentation par jour"
FROM frequentations f
JOIN trigrammes tr ON tr.uic_code = f.uic_code
JOIN gares g ON g.trigramme = tr.trigramme
WHERE f.année == 2022;

