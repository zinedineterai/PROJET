from menu import *
import pygame 
from objet_gestion import * 
# ---------- Programme principal ----------

def main():
    pygame.init()

    # 0) Charger les images des pièces (catalogue + jeu)
    charger_images_pieces()

    # 1) Musique de fond (en boucle)
    music_volume = 0.3  # volume initial : 50 %
    try:
        pygame.mixer.init()
        # Mets ton fichier de musique ici (par exemple .ogg ou .mp3)
        pygame.mixer.music.load("assets/audio/main_theme.ogg")
        pygame.mixer.music.set_volume(music_volume)
        pygame.mixer.music.play(-1)  # -1 = boucle infinie
    except Exception as e:
        print("Impossible de charger la musique :", e)

    # 2) Choix de résolution pour le MENU
    w, h, fullscreen = choose_resolution_screen()

    # 3) Fenêtre principale (menu)
    screen, size, title_font, btn_font, foot_font = setup_display(w, h, fullscreen)

    # état de la partie (pour savoir si "Reprendre" est dispo)
    partie_en_cours = False
    scene_jeu = None  # contiendra ton objet SceneJeu quand une partie aura été lancée

    while True:
        # --------- MENU PRINCIPAL ---------
        action = main_menu(screen, size, title_font, btn_font, foot_font, partie_en_cours)

        # ======= GESTION DES CHOIX DU MENU PRINCIPAL =======

        if action in ("QUIT", None):
            pygame.quit()
            sys.exit()

        elif action == "NEW_GAME":
            scene_jeu = run_blue_prince_loop(w, h, fullscreen, scene_jeu=None)
            partie_en_cours = True
            # on revient au MENU avec la même résolution
            screen, size, title_font, btn_font, foot_font = setup_display(w, h, fullscreen)

        elif action == "RESUME":
            if scene_jeu is not None:
                scene_jeu = run_blue_prince_loop(w, h, fullscreen, scene_jeu=scene_jeu)
                # on revient au MENU avec la même résolution
                screen, size, title_font, btn_font, foot_font = setup_display(w, h, fullscreen)

        elif action == "OPTIONS":
            # Ouvre l'écran d'options et récupère éventuellement :
            # - nouvelle résolution
            # - nouveau volume
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
            w, h, fullscreen, music_volume = opt.run()

            # On recrée la fenêtre avec la nouvelle résolution
            screen, size, title_font, btn_font, foot_font = setup_display(w, h, fullscreen)

            # On applique le nouveau volume à la musique
            try:
                pygame.mixer.music.set_volume(music_volume)
            except pygame.error:
                pass

        elif action == "DECOUVERTE":
            # Boucle du sous-menu Découverte
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

