import sys
import pygame
from menu import *            # écrans de menu / options / découverte
from objet_gestion import *   # logique du jeu + run_blue_prince_loop + images des pièces


def main():
    # Init Pygame (fenêtre, événements, etc.)
    pygame.init()

    # Charger une fois les images des pièces (jeu + catalogue)
    charger_images_pieces()

    # Musique de fond
    music_volume = 0.3
    try:
        pygame.mixer.init()
        pygame.mixer.music.load("assets/audio/main_theme.ogg")
        pygame.mixer.music.set_volume(music_volume)
        pygame.mixer.music.play(-1)   # -1 = boucle infinie
    except Exception as e:
        print("Impossible de charger la musique :", e)

    # Choix de la résolution au lancement
    w, h, fullscreen = choose_resolution_screen()

    # Création de la fenêtre principale du menu
    screen, size, title_font, btn_font, foot_font = setup_display(w, h, fullscreen)

    # État de la partie (pour "Reprendre")
    partie_en_cours = False
    scene_jeu = None

    # --------- Boucle principale (menu) ---------
    while True:
        action = main_menu(screen, size, title_font, btn_font, foot_font, partie_en_cours)

        # Quitter le jeu proprement
        if action in ("QUIT", None):
            pygame.quit()
            sys.exit()

        # Nouvelle partie
        elif action == "NEW_GAME":
            scene_jeu = run_blue_prince_loop(w, h, fullscreen, scene_jeu=None)
            partie_en_cours = True
            # Retour au menu avec la même résolution
            screen, size, title_font, btn_font, foot_font = setup_display(w, h, fullscreen)

        # Reprendre la partie
        elif action == "RESUME":
            if scene_jeu is not None:
                scene_jeu = run_blue_prince_loop(w, h, fullscreen, scene_jeu=scene_jeu)
                # Retour au menu avec la même résolution
                screen, size, title_font, btn_font, foot_font = setup_display(w, h, fullscreen)

        # Options (volume + résolution)
        elif action == "OPTIONS":
            opt = OptionsScreen(
                screen,
                size,
                title_font,
                btn_font,
                foot_font,
                volume_init=music_volume,
                w_init=w,
                h_init=h,
                fullscreen_init=fullscreen,
            )
            # Récupère nouvelle résolution + volume
            w, h, fullscreen, music_volume = opt.run()

            # Recrée la fenêtre avec les nouveaux paramètres
            screen, size, title_font, btn_font, foot_font = setup_display(w, h, fullscreen)

            # Met à jour le volume de la musique
            try:
                pygame.mixer.music.set_volume(music_volume)
            except pygame.error:
                pass

        # Menu Découverte (catalogue, inventaire, objets…)
        elif action == "DECOUVERTE":
            while True:
                discovery = DiscoveryMenu(screen, size, title_font, btn_font, foot_font)
                sub = discovery.run()

                if sub in ("BACK", None):
                    break
                elif sub == "Catalogue des pièces":
                    cat_ui = RoomCatalogueScreen(screen, size, title_font, btn_font, foot_font)
                    cat_ui.run()
                elif sub == "Inventaire":
                    show_inventory(screen, size, title_font, btn_font, foot_font)
                elif sub == "PERMANENTS":
                    show_permanent_objects(screen, size, title_font, btn_font, foot_font)
                elif sub == "AUTRES":
                    show_other_objects(screen, size, title_font, btn_font, foot_font)


if __name__ == "__main__":
    main()


