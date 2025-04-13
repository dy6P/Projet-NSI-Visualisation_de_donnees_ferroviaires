from math import*
import sqlite3
import folium
from sqlite3 import Error


# Requêtes SQL avec le module sqlite3

conn = sqlite3.connect("Base_de_données.db")
cur = conn.cursor()

# Positions géographiques des gares

cur.execute(""" SELECT g.nom AS "gare", v.ville, g.latitude, g.longitude
                FROM gares g
                JOIN villes v ON v.insee_code = g.insee_code; """)
conn.commit()

positions = []
rows = cur.fetchall()
for r in rows:
    r_2 = []
    for chaine in r:
        if type(chaine) is str:
            chaine = chaine.lower()


        r_2.append(chaine)
    positions.append(list(r_2))

# Fréquentations des gares

cur.execute(""" SELECT g.nom AS "gare", f.fréquentation / 365 AS "fréquentation par jour"
                FROM frequentations f
                JOIN trigrammes tr ON tr.uic_code = f.uic_code
                JOIN gares g ON g.trigramme = tr.trigramme
                WHERE f.année == 2022; """)
conn.commit()

frequentations = []
rows = cur.fetchall()
for r in rows:
    r_2 = []
    for chaine in r:
        if type(chaine) is str:
            chaine = chaine.lower()
        r_2.append(chaine)
    frequentations.append(list(r_2))

# Tarifs des voyages

cur.execute(""" SELECT (ta.prix_minimum + ta.prix_maximum) / 2 AS "prix moyen", g_o.nom, g_d.nom, ta.transporteur
                FROM tarifs ta
                JOIN trigrammes tr_o ON tr_o.uic_code = ta.uic_origine
                JOIN trigrammes tr_d ON tr_d.uic_code = ta.uic_destination
                JOIN gares g_o ON g_o.trigramme = tr_o.trigramme
                JOIN gares g_d ON g_d.trigramme = tr_d.trigramme; """)
conn.commit()

tarifs = []
rows = cur.fetchall()
for r in rows:
    r_2 = []
    for chaine in r:
        if type(chaine) is str:
            chaine = chaine.lower()
        r_2.append(chaine)
    tarifs.append(list(r_2))

conn.close()


# Création d'une classe graphe pour représenter les voyages de chaque transporteur

class Graphe_ferroviaire:

    def __init__(self, transporteur, calque):
        self._gares = {}
        self._transporteur = transporteur
        self._calque = calque

    def get_gares(self):
        return self._gares

    def ajouter_gares(self):
        for l in positions:
            if l[0] not in self._gares:
                self._gares[l[0]] = {}

    def ajouter_trajets(self):
        for l in tarifs:
            if l[3] in self._transporteur:
                self._gares[l[1]][l[2]] = l[0]

    def dijkstra(self, origine):
        prix = {gare: float('infinity') for gare in self._gares}
        prix[origine] = 0
        predecesseurs = {gare: None for gare in self._gares}
        gares_non_visites = self._gares.copy()
        while gares_non_visites:
            gare_courante = min(gares_non_visites, key=lambda gare: prix[gare])
            del gares_non_visites[gare_courante]
            for voisin, poids in self._gares[gare_courante].items():
                prix_alternatif = prix[gare_courante] + poids
                if prix_alternatif < prix[voisin]:
                    prix[voisin] = prix_alternatif
                    predecesseurs[voisin] = gare_courante
        return prix, predecesseurs

    def calcul_prix(self, A, B):
        return self.dijkstra(A)[0][B]

    def calcul_itineraire(self, A, B):
        predecesseurs = self.dijkstra(A)[1]
        itineraire = []
        gare_courante = B
        while gare_courante is not None:
            itineraire.insert(0, gare_courante)
            gare_courante = predecesseurs[gare_courante]
        return itineraire

    def gares_trajet(self, A, B):
        gares_origine = []
        gares_destination = []
        candidats_gares = []
        candidats_tarifs = []
        for l in positions:
            if l[0] in self._gares and l[1] == A and not l[0] in gares_origine:
                gares_origine.append(l[0])
            if l[0] in self._gares and l[1] == B and not l[0] in gares_destination:
                gares_destination.append(l[0])
        for g_o in gares_origine:
            for g_d in gares_destination:
                candidats_gares.append([g_o, g_d])
                candidats_tarifs.append(self.calcul_prix(g_o, g_d))
                candidats_gares.append([g_d, g_o])
                candidats_tarifs.append(self.calcul_prix(g_d, g_o))
        indice = candidats_tarifs.index(min(candidats_tarifs))
        return self.calcul_itineraire(candidats_gares[indice][0], candidats_gares[indice][1])

    def affichage_gares_origine_destination(self):
        for l in positions:
            if l[0] in gares_trajet and l[0] == gares_trajet[0] or l[0] == gares_trajet[- 1]:
                folium.Marker(
                    [l[2], l[3]],
                    popup = "{} ({} personnes par jour)".format(l[0], self.frequentations_trajet()[l[0]])
                    ).add_to(self._calque)

    def affichage_lignes_trajet(self):
        for g in range(len(gares_trajet) - 1):
            if gares_trajet[g + 1] is not None:
                g_o = gares_trajet[g]
                g_d = gares_trajet[g + 1]
                for l in positions:
                    if l[0] == g_o:
                        c_o = [l[2], l[3]]
                    if l[0] == g_d:
                        c_d = [l[2], l[3]]
                for l in tarifs:
                    if g_o == l[1] and g_d == l[2] and l[3] in self._transporteur:
                        folium.PolyLine(
                            locations = (c_o, c_d),
                            color = "red",
                            weight = 4,
                            popup = "tarif moyen = {} euros".format(self.calcul_prix(g_o, g_d))
                            ).add_to(self._calque)

    def affichage_gares_trajet(self):
        for l in positions:
            if l[0] in gares_trajet and l[0] != gares_trajet[0] and l[0] != gares_trajet[- 1]:
                folium.Marker(
                    [l[2], l[3]],
                    popup = "{} ({} personnes par jour)".format(l[0], self.frequentations_trajet()[l[0]])
                    ).add_to(self._calque)

    def affichage_ligne_totale(self):
        for l in positions:
            if l[0] == gares_trajet[0]:
                c_o = [l[2], l[3]]
            if l[0] == gares_trajet[- 1]:
                c_d = [l[2], l[3]]
        if len(gares_trajet) > 1:
            folium.PolyLine(
                locations = (c_o, c_d),
                color = "magenta",
                weight = 4,
                popup = "coût total moyen = {} euros".format(self.calcul_prix(gares_trajet[0], gares_trajet[- 1]))
                ).add_to(self._calque)

    def frequentations_trajet(self):
        f = {}
        for l in frequentations:
            if l[0] in gares_trajet:
                f[l[0]] = l[1]
        return f


def ville_origine():
    stop = False
    ville_origine = input("Ville de départ -> ")
    ville_origine = ville_origine.lower()
    for l in positions:
        if l[1] == ville_origine:
            stop = True
    while not stop:
        ville_origine = input("Ville de départ -> ")
        for l in positions:
            if l[1] == ville_origine:
                stop = True
    return ville_origine

def ville_destination():
    stop = False
    ville_destination = input("Ville d'arrivée -> ")
    ville_destination = ville_destination.lower()
    for l in positions:
        if l[1] == ville_destination:
            stop = True
    while not stop:
        ville_destination = input("Ville d'arrivée -> ")
        for l in positions:
            if l[1] == ville_destination:
                stop = True
    return ville_destination

def coordonnees_milieu():
    for l in positions :
        if l[1] == ville_origine:
            o_latitude = l[2]
            o_longitude = l[3]
        if l[1] == ville_destination:
            d_latitude = l[2]
            d_longitude = l[3]
    return [(o_latitude + d_latitude)/2, (o_longitude + d_longitude)/2]


# Choix du départ et de l'arrivée

ville_origine = ville_origine()
ville_destination = ville_destination()

# Création de la carte et de ses différents calques

transporteurs_France = folium.Map(location = coordonnees_milieu(), zoom_start = 7)
origine_destination = folium.FeatureGroup(name="GARES ORIGINE-DESTINATION", control = False).add_to(transporteurs_France)
tgv_inoui = folium.FeatureGroup(name="Trajet TGV INOUI", show = False).add_to(transporteurs_France)
ouigo = folium.FeatureGroup(name="Trajet OUIGO", show = False).add_to(transporteurs_France)
total_tgv_inoui = folium.FeatureGroup(name="TOTAL TGV INOUI").add_to(transporteurs_France)
total_ouigo = folium.FeatureGroup(name="TOTAL OUIGO", show = False).add_to(transporteurs_France)

# Instanciation des différents transporteurs en France

France_origine_destination = Graphe_ferroviaire(["tgv inoui", "ouigo", "ouigo train classique"], origine_destination)
France_tgv_inoui = Graphe_ferroviaire(["tgv inoui"], tgv_inoui)
France_ouigo = Graphe_ferroviaire(["ouigo", "ouigo train classique"], ouigo)
Total_tgv_inoui = Graphe_ferroviaire(["tgv inoui"], total_tgv_inoui)
Total_ouigo = Graphe_ferroviaire(["ouigo", "ouigo train classique"], total_ouigo)

# Traitement des transporteurs

liste = [France_origine_destination, France_tgv_inoui, France_ouigo, Total_tgv_inoui, Total_ouigo]
for t in liste:
    t.ajouter_gares()
    t.ajouter_trajets()
    gares_trajet = t.gares_trajet(ville_origine, ville_destination)
    if t is France_origine_destination:
        t.affichage_gares_origine_destination()
    if t is France_tgv_inoui or t is France_ouigo:
        t.affichage_gares_trajet()
        t.affichage_lignes_trajet()
    if t is Total_tgv_inoui or t is Total_ouigo:
        t.affichage_ligne_totale()

# Fin

folium.LayerControl().add_to(transporteurs_France)
transporteurs_France.save("transporteurs_France.html")





