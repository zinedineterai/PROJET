# main.py
import sys
import os
import functools
import pygame
from jeu import *           # éléments du vrai jeu (SceneJeu, constantes, etc.)
from objet_gestion import * # données sur les objets (inventaire, objets permanents, etc.)
from main import *          # ⚠ à éviter normalement, mais je ne touche pas à ta logique


# ---------- Config / Couleurs ----------
TITLE = "Blue Prince — Projet POO"
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BG = (18, 22, 28)
PRIMARY = (80, 160, 255)
PRIMARY_HOVER = (120, 190, 255)
GREY = (200, 200, 200)

pygame.init()
clock = pygame.time.Clock()

# ---------- Image de fond du menu ----------
# On charge une image de fond si elle existe, sinon on aura un fond uni.
BG_IMAGE_ORIG = None
try:
    BG_IMAGE_ORIG = pygame.image.load("assets/menu_bg.jpg")
except Exception:
    BG_IMAGE_ORIG = None  # si le fichier n'existe pas, on garde un fond uni

# ---------- Fonctions de texte communes au MENU ----------

# Petit cache de polices pour ne pas recréer les fonts à chaque frame.
_FONT_CACHE = {}

def police(size: int) -> pygame.font.Font:
    """Retourne une police Pygame mise en cache pour une taille donnée."""
    if size in _FONT_CACHE:
        return _FONT_CACHE[size]
    f = pygame.font.Font(None, size)   # ou SysFont("arial", size)
    _FONT_CACHE[size] = f
    return f

def _wrap_text(text: str, font: pygame.font.Font, max_width: int):
    """Coupe un texte long en plusieurs lignes pour respecter une largeur max."""
    words = text.split()
    lines = []
    current = ""

    for w in words:
        test = (current + " " + w).strip()
        if font.size(test)[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = w

    if current:
        lines.append(current)

    return lines


def draw_background(surface):
    """Dessine le fond du menu (image redimensionnée ou fond uni)."""
    if BG_IMAGE_ORIG is not None:
        w, h = surface.get_size()
        bg = pygame.transform.smoothscale(BG_IMAGE_ORIG, (w, h))
        surface.blit(bg, (0, 0))
    else:
        surface.fill(BG)

# ---------- Utils ----------
def draw_text_center(surface, text, font, color, center):
    """Affiche un texte centré à une position donnée."""
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=center)
    surface.blit(surf, rect)
    return rect

@functools.lru_cache(maxsize=128)
def load_icon_cached(path, size):
    """Charge une image en cache et la redimensionne à 'size'."""
    try:
        if path and os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            return pygame.transform.smoothscale(img, size)
    except Exception:
        pass
    return None  # si erreur ou fichier absent, on renvoie None

def wrap_text(text, font, max_width):
    """Coupe un texte en plusieurs lignes pour tenir dans max_width."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if font.size(t)[0] <= max_width:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

class Button:
    """Bouton rectangulaire cliquable avec texte centré."""
    def __init__(self, text, center_pos, width=420, height=90, radius=16, font=None):
        self.text = text
        self.rect = pygame.Rect(0, 0, width, height)
        self.rect.center = center_pos
        self.radius = radius
        self.font = font or pygame.font.Font(None, 48)

    def draw(self, surf):
        """Dessine le bouton et gère le survol de la souris."""
        mouse_pos = pygame.mouse.get_pos()
        hovered = self.rect.collidepoint(mouse_pos)
        color = PRIMARY_HOVER if hovered else PRIMARY
        pygame.draw.rect(surf, color, self.rect, border_radius=self.radius)
        pygame.draw.rect(surf, BLACK, self.rect, width=3, border_radius=self.radius)
        txt = self.font.render(self.text, True, BLACK)
        surf.blit(txt, txt.get_rect(center=self.rect.center))
        return hovered

    def is_clicked(self, event):
        """Retourne True si le bouton est cliqué avec le bouton gauche."""
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )

# ---------- Écran de choix de résolution (500x500) ----------
def choose_resolution_screen():
    """Petit écran séparé pour choisir la résolution au lancement."""
    picker = pygame.display.set_mode((500, 500))
    pygame.display.set_caption(f"{TITLE} — Choix de la résolution")

    title_font = pygame.font.Font(None, 42)
    opt_font = pygame.font.Font(None, 32)
    foot_font = pygame.font.Font(None, 24)

    # Liste des options possibles de résolution
    options = [
        ("1280 x 720", (1280, 720)),
        ("1600 x 900", (1600, 900)),
        ("1920 x 1080", (1920, 1080)),
        ("2560 x 1440", (2560, 1440)),
        ("Fenêtre adaptative (écran)", "desktop"),
        ("Plein écran", "fullscreen"),
    ]
    selected_idx = 2  # 1080p par défaut
    validate_btn = Button("Valider", (250, 430), width=260, height=60, font=opt_font)

    # On prépare les rectangles des "radios" à cliquer
    radio_rects = []
    start_y, spacing = 140, 50
    for i in range(len(options)):
        radio_rects.append(pygame.Rect(80, start_y + i * spacing, 24, 24))

    # Boucle de l'écran de choix
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse = event.pos
                # On détecte sur quel bouton radio on clique
                for i, r in enumerate(radio_rects):
                    label_rect = pygame.Rect(r.right + 10, r.y - 6, 320, r.height + 12)
                    if r.collidepoint(mouse) or label_rect.collidepoint(mouse):
                        selected_idx = i
                # Bouton "Valider"
                if validate_btn.is_clicked(event):
                    _, value = options[selected_idx]
                    if value == "fullscreen":
                        return (0, 0, True)
                    elif value == "desktop":
                        info = pygame.display.Info()
                        return (info.current_w, info.current_h, False)
                    else:
                        return (*value, False)

        picker.fill((30, 30, 38))
        draw_text_center(picker, "Choisissez votre résolution", title_font, WHITE, (250, 60))
        draw_text_center(picker, "Cliquez puis 'Valider'", foot_font, GREY, (250, 95))

        # Dessin des radios + labels
        for i, (label, _) in enumerate(options):
            r = radio_rects[i]
            pygame.draw.ellipse(picker, WHITE, r, width=2)
            if i == selected_idx:
                inner = r.inflate(-10, -10)
                pygame.draw.ellipse(picker, PRIMARY, inner)
            txt = opt_font.render(label, True, WHITE)
            picker.blit(txt, (r.right + 10, r.y - 6))

        validate_btn.draw(picker)
        draw_text_center(picker, "Échap pour quitter", foot_font, GREY, (250, 480))

        pygame.display.flip()
        clock.tick(60)

# ---------- Construction écran principal ----------
def setup_display(width, height, fullscreen=False):
    """
    Crée la fenêtre principale avec la bonne résolution
    et prépare les polices dépendantes de la taille.
    """
    flags = pygame.FULLSCREEN if fullscreen else 0
    if fullscreen:
        screen = pygame.display.set_mode((0, 0), flags)
        info = pygame.display.Info()
        width, height = info.current_w, info.current_h
    else:
        screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption(TITLE)

    # Polices qui s'adaptent à la hauteur de la fenêtre
    title_font = pygame.font.Font(None, max(72, height // 9))
    btn_font = pygame.font.Font(None, max(38, height // 20))
    foot_font = pygame.font.Font(None, max(20, height // 45))
    return screen, (width, height), title_font, btn_font, foot_font

# ---------- Dessins communs ----------
def draw_title(surf, size, title_font, btn_font, subtitle="Projet POO — Page d’accueil"):
    """Affiche le titre du jeu + un sous-titre centré en haut."""
    WIDTH, HEIGHT = size
    t_surf = title_font.render("BLUE PRINCE", True, WHITE)
    s_surf = btn_font.render(subtitle, True, GREY)
    surf.blit(t_surf, t_surf.get_rect(center=(WIDTH//2, HEIGHT//4)))
    surf.blit(s_surf, s_surf.get_rect(center=(WIDTH//2, HEIGHT//4 + title_font.get_height()//2)))

def draw_footer(surf, size, foot_font, text="Astuce : clique sur un bouton — Échap pour quitter"):
    """Texte d'aide en bas de l'écran."""
    WIDTH, HEIGHT = size
    h_surf = foot_font.render(text, True, GREY)
    surf.blit(h_surf, h_surf.get_rect(midbottom=(WIDTH//2, HEIGHT-20)))

# ---------- Écran placeholder (utile si besoin ailleurs) ----------
def dummy_screen(screen, size, foot_font, label):
    """
    Écran temporaire générique (utile si on veut un écran vide
    avec juste un texte et la touche Échap pour revenir).
    """
    WIDTH, HEIGHT = size
    title = pygame.font.Font(None, max(48, HEIGHT // 18)).render(f"Écran: {label}", True, WHITE)
    back_text = foot_font.render("Échap pour revenir", True, GREY)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return
                draw_background(screen)
        # petit voile sombre pour bien lire le texte
        voile = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        voile.fill((0, 0, 0, 140))
        screen.blit(voile, (0, 0))

        screen.blit(title, title.get_rect(center=(WIDTH//2, HEIGHT//2 - 20)))
        screen.blit(back_text, back_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 40)))
        pygame.display.flip()
        clock.tick(60)

# ---------- Menu principal ----------
def main_menu(screen, size, title_font, btn_font, foot_font, partie_en_cours: bool):
    """
    Affiche le menu principal :
    - Jouer / Reprendre
    - Découverte
    - Options
    - Quitter
    Renvoie l'action choisie sous forme de code.
    """
    WIDTH, HEIGHT = size
    gap = max(80, HEIGHT // 9)
    start_y = HEIGHT // 2 - gap + 50

    # Création des 4 gros boutons du menu principal
    buttons = [
        Button("Jouer / Reprendre la partie", (WIDTH // 2, start_y),
               width=max(360, WIDTH // 3), height=max(70, HEIGHT // 12), font=btn_font),
        Button("Découverte", (WIDTH // 2, start_y + gap),
               width=max(320, WIDTH // 4), height=max(70, HEIGHT // 12), font=btn_font),
        Button("Options", (WIDTH // 2, start_y + 2 * gap),
               width=max(320, WIDTH // 4), height=max(70, HEIGHT // 12), font=btn_font),
        Button("Quitter", (WIDTH // 2, start_y + 3 * gap),
               width=max(320, WIDTH // 4), height=max(70, HEIGHT // 12), font=btn_font),
    ]

    # Boucle du menu principal
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "QUIT"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "QUIT"

            # Gestion des clics sur les boutons
            for b in buttons:
                if b.is_clicked(event):
                    if b.text.startswith("Jouer"):
                        # Sous-menu "Reprendre / Nouvelle partie"
                        res = play_or_resume_menu(screen, size, btn_font, foot_font, partie_en_cours)
                        if res in ("RESUME", "NEW_GAME"):
                            return res
                    elif b.text == "Découverte":
                        return "DECOUVERTE"
                    elif b.text == "Options":
                        return "OPTIONS"
                    elif b.text == "Quitter":
                        return "QUIT"

        draw_background(screen)
        for b in buttons:
            b.draw(screen)
        draw_footer(screen, size, foot_font)
        pygame.display.flip()
        clock.tick(60)


def play_or_resume_menu(screen, size, btn_font, foot_font, partie_en_cours: bool):
    """
    Petit menu centré :
    - Reprendre la partie
    - Nouvelle partie
    - Retour
    Renvoie "RESUME", "NEW_GAME" ou "BACK".
    """
    WIDTH, HEIGHT = size
    gap = max(70, HEIGHT // 12)
    center_y = HEIGHT // 2

    btn_resume = Button("Reprendre la partie",
                        (WIDTH // 2, center_y - gap),
                        width=max(360, WIDTH // 3), height=max(65, HEIGHT // 14), font=btn_font)
    btn_new = Button("Nouvelle partie",
                     (WIDTH // 2, center_y),
                     width=max(360, WIDTH // 3), height=max(65, HEIGHT // 14), font=btn_font)
    btn_back = Button("← Retour",
                      (WIDTH // 2, center_y + gap),
                      width=max(260, WIDTH // 4), height=max(60, HEIGHT // 15), font=btn_font)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "BACK"

            if btn_back.is_clicked(event):
                return "BACK"

            # Reprendre la partie (si une partie existe)
            if btn_resume.is_clicked(event) and partie_en_cours:
                return "RESUME"

            # Nouvelle partie
            if btn_new.is_clicked(event):
                return "NEW_GAME"

        # fond semi-transparent par-dessus le menu principal
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        # cadre central
        box_w, box_h = int(WIDTH * 0.6), int(HEIGHT * 0.55)
        box = pygame.Rect(0, 0, box_w, box_h)
        box.center = (WIDTH // 2, HEIGHT // 2)
        pygame.draw.rect(screen, (25, 30, 40), box, border_radius=18)
        pygame.draw.rect(screen, PRIMARY, box, width=3, border_radius=18)

        # titre
        title_font_local = pygame.font.Font(None, max(40, HEIGHT // 16))
        draw_text_center(screen, "Jouer / Reprendre", title_font_local, WHITE, (WIDTH // 2, box.y + 55))

        # boutons
        # Reprendre grisé si aucune partie
        if not partie_en_cours:
            # on dessine le bouton normalement, puis on ajoute un voile gris
            btn_resume.draw(screen)
            voile = pygame.Surface(btn_resume.rect.size, pygame.SRCALPHA)
            voile.fill((0, 0, 0, 140))
            screen.blit(voile, btn_resume.rect.topleft)
            txt = pygame.font.Font(None, 24).render("(aucune partie en cours)", True, GREY)
            screen.blit(txt, txt.get_rect(center=(btn_resume.rect.centerx, btn_resume.rect.bottom + 18)))
        else:
            btn_resume.draw(screen)

        btn_new.draw(screen)
        btn_back.draw(screen)

        # info en bas du cadre
        foot_text = "Échap : retour au menu principal"
        foot = foot_font.render(foot_text, True, GREY)
        screen.blit(foot, foot.get_rect(midbottom=(WIDTH // 2, box.bottom - 12)))

        pygame.display.flip()
        clock.tick(60)


# ---------- Catalogue des pièces (rooms) ----------
class RoomCatalogueScreen:
    """
    Écran de catalogue des pièces (dans le menu Découverte).
    On peut changer d'étage (couleur) et de pièce avec le clavier.
    """

    def __init__(self, screen, size, title_font, btn_font, foot_font):
        self.screen = screen
        self.size = size
        self.title_font = title_font
        self.btn_font = btn_font
        self.foot_font = foot_font

        self.running = True

        # Ordre des "étages" (groupes de couleurs)
        self.couleurs = ["Bleue", "Verte", "Violette", "Orange", "Rouge", "Jaune"]
        self.etage_index = 0          # étage courant (couleur)
        self.room_index = 0           # index de la pièce dans cet étage

        # Petit texte d'explication pour chaque couleur
        self.couleur_desc = {
            "Bleue":    "Pièces bleues : salles communes aux effets variés (un peu de tout).",
            "Verte":    "Pièces vertes : jardins / serres, beaucoup d'endroits à creuser et de gemmes.",
            "Violette": "Pièces violettes : chambres qui redonnent surtout des pas (repos).",
            "Orange":   "Pièces oranges : couloirs / escaliers, beaucoup de portes (bonne connectivité).",
            "Rouge":    "Pièces rouges : salles dangereuses, gros risques de perdre des pas.",
            "Jaune":    "Pièces jaunes : boutiques et salles spéciales (magasin, vault, casino...).",
        }

        # Couleurs d'encadrement (importées depuis jeu.py)
        self.couleur_rgb = {
            "Bleue":    C_BLEU,
            "Verte":    C_VERT,
            "Violette": C_VIOLET,
            "Orange":   C_ORANGE,
            "Rouge":    C_ROUGE,
            "Jaune":    C_JAUNE,
        }

        # Dictionnaire couleur -> liste de rooms
        self.rooms_by_color = {c: [] for c in self.couleurs}

        # On parcourt toutes les rooms et on les range par couleur
        for room in ROOM_DATA:
            c = room.get("color")
            if c not in self.rooms_by_color:
                continue

            # on charge l'image depuis le champ "icon"
            img = None
            icon_path = room.get("icon")
            if icon_path:
                img = load_icon_cached(icon_path, (600, 320))

            self.rooms_by_color[c].append({
                "name":  room["name"],
                "color": c,
                "group": room.get("group", ""),
                "desc":  room.get("desc", ""),
                "image": img,
            })

        # On trie chaque liste par ordre alphabétique de nom
        for c in self.couleurs:
            self.rooms_by_color[c].sort(key=lambda r: r["name"])

    # ---------------- boucle principale ----------------
    def run(self):
        """Boucle d'affichage / interaction du catalogue."""
        clock_local = pygame.time.Clock()
        while self.running:
            dt = clock_local.tick(60) / 1000.0  # dt si un jour on en a besoin

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                elif event.type == pygame.KEYDOWN:
                    # Quitter l'écran de catalogue
                    if event.key == TOUCHE_RETOUR:
                        self.running = False
                        return

                    # Changer d'étage (couleur)
                    if event.key in KEY_UPS:   # Z / W
                        self.etage_index = (self.etage_index - 1) % len(self.couleurs)
                        self.room_index = 0
                    elif event.key in KEY_DOWNS:  # S
                        self.etage_index = (self.etage_index + 1) % len(self.couleurs)
                        self.room_index = 0

                    # Changer de room dans l'étage courant
                    elif event.key in KEY_LEFTS:  # Q / A
                        rooms = self.rooms_by_color[self.couleurs[self.etage_index]]
                        if rooms:
                            self.room_index = (self.room_index - 1) % len(rooms)
                    elif event.key in KEY_RIGHTS:  # D
                        rooms = self.rooms_by_color[self.couleurs[self.etage_index]]
                        if rooms:
                            self.room_index = (self.room_index + 1) % len(rooms)

            self.draw()
            pygame.display.flip()

    # ---------------- dessin ----------------
    def draw(self):
        """Dessine l'écran de catalogue pour la pièce et la couleur courantes."""
        w, h = self.size
        surf = self.screen
        surf.fill(BG)

        # Titre principal
        titre = "Catalogue des pièces"
        texte(surf, titre, (w // 2, 40), 42, COULEUR_TEXTE, centre=True)

        # Couleur / étage courant (nom lisible)
        couleur_courante = self.couleurs[self.etage_index]
        label_couleur = {
            "Bleue":    "pièces bleues",
            "Verte":    "pièces vertes",
            "Violette": "pièces violettes",
            "Orange":   "pièces oranges",
            "Rouge":    "pièces rouges",
            "Jaune":    "pièces jaunes",
        }[couleur_courante]

        header = f"Étage : {label_couleur}"
        texte(surf, header, (w // 2, 90), 26, COULEUR_TEXTE, centre=True)

        # Texte explicatif selon la couleur
        exp = self.couleur_desc.get(couleur_courante, "")
        if exp:
            texte(surf, exp, (w // 2, 120), 20, COULEUR_MUTE, centre=True)

        rooms = self.rooms_by_color[couleur_courante]
        if not rooms:
            # Cas où aucune pièce n'est définie pour cette couleur
            texte(
                surf,
                "Aucune pièce définie pour cette couleur.",
                (w // 2, h // 2),
                26,
                COULEUR_TEXTE,
                centre=True,
            )
            return

        room = rooms[self.room_index]

        # Carte centrale qui contient l'image + description
        card_w, card_h = int(w * 0.5), int(h * 0.6)
        card = pygame.Rect(0, 0, card_w, card_h)
        card.center = (w // 2, h // 2 + 40)

        pygame.draw.rect(surf, (20, 20, 30), card)
        border_col = self.couleur_rgb.get(couleur_courante, COULEUR_ACCENT)
        pygame.draw.rect(surf, border_col, card, 4)

        # Nom de la room en haut de la carte
        texte(surf, room["name"], (card.centerx, card.y + 24), 28, COULEUR_TEXTE, centre=True)

        # Zone réservée pour l'image de la pièce
        img_zone = pygame.Rect(
            card.x + 20,
            card.y + 60,
            card.w - 40,
            int(card.h * 0.45),
        )

        img = room.get("image")

        if img:
            # On centre l'image dans la zone (elle est déjà à peu près à la bonne taille)
            img_rect = img.get_rect()
            img_rect.center = img_zone.center
            surf.blit(img, img_rect)
        else:
            # placeholder si jamais l'image n'est pas trouvée
            pygame.draw.rect(surf, (40, 40, 60), img_zone)
            pygame.draw.rect(surf, border_col, img_zone, 2)
            texte(surf, "Aperçu non disponible", img_zone.center, 20, COULEUR_MUTE, centre=True)

        # Description textuelle en bas de la carte
        y_text = img_zone.bottom + 16

        if room.get("group"):
            texte(surf, f"Groupe : {room['group']}", (card.x + 24, y_text), 22, COULEUR_TEXTE)
            y_text += 30

        desc = room.get("desc", "")
        if desc:
            # Découpage très simple en 2 lignes max
            mots = desc.split()
            line1 = []
            line2 = []
            for m in mots:
                if len(" ".join(line1 + [m])) < 40:
                    line1.append(m)
                else:
                    line2.append(m)

            texte(surf, " ".join(line1), (card.x + 24, y_text), 20, COULEUR_MUTE)
            y_text += 24
            if line2:
                texte(surf, " ".join(line2), (card.x + 24, y_text), 20, COULEUR_MUTE)

        # Rappel des touches en bas de l'écran
        help_text = "Z/S : changer d'étage  |  Q/D : changer de pièce  |  Échap : retour"
        texte(surf, help_text, (w // 2, h - 40), 20, COULEUR_MUTE, centre=True)


# ---------- Classe: Découverte (avec sous-menu Objets) ----------
class DiscoveryMenu:
    """Sous-menu 'Découverte' : catalogue des pièces, inventaire et objets."""
    def __init__(self, screen, size, title_font, btn_font, foot_font):
        self.screen = screen
        self.size = size
        self.title_font = title_font
        self.btn_font = btn_font
        self.foot_font = foot_font
        self.WIDTH, self.HEIGHT = size
        self.gap = max(80, self.HEIGHT // 10)
        self.start_y = self.HEIGHT // 2 - self.gap + 50

        # Trois choix principaux dans Découverte
        self.buttons = [
            Button("Catalogue des pièces",         (self.WIDTH//2, self.start_y),
                   width=max(380, self.WIDTH//3), height=max(70, self.HEIGHT//12), font=self.btn_font),
            Button("Inventaire",                   (self.WIDTH//2, self.start_y + self.gap),
                   width=max(380, self.WIDTH//3), height=max(70, self.HEIGHT//12), font=self.btn_font),
            Button("Objets",                       (self.WIDTH//2, self.start_y + 2*self.gap),
                   width=max(380, self.WIDTH//3), height=max(70, self.HEIGHT//12), font=self.btn_font),
        ]
        self.back_btn = Button("← Retour", (self.WIDTH//2, self.start_y + 4*self.gap),
                               width=max(280, self.WIDTH//5), height=max(60, self.HEIGHT//14), font=self.btn_font)

    def run(self):
        """Boucle du sous-menu Découverte."""
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return "BACK"
                if self.back_btn.is_clicked(event):
                    return "BACK"
                for b in self.buttons:
                    if b.is_clicked(event):
                        if b.text == "Objets":
                            return self.run_objects_menu()
                        else:
                            # Renvoie directement le texte du bouton ("Catalogue des pièces" ou "Inventaire")
                            return b.text

            draw_background(self.screen)
            for b in self.buttons:
                b.draw(self.screen)
            self.back_btn.draw(self.screen)
            draw_footer(self.screen, self.size, self.foot_font, text="Échap pour revenir")
            pygame.display.flip()
            clock.tick(60)

    def run_objects_menu(self):
        """
        Sous-sous-menu pour séparer les objets permanents
        et les autres objets.
        """
        import pygame
        gap = max(80, self.HEIGHT // 10)
        start_y = self.HEIGHT // 2 - gap
        buttons = [
            Button("Objets permanents", (self.WIDTH//2, start_y),
                   width=max(380, self.WIDTH//3), height=max(70, self.HEIGHT//12), font=self.btn_font),
            Button("Autres objets",     (self.WIDTH//2, start_y + gap),
                   width=max(380, self.WIDTH//3), height=max(70, self.HEIGHT//12), font=self.btn_font),
        ]
        back_btn = Button("← Retour", (self.WIDTH//2, start_y + 2*gap),
                          width=max(280, self.WIDTH//5), height=max(60, self.HEIGHT//14), font=self.btn_font)

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return "BACK"
                if back_btn.is_clicked(event):
                    return "BACK"
                for b in buttons:
                    if b.is_clicked(event):
                        # On renvoie un code simple selon le bouton
                        return "PERMANENTS" if b.text == "Objets permanents" else "AUTRES"

            draw_background(self.screen)
            for b in buttons:
                b.draw(self.screen)
            back_btn.draw(self.screen)
            draw_footer(self.screen, self.size, self.foot_font, text="Échap pour revenir")
            pygame.display.flip()
            clock.tick(60)

# ---------- Écran de liste scrollable ----------
class ScrollListScreen:
    """
    Écran générique pour afficher une liste d'items avec :
    - icône (facultatif)
    - titre
    - description multi-lignes
    avec scroll vertical.
    """
    def __init__(self, screen, size, title_font, item_font, foot_font, title, items):
        self.screen = screen
        self.W, self.H = size
        self.title_font = title_font
        self.item_font = item_font
        self.foot_font = foot_font
        self.title = title
        self.items = items

        # Paramètres d'UI (marges, hauteur de ligne, etc.)
        self.margin = max(24, self.W // 80)
        self.header_h = max(80, self.H // 6)
        self.item_h = max(96, self.H // 10)
        self.icon_size = (self.item_h - 24, self.item_h - 24)
        self.row_gap = max(8, self.H // 120)

        # Zone dans laquelle la liste peut défiler
        self.list_rect = pygame.Rect(self.margin, self.header_h,
                                     self.W - 2*self.margin, self.H - self.header_h - 80)
        self.scroll_y = 0
        self.scroll_speed = max(24, self.item_h // 6)

        # Bouton de retour en bas de l'écran
        self.back_btn = Button("← Retour",
                               (self.W//2, self.H - 30),
                               width=max(240, self.W//6), height=max(48, self.H//18),
                               font=self.item_font)

        # Pré-calcul des lignes à afficher
        self.rows = self._build_rows()

    def _build_rows(self):
        """Construit les 'lignes' internes (position, texte, icône) à partir des items."""
        rows = []
        x = self.list_rect.x + 16
        y = 0
        text_w = self.list_rect.w - self.icon_size[0] - 48

        for it in self.items:
            icon = load_icon_cached(it.get("icon"), self.icon_size)
            title_surf = self.item_font.render(it["name"], True, (255, 255, 255))
            desc_lines = wrap_text(it.get("desc", ""), self.foot_font, text_w)
            rows.append({
                "rect": pygame.Rect(x, y, self.list_rect.w - 16, self.item_h),
                "icon": icon,
                "title": title_surf,
                "desc_lines": desc_lines,
            })
            y += self.item_h + self.row_gap
        # hauteur totale du contenu scrollable
        self.content_h = max(y - self.row_gap, self.list_rect.h)
        return rows

    def _draw_row(self, surface, row, y_offset):
        """Dessine une ligne individuelle de la liste (si elle est visible)."""
        r = row["rect"].copy()
        r.y = self.list_rect.y + (row["rect"].y - self.scroll_y) + y_offset
        if r.bottom < self.list_rect.top or r.top > self.list_rect.bottom:
            return

        pygame.draw.rect(surface, (35, 40, 50), r, border_radius=12)
        pygame.draw.rect(surface, (0, 0, 0), r, width=2, border_radius=12)

        icon_rect = pygame.Rect(r.x + 12, r.y + 12, *self.icon_size)
        if row["icon"]:
            surface.blit(row["icon"], icon_rect)
        else:
            # petit placeholder pour les items sans icône
            pygame.draw.rect(surface, (70, 80, 95), icon_rect, border_radius=8)
            pygame.draw.line(surface, (40, 45, 60), icon_rect.topleft, icon_rect.bottomright, 2)
            pygame.draw.line(surface, (40, 45, 60), icon_rect.topright, icon_rect.bottomleft, 2)

        # Texte (titre + description)
        tx = icon_rect.right + 16
        ty = r.y + 12
        surface.blit(row["title"], (tx, ty))
        ty += row["title"].get_height() + 6
        for line in row["desc_lines"]:
            ls = self.foot_font.render(line, True, (200, 200, 200))
            surface.blit(ls, (tx, ty))
            ty += ls.get_height() + 2

    def _draw_scrollbar(self, surface):
        """Dessine la petite barre de scroll sur la droite si nécessaire."""
        if self.content_h <= self.list_rect.h:
            return
        bar_w = 8
        track = pygame.Rect(self.list_rect.right - bar_w - 4, self.list_rect.y, bar_w, self.list_rect.h)
        pygame.draw.rect(surface, (55, 60, 70), track, border_radius=4)
        ratio = self.list_rect.h / self.content_h
        thumb_h = max(int(self.list_rect.h * ratio), 24)
        max_scroll = self.content_h - self.list_rect.h
        t = 0 if max_scroll == 0 else self.scroll_y / max_scroll
        thumb_y = track.y + int((track.h - thumb_h) * t)
        thumb = pygame.Rect(track.x, thumb_y, bar_w, thumb_h)
        pygame.draw.rect(surface, (120, 190, 255), thumb, border_radius=4)

    def run(self):
        """Boucle d'affichage et de gestion du scroll."""
        import pygame
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "BACK"
                    # Scroll clavier
                    elif event.key in (pygame.K_UP, pygame.K_z):
                        self.scroll_y = max(0, self.scroll_y - self.scroll_speed)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self.scroll_y = min(self.content_h - self.list_rect.h, self.scroll_y + self.scroll_speed)
                    elif event.key == pygame.K_PAGEUP:
                        self.scroll_y = max(0, self.scroll_y - self.list_rect.h // 2)
                    elif event.key == pygame.K_PAGEDOWN:
                        self.scroll_y = min(self.content_h - self.list_rect.h, self.scroll_y + self.list_rect.h // 2)

                # Scroll molette
                if event.type == pygame.MOUSEWHEEL and self.content_h > self.list_rect.h:
                    self.scroll_y = min(max(0, self.scroll_y - event.y * self.scroll_speed),
                                        self.content_h - self.list_rect.h)

                # Retour
                if self.back_btn.is_clicked(event):
                    return "BACK"

            draw_background(self.screen)
            draw_title(self.screen, (self.W, self.H), self.title_font, self.item_font, subtitle=self.title)

            # On limite le dessin à la zone de la liste (clip)
            clip = self.screen.get_clip()
            self.screen.set_clip(self.list_rect)
            for row in self.rows:
                self._draw_row(self.screen, row, y_offset=0)
            self.screen.set_clip(clip)

            self._draw_scrollbar(self.screen)
            self.back_btn.draw(self.screen)
            draw_footer(self.screen, (self.W//2, self.H), self.foot_font,
                        text="Molette/↑↓ pour défiler — Échap ou Retour")

            pygame.display.flip()
            clock.tick(60)

# ---------- Helpers d'écrans objets ----------
def show_permanent_objects(screen, size, title_font, btn_font, foot_font):
    """Affiche l'écran des objets permanents en utilisant ScrollListScreen."""
    ui = ScrollListScreen(screen, size, title_font, btn_font, foot_font,
                          title="Objets permanents", items=PERMANENT_OBJECTS)
    return ui.run()

def show_other_objects(screen, size, title_font, btn_font, foot_font):
    """Affiche l'écran des autres objets."""
    ui = ScrollListScreen(screen, size, title_font, btn_font, foot_font,
                          title="Autres objets", items=OTHER_OBJECTS)
    return ui.run()

def show_inventory(screen, size, title_font, btn_font, foot_font):
    """Affiche l'inventaire du joueur (pour la partie Découverte)."""
    ui = ScrollListScreen(
        screen,
        size,
        title_font,
        btn_font,
        foot_font,
        title="Inventaire du joueur / de la joueuse",
        items=INVENTORY_ITEMS,
    )
    return ui.run()

class OptionsScreen:
    """
    Écran d'options :
    - Volume de la musique
    - Changement de résolution (réutilise choose_resolution_screen)
    """
    def __init__(self, screen, size, title_font, btn_font, foot_font,
                 volume_init: float, w_init: int, h_init: int, fullscreen_init: bool):
        self.screen = screen
        self.size = size
        self.title_font = title_font
        self.btn_font = btn_font
        self.foot_font = foot_font

        self.WIDTH, self.HEIGHT = size
        self.volume = float(volume_init)
        self.w = w_init
        self.h = h_init
        self.fullscreen = fullscreen_init

        # Menu simple avec 3 lignes
        self.options = [
            "Volume musique",
            "Changer la résolution",
            "Retour"
        ]
        self.selected = 0

    def run(self):
        """Boucle de l'écran d'options (gestion du volume + changement de résolution)."""
        clock_local = pygame.time.Clock()
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    # On ne quitte pas le jeu ici : main() décidera
                    running = False

                elif event.type == pygame.KEYDOWN:
                    # Navigation haut / bas
                    if event.key in KEY_UPS:
                        self.selected = (self.selected - 1) % len(self.options)
                    elif event.key in KEY_DOWNS:
                        self.selected = (self.selected + 1) % len(self.options)

                    # Ajuster le volume (gauche/droite) si la 1ère ligne est sélectionnée
                    elif event.key in KEY_LEFTS and self.selected == 0:
                        self.volume = max(0.0, self.volume - 0.1)
                        try:
                            pygame.mixer.music.set_volume(self.volume)
                        except pygame.error:
                            pass
                    elif event.key in KEY_RIGHTS and self.selected == 0:
                        self.volume = min(1.0, self.volume + 0.1)
                        try:
                            pygame.mixer.music.set_volume(self.volume)
                        except pygame.error:
                            pass

                    # Valider (Entrée / Espace)
                    elif event.key in TOUCHE_OKS:
                        current = self.options[self.selected]

                        # 1) Volume : rien à faire de plus, déjà appliqué
                        if current == "Volume musique":
                            pass  # on reste sur l'écran

                        # 2) Changer résolution : on ouvre l'écran de choix
                        elif current == "Changer la résolution":
                            new_w, new_h, new_fullscreen = choose_resolution_screen()
                            # On met à jour et on retourne vers main
                            self.w = new_w
                            self.h = new_h
                            self.fullscreen = new_fullscreen
                            return self.w, self.h, self.fullscreen, self.volume

                        # 3) Retour
                        elif current == "Retour":
                            running = False

                    # Échap = retour
                    elif event.key == TOUCHE_RETOUR:
                        running = False

            # ---------- DESSIN DE L'ÉCRAN D'OPTIONS ----------
            self._draw()
            pygame.display.flip()
            clock_local.tick(60)

        # Si on quitte sans changer la résolution, on renvoie les valeurs actuelles
        return self.w, self.h, self.fullscreen, self.volume

    def _draw(self):
        """Dessine le contenu de l'écran d'options (texte + lignes de menu)."""
        self.screen.fill((10, 10, 20))

        # Titre
        titre_surf = self.title_font.render("Options", True, COULEUR_TEXTE)
        titre_rect = titre_surf.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 6))
        self.screen.blit(titre_surf, titre_rect)

        # Lignes de menu
        cx = self.WIDTH // 2
        start_y = self.HEIGHT // 3
        gap = 70

        for i, label in enumerate(self.options):
            color = COULEUR_ACCENT if i == self.selected else COULEUR_TEXTE

            if label == "Volume musique":
                txt = f"{label} : {int(self.volume * 100)}%"
            elif label == "Changer la résolution":
                mode = f"{self.w}x{self.h}"
                if self.fullscreen:
                    mode += " (plein écran)"
                txt = f"{label} ({mode})"
            else:
                txt = label

            surf = self.btn_font.render(txt, True, color)
            rect = surf.get_rect(center=(cx, start_y + i * gap))
            self.screen.blit(surf, rect)

        # Aide en bas
        help_txt = "Z/Q/S/D : naviguer  |  ←/→ : volume  |  Entrée : valider  |  Échap : retour"
        help_surf = self.foot_font.render(help_txt, True, COULEUR_MUTE)
        help_rect = help_surf.get_rect(center=(self.WIDTH // 2, self.HEIGHT - 40))
        self.screen.blit(help_surf, help_rect)

# ---------- Boucle du vrai jeu Blue Prince ----------
def run_blue_prince_loop(w, h, fullscreen, scene_jeu=None):
    """
    Lance la boucle principale du jeu (SceneJeu) avec la MÊME résolution que le menu.
    Gère aussi la reprise de partie (scene_jeu existante).
    """

    # On recrée la fenêtre du jeu dans le même mode que le menu
    if fullscreen:
        flags = pygame.FULLSCREEN
        game_screen = pygame.display.set_mode((0, 0), flags)  # plein écran
        # récupération de la vraie taille de l'écran
        w, h = game_screen.get_size()
    else:
        flags = 0
        game_screen = pygame.display.set_mode((w, h), flags)  # même taille que le menu

    pygame.display.set_caption(TITLE)
    clock_local = pygame.time.Clock()

    # Synchronise la géométrie du jeu (LARGEUR, HAUTEUR…) avec la résolution courante
    init_game_geometry(w, h)

    # Nouvelle partie ou reprise
    if scene_jeu is None:
        scene_jeu = SceneJeu()   # utilise maintenant les bons LARGEUR/HAUTEUR

    running = True
    while running:
        dt = clock_local.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # On laisse la scène gérer ses événements (mouvements, portes, etc.)
            res = scene_jeu.gerer_evenement(event)
            if res == "menu":   # Échap dans le jeu -> retour au menu principal
                running = False
                break

        scene_jeu.update(dt)
        scene_jeu.dessiner(game_screen)
        pygame.display.flip()

    # On retourne la scène pour pouvoir la reprendre plus tard (partie en cours)
    return scene_jeu
