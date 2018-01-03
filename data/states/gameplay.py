from math import pi, degrees
from random import randint, choice
from itertools import cycle

import pygame as pg

from .. import tools, prepare
from ..components.labels import Label, MultiLineLabel, Textbox
from ..components.word_generator import load_words
from ..components.angles import get_angle, get_distance
from ..components.animation import Animation
from ..components.game_objects import Star, Word, Turret, Lazer


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


class Gameplay(tools._State):
    def __init__(self):
        super(Gameplay, self).__init__()
        sr = prepare.SCREEN_RECT
        self.song = prepare.MUSIC["game"]
        self.hills = prepare.GFX["hills"]
        self.hills_rect = self.hills.get_rect(bottomleft=sr.bottomleft)
        self.dashboard = prepare.GFX["dashboard"]
        self.dash_rect = self.dashboard.get_rect(bottomleft=sr.bottomleft)
        self.difficulties = {
                "Easy": (4500, 8, .02),
                "Normal": (3500, 10, .025),
                "Hard": (3000, 12, .03),
                "Insane": (2500, 12, .05)}

    def new_game(self, difficulty):
        sr = prepare.SCREEN_RECT
        self.textbox = Textbox({"midbottom": sr.midbottom}, box_size=(320, 64),
                                           font_size=36, text_color="gray20",
                                           font_path=prepare.FONTS["Xolonium-Regular"],
                                           cursor_color="gray20")
        self.turret = Turret((sr.centerx, sr.bottom - 65))
        self.word_speed = .02
        self.word_timer = 0
        self.word_frequency, max_length, self.word_speed = self.difficulties[difficulty]
        self.words_dict = load_words(max_length)
        self.words = pg.sprite.Group()
        self.make_word_spots()
        self.add_random_word()
        self.points = 0
        self.num_solved = 0
        self.game_time = 0
        self.animations = pg.sprite.Group()
        self.lazers = pg.sprite.Group()
        self.stars = [Star((randint(1, sr.right), randint(1, sr.bottom - 150)))
                           for _ in range(100)]
        pg.mixer.music.load(self.song)
        pg.mixer.music.play(-1)
        self.def_label = None
        self.make_ui_labels()

    def startup(self, persistent):
        self.persist = persistent
        difficulty = self.persist["difficulty"]
        self.new_game(difficulty)

    def make_word_spots(self):
        w, h  = prepare.SCREEN_SIZE
        spots = [(w + 128, 80 + (128 * x)) for x in (1, 3, 0, 2)]
        self.word_spots = cycle(spots)

    def add_random_word(self):
        text = choice(self.words_dict.keys())
        pos = next(self.word_spots)
        Word(text, pos, self.word_speed, self.words)

    def closest_match(self):
        entered = self.textbox.buffer
        closest = None, 0
        for word in self.words:
            score = 0
            for char, entered_char in zip(word.word, entered):
                if char == entered_char:
                    score += 1
            if score > closest[1]:
                closest = word, score
        return closest[0]

    def make_definition(self, word):
        defined = self.words_dict[word]
        try:
            text = "{}: {}".format(word.upper(), defined)
        except:
            text = "{}: ".format(word.upper())
        self.def_label = MultiLineLabel(text, {"topleft": (805, 630)},
                font_size=14, font_path=prepare.FONTS["Xolonium-Regular"],
                char_limit=58)

    def make_ui_labels(self):
        self.labels = pg.sprite.Group()
        style = {"font_path": prepare.FONTS["Xolonium-Regular"],
                     "text_color": "gray20"}
        Label("Words", {"topleft": (300, 630)}, self.labels,
                 font_size=24, **style)
        Label("Characters", {"topleft": (300, 680)}, self.labels,
                 font_size=24, **style)
        self.words_label = Label("{}".format(self.num_solved),
                                            {"topright": (290, 630)}, self.labels,
                                            font_size=24, **style)
        self.chars_label = Label("{}".format(self.points),
                                           {"topright": (290, 680)}, self.labels,
                                           font_size=24, **style)
        self.time_label = Label(time_format(self.game_time),
                                          {"center": (100, 650)}, self.labels,
                                          font_size=32, **style)

    def game_over(self):
        self.done = True
        self.next = "GAMEOVER"
        self.persist["game time"] = self.game_time
        self.persist["num words"] = self.num_solved
        self.persist["num chars"] = self.points
        self.persist["stars"] = self.stars

    def get_event(self,event):
        if event.type == pg.QUIT:
            self.quit = True
        elif event.type == pg.KEYUP:
            if event.key == pg.K_ESCAPE:
                self.game_over()
        self.textbox.get_event(event)

    def update(self, dt):
        self.animations.update(dt)
        self.game_time += dt
        for star in self.stars:
            star.update(dt)
        self.word_timer += dt
        if self.word_timer >= self.word_frequency:
            self.word_timer -= self.word_frequency
            self.add_random_word()
        for word in self.words:
            word.update(dt)
            if word.rect.right < 0:
                self.game_over()
        self.textbox.update(dt)
        self.turret.update(dt)
        closest = self.closest_match()
        if closest is not None:
            angle = get_angle(self.turret.base_rect.center,
                                        closest.label.rect.center)
            self.turret.seek_angle(angle)
        self.time_label.set_text(time_format(self.game_time))

        if self.textbox.final:
            for word in self.words:
                if self.textbox.final == word.word:
                    self.num_solved += 1
                    self.points += len(word.word)
                    self.words_label.set_text("{}".format(self.num_solved))
                    self.chars_label.set_text("{}".format(self.points))
                    self.make_definition(word.word)
                    self.turret.shoot(word)
                    lazer = Lazer(self.turret.rect.center, word, self.lazers)
                    dist = float(get_distance(self.turret.rect.center, 
                                                          word.rect.center))
                    ani = Animation(centerx=word.rect.centerx,
                                            centery=word.rect.centery,
                                            duration=dist, round_values=True)
                    ani.start(lazer.rect)
                    ani.callback = lazer.die
                    self.animations.add(ani)
            self.textbox.clear()

    def draw(self, surface):
        surface.fill(pg.Color("black"))
        for star in self.stars:
            star.draw(surface)
        surface.blit(self.hills, self.hills_rect)
        for word in self.words:
            word.draw(surface)
        self.lazers.draw(surface)
        self.turret.draw(surface)
        surface.blit(self.dashboard, self.dash_rect)
        self.textbox.draw(surface)
        if self.def_label is not None:
            self.def_label.draw(surface)
        self.labels.draw(surface)


