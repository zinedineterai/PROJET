import pygame
import random
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from menu import *   # touches, ROOM_DATA, etc.
from main import *   # couleurs UI (COULEUR_TEXTE, etc.)


# ------------------ Paramètres d'écran ------------------
# Résolution par défaut (si on lance jeu.py tout seul, sans passer par le menu)
BASE_LARGEUR, BASE_HAUTEUR = 1920, 1080
LARGEUR, HAUTEUR = BASE_LARGEUR, BASE_HAUTEUR

FPS = 60
# Largeur des panneaux gauche / droite
GAUCHE_W, DROITE_W = 380, 420
# Largeur de la zone centrale (plateau)
CENTRE_W = LARGEUR - GAUCHE_W - DROITE_W

def init_game_geometry(w, h):
    """
    Appelé par le menu pour synchroniser la géométrie du jeu
    avec la résolution choisie (w, h).
    Met à jour LARGEUR / HAUTEUR / CENTRE_W.
    """
    global LARGEUR, HAUTEUR, CENTRE_W
    LARGEUR, HAUTEUR = w, h
    CENTRE_W = LARGEUR - GAUCHE_W - DROITE_W

# Couleurs UI (panneaux, textes, etc.)
COULEUR_PANNEAU = (20, 20, 28)
COULEUR_TEXTE   = (235, 235, 245)
COULEUR_ACCENT  = (110, 170, 255)
COULEUR_MUTE    = (150, 150, 170)

# Couleurs des rooms (logique du PDF)
C_JAUNE  = (230, 200, 80)    # shop
C_VERT   = (100, 200, 120)   # jardins
C_VIOLET = (160, 120, 220)   # chambres (rend des pas)
C_ORANGE = (240, 150, 60)    # couloirs
C_ROUGE  = (210, 70, 70)     # indésirables
C_BLEU   = (90, 140, 240)    # communes

# ------------------ Touches ------------------
# Raccourcis pour valider / retour
TOUCHE_OKS    = {pygame.K_SPACE, pygame.K_RETURN}
TOUCHE_RETOUR = pygame.K_ESCAPE

# ZQSD + WASD = choisir la porte
KEY_UPS    = {pygame.K_z, pygame.K_w}
KEY_DOWNS  = {pygame.K_s}
KEY_LEFTS  = {pygame.K_q, pygame.K_a}
KEY_RIGHTS = {pygame.K_d}

# Flèches = visiter les chambres déjà découvertes (déplacement gratuit)
ARROW_UP    = pygame.K_UP
ARROW_DOWN  = pygame.K_DOWN
ARROW_LEFT  = pygame.K_LEFT
ARROW_RIGHT = pygame.K_RIGHT

# ------------------ Police / texte ------------------
# Petit cache de polices pour éviter de recréer la font à chaque fois
_cache_police: Dict[int, pygame.font.Font] = {}
def police(sz: int) -> pygame.font.Font:
    f = _cache_police.get(sz)
    if f:
        return f
    _cache_police[sz] = pygame.font.SysFont("arial", sz)
    return _cache_police[sz]

def texte(surface, txt, pos, size=24, couleur=(255,255,255), centre=False):
    """Affiche un texte à l'écran (centré ou non)."""
    font = pygame.font.Font(None, size)
    s = font.render(txt, True, couleur)
    r = s.get_rect()
    if centre:
        r.center = pos
    else:
        r.topleft = pos
    surface.blit(s, r)


# ------------------ Images de rooms ------------------
ROOM_IMAGES = {}

def charger_images_pieces():
    """
    Charge les images des pièces une fois au début,
    à partir du champ "icon" dans ROOM_DATA.
    """
    for r in ROOM_DATA:
        chemin = r["icon"]
        nom = r["name"]

        if chemin and os.path.exists(chemin):
            try:
                img = pygame.image.load(chemin).convert_alpha()
                ROOM_IMAGES[nom] = img
            except Exception:
                # Si l'image est cassée, on ignore → la case sera dessinée en couleur.
                pass


# ------------------ Inventaire & objets ------------------
@dataclass
class Inventaire:
    """Inventaire du joueur (pas, or, gemmes, clés, objets, etc.)."""
    pas: int = 70
    or_: int = 500
    gemmes: int = 2
    cles: int = 0
    des: int = 0

    # dictionnaire des autres objets : nom -> quantité
    autres_objets: Dict[str, int] = field(default_factory=dict)

    # Objets permanents
    pelle: bool = False
    marteau: bool = False
    kit_crochetage: bool = False
    detecteur_metaux: bool = False
    patte_lapin: bool = False

    def consommer_pas(self, n: int = 1):
        """Consomme n pas (sans descendre en dessous de 0)."""
        self.pas = max(0, self.pas - n)

    def ajouter_autre_objet(self, nom: str, nb: int = 1):
        """Ajoute un objet consommable dans la section 'Autres objets'."""
        self.autres_objets[nom] = self.autres_objets.get(nom, 0) + nb

    def consommer_autre_objet(self, nom: str, messages: "MessageBar"):
        """Consomme un objet (Pomme, Repas, ...) et applique son effet sur les pas."""
        q = self.autres_objets.get(nom, 0)
        if q <= 0:
            messages.show(f"Tu n'as plus de {nom}.")
            return
        self.autres_objets[nom] = q - 1

        if nom in AUTRES_CATALOGUE:
            _, gain = AUTRES_CATALOGUE[nom]
            self.pas += gain
            messages.show(f"{nom} consommé : +{gain} pas.")
        else:
            messages.show(f"{nom} consommé.")

    def ajouter_objet_permanent(self, nom: str):
        """Débloque un objet permanent (pelle, marteau, etc.)."""
        n = nom.lower()
        if "pelle" in n:
            self.pelle = True
        elif "marteau" in n:
            self.marteau = True
        elif "crochet" in n or "crochetage" in n:
            self.kit_crochetage = True
        elif "détecteur" in n or "detecteur" in n:
            self.detecteur_metaux = True
        elif "patte" in n:
            self.patte_lapin = True

# Catalogue simple des consommables (effet sur les pas)
AUTRES_CATALOGUE = {
    "Pomme":    ("+2 pas", 2),
    "Banane":   ("+3 pas", 3),
    "Gâteau":   ("+10 pas", 10),
    "Sandwich": ("+15 pas", 15),
    "Repas":    ("+25 pas", 25),
}

# ------------------ Rooms ------------------
@dataclass
class Piece:
    """Modèle de pièce dans le manoir (couleur, rareté, effets, etc.)."""
    nom: str
    couleur: Tuple[int, int, int]
    rarete: int        # 1 commun, 2 un peu rare, 3 rare
    cout_gemmes: int   # 0 / 1 / 2...
    effets: List[str]  # texte court
    actions: Dict[str, int]  # ex: {"Gemmes":30, "Creuser":25, "Coffre":10}

def nb_portes_theoriques(piece: Piece) -> int:
    """Nombre de portes théorique pour cette pièce en fonction de sa couleur."""
    if piece.couleur == C_ORANGE:  # couloirs
        return 4
    if piece.couleur == C_BLEU:    # communes
        return 3
    if piece.couleur == C_VIOLET:  # chambres
        return 2
    if piece.couleur == C_VERT:    # jardins
        return 3
    if piece.couleur == C_ROUGE:   # indésirables
        return 1
    if piece.couleur == C_JAUNE:   # shops
        return 2
    return 3


# ======================= Catalogue de pièces =======================
# Liste des modèles de rooms (tirage aléatoire dans TiragePieces)
PIECES_MODELES: List[Piece] = [
    # ----- Rooms "fondation" / communes (bleues) -----
    Piece("Entrance Hall", C_BLEU, 1, 0,
          ["Pièce de départ", "Quelques ressources"],
          {"Clé": 10, "Gemmes": 5, "+Pas": 10}),
    Piece("Foundation", C_BLEU, 1, 0,
          ["Basique", "Peu d'effets"],
          {"Clé": 5, "Gemmes": 5}),
    Piece("Spare Room", C_BLEU, 1, 0,
          ["Petite salle", "Chance légère de ressources"],
          {"Clé": 10, "Gemmes": 10}),
    Piece("Rotunda", C_ORANGE, 1, 0,
          ["Couloir circulaire", "Plusieurs portes"],
          {"Clé": 5}),
    Piece("Parlor", C_BLEU, 1, 0,
          ["Salon", "Un peu de tout"],
          {"Clé": 10, "Gemmes": 15}),
    Piece("Billiard Room", C_BLEU, 1, 0,
          ["Salle de billard", "Quelques pièces"],
          {"Gemmes": 15, "Clé": 5}),
    Piece("Gallery", C_BLEU, 1, 0,
          ["Galerie", "Chance d'or"],
          {"Gemmes": 10}),
    Piece("Closet", C_BLEU, 1, 0,
          ["Placard", "Petits objets"],
          {"Clé": 10}),
    Piece("Walk-in Closet", C_BLEU, 1, 0,
          ["Grand placard", "Ressources variées"],
          {"Clé": 15, "Gemmes": 10}),
    Piece("Attic", C_BLEU, 1, 0,
          ["Grenier", "Objet caché"],
          {"Clé": 15, "Gemmes": 10, "Coffre": 20}),
    Piece("Storeroom", C_BLEU, 1, 0,
          ["Réserve", "Beaucoup d'objets"],
          {"Clé": 10, "Gemmes": 15, "Coffre": 25}),

    # ----- Rooms "milieu" ----- 
    Piece("Nook", C_BLEU, 2, 0,
          ["Coin tranquille", "Quelques ressources"],
          {"Clé": 10, "Gemmes": 10}),
    Piece("Garage", C_BLEU, 2, 0,
          ["Garage", "Objets métalliques"],
          {"Clé": 15, "Gemmes": 10}),
    Piece("Music Room", C_BLEU, 2, 0,
          ["Salle de musique", "Parfois des gemmes"],
          {"Gemmes": 20}),
    Piece("Den", C_VERT, 2, 0,
          ["Foyer", "Souvent une gemme"],
          {"Gemmes": 60, "Coffre": 20}),
    Piece("Wine Cellar", C_BLEU, 2, 0,
          ["Cave à vin", "Coffres et gemmes"],
          {"Gemmes": 30, "Coffre": 35}),
    Piece("Trophy Room", C_BLEU, 2, 0,
          ["Salle des trophées", "Objets rares"],
          {"Clé": 20, "Gemmes": 20, "Coffre": 30}),
    Piece("Ballroom", C_ORANGE, 2, 0,
          ["Grande salle de bal", "Beaucoup de portes"],
          {"Clé": 10}),
    Piece("Pantry", C_JAUNE, 2, 1,
          ["Garde-manger", "Beaucoup de nourriture"],
          {"+Pas": 60, "Gemmes": 10}),
    Piece("Rumpus Room", C_BLEU, 2, 0,
          ["Salle de jeux", "Ressources variées"],
          {"Gemmes": 20, "+Pas": 20}),
    Piece("Vault", C_JAUNE, 2, 2,
          ["Coffre-fort", "Beaucoup de coffres"],
          {"Clé": 15, "Gemmes": 25, "Coffre": 60}),
    Piece("Office", C_BLEU, 2, 0,
          ["Bureau", "Clés et gemmes"],
          {"Clé": 20, "Gemmes": 15}),

    # ----- Bibliothèque / étude (niveau 3) -----
    Piece("Drawing Room", C_BLEU, 2, 1,
          ["Salon élégant", "Petits bonus"],
          {"Gemmes": 20, "+Pas": 20}),
    Piece("Study", C_BLEU, 2, 1,
          ["Étude", "Clés cachées"],
          {"Clé": 25, "Gemmes": 10}),
    Piece("Library", C_BLEU, 2, 1,
          ["Bibliothèque", "Quelques gemmes"],
          {"Gemmes": 25}),
    Piece("Chamber of Mirrors", C_ROUGE, 3, 2,
          ["Salle dangereuse", "Peut faire perdre des pas"],
          {"Gemmes": 30, "-Pas": 40}),
    Piece("The Pool", C_VERT, 3, 1,
          ["Piscine", "Objets sous l'eau"],
          {"Gemmes": 25, "Clé": 15, "Creuser": 40}),

    # ----- Jardins (vertes) -----
    Piece("Garden", C_VERT, 2, 0,
          ["Jardin d'intérieur", "Gemmes et endroits à creuser"],
          {"Gemmes": 35, "Creuser": 60, "Clé": 10}),
    Piece("Greenhouse", C_VERT, 3, 1,
          ["Serre", "Beaucoup d'endroits à creuser"],
          {"Gemmes": 40, "Creuser": 80, "Clé": 15, "Coffre": 20}),
    Piece("Solarium", C_VERT, 3, 1,
          ["Solarium", "Bonus de pas et gemmes"],
          {"Gemmes": 30, "Creuser": 50, "+Pas": 40}),
    Piece("Veranda", C_VERT, 2, 0,
          ["Véranda", "Endroits à creuser"],
          {"Creuser": 60, "Gemmes": 20}),

    # ----- Chambres (violettes) -----
    Piece("Bedroom", C_VIOLET, 2, 0,
          ["Chambre", "Redonne des pas"],
          {"+Pas": 70}),
    Piece("Boudoir", C_VIOLET, 2, 1,
          ["Boudoir", "Beaucoup de repos"],
          {"+Pas": 90, "Gemmes": 10}),
    Piece("Guest Room", C_VIOLET, 2, 0,
          ["Chambre d'amis", "Redonne quelques pas"],
          {"+Pas": 60}),
    Piece("Nursery", C_VIOLET, 2, 0,
          ["Chambre d'enfant", "Rend des pas"],
          {"+Pas": 55}),
    Piece("Maid's Chamber", C_VIOLET, 2, 0,
          ["Chambre de bonne", "Petits bonus"],
          {"+Pas": 40, "Gemmes": 10}),

    # ----- Couloirs (oranges) -----
    Piece("Corridor", C_ORANGE, 1, 0,
          ["Couloir", "Beaucoup de portes"],
          {"Clé": 5}),
    Piece("Long Corridor", C_ORANGE, 2, 0,
          ["Long couloir", "Encore plus de portes"],
          {"Clé": 10}),
    Piece("Grand Staircase", C_ORANGE, 2, 1,
          ["Grand escalier", "Bonne connectivité"],
          {"Clé": 10}),
    Piece("Cloister", C_ORANGE, 3, 1,
          ["Cloître", "Couloirs multiples"],
          {"Clé": 10, "Gemmes": 10}),

    # ----- Salles rouges -----
    Piece("Furnace", C_ROUGE, 3, 1,
          ["Fournaise", "Peut retirer des pas"],
          {"-Pas": 60, "Gemmes": 20}),
    Piece("Boiler Room", C_ROUGE, 3, 1,
          ["Chaufferie", "Dangereuse mais rentable"],
          {"-Pas": 40, "Gemmes": 30, "Clé": 15}),
    Piece("Closed Exhibit", C_ROUGE, 3, 2,
          ["Exposition fermée", "Souvent mauvais plan"],
          {"-Pas": 50, "Gemmes": 20}),
    Piece("Darkroom", C_ROUGE, 2, 1,
          ["Chambre noire", "Peut faire perdre des pas"],
          {"-Pas": 50, "Gemmes": 20}),

    # ----- Shops (jaunes) -----
    Piece("Bookshop", C_JAUNE, 3, 2,
          ["Librairie", "Échange or contre objets"],
          {"Gemmes": 25, "+Pas": 30}),
    Piece("Casino", C_JAUNE, 3, 3,
          ["Casino", "Très risqué"],
          {"Gemmes": 40, "-Pas": 40, "+Pas": 40}),
    Piece("Dining Room", C_JAUNE, 2, 1,
          ["Salle à manger", "Nourriture (pas)"],
          {"+Pas": 70}),
    Piece("Cafeteria", C_JAUNE, 2, 1,
          ["Cafétéria", "Beaucoup de nourriture"],
          {"+Pas": 80, "Gemmes": 10}),

    # ----- Autres bleues -----
    Piece("Archives", C_BLEU, 2, 1,
          ["Archives", "Clés et gemmes"],
          {"Clé": 25, "Gemmes": 20}),
    Piece("Aquarium", C_BLEU, 2, 1,
          ["Aquarium", "Objets sous l'eau"],
          {"Gemmes": 25, "Clé": 10}),
    Piece("Observatory", C_BLEU, 3, 2,
          ["Observatoire", "Bonus variés"],
          {"Gemmes": 30, "Clé": 15, "+Pas": 20}),
    Piece("Chapel", C_BLEU, 2, 1,
          ["Chapelle", "Petit bonus de pas"],
          {"+Pas": 30, "Gemmes": 10}),

    # ----- Objectif -----
    Piece("Antechamber", C_BLEU, 3, 0,
          ["Dernière pièce", "But du jeu"],
          {"Gemmes": 0}),
]

# ------------------ Grille & Portes ------------------
GRID_W, GRID_H = 5, 9  # 5 colonnes, 9 rangées (0 = haut)

def niveau_verrou_pour_ligne(y: int) -> int:
    """
    Donne un niveau de verrou (0,1,2) selon la ligne y.
    Plus on monte dans la grille, plus les portes difficiles apparaissent.
    """
    if y == GRID_H - 1:
        return 0
    if y == 0:
        return 2
    base = [0, 1, 2]
    dist_top = (GRID_H - 1) - y
    w0 = max(1, 5 - dist_top)
    w1 = max(1, 1 + dist_top)
    w2 = max(1, dist_top // 2 + 1)
    return random.choices(base, weights=[w0, w1, w2], k=1)[0]

@dataclass
class Cellule:
    """
    Cellule de la grille : contient la pièce, les portes,
    et tout ce qui peut exister dans cette case (coffre, shop, trou, etc.).
    """
    piece: Optional[Piece] = None
    decouverte: bool = False
    portes: Dict[str, int] = field(default_factory=lambda: {"N": 0, "E": 0, "S": 0, "W": 0})
    portes_existent: Dict[str, bool] = field(default_factory=lambda: {"N": False, "E": False, "S": False, "W": False})
    has_coffre: bool = False
    has_trou: bool = False
    has_casier: bool = False
    is_shop: bool = False
    pickables: List[Dict] = field(default_factory=list)
    loot_genere: bool = False

# ------------------ Panneaux d'UI ------------------
class Panneau:
    """Panneau de base (titre + cadre)."""
    def __init__(self, rect: pygame.Rect, titre: str):
        self.rect = rect
        self.titre = titre
    def dessiner(self, surf: pygame.Surface):
        pygame.draw.rect(surf, COULEUR_PANNEAU, self.rect)
        pygame.draw.rect(surf, (45, 45, 60), self.rect, 2)
        texte(surf, self.titre, (self.rect.x + 16, self.rect.y + 12), 26, COULEUR_ACCENT)

class PanneauPermanents(Panneau):
    """Panneau qui liste les objets permanents débloqués."""
    def __init__(self, rect: pygame.Rect, inv: Inventaire):
        super().__init__(rect, "Objets permanents")
        self.inv = inv
    def dessiner(self, surf: pygame.Surface):
        super().dessiner(surf)
        y = self.rect.y + 56
        lignes = [
            ("Pelle", self.inv.pelle),
            ("Marteau", self.inv.marteau),
            ("Kit crochetage", self.inv.kit_crochetage),
            ("Détecteur de métaux", self.inv.detecteur_metaux),
            ("Patte de lapin", self.inv.patte_lapin),
        ]
        for nom, ok in lignes:
            col = (120, 220, 160) if ok else COULEUR_MUTE
            texte(surf, f"[{'✓' if ok else ' '}] {nom}", (self.rect.x + 20, y), 22, col)
            y += 32

class PanneauInventaire(Panneau):
    """Panneau qui affiche les ressources (pas, or, gemmes, etc.)."""
    def __init__(self, rect: pygame.Rect, inv: Inventaire):
        super().__init__(rect, "Inventaire")
        self.inv = inv
    def dessiner(self, surf: pygame.Surface):
        super().dessiner(surf)
        y = self.rect.y + 56
        texte(surf, f"Pas : {self.inv.pas}",         (self.rect.x + 20, y), 24); y += 30
        texte(surf, f"Or : {self.inv.or_}",          (self.rect.x + 20, y), 24); y += 30
        texte(surf, f"Gemmes : {self.inv.gemmes}",   (self.rect.x + 20, y), 24); y += 30
        texte(surf, f"Clés : {self.inv.cles}",       (self.rect.x + 20, y), 24); y += 30
        texte(surf, f"Dés : {self.inv.des}",         (self.rect.x + 20, y), 24); y += 36
        texte(surf, "Autres objets :", (self.rect.x + 20, y), 22, COULEUR_MUTE); y += 28
        for nom, qte in list(self.inv.autres_objets.items())[:10]:
            texte(surf, f"• {nom} x{qte}", (self.rect.x + 26, y), 20); y += 24

# ------------------ Message bar ------------------
class MessageBar:
    """
    Petite barre de message en bas de la zone centrale
    pour afficher les infos (erreurs, loot, etc.).
    """
    def __init__(self):
        self.msg = ""
        self.timer = 0.0
    def show(self, txt: str, sec=2.0):
        self.msg = txt
        self.timer = sec
    def update(self, dt: float):
        if self.timer > 0:
            self.timer = max(0.0, self.timer - dt)
    def draw(self, surf: pygame.Surface):
        if self.timer <= 0 or not self.msg:
            return
        bar = pygame.Rect(GAUCHE_W, int(HAUTEUR * 0.92), CENTRE_W, 50)
        pygame.draw.rect(surf, (24, 24, 34), bar)
        pygame.draw.rect(surf, (60, 60, 80), bar, 2)
        texte(surf, self.msg, (bar.centerx, bar.centery), 22, COULEUR_TEXTE, centre=True)

# ------------------ Plateau (grille au centre) ------------------
class Plateau:
    """
    Gère la grille 5x9 :
    - stockage des cellules
    - position du joueur
    - dessin des cases / portes / curseurs.
    """
    def __init__(self, rect: pygame.Rect, inv: Inventaire):
        self.rect = rect
        self.inv = inv
        self.grid: List[List[Cellule]] = [[Cellule() for _ in range(GRID_H)] for _ in range(GRID_W)]

        # Joueur au centre en bas
        self.x = GRID_W // 2
        self.y = GRID_H - 1
        # Curseur de visite (flèches)
        self.vx = self.x
        self.vy = self.y

        # Case de départ = Entrée
        start = self.grid[self.x][self.y]
        start.decouverte = True
        start.piece = Piece("Entrance Hall", C_BLEU, 1, 0, ["Départ"], {"Divers": 100})

        # Génération des niveaux de verrous (+ reset portes_existent)
        self._init_portes()
        # L'entrée a déjà quelques portes possibles
        start.portes_existent = {"N": True, "E": True, "S": False, "W": True}

        # Direction courante (N,E,S,W)
                # ----- Case VICTOIRE : tout en haut au milieu -----
        vx = GRID_W // 2
        vy = 0  # ligne du haut
        cell_victoire = self.grid[vx][vy]
        # On place directement la pièce "Antechamber" dans cette case
        cell_victoire.piece = Piece(
            "Antechamber",
            C_BLEU,           # couleur bleue par défaut (tu peux changer)
            3,
            0,
            ["Dernière pièce", "But du jeu"],
            {"Gemmes": 0},
        )
        cell_victoire.decouverte = True  # elle apparaîtra quand on y entre

        self.dirs = ["N", "E", "S", "W"]
        self.dir_idx = 0

    # ----------------------------------------------------------------------
    def _init_portes(self):
        """Attribue un niveau de verrou à chaque porte de chaque cellule."""
        for gx in range(GRID_W):
            for gy in range(GRID_H):
                c = self.grid[gx][gy]
                c.portes = {d: niveau_verrou_pour_ligne(gy) for d in ["N","E","S","W"]}
                c.portes_existent = {"N": False, "E": False, "S": False, "W": False}

        # Pas de portes hors-grille (haut / bas / bords)
        for gx in range(GRID_W):
            self.grid[gx][0].portes["N"] = 0
            self.grid[gx][GRID_H-1].portes["S"] = 2
        for gy in range(GRID_H):
            self.grid[0][gy].portes["W"] = 0
            self.grid[GRID_W-1][gy].portes["E"] = 0

    # ----------------------------------------------------------------------
    def changer_direction(self, dx: int):
        """Change la direction de la flèche (non utilisé directement ici)."""
        self.dir_idx = (self.dir_idx + dx) % 4

    def direction(self) -> str:
        """Renvoie la direction courante ('N','E','S','W')."""
        return self.dirs[self.dir_idx]

    # ----------------------------------------------------------------------
    def deplacement_possible(self, d: str) -> bool:
        """Vérifie si on peut aller dans la direction d (porte existante + dans la grille)."""
        nx, ny = self.x, self.y
        if d == "N": ny -= 1
        if d == "S": ny += 1
        if d == "W": nx -= 1
        if d == "E": nx += 1
        if not (0 <= nx < GRID_W and 0 <= ny < GRID_H):
            return False
        return self.grid[self.x][self.y].portes_existent.get(d, False)

    # ----------------------------------------------------------------------
    def niveau_verrou_direction(self, d: str) -> int:
        """Renvoie le niveau de verrou pour la porte dans la direction d."""
        return self.grid[self.x][self.y].portes[d]

    # ----------------------------------------------------------------------
    def dessiner(self, surf: pygame.Surface):
        """Dessine la grille, le joueur, les portes, et les aides."""
        pygame.draw.rect(surf, (12,12,18), self.rect)
        pygame.draw.rect(surf, (50,50,70), self.rect, 2)

        margin = 30
        gw = self.rect.w - margin*2
        gh = self.rect.h - margin*2 - 80
        cw = gw // GRID_W
        ch = gh // GRID_H
        origin = (self.rect.x + margin, self.rect.y + margin)

        # ALIAS : noms différents entre pièce & images (pour les clés ROOM_IMAGES)
        alias = {
            "Entrée": "Entrance Hall",
            "Antechambre": "Antechamber"
        }

        # ==========================
        #   DESSIN DES CELLULES
        # ==========================
        for gx in range(GRID_W):
            for gy in range(GRID_H):
                r = pygame.Rect(origin[0] + gx*cw + 4,
                                origin[1] + gy*ch + 4,
                                cw - 8, ch - 8)

                cell = self.grid[gx][gy]

                if cell.decouverte and cell.piece:
                    piece = cell.piece

                    # contour = couleur de la pièce
                    pygame.draw.rect(surf, piece.couleur, r, 3, border_radius=10)

                    # intérieur légèrement plus sombre
                    inner = r.inflate(-8, -8)
                    pygame.draw.rect(surf, (15,15,25), inner, border_radius=8)

                    # nom normalisé pour récupérer l'image
                    nom = alias.get(piece.nom, piece.nom)
                    img = ROOM_IMAGES.get(nom)

                    if img:
                        # On adapte l'image à la case (garde les proportions)
                        iw, ih = img.get_size()
                        scale = min(inner.w / iw, inner.h / ih)
                        img2 = pygame.transform.smoothscale(img, (int(iw*scale), int(ih*scale)))
                        surf.blit(img2, img2.get_rect(center=inner.center))

                    if img:
                        iw, ih = img.get_size()
                        scale = min(inner.w / iw, inner.h / ih)
                        img2 = pygame.transform.smoothscale(img, (int(iw*scale), int(ih*scale)))
                        surf.blit(img2, img2.get_rect(center=inner.center))

                    else:
                        # Cas spécial : case VICTOIRE sans image
                        if (
                            piece.nom.lower().strip() == "antechamber"
                            and gx == GRID_W // 2
                            and gy == 0
                        ):
                            # fond vert + texte "Victoire"
                            pygame.draw.rect(surf, (60, 160, 80), inner, border_radius=8)
                            texte(surf, "Victoire", inner.center, 18, (255, 255, 255), centre=True)
                        else:
                            # pas d'image → couleur sombre adaptée
                            base = piece.couleur
                            fill = (base[0]//2, base[1]//2, base[2]//2)
                            pygame.draw.rect(surf, fill, inner, border_radius=8)


                else:
                    # case non découverte
                    pygame.draw.rect(surf, (28,28,40), r, border_radius=10)
                    pygame.draw.rect(surf, (60,60,80), r, 1, border_radius=10)

        # ==========================
        #  CURSEUR DU JOUEUR
        # ==========================
        rcur = pygame.Rect(origin[0]+self.x*cw+4, origin[1]+self.y*ch+4, cw-8, ch-8)
        pygame.draw.rect(surf, COULEUR_ACCENT, rcur, 4, border_radius=12)
        texte(surf, "Vous", (rcur.centerx, rcur.centery), 18, COULEUR_TEXTE, centre=True)

        # ==========================
        #  CURSEUR VISITE
        # ==========================
        if (self.vx, self.vy) != (self.x, self.y):
            rview = pygame.Rect(origin[0]+self.vx*cw+6, origin[1]+self.vy*ch+6, cw-12, ch-12)
            # bordure en pointillés
            for i in range(rview.x, rview.x+rview.w, 10):
                pygame.draw.line(surf, (200,200,200), (i,rview.y), (i+5,rview.y), 1)
                pygame.draw.line(surf, (200,200,200), (i,rview.bottom), (i+5,rview.bottom), 1)

            for j in range(rview.y, rview.y+rview.h, 10):
                pygame.draw.line(surf, (200,200,200), (rview.x,j), (rview.x,j+5), 1)
                pygame.draw.line(surf, (200,200,200), (rview.right,j), (rview.right,j+5), 1)

        # ==========================
        #  ONGLET DES PORTES
        # ==========================
        tabs = {
            "N": pygame.Rect(rcur.centerx-20, rcur.y-6, 40, 6),
            "S": pygame.Rect(rcur.centerx-20, rcur.bottom, 40, 6),
            "W": pygame.Rect(rcur.x-6, rcur.centery-20, 6, 40),
            "E": pygame.Rect(rcur.right, rcur.centery-20, 6, 40),
        }

        for d, rr in tabs.items():
            nx, ny = self.x, self.y
            if d == "N": ny -= 1
            elif d == "S": ny += 1
            elif d == "W": nx -= 1
            elif d == "E": nx += 1

            if 0 <= nx < GRID_W and 0 <= ny < GRID_H:
                if self.grid[self.x][self.y].portes_existent.get(d, False):
                    opened = self.grid[nx][ny].decouverte and self.grid[nx][ny].piece
                    if opened:
                        col = (255,255,255)
                    else:
                        lvl = self.niveau_verrou_direction(d)
                        # couleur selon niveau de verrou
                        col = (120,200,140) if lvl==0 else (230,180,90) if lvl==1 else (220,100,100)
                    pygame.draw.rect(surf, col, rr)

                # Encadrement de la direction sélectionnée
                if d == self.direction():
                    pygame.draw.rect(surf, COULEUR_ACCENT, rr.inflate(6,6), 2)

        # ==========================
        # Aide en bas de la zone centrale
        # ==========================
        aide1 = "ZQSD/WASD = choisir porte  |  Entrée/Espace = OK  |  R = relancer (dé)"
        aide2 = "Flèches = visiter | C creuser  O coffre  L casier  B boutique"
        texte(surf, aide1, (self.rect.centerx, self.rect.bottom-52), 18, COULEUR_MUTE, centre=True)
        texte(surf, aide2, (self.rect.centerx, self.rect.bottom-28), 18, COULEUR_MUTE, centre=True)


# ------------------ Overlay tirage de pièces ------------------
class TiragePieces:
    """
    Overlay qui s'affiche quand on ouvre une nouvelle porte :
    choix de 3 pièces, avec coût en gemmes et infos.
    """
    def __init__(self, rect: pygame.Rect, inv: Inventaire):
        self.rect = rect
        self.inv = inv
        self.visible = False
        self.choix: List[Piece] = []
        self.idx = 0
        self.nb_dirs_max = 4

    def _pondere(self, p: Piece) -> int:
        """Calcule un poids de tirage selon la rareté + patte de lapin."""
        base = {1: 60, 2: 30, 3: 10}[p.rarete]
        if self.inv.patte_lapin:
            base += 5
        return max(1, base)

    def generer(self):
        """Génère 3 pièces au hasard avec pondération."""
        pool = PIECES_MODELES
        self.choix = random.choices(pool, weights=[self._pondere(p) for p in pool], k=3)
        # On force au moins une pièce qui ne coûte pas de gemmes
        if all(p.cout_gemmes > 0 for p in self.choix):
            zero = [p for p in pool if p.cout_gemmes == 0]
            if zero:
                self.choix[0] = random.choice(zero)
        self.idx = 0
        self.visible = True

    def gerer_evenement(self, e: pygame.event.Event):
        """Gestion des touches pendant le tirage (← → Entrée R)."""
        if not self.visible:
            return
        if e.type == pygame.KEYDOWN:
            if e.key in KEY_LEFTS:
                self.idx = (self.idx - 1) % 3
            elif e.key in KEY_RIGHTS:
                self.idx = (self.idx + 1) % 3
            elif e.key in TOUCHE_OKS or e.key == TOUCHE_RETOUR:
                self.visible = False
            elif e.key == pygame.K_r and self.inv.des > 0:
                self.inv.des -= 1
                self.generer()

    def dessiner(self, surf: pygame.Surface):
        """Dessine l'overlay de tirage de pièces."""
        if not self.visible:
            return

        # voile sombre
        dim = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 180))
        surf.blit(dim, (0, 0))

        zone = pygame.Rect(GAUCHE_W, 40, CENTRE_W, int(HAUTEUR * 0.6))
        texte(
            surf,
            "Choisir une pièce (←/→, Entrée) — R pour relancer (consomme 1 dé)",
            (zone.centerx, zone.y - 8),
            26,
            COULEUR_TEXTE,
            centre=True
        )

        w = int(zone.w * 0.28)
        h = int(zone.h * 0.62)
        xs = [zone.centerx - w - 20, zone.centerx, zone.centerx + w + 20]

        for i, p in enumerate(self.choix):
            card = pygame.Rect(0, 0, w, h)
            card.center = (xs[i], zone.centery)

            pygame.draw.rect(surf, (20, 20, 30), card)
            pygame.draw.rect(surf, p.couleur, card, 4)

            texte(surf, p.nom, (card.centerx, card.y + 16), 24, COULEUR_TEXTE, centre=True)

            # effets listés
            y = card.y + 52
            for eff in p.effets[:3]:
                texte(surf, f"• {eff}", (card.x + 18, y), 20)
                y += 22

            # zone info loot + portes
            y_info = card.bottom - 96
            rect_info = pygame.Rect(card.x, y_info - 6, card.w, 90)
            pygame.draw.rect(surf, (20, 20, 30), rect_info)

            # nombre de portes possibles
            n_portes_theo = nb_portes_theoriques(p)
            n_portes = min(n_portes_theo, self.nb_dirs_max)
            texte(
                surf,
                f"Portes disponibles : {n_portes}",
                (card.x + 18, y_info),
                20,
                COULEUR_ACCENT
            )
            y_info += 22

            # tags de loot (pour la description rapide)
            tags_affichables: List[str] = []
            for k, v in p.actions.items():
                if not isinstance(v, int):
                    continue
                if k in ("Clé", "Gemmes", "Coffre", "Creuser", "+Pas", "-Pas"):
                    nom_aff = k
                    if k == "+Pas":
                        nom_aff = "Bonus pas"
                    elif k == "-Pas":
                        nom_aff = "Perte pas"
                    tags_affichables.append(f"{nom_aff} : {v}%")

            loot_line = " / ".join(tags_affichables) if tags_affichables else "Aucun bonus particulier"

            texte(
                surf,
                loot_line,
                (card.x + 18, y_info),
                18,
                COULEUR_MUTE
            )

            # coût en gemmes
            cout = f"Coût en gemmes : {p.cout_gemmes}"
            col_cout = (220, 200, 90) if p.cout_gemmes > 0 else (140, 200, 160)
            texte(surf, cout, (card.centerx, card.bottom - 26), 20, col_cout, centre=True)

            # surbrillance de la carte sélectionnée
            if i == self.idx:
                pygame.draw.rect(surf, COULEUR_ACCENT, card.inflate(10, 10), 3)

        # bandeau avec ressources
        bas = pygame.Rect(GAUCHE_W, int(HAUTEUR * 0.65), CENTRE_W, 54)
        pygame.draw.rect(surf, (24, 24, 34), bas)
        pygame.draw.rect(surf, (60, 60, 80), bas, 2)
        texte(
            surf,
            f"Gemmes : {self.inv.gemmes}  |  Dés : {self.inv.des}",
            (bas.centerx, bas.centery),
            22,
            COULEUR_TEXTE,
            centre=True
        )

# ------------------ Shop Overlay ------------------
class ShopOverlay:
    """
    Boutique simple :
    - On l'ouvre avec B (si la case est un shop).
    - On choisit un objet avec ←/→.
    - On achète avec Entrée.
    """
    def __init__(self, rect: pygame.Rect, inv: Inventaire, messages: "MessageBar"):
        self.rect = rect
        self.inv = inv
        self.messages = messages
        self.visible = False
        self.idx = 0

        # Liste d'objets vendus (prix en or + effet)
        self.items = [
            {"nom": "Petit repas (+10 pas)",  "prix": 5,  "objet": "Repas"},
            {"nom": "Grand repas (+25 pas)",  "prix": 10, "objet": "Repas"},
            {"nom": "Dé supplémentaire",      "prix": 8,  "gain_de": 1},
            {"nom": "Clé supplémentaire",     "prix": 6,  "gain_cle": 1},
            {"nom": "Gemmes (+1)",            "prix": 7,  "gain_gemme": 1},
            {"nom": "Pelle (objet permanent)",        "prix": 15, "permanent": "Pelle"},
            {"nom": "Patte de lapin (objet permanent)", "prix": 20, "permanent": "Patte de lapin"},
        ]

    def ouvrir(self):
        """Affiche la boutique."""
        self.visible = True
        self.idx = 0
        self.messages.show("Boutique ouverte (←/→ pour choisir, Entrée pour acheter).")

    def fermer(self):
        """Ferme la boutique."""
        self.visible = False
        self.messages.show("Boutique fermée.")

    def handle(self, e: pygame.event.Event):
        """Gestion des touches dans la boutique."""
        if not self.visible:
            return

        if e.type == pygame.KEYDOWN:
            if e.key in KEY_LEFTS:
                self.idx = (self.idx - 1) % len(self.items)
            elif e.key in KEY_RIGHTS:
                self.idx = (self.idx + 1) % len(self.items)

            elif e.key in TOUCHE_OKS:
                # Achat de l'item sélectionné
                item = self.items[self.idx]
                prix = item["prix"]

                if self.inv.or_ < prix:
                    self.messages.show("Pas assez d'or pour acheter cet objet.")
                    return

                self.inv.or_ -= prix

                # Effets directs
                if "gain_de" in item:
                    self.inv.des += item["gain_de"]
                if "gain_cle" in item:
                    self.inv.cles += item["gain_cle"]
                if "gain_gemme" in item:
                    self.inv.gemmes += item["gain_gemme"]

                # Objet consommable : stocké dans Autres objets
                if "objet" in item:
                    self.inv.ajouter_autre_objet(item["objet"])

                # Objet permanent
                if "permanent" in item:
                    self.inv.ajouter_objet_permanent(item["permanent"])

                self.messages.show(f"Acheté : {item['nom']}")

            elif e.key == TOUCHE_RETOUR or e.key == pygame.K_ESCAPE or e.key == pygame.K_b:
                # Fermeture de la boutique
                self.fermer()

    def draw(self, surf: pygame.Surface):
        """Dessine l'overlay de boutique."""
        if not self.visible:
            return

        dim = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 180))
        surf.blit(dim, (0, 0))

        zone = pygame.Rect(
            self.rect.x + 40,
            self.rect.y + 60,
            self.rect.w - 80,
            self.rect.h - 120
        )

        pygame.draw.rect(surf, (20, 20, 30), zone)
        pygame.draw.rect(surf, (80, 80, 120), zone, 2)

        texte(surf, "Boutique", (zone.centerx, zone.y + 22), 28, COULEUR_TEXTE, centre=True)
        texte(
            surf,
            f"Or : {self.inv.or_}   Gemmes : {self.inv.gemmes}",
            (zone.centerx, zone.y + 52),
            22,
            COULEUR_MUTE,
            centre=True
        )

        w = int(zone.w * 0.24)
        h = int(zone.h * 0.45)
        xs = [
            zone.centerx - w - 20,
            zone.centerx,
            zone.centerx + w + 20,
        ]

        n = len(self.items)
        indices = [(self.idx - 1) % n, self.idx, (self.idx + 1) % n]

        for pos, idx_item in enumerate(indices):
            item = self.items[idx_item]
            card = pygame.Rect(0, 0, w, h)
            card.center = (xs[pos], zone.centery)

            pygame.draw.rect(surf, (26, 26, 40), card)
            pygame.draw.rect(
                surf,
                COULEUR_ACCENT if idx_item == self.idx else (80, 80, 110),
                card,
                3
            )

            texte(surf, item["nom"], (card.centerx, card.y + 18), 20, COULEUR_TEXTE, centre=True)
            texte(surf, f"Prix : {item['prix']} or", (card.centerx, card.y + 46),
                  18, (220, 200, 120), centre=True)

            # Affichage des gains possibles
            y = card.y + 78
            if "gain_pas" in item:
                texte(surf, f"+{item['gain_pas']} pas", (card.x + 12, y), 18); y += 20
            if "gain_de" in item:
                texte(surf, f"+{item['gain_de']} dé", (card.x + 12, y), 18); y += 20
            if "gain_cle" in item:
                texte(surf, f"+{item['gain_cle']} clé", (card.x + 12, y), 18); y += 20
            if "gain_gemme" in item:
                texte(surf, f"+{item['gain_gemme']} gemme", (card.x + 12, y), 18); y += 20
            if "objet" in item:
                texte(surf, f"Ajouté à Autres objets", (card.x + 12, y), 18, COULEUR_MUTE); y += 20
            if "permanent" in item:
                texte(surf, f"Objet permanent", (card.x + 12, y), 18, COULEUR_MUTE); y += 20

        bas = pygame.Rect(zone.x, zone.bottom - 48, zone.w, 40)
        pygame.draw.rect(surf, (16, 16, 26), bas)
        pygame.draw.rect(surf, (60, 60, 90), bas, 1)
        texte(
            surf,
            "← / → : choisir  |  Entrée : acheter  |  Échap ou B : quitter la boutique",
            (bas.centerx, bas.centery),
            20,
            COULEUR_TEXTE,
            centre=True
        )

# ------------------ Overlay consommation (touche M) ------------------
class UseItemOverlay:
    """
    Menu pour consommer un objet de 'Autres objets'.
    - Visible quand self.visible == True
    - Contrôles : ↑/↓ pour choisir, Entrée pour consommer, Échap pour fermer.
    """
    def __init__(self, rect: pygame.Rect, inv: Inventaire, messages: "MessageBar"):
        self.rect = rect
        self.inv = inv
        self.messages = messages
        self.visible = False
        self.selection = 0

    def toggle(self):
        """Ouvre / ferme le menu de consommation."""
        if self.visible:
            self.visible = False
        else:
            self.visible = True
            self.selection = 0

    def handle(self, e: pygame.event.Event):
        """Gestion des touches dans le menu de consommation."""
        if not self.visible:
            return

        if e.type == pygame.KEYDOWN:
            noms = list(self.inv.autres_objets.keys())
            if not noms:
                self.messages.show("Aucun objet à consommer.")
                self.visible = False
                return

            if e.key in KEY_UPS:
                self.selection = (self.selection - 1) % len(noms)
            elif e.key in KEY_DOWNS:
                self.selection = (self.selection + 1) % len(noms)
            elif e.key in TOUCHE_OKS:
                # consomme l'objet sélectionné
                nom = noms[self.selection]
                self.inv.consommer_autre_objet(nom, self.messages)
                if self.inv.autres_objets.get(nom, 0) <= 0:
                    self.inv.autres_objets.pop(nom, None)
                if not self.inv.autres_objets:
                    self.visible = False
            elif e.key == pygame.K_ESCAPE:
                self.visible = False

    def draw(self, surf: pygame.Surface):
        """Dessine le menu de consommation."""
        if not self.visible:
            return

        dim = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 160))
        surf.blit(dim, (0, 0))

        pygame.draw.rect(surf, (25, 25, 40), self.rect)
        pygame.draw.rect(surf, (120, 120, 200), self.rect, 2)

        noms = list(self.inv.autres_objets.keys())
        if not noms:
            texte(surf, "Aucun objet à consommer", self.rect.center,
                  24, COULEUR_TEXTE, centre=True)
            return

        y = self.rect.y + 40
        for i, nom in enumerate(noms):
            qte = self.inv.autres_objets[nom]
            color = COULEUR_ACCENT if i == self.selection else COULEUR_TEXTE
            texte(surf, f"{nom} x{qte}", (self.rect.x + 30, y), 24, color)
            y += 32

        texte(
            surf,
            "↑/↓ : choisir   Entrée : consommer   Échap : fermer",
            (self.rect.centerx, self.rect.bottom - 20),
            20,
            COULEUR_MUTE,
            centre=True,
        )


# ------------------ Scène de jeu principale ------------------
class SceneJeu:
    """
    Gère toute la logique de la partie :
    - inventaire
    - plateau (grille)
    - tirage de rooms
    - boutique, messages, overlay consommation.
    """
    def __init__(self):
        self.inv = Inventaire()

        # Découpage de l'écran en 3 zones
        self.zone_gauche = pygame.Rect(0, 0, GAUCHE_W, HAUTEUR)
        self.zone_droite = pygame.Rect(LARGEUR - DROITE_W, 0, DROITE_W, HAUTEUR)
        self.zone_centre = pygame.Rect(GAUCHE_W, 0, CENTRE_W, HAUTEUR)

        # Panneaux / objets de jeu
        self.panel_perm = PanneauPermanents(self.zone_gauche, self.inv)
        self.panel_inv  = PanneauInventaire(self.zone_droite, self.inv)
        self.plateau    = Plateau(self.zone_centre, self.inv)
        self.tirage     = TiragePieces(self.zone_centre, self.inv)
        self.messages   = MessageBar()
        self.shop       = ShopOverlay(self.zone_centre, self.inv, self.messages)

        # Menu de consommation (touche M)
        rect_conso = pygame.Rect(0, 0, 520, 260)
        rect_conso.center = (LARGEUR // 2, HAUTEUR // 2)
        self.conso = UseItemOverlay(rect_conso, self.inv, self.messages)

        self.ouverture_en_cours = False  # True pendant qu'on choisit une nouvelle pièce
        self.menu_actions: List[Dict] = []  # actions 1..9 en bas à gauche

        # Curseur de visite initial = position joueur
        self.plateau.vx, self.plateau.vy = self.plateau.x, self.plateau.y

    # ---------- utilitaires ----------
    def current_cell(self) -> Cellule:
        """Renvoie la cellule où se trouve le joueur."""
        return self.plateau.grid[self.plateau.x][self.plateau.y]

    def _rebuild_actions_bas_gauche(self):
        """
        Reconstruit la liste des actions possibles (ramasser, creuser, coffre, shop)
        pour l'affichage 1..9 en bas à gauche.
        """
        self.menu_actions = []
        cell = self.current_cell()
        for pk in cell.pickables:
            if pk.get("type") == "item":
                nom = pk["nom"]
                label = f"Ramasser {nom}"
                self.menu_actions.append({"label": label, "kind": "pickup", "data": pk})
        if cell.has_trou:
            self.menu_actions.append({"label": "Creuser", "kind": "action", "req": "pelle"})
        if cell.has_coffre:
            self.menu_actions.append({"label": "Ouvrir coffre", "kind": "action", "req": "coffre"})
        if cell.has_casier:
            self.menu_actions.append({"label": "Ouvrir casier", "kind": "action", "req": "casier"})
        if cell.is_shop:
            self.menu_actions.append({"label": "Ouvrir boutique", "kind": "action", "req": None})

    # ---------- tirage / ouverture ----------
    def tenter_ouvrir_porte(self, direction: str):
        """
        Essaye d'ouvrir une porte dans la direction donnée :
        - vérifie le niveau de verrou
        - consomme clés / kit si nécessaire
        - prépare le tirage de 3 pièces.
        """
        if not self.plateau.deplacement_possible(direction):
            self.messages.show("Impossible : mur ou pas de porte.")
            return

        lvl = self.plateau.niveau_verrou_direction(direction)
        if lvl == 1:
            if self.inv.kit_crochetage:
                pass
            elif self.inv.cles > 0:
                self.inv.cles -= 1
            else:
                self.messages.show("Porte verrouillée (clé ou kit requis).")
                return
        elif lvl == 2:
            if self.inv.cles > 0:
                self.inv.cles -= 1
            else:
                self.messages.show("Double tour : clé requise.")
                return

        # Coordonnées de la cellule cible
        cx, cy = self.plateau.x, self.plateau.y
        nx, ny = cx, cy
        if direction == "N": ny -= 1
        if direction == "S": ny += 1
        if direction == "W": nx -= 1
        if direction == "E": nx += 1

        # Nombre maximum de directions possibles pour la future room
        possibles = []
        for d in ["N", "E", "S", "W"]:
            tx, ty = nx, ny
            if d == "N": ty -= 1
            if d == "S": ty += 1
            if d == "W": tx -= 1
            if d == "E": tx += 1
            if 0 <= tx < GRID_W and 0 <= ty < GRID_H:
                possibles.append(d)

        self.tirage.nb_dirs_max = len(possibles)
        self.tirage.generer()
        self.ouverture_en_cours = True

    def valider_tirage(self) -> Optional[Piece]:
        """
        Finalise le tirage :
        - vérifie le coût en gemmes
        - renvoie la pièce choisie ou None si pas assez de gemmes.
        """
        if not self.tirage.choix:
            return None
        p = self.tirage.choix[self.tirage.idx]
        if p.cout_gemmes > 0:
            if self.inv.gemmes < p.cout_gemmes:
                self.messages.show("Pas assez de gemmes.")
                return None
            self.inv.gemmes -= p.cout_gemmes
        self.ouverture_en_cours = False
        return p

    # ---------- génération loot ----------
    def _generer_loot_si_premiere_fois(self, p: Piece, cell: Cellule):
        """
        Génère le contenu de la cellule (shop, trou, coffre, pickables...)
        la première fois qu'on entre dans cette pièce.
        """
        if cell.loot_genere:
            return

        cell.is_shop    = (p.couleur == C_JAUNE)
        cell.has_casier = (p.nom.lower().strip() == "locker room")

        # Probabilité d'avoir un trou à creuser
        if "Creuser" in p.actions and isinstance(p.actions["Creuser"], int):
            proba_trou = p.actions["Creuser"] / 100.0
        else:
            proba_trou = 0.5 if p.couleur == C_VERT else 0.0
        cell.has_trou = (random.random() < proba_trou)

        # Probabilité d'avoir un coffre
        proba_coffre = p.actions.get("Coffre", 0) / 100.0
        cell.has_coffre = (random.random() < proba_coffre)

        # Bonus de chances grâce aux objets permanents
        bonus_keys = 10 if self.inv.detecteur_metaux else 0
        bonus_any  = 5  if self.inv.patte_lapin else 0

        # Clés possibles
        val_cle = p.actions.get("Clé", 0)
        if isinstance(val_cle, int) and random.random() < (val_cle + bonus_keys + bonus_any) / 100.0:
            cell.pickables.append({"type": "item", "nom": "Clé"})

        # Gemmes possibles
        val_gem = p.actions.get("Gemmes", 0)
        if isinstance(val_gem, int) and random.random() < (val_gem + bonus_any) / 100.0:
            cell.pickables.append({"type": "item", "nom": "Gemme"})

        # Or aléatoire dans certaines bleues
        if p.couleur == C_BLEU and random.random() < 0.25:
            cell.pickables.append({"type": "item", "nom": "Or", "quant": random.randint(1, 4)})

        # Si la pièce avait des actions mais qu'on n'a rien généré, on ajoute un petit bonus
        total_actions = sum(v for v in p.actions.values() if isinstance(v, int))
        if total_actions > 0 and not cell.pickables and not cell.has_trou and not cell.has_coffre and not cell.is_shop:
            if random.random() < 0.5:
                cell.pickables.append({"type": "item", "nom": "Clé"})
            else:
                cell.pickables.append({"type": "item", "nom": "Gemme"})

        cell.loot_genere = True

    def appliquer_entree_dans_piece(self, p: Piece):
        """
        Applique les effets d'entrée dans la pièce (bonus ou malus de pas),
        génère le loot, met à jour les actions et affiche un message.
        """
        if "+Pas" in p.actions:
            self.inv.pas += 5
        if "-Pas" in p.actions and self.inv.pas > 0:
            self.inv.pas = max(0, self.inv.pas - 3)

        cell = self.current_cell()
        self._generer_loot_si_premiere_fois(p, cell)
        self._rebuild_actions_bas_gauche()
        self.messages.show(f"Entrée dans {p.nom}")

        # Condition de victoire : atteindre l'Antichambre au centre de la rangée du haut
        if p.nom.lower().strip() == "antechamber" and self.plateau.x == GRID_W // 2 and self.plateau.y == 0:
            self.messages.show("Victoire ! Vous avez atteint l'Antichambre.", 4.0)

    # ---------- actions locales ----------
    def action_creuser(self):
        """Action 'Creuser' si un trou est présent dans la cellule."""
        cell = self.current_cell()
        if not cell.has_trou:
            self.messages.show("Rien à creuser ici."); return
        if not self.inv.pelle:
            self.messages.show("Il faut une pelle."); return

        if random.random() < 0.25:
            self.messages.show("Tu n'as rien trouvé en creusant.")
        else:
            lot = random.choice(list(AUTRES_CATALOGUE.keys()))
            self.inv.ajouter_autre_objet(lot)
            self.messages.show(f"Tu trouves {lot} (ajouté à Autres objets)")
        cell.has_trou = False
        self._rebuild_actions_bas_gauche()

    def action_coffre(self):
        """Action 'Ouvrir coffre' si un coffre est présent dans la cellule."""
        cell = self.current_cell()
        if not cell.has_coffre:
            self.messages.show("Pas de coffre ici."); return
        if not (self.inv.marteau or self.inv.cles > 0):
            self.messages.show("Coffre verrouillé (clé ou marteau)."); return
        if not self.inv.marteau:
            self.inv.cles -= 1
        lot = random.choice(list(AUTRES_CATALOGUE.keys()))
        self.inv.ajouter_autre_objet(lot)
        self.messages.show(f"Coffre : {lot} (ajouté à Autres objets)")
        cell.has_coffre = False
        self._rebuild_actions_bas_gauche()

    def action_casier(self):
        """Action 'Ouvrir casier' dans la Locker Room."""
        cell = self.current_cell()
        if not cell.has_casier:
            self.messages.show("Pas de casier ici."); return
        if self.inv.cles <= 0:
            self.messages.show("Casier verrouillé (clé requise)."); return
        self.inv.cles -= 1
        lot = random.choice(list(AUTRES_CATALOGUE.keys()))
        self.inv.ajouter_autre_objet(lot)
        self.messages.show(f"Casier : {lot} (ajouté à Autres objets)")
        cell.has_casier = False
        self._rebuild_actions_bas_gauche()

    # ---------- menu 1..9 ----------
    def valider_num(self, idx: int):
        """Exécute l'action associée à la touche 1..9."""
        if idx < 0 or idx >= len(self.menu_actions):
            return
        entry = self.menu_actions[idx]
        kind = entry.get("kind")
        if kind == "pickup":
            # ramasser un objet au sol
            pk = entry["data"]; nom = pk["nom"]
            if nom == "Clé":
                self.inv.cles += 1
            elif nom == "Gemme":
                self.inv.gemmes += 1
            elif nom == "Or":
                self.inv.or_ += pk.get("quant", 1)
            else:
                self.inv.ajouter_autre_objet(nom)
            try:
                self.current_cell().pickables.remove(pk)
            except ValueError:
                pass
            self._rebuild_actions_bas_gauche()
            self.messages.show(f"Ramassé : {nom}")
        elif kind == "action":
            # action spéciale (creuser, coffre, casier, boutique)
            label = entry["label"]; req = entry.get("req")
            if label == "Ouvrir boutique":
                self.shop.ouvrir(); return
            if req == "pelle":
                self.action_creuser(); return
            if req == "coffre":
                self.action_coffre(); return
            if req == "casier":
                self.action_casier(); return

    # ---------- événements ----------
    def gerer_evenement(self, e: pygame.event.Event):
        """
        Gère tous les événements clavier :
        - overlay consommation
        - tirage
        - boutique
        - déplacement, ouverture de portes, etc.
        """
        # 0) menu de consommation
        if self.conso.visible:
            self.conso.handle(e)
            return

        # 1) tirage de pièces
        if self.tirage.visible:
            prev_visible = self.tirage.visible
            self.tirage.gerer_evenement(e)

            # Si le tirage vient de se fermer et qu'on était en ouverture de porte
            if prev_visible and not self.tirage.visible and self.ouverture_en_cours:
                piece = self.valider_tirage()
                if piece is None:
                    self.ouverture_en_cours = False
                    return

                d = self.plateau.direction()
                px, py = self.plateau.x, self.plateau.y
                nx, ny = px, py
                if d == "N": ny -= 1
                if d == "S": ny += 1
                if d == "W": nx -= 1
                if d == "E": nx += 1

                cell = self.plateau.grid[nx][ny]
                cell.piece = piece
                cell.decouverte = True

                # Nombre de portes que la pièce veut
                cible = nb_portes_theoriques(piece)

                # Directions possibles (pas hors grille)
                possibles = []
                for dd in ["N", "E", "S", "W"]:
                    tx, ty = nx, ny
                    if dd == "N": ty -= 1
                    if dd == "S": ty += 1
                    if dd == "W": tx -= 1
                    if dd == "E": tx += 1
                    if 0 <= tx < GRID_W and 0 <= ty < GRID_H:
                        possibles.append(dd)

                cell.portes_existent = {k: False for k in ["N", "E", "S", "W"]}

                # On force une porte de retour vers la cellule précédente
                opp = {"N": "S", "S": "N", "E": "W", "W": "E"}[d]
                if opp in possibles:
                    cell.portes_existent[opp] = True

                nb_voulues = min(cible, len(possibles))
                deja_ouvertes = 1 if cell.portes_existent[opp] else 0
                restant = max(0, nb_voulues - deja_ouvertes)

                # On choisit d'autres directions pour compléter
                autres = [dd for dd in possibles if dd != opp]
                random.shuffle(autres)
                for dd in autres[:restant]:
                    cell.portes_existent[dd] = True

                # On ouvre la porte correspondante dans la pièce précédente
                prev_cell = self.plateau.grid[px][py]
                prev_cell.portes_existent[d] = True

                # On déplace le joueur sur la nouvelle pièce
                self.plateau.x, self.plateau.y = nx, ny
                self.inv.consommer_pas(1)

                # Génération du loot et message
                self._generer_loot_si_premiere_fois(piece, cell)
                self._rebuild_actions_bas_gauche()
                self.messages.show(f"Entrée dans {piece.nom}")
                self.plateau.vx, self.plateau.vy = self.plateau.x, self.plateau.y

                # Check victoire
                if piece.nom.lower().strip() == "antechamber" and self.plateau.x == GRID_W // 2 and self.plateau.y == 0:
                    self.messages.show("Victoire ! Vous avez atteint l'Antichambre.", 4.0)

                self.ouverture_en_cours = False
            return

        # 2) boutique
        if self.shop.visible:
            self.shop.handle(e)
            return

        # 3) ESC pour retour menu (le main interprétera "menu")
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            if not self.tirage.visible and not self.shop.visible:
                return "menu"

        if e.type == pygame.KEYDOWN:
            # touche M = menu de consommation
            if e.key == pygame.K_m:
                self.conso.toggle()
                return

            cell = self.current_cell()

            # ZQSD : choisir la direction de la porte (si elle existe)
            if e.key in (pygame.K_z, pygame.K_w):
                if cell.portes_existent.get("N", False):
                    self.plateau.dir_idx = 0
            elif e.key in (pygame.K_s,):
                if cell.portes_existent.get("S", False):
                    self.plateau.dir_idx = 2
            elif e.key in (pygame.K_q, pygame.K_a):
                if cell.portes_existent.get("W", False):
                    self.plateau.dir_idx = 3
            elif e.key in (pygame.K_d,):
                if cell.portes_existent.get("E", False):
                    self.plateau.dir_idx = 1

            # Flèches : visite des rooms déjà posées (déplacement payant en pas)
            elif e.key in (ARROW_LEFT, ARROW_RIGHT, ARROW_UP, ARROW_DOWN):
                d = None
                if e.key == ARROW_LEFT:  d = "W"
                if e.key == ARROW_RIGHT: d = "E"
                if e.key == ARROW_UP:    d = "N"
                if e.key == ARROW_DOWN:  d = "S"

                nx, ny = self.plateau.x, self.plateau.y
                if d == "N": ny -= 1
                if d == "S": ny += 1
                if d == "W": nx -= 1
                if d == "E": nx += 1

                if 0 <= nx < GRID_W and 0 <= ny < GRID_H:
                    cur = self.current_cell()
                    if cur.portes_existent.get(d, False):
                        neigh = self.plateau.grid[nx][ny]
                        if neigh.decouverte and neigh.piece is not None:
                            opp = {"N": "S", "S": "N", "E": "W", "W": "E"}[d]
                            if neigh.portes_existent.get(opp, False):
                                self.plateau.x, self.plateau.y = nx, ny
                                self.inv.consommer_pas(1)
                                self.appliquer_entree_dans_piece(neigh.piece)
                                self.plateau.vx, self.plateau.vy = nx, ny

            # OK : entrer / ouvrir nouvelle pièce
            elif e.key in TOUCHE_OKS:
                d = self.plateau.direction()
                nx, ny = self.plateau.x, self.plateau.y
                if d == "N": ny -= 1
                if d == "S": ny += 1
                if d == "W": nx -= 1
                if d == "E": nx += 1

                if 0 <= nx < GRID_W and 0 <= ny < GRID_H:
                    neigh = self.plateau.grid[nx][ny]

                    # ✅ Si la room existe déjà (ex : Antechamber), on entre directement
                    if cell.portes_existent.get(d, False) and neigh.piece is not None:
                        self.plateau.x, self.plateau.y = nx, ny
                        neigh.decouverte = True
                        self.inv.consommer_pas(1)
                        self.appliquer_entree_dans_piece(neigh.piece)
                        self.plateau.vx, self.plateau.vy = nx, ny
                        return

                # Sinon : on ouvre une nouvelle pièce via un tirage
                if not self.plateau.deplacement_possible(d):
                    self.messages.show("Impossible d'aller là.")
                    return
                self.tenter_ouvrir_porte(d)


            # Raccourcis actions locales
            elif e.key == pygame.K_c:
                self.action_creuser()
            elif e.key == pygame.K_o:
                self.action_coffre()
            elif e.key == pygame.K_l:
                self.action_casier()
            elif e.key == pygame.K_b:
                if cell.is_shop:
                    self.shop.ouvrir()
                else:
                    self.messages.show("Pas de boutique ici.")
            # Actions 1..9
            elif pygame.K_1 <= e.key <= pygame.K_9:
                idx = e.key - pygame.K_1
                self.valider_num(idx)

    # ---------- rendu / fin ----------
    def _dessiner_menu_bas_gauche(self, surf: pygame.Surface):
        """Dessine les actions numérotées 1..9 en bas à gauche."""
        zone = pygame.Rect(12, HAUTEUR - 220, GAUCHE_W - 24, 208)
        pygame.draw.rect(surf, (18, 18, 26), zone)
        pygame.draw.rect(surf, (60, 60, 80), zone, 1)
        texte(surf, "Actions (1..9)", (zone.x + 10, zone.y + 8), 20, COULEUR_ACCENT)
        y = zone.y + 34
        for i, entry in enumerate(self.menu_actions[:9], start=1):
            label = entry["label"]
            ok = True
            if entry.get("kind") == "action":
                req = entry.get("req")
                # on colore en rouge si condition non remplie
                if req == "pelle":    ok = self.inv.pelle
                elif req == "coffre": ok = (self.inv.marteau or self.inv.cles > 0)
                elif req == "casier": ok = (self.inv.cles > 0)
            col = (120, 220, 160) if ok else (220, 120, 120)
            texte(surf, f"{i}. {label}", (zone.x + 12, y), 20, col)
            y += 22

    def _bloque_sans_progression(self) -> bool:
        """
        Détecte un état "bloqué" où aucune porte ne permet
        d'avancer (pas de clé/kit pour ouvrir, etc.).
        """
        dirs = ["N", "E", "S", "W"]
        for d in dirs:
            nx, ny = self.plateau.x, self.plateau.y
            if d == "N": ny -= 1
            if d == "S": ny += 1
            if d == "W": nx -= 1
            if d == "E": nx += 1
            if nx < 0 or nx >= GRID_W or ny < 0 or ny >= GRID_H:
                continue
            if not self.current_cell().portes_existent.get(d, False):
                continue
            voisin = self.plateau.grid[nx][ny]
            if voisin.decouverte and voisin.piece is not None:
                return False
            lvl = self.plateau.niveau_verrou_direction(d)
            if lvl == 0: return False
            if lvl == 1 and (self.inv.kit_crochetage or self.inv.cles > 0): return False
            if lvl == 2 and (self.inv.cles > 0): return False
        return True

    def dessiner(self, surf: pygame.Surface):
        """Dessine l'écran de jeu complet (panneaux, plateau, overlays)."""
        self.panel_perm.dessiner(surf)
        self.panel_inv.dessiner(surf)
        self.plateau.dessiner(surf)
        self._dessiner_menu_bas_gauche(surf)
        if self.tirage.visible: self.tirage.dessiner(surf)
        if self.shop.visible:   self.shop.draw(surf)
        self.conso.draw(surf)
        self.messages.draw(surf)

        # Écran de défaite si plus de pas
        if self.inv.pas == 0:
            dim = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
            dim.fill((0, 0, 0, 200))
            surf.blit(dim, (0, 0))
            texte(surf, "Défaite : vous n'avez plus de pas.",
                  (LARGEUR // 2, HAUTEUR // 2), 36, (240, 120, 120), centre=True)
        # Écran "bloqué" si aucune progression possible
        elif self._bloque_sans_progression():
            dim = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
            dim.fill((0, 0, 0, 160))
            surf.blit(dim, (0, 0))
            texte(surf, "Bloqué : aucune progression possible (portes inaccessibles).",
                  (LARGEUR // 2, HAUTEUR // 2), 32, (240, 120, 120), centre=True)

    def update(self, dt: float):
        """Update simple (pour le moment, seulement la barre de messages)."""
        self.messages.update(dt)








