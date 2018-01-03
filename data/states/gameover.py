from random import choice

import pygame as pg

from .. import tools, prepare
from ..components.labels import Label, Blinker

def zfill(num):
    if num < 10:
        return "0{}".format(num)
    return "{}".format(num)
    
def time_format(milliseconds):
    total_seconds = milliseconds // 1000
    seconds = total_seconds % 60
    minutes = (total_seconds // 60) % 60
    hours = minutes // 60
    if hours:
        return "{}:{}:{}".format(zfill(hours), zfill(minutes), zfill(seconds))
    elif minutes:
        return "{}:{}".format(zfill(minutes), zfill(seconds))
    else:
        return ":{}".format(zfill(seconds))


class GameOverScreen(tools._State):
    def __init__(self):
        super(GameOverScreen, self).__init__()
        self.font = prepare.FONTS["Xolonium-Regular"]
        self.bold = prepare.FONTS["Xolonium-Bold"]
        self.colors = [prepare.GFX["ship{}".format(x)].get_at((0, 112))
                            for x in range(7)]
        self.hills = prepare.GFX["hills"]
        self.hills_rect = self.hills.get_rect(bottomleft=prepare.SCREEN_RECT.bottomleft)
        
    def startup(self, persistent):
        sr = prepare.SCREEN_RECT
        self.persist = persistent
        difficulty = self.persist["difficulty"]
        game_time = self.persist["game time"]
        num_chars = "{}".format(self.persist["num chars"])
        num_words = "{}".format(self.persist["num words"])
        wpm = (self.persist["num chars"] / 5.) / (game_time / 60000.)
        self.stars = self.persist["stars"]
        self.blinkers = pg.sprite.Group()
        self.title = Blinker("Game Over", {"midtop": (sr.centerx, 20)},
                                  600, self.blinkers, font_size=96, font_path=self.bold,
                                  text_color=choice(self.colors))
        self.prompt = Blinker("SPACE to continue - ESC to quit",
                                       {"midbottom": (sr.centerx, sr.bottom - 10)}, 900,
                                       self.blinkers, font_path=self.font, font_size=32)
        self.make_labels(difficulty, game_time, num_words, num_chars, wpm)

    def make_labels(self, difficulty, game_time, num_words, num_chars, wpm):
        self.labels = pg.sprite.Group()
        cx = prepare.SCREEN_RECT.centerx
        Label(time_format(game_time), {"midtop": (cx, 150)},
                self.labels, font_size=80, font_path=self.bold)
        Label(difficulty, {"midtop": (cx, 250)}, self.labels, font_size=24, font_path=self.bold)
        
        info = [("Words", num_words), ("Chars", num_chars), ("WPM", "{}".format(int(wpm)))]
        top = 320
        for title, num in info:
            Label(num, {"topright": (cx - 20, top)}, self.labels, font_path=self.bold, font_size=32)
            Label(title, {"topleft": (cx + 20, top)}, self.labels, font_path=self.bold, font_size=32)
            top += 80

    def get_event(self,event):
        if event.type == pg.QUIT:
            self.quit = True
        elif event.type == pg.KEYUP:
            if event.key == pg.K_ESCAPE:
                self.quit = True
            elif event.key == pg.K_SPACE:
                self.done = True
                self.next = "TITLE"
        elif event.type == pg.MOUSEBUTTONUP:
            self.done = True
            self.next = "TITLE"
            
    def update(self, dt):
        blink = self.title.visible
        self.title.update(dt)
        if blink and not self.title.visible:
            self.title.text_color = choice(self.colors)
            self.title.update_text()
        self.prompt.update(dt)
        for star in self.stars:
            star.update(dt)

    def draw(self, surface):
        surface.fill(pg.Color("black"))
        for star in self.stars:
            star.draw(surface)
        surface.blit(self.hills, self.hills_rect)
        self.title.draw(surface)
        self.labels.draw(surface)
        self.prompt.draw(surface)
        