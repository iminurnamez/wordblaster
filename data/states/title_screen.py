from random import randint

import pygame as pg

from .. import tools, prepare
from ..components.labels import Label, Button, ButtonGroup
from ..components.game_objects import Star, Word, MaskedButton


class TitleScreen(tools._State):
    def __init__(self):
        super(TitleScreen, self).__init__()
        self.difficulty = "Easy"
        self.font = prepare.FONTS["Xolonium-Regular"]
        self.bold = prepare.FONTS["Xolonium-Bold"]
        self.hills = prepare.GFX["hills"]
        self.hills_rect = self.hills.get_rect(bottomleft=prepare.SCREEN_RECT.bottomleft)
        self.reset()


    def reset(self):
        sr = prepare.SCREEN_RECT
        self.stars = [Star((randint(1, sr.right), randint(1, sr.bottom - 150)))
                           for _ in range(100)]
        self.make_buttons()
        pg.mouse.set_pos(self.button_centers[self.button_index])

    def make_buttons(self):
        self.buttons = ButtonGroup()
        self.button_centers = []
        self.button_index = 0
        cy = 90
        cx = prepare.SCREEN_RECT.centerx
        for diff in ["Easy", "Normal", "Hard", "Insane"]:
            word = Word(diff, (0, 0), .02)
            img = word.frame.copy()
            img_rect =  img.get_rect()
            word.label.rect.center = word.center_offset
            word.label.draw(img)
            MaskedButton(img, (cx, cy), self.set_difficulty, [diff], self.buttons)
            self.button_centers.append((cx, cy))
            cy += 180

    def set_difficulty(self, difficulty):
        self.done = True
        self.next = "GAMEPLAY"
        self.persist["difficulty"] = difficulty

    def scroll(self, direction):
        self.button_index += direction
        if self.button_index < 0:
            self.button_index = len(self.buttons) - 1
        elif self.button_index > len(self.buttons) - 1:
            self.button_index = 0
        pg.mouse.set_pos(self.button_centers[self.button_index])

    def startup(self, persistent):
        self.persist = persistent
        self.reset()

    def get_event(self,event):
        if event.type == pg.QUIT:
            self.quit = True
        elif event.type == pg.KEYUP:
            if event.key == pg.K_ESCAPE:
                self.quit = True
            elif event.key == pg.K_UP:
                self.scroll(-1)
            elif event.key == pg.K_DOWN:
                self.scroll(1)
            elif event.key == pg.K_RETURN:
                click = pg.event.Event(pg.MOUSEBUTTONUP, button=1,
                                                 pos=self.button_centers[self.button_index])
                pg.event.post(click)
        self.buttons.get_event(event)

    def update(self, dt):
        self.buttons.update(dt, pg.mouse.get_pos())
        for star in self.stars:
            star.update(dt)

    def draw(self, surface):
        surface.fill(pg.Color("black"))
        for star in self.stars:
            star.draw(surface)
        surface.blit(self.hills, self.hills_rect)
        self.buttons.draw(surface)