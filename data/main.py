from . import prepare,tools
from .states import title_screen, gameplay, gameover

def main():
    controller = tools.Control(prepare.ORIGINAL_CAPTION)
    states = {"TITLE": title_screen.TitleScreen(),
                   "GAMEPLAY": gameplay.Gameplay(),
                   "GAMEOVER": gameover.GameOverScreen()}
    controller.setup_states(states, "TITLE")
    controller.main()
