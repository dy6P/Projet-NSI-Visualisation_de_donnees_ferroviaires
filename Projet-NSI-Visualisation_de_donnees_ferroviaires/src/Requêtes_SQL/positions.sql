SELECT g.nom AS "gare", v.ville, g.latitude, g.longitude
FROM gares g
JOIN villes v ON v.insee_code = g.insee_code;
