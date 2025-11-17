import pygame

# ---------- Données Objets ----------
# Mets des chemins d'images si tu en as (PNG/JPG). Sinon laisse None.
PERMANENT_OBJECTS = [
    {"name": "Pelle",
     "desc": "Permet de creuser certains emplacements pour trouver des objets.",
     "icon": "assets/objets/pelle.png"},
    {"name": "Marteau",
     "desc": "Brise les cadenas des coffres sans dépenser de clé.",
     "icon": "assets/objets/marteau.png"},
    {"name": "Kit de crochetage",
     "desc": "Ouvre les portes niveau 1 sans consommer de clé.",
     "icon": "assets/objets/kit_crochetage.png"},
    {"name": "Détecteur de métaux",
     "desc": "Augmente la probabilité de trouver des clés et des pièces.",
     "icon": "assets/objets/detecteur_metaux.png"},
    {"name": "Patte de lapin",
     "desc": "Augmente la probabilité de trouver des objets rares.",
     "icon": "assets/objets/patte_lapin.png"},
]

OTHER_OBJECTS = [
    {"name": "Pomme",
     "desc": "Rend 2 pas au joueur ou à la joueuse.",
     "icon": "assets/objets/pomme.png"},
    {"name": "Banane",
     "desc": "Rend 3 pas.",
     "icon": "assets/objets/banane.png"},
    {"name": "Gâteau",
     "desc": "Rend 10 pas.",
     "icon": "assets/objets/gateau.png"},
    {"name": "Sandwich",
     "desc": "Rend 15 pas.",
     "icon": "assets/objets/sandwich.png"},
    {"name": "Repas",
     "desc": "Rend 25 pas.",
     "icon": "assets/objets/repas.png"},
    {"name": "Coffre",
     "desc": "S'ouvre avec une clé ou le marteau. Contenu aléatoire (objets consommables).",
     "icon": "assets/objets/coffre.png"},
    {"name": "Endroit à creuser",
     "desc": "Nécessite la pelle. Peut contenir des objets consommables (ou rien).",
     "icon": "assets/objets/creuser.png"},
    {"name": "Casier (vestiaire)",
     "desc": "Uniquement dans le vestiaire. S'ouvre avec une clé. Contenu aléatoire.",
     "icon": "assets/objets/casier.png"},
]
INVENTORY_ITEMS = [
    {
        "name": "Pas",
        "desc": "Ressource principale. On commence à 70 pas et on en perd 1 à chaque déplacement vers une nouvelle pièce.",
        "icon": "assets/inventaire/pas.png",
    },
    {
        "name": "Pièces d'or",
        "desc": "Monnaie. Sert à acheter des objets dans les pièces jaunes (magasins).",
        "icon": "assets/inventaire/or.png",
    },
    {
        "name": "Gemmes",
        "desc": "Ressource rare. Sert à payer certaines pièces lors du tirage au sort.",
        "icon": "assets/inventaire/gemme.png",
    },
    {
        "name": "Clés",
        "desc": "Permettent d'ouvrir les portes verrouillées et les coffres.",
        "icon": "assets/inventaire/cle.png",
    },
    {
        "name": "Dés",
        "desc": "Permettent de relancer le tirage de 3 pièces lorsque l'on ouvre une nouvelle porte.",
        "icon": "assets/inventaire/de.png",
    },
]
ROOM_DATA = [
    # ====== PIÈCES BLEUES — COMMUNES / FONDATION ======
    {
        "name": "Entrance Hall",
        "color": "Bleue",
        "group": "Commune",
        "desc": "Pièce de départ. Quelques ressources de base.",
        "icon": "assets/rooms/entrance_hall.png",
    },
    {
        "name": "Foundation",
        "color": "Bleue",
        "group": "Commune",
        "desc": "Salle simple avec peu d'effets particuliers.",
        "icon": "assets/rooms/foundation.png",
    },
    {
        "name": "Spare Room",
        "color": "Bleue",
        "group": "Commune",
        "desc": "Petite salle avec une faible chance de ressources.",
        "icon": "assets/rooms/spare_room.png",
    },
    {
        "name": "Parlor",
        "color": "Bleue",
        "group": "Commune",
        "desc": "Salon du manoir, un peu d'or et de clés possibles.",
        "icon": "assets/rooms/parlor.png",
    },
    {
        "name": "Billiard Room",
        "color": "Bleue",
        "group": "Commune",
        "desc": "Salle de billard, quelques pièces ou gemmes.",
        "icon": "assets/rooms/billiard_room.png",
    },
    {
        "name": "Gallery",
        "color": "Bleue",
        "group": "Commune",
        "desc": "Galerie d'art, chance de trouver de l'or ou des gemmes.",
        "icon": "assets/rooms/gallery.png",
    },
    {
        "name": "Closet",
        "color": "Bleue",
        "group": "Commune",
        "desc": "Petit placard, peut contenir une clé.",
        "icon": "assets/rooms/closet.png",
    },
    {
        "name": "Walk-in Closet",
        "color": "Bleue",
        "group": "Commune",
        "desc": "Grand placard avec plus de ressources possibles.",
        "icon": "assets/rooms/walk_in_closet.png",
    },
    {
        "name": "Attic",
        "color": "Bleue",
        "group": "Commune",
        "desc": "Grenier du manoir, souvent un coffre ou un objet caché.",
        "icon": "assets/rooms/attic.png",
    },
    {
        "name": "Storeroom",
        "color": "Bleue",
        "group": "Commune",
        "desc": "Réserve remplie d'objets, chance élevée de coffre.",
        "icon": "assets/rooms/storeroom.png",
    },

    # ====== PIÈCES BLEUES — MILIEU / ZONES VARIÉES ======
    {
        "name": "Nook",
        "color": "Bleue",
        "group": "Milieu",
        "desc": "Petit coin tranquille avec quelques ressources.",
        "icon": "assets/rooms/nook.png",
    },
    {
        "name": "Garage",
        "color": "Bleue",
        "group": "Milieu",
        "desc": "Garage du manoir, objets métalliques et clés possibles.",
        "icon": "assets/rooms/garage.png",
    },
    {
        "name": "Music Room",
        "color": "Bleue",
        "group": "Milieu",
        "desc": "Salle de musique, bonne chance de gemmes.",
        "icon": "assets/rooms/music_room.png",
    },
    {
        "name": "Wine Cellar",
        "color": "Bleue",
        "group": "Milieu",
        "desc": "Cave à vin, mélange de coffres et de gemmes.",
        "icon": "assets/rooms/wine_cellar.png",
    },
    {
        "name": "Trophy Room",
        "color": "Bleue",
        "group": "Milieu",
        "desc": "Salle des trophées, objets rares et coffres possibles.",
        "icon": "assets/rooms/trophy_room.png",
    },
    {
        "name": "Rumpus Room",
        "color": "Bleue",
        "group": "Milieu",
        "desc": "Salle de jeux, bonus variés et parfois des pas.",
        "icon": "assets/rooms/rumpus_room.png",
    },
    {
        "name": "Office",
        "color": "Bleue",
        "group": "Milieu",
        "desc": "Bureau, souvent des clés ou des gemmes.",
        "icon": "assets/rooms/office.png",
    },
    {
        "name": "Drawing Room",
        "color": "Bleue",
        "group": "Supérieure",
        "desc": "Salon élégant avec quelques bonus de pas et gemmes.",
        "icon": "assets/rooms/drawing_room.png",
    },
    {
        "name": "Study",
        "color": "Bleue",
        "group": "Supérieure",
        "desc": "Étude avec des clés cachées dans les tiroirs.",
        "icon": "assets/rooms/study.png",
    },
    {
        "name": "Library",
        "color": "Bleue",
        "group": "Supérieure",
        "desc": "Bibliothèque, petite source de gemmes.",
        "icon": "assets/rooms/library.png",
    },
    {
        "name": "Archives",
        "color": "Bleue",
        "group": "Supérieure",
        "desc": "Archives poussiéreuses, mélange de clés et de gemmes.",
        "icon": "assets/rooms/archives.png",
    },
    {
        "name": "Aquarium",
        "color": "Bleue",
        "group": "Supérieure",
        "desc": "Aquarium intérieur, objets sous l'eau.",
        "icon": "assets/rooms/aquarium.png",
    },
    {
        "name": "Observatory",
        "color": "Bleue",
        "group": "Supérieure",
        "desc": "Observatoire, bonus variés (pas, gemmes, clés).",
        "icon": "assets/rooms/observatory.png",
    },
    {
        "name": "Chapel",
        "color": "Bleue",
        "group": "Supérieure",
        "desc": "Chapelle, rend quelques pas et peut donner une gemme.",
        "icon": "assets/rooms/chapel.png",
    },

    # ====== JARDINS / SERRES — PIÈCES VERTES ======
    {
        "name": "Den",
        "color": "Verte",
        "group": "Jardin",
        "desc": "Pièce cosy, souvent une gemme et parfois un coffre.",
        "icon": "assets/rooms/den.png",
    },
    {
        "name": "Garden",
        "color": "Verte",
        "group": "Jardin",
        "desc": "Jardin d'intérieur avec beaucoup d'endroits à creuser.",
        "icon": "assets/rooms/garden.png",
    },
    {
        "name": "Greenhouse",
        "color": "Verte",
        "group": "Jardin",
        "desc": "Serre remplie de plantes, nombreux emplacements à creuser.",
        "icon": "assets/rooms/greenhouse.png",
    },
    {
        "name": "Solarium",
        "color": "Verte",
        "group": "Jardin",
        "desc": "Pièce lumineuse, donne des pas et des gemmes.",
        "icon": "assets/rooms/solarium.png",
    },
    {
        "name": "Veranda",
        "color": "Verte",
        "group": "Jardin",
        "desc": "Véranda, plusieurs endroits à creuser.",
        "icon": "assets/rooms/veranda.png",
    },
    {
        "name": "The Pool",
        "color": "Verte",
        "group": "Jardin",
        "desc": "Piscine intérieure, objets sous l'eau à récupérer.",
        "icon": "assets/rooms/the_pool.png",
    },

    # ====== CHAMBRES / REPOS — PIÈCES VIOLETTES ======
    {
        "name": "Bedroom",
        "color": "Violette",
        "group": "Chambre",
        "desc": "Chambre classique qui rend un bon nombre de pas.",
        "icon": "assets/rooms/bedroom.png",
    },
    {
        "name": "Boudoir",
        "color": "Violette",
        "group": "Chambre",
        "desc": "Boudoir luxueux, rend beaucoup de pas et parfois une gemme.",
        "icon": "assets/rooms/boudoir.png",
    },
    {
        "name": "Guest Room",
        "color": "Violette",
        "group": "Chambre",
        "desc": "Chambre d'amis, rend quelques pas.",
        "icon": "assets/rooms/guest_room.png",
    },
    {
        "name": "Nursery",
        "color": "Violette",
        "group": "Chambre",
        "desc": "Chambre d'enfant, rend des pas.",
        "icon": "assets/rooms/nursery.png",
    },
    {
        "name": "Maid's Chamber",
        "color": "Violette",
        "group": "Chambre",
        "desc": "Chambre de bonne, petits bonus de pas et gemmes.",
        "icon": "assets/rooms/maids_chamber.png",
    },

    # ====== COULOIRS / ESCALIERS — PIÈCES ORANGES ======
    {
        "name": "Rotunda",
        "color": "Orange",
        "group": "Couloir",
        "desc": "Couloir circulaire avec plusieurs portes.",
        "icon": "assets/rooms/rotunda.png",
    },
    {
        "name": "Ballroom",
        "color": "Orange",
        "group": "Couloir",
        "desc": "Grande salle de bal, souvent beaucoup de portes.",
        "icon": "assets/rooms/ballroom.png",
    },
    {
        "name": "Corridor",
        "color": "Orange",
        "group": "Couloir",
        "desc": "Couloir simple, bonne connectivité.",
        "icon": "assets/rooms/corridor.png",
    },
    {
        "name": "Long Corridor",
        "color": "Orange",
        "group": "Couloir",
        "desc": "Long couloir avec davantage de portes.",
        "icon": "assets/rooms/long_corridor.png",
    },
    {
        "name": "Grand Staircase",
        "color": "Orange",
        "group": "Couloir",
        "desc": "Grand escalier, relie plusieurs zones du manoir.",
        "icon": "assets/rooms/grand_staircase.png",
    },
    {
        "name": "Cloister",
        "color": "Orange",
        "group": "Couloir",
        "desc": "Cloître avec de nombreuses connexions.",
        "icon": "assets/rooms/cloister.png",
    },

    # ====== PIÈCES JAUNES — BOUTIQUES / NOURRITURE ======
    {
        "name": "Pantry",
        "color": "Jaune",
        "group": "Magasin",
        "desc": "Garde-manger avec beaucoup de nourriture (pas).",
        "icon": "assets/rooms/pantry.png",
    },
    {
        "name": "Vault",
        "color": "Jaune",
        "group": "Magasin",
        "desc": "Coffre-fort rempli de coffres à ouvrir.",
        "icon": "assets/rooms/vault.png",
    },
    {
        "name": "Bookshop",
        "color": "Jaune",
        "group": "Magasin",
        "desc": "Librairie, échange d'or contre bonus variés.",
        "icon": "assets/rooms/bookshop.png",
    },
    {
        "name": "Casino",
        "color": "Jaune",
        "group": "Magasin",
        "desc": "Casino très risqué : peut donner ou retirer des pas.",
        "icon": "assets/rooms/casino.png",
    },
    {
        "name": "Dining Room",
        "color": "Jaune",
        "group": "Magasin",
        "desc": "Salle à manger, beaucoup de nourriture (pas).",
        "icon": "assets/rooms/dining_room.png",
    },
    {
        "name": "Cafeteria",
        "color": "Jaune",
        "group": "Magasin",
        "desc": "Cafétéria, gros bonus de pas et quelques gemmes.",
        "icon": "assets/rooms/cafeteria.png",
    },

    # ====== PIÈCES ROUGES — DANGEREUSES / MALUS ======
    {
        "name": "Chamber of Mirrors",
        "color": "Rouge",
        "group": "Dangereuse",
        "desc": "Salle de miroirs, peut faire perdre des pas.",
        "icon": "assets/rooms/chamber_of_mirrors.png",
    },
    {
        "name": "Furnace",
        "color": "Rouge",
        "group": "Dangereuse",
        "desc": "Fournaise brûlante, retire souvent des pas.",
        "icon": "assets/rooms/furnace.png",
    },
    {
        "name": "Boiler Room",
        "color": "Rouge",
        "group": "Dangereuse",
        "desc": "Chaufferie dangereuse mais parfois rentable.",
        "icon": "assets/rooms/boiler_room.png",
    },
    {
        "name": "Closed Exhibit",
        "color": "Rouge",
        "group": "Dangereuse",
        "desc": "Exposition fermée, souvent un très mauvais plan.",
        "icon": "assets/rooms/closed_exhibit.png",
    },
    {
        "name": "Darkroom",
        "color": "Rouge",
        "group": "Dangereuse",
        "desc": "Chambre noire, peut faire perdre beaucoup de pas.",
        "icon": "assets/rooms/darkroom.png",
    },

    # ====== OBJECTIF FINAL ======
    {
        "name": "Antechamber",
        "color": "Bleue",
        "group": "Objectif",
        "desc": "Antichambre au sommet du manoir : atteindre cette pièce pour gagner.",
        "icon": "assets/rooms/antechamber.png",
    },
]
# ---------------------------------------------------------
# Couleurs de cadre pour les pièces (même logique que dans jeu.py)
# ---------------------------------------------------------
COLOR_FRAME = {
    "Bleue":   (90, 140, 240),   # communes
    "Verte":   (100, 200, 120),  # jardins
    "Violette": (160, 120, 220), # chambres
    "Orange":  (240, 150, 60),   # couloirs
    "Rouge":   (210, 70, 70),    # dangereuses
    "Jaune":   (230, 200, 80),   # shops
}

COLOR_ORDER = ["Bleue", "Verte", "Violette", "Orange", "Rouge", "Jaune"]



