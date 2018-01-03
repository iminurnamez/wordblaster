from random import randint
from itertools import cycle
from math import pi, degrees

import pygame as pg

from .. import tools, prepare
from ..components.labels import Label
from ..components.animation import Animation
from ..components.angles import get_angle


class Star(object):
    twinkle = pg.Surface((4, 4)).convert_alpha()
    twinkle.fill(pg.Color("white"))
    twinkle.set_alpha(64)
    twinkle_range = (200, 2000)
    def __init__(self, pos):
        self.pos = pos
        self.ticks = randint(0, 4)
        self.frequency = randint(*self.twinkle_range)
        
    def update(self, dt):
        self.ticks += 1
        self.twinkling = False
        if not self.ticks % self.frequency:
            self.twinkling = True
            self.frequency = randint(*self.twinkle_range)
 
    def move(self, offset):
        self.pos = (self.pos[0], self.pos[1] - offset[1])
        
    def draw(self, surface):
        twinkler = pg.Rect(self.pos, (2, 2))
        if self.twinkling:
            surface.blit(self.twinkle, (twinkler.left - 1, twinkler.top - 1))
        pg.draw.rect(surface, pg.Color("lightcyan"), twinkler)


class Word(pg.sprite.Sprite):
    center_offset = (92, 104)
    def __init__(self, word, pos, speed, *groups):
        super(Word, self).__init__(*groups)
        self.word = word
        self.label = Label(word, {"center": pos}, font_size=20, text_color="gray30",
                                 font_path=prepare.FONTS["Xolonium-Regular"])
        self.pos = pos
        self.speed = speed
        self.timer = 0
        self.ani_frequency = 120
        x = randint(0, 6)
        frames = tools.strip_from_sheet(prepare.GFX["ship{}".format(x)],
                                                         (0, 0), (184, 144), 8)
        self.frames = cycle(frames)
        self.frame = next(self.frames)
        self.rect = self.frame.get_rect(center=self.pos)
        
    def explode(self):
        self.kill()
        
    def update(self, dt):
        self.timer += dt
        if self.timer >= self.ani_frequency:
            self.timer -= self.ani_frequency
            self.frame = next(self.frames)
        self.pos = self.pos[0] - (self.speed * dt), self.pos[1]
        self.rect.center = self.pos
        self.label.rect.center = (self.rect.left + self.center_offset[0],
                                           self.rect.top + self.center_offset[1])
        
    def draw(self, surface):
        surface.blit(self.frame, self.rect)
        self.label.draw(surface)


class Turret(object):
    dish_offset = (31, 7)
    def __init__(self, midbottom):
        self.base = prepare.GFX["dish_base"]
        self.barrel = prepare.GFX["dish"]
        self.angle = self.target_angle = 0
        self.base_rect = self.base.get_rect(midbottom=midbottom)
        center = (self.base_rect.left + self.dish_offset[0],
                       self.base_rect.top + self.dish_offset[1])
        self.barrel_rect = self.barrel.get_rect(center=center)
        self.rotation_speed = .005
        self.seek_angle(.5 * pi)
        self.make_image()
        self.shoot_sound = prepare.SFX["lazer"]
        
    def seek_angle(self, target_angle):
        self.target_angle = target_angle
        
    def make_image(self):
        self.image = pg.transform.rotate(self.barrel, degrees(self.angle))
        center = (self.base_rect.left + self.dish_offset[0],
                      self.base_rect.top + self.dish_offset[1])
        self.rect = self.image.get_rect(center=center)
        
    def shoot(self, word):
        self.shoot_sound.play()
        
    def update(self, dt):
        if self.angle < self.target_angle:
            self.angle += min(self.rotation_speed * dt, self.target_angle - self.angle)
        elif self.angle > self.target_angle:
            self.angle -= min(self.rotation_speed * dt, self.angle - self.target_angle)
        self.make_image()
            
    def draw(self, surface):
        surface.blit(self.base, self.base_rect)
        surface.blit(self.image, self.rect)

        
class Lazer(pg.sprite.Sprite):
    def __init__(self, origin, word, *groups):
        super(Lazer, self).__init__(*groups)
        self.word = word
        angle = degrees(get_angle(origin, word.rect.center))
        self.image = pg.transform.rotate(prepare.GFX["lazer"], angle)
        self.rect = self.image.get_rect(center=origin)
        
    def die(self):
        self.word.kill()
        self.kill()
        
        
class MaskedButton(pg.sprite.Sprite):
    inflate_time = 120
    deflate_time = 120

    def __init__(self, image, centerpoint, callback, args, *groups):
        super(MaskedButton, self).__init__(*groups)
        size = max(image.get_size())
        self.base_image = pg.Surface((size, size)).convert_alpha()
        self.base_rect = self.base_image.get_rect(center=centerpoint)
        img_rect = image.get_rect(center=(size//2, size//2))
        self.base_image.fill((0,0,0,0))
        self.base_image.blit(image, img_rect)
        self.size = self.initial_size = size
        self.make_images()
        self.hovered = False
        self.animations = pg.sprite.Group()
        self.held = False
        self.units_per_click = 1
        self.clicked = False
        self.call = callback
        self.args = args
        self.visible = True
        self.active = True

    def mask_point_collide(self, pos):
        dx = pos[0] - self.rect.left
        dy = pos[1] - self.rect.top
        try:
            return self.mask.get_at((dx, dy))
        except IndexError:
            return False

    def make_images(self):
        self.images, self.rects, self.masks = {}, {}, {}
        self.low = int(self.size * .95)
        self.high = int(self.size * 1.2)
        for x in range(int(self.low * .4), int(self.high * 1.6)):
            img = pg.transform.smoothscale(self.base_image, (x, x))
            rect = img.get_rect(center=self.base_rect.center)
            mask = pg.mask.from_surface(img, 0)
            self.images[x] = img
            self.rects[x] = rect
            self.masks[x] = mask

    def get_event(self, event):
        if not self.visible:
            return
        if event.type == pg.MOUSEBUTTONDOWN:
            pass
        elif event.type == pg.MOUSEBUTTONUP:
            if event.button == 1 and self.hovered:
                self.clicked = True

    def update(self, dt, mouse_pos):
        self.animations.update(dt)
        hover = self.hovered
        size = int(self.size)
        self.image = self.images[size]
        self.mask = self.masks[size]
        self.rect = self.rects[size]
        self.hovered = self.mask_point_collide(mouse_pos)
        held = pg.mouse.get_pressed()[0]
        if not held and self.held:
            self.held = False
            if self.hovered:
                self.inflate(self.high)
            else:
                self.inflate(self.initial_size)
        elif self.hovered and held and not self.held:
            self.inflate(self.low)
            self.held = True
        elif not hover and self.hovered:
            self.inflate(self.high)
        elif hover and not self.hovered:
            self.inflate(self.initial_size)
        elif not self.hovered and self.held:
            self.held = False
            self.inflate(self.initial_size)
        if self.clicked:
            if self.args:
                self.call(*self.args)
            else:
                self.call()
        self.clicked = False

    def inflate(self, target):
        self.animations.empty()
        dur = self.inflate_time
        ani = Animation(size=target, duration=dur, transition="out_elastic")
        ani.start(self)
        self.animations.add(ani)

    def draw(self, surface):
        if self.visible:
            surface.blit(self.image, self.rect)