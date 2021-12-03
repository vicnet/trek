#!/usr/bin/env python

import random
import math

import pygame

import builder
import model


BLACK = pygame.Color('black')


class Circle:
    def __init__(self, circle_model, center, radius):
        self.model = circle_model
        self.model.subscribe('update', self.update)
        self.center = center
        self.radius = radius
        self.font = pygame.font.Font('freesansbold.ttf', 50)
    
    def collide(self, p):
        sqx = (p[0] - self.center[0])**2
        sqy = (p[1] - self.center[1])**2
        return sqx + sqy < self.radius**2
    
    def update(self):
        self.draw(display)

    def rotate(self, a):
        return (self.center[0] + self.radius*math.cos(a),
                self.center[1] + self.radius*math.sin(a) )

    def draw(self, display):
        if self.model.value is not None:
            text = self.font.render(str(self.model.value), True, BLACK)
            rect = text.get_rect(center=self.center)
            display.blit(text, rect)
        if self.model.mapped:
            dec = math.radians(45)
            for d in range(-self.radius,self.radius, 5):
                a = math.acos(d/self.radius)
                #pygame.draw.circle(display, (255,0,0), self.center, self.radius)
                start = self.rotate(dec+a)
                stop = self.rotate(dec-a)
                pygame.draw.line(display, (127,127,127), start, stop)

class Circles:
    def __init__(self, circles_model):
        self.model = circles_model
        self.circles = []
        circles = builder.get_circles('dunai.jpg')
        if len(circles)!=19:
            raise Exception('missing circles')
        for i,circle in enumerate(circles):
            x,y,r = circle
            c = Circle(self.model[i], (x,y), r)
            self.circles.append(c)

    def collide(self, p):
        for i,c in enumerate(self.circles):
            if c.collide(p):
                return i
        return None

    def draw(self, display):
        for c in self.circles:
            c.draw(display)

class Path:
    def __init__(self, path_model, circles):
        self.model = path_model
        self.model.subscribe('update', self.update)
        self.circles = circles
        
    def update(self):
        self.draw(display)

    def draw_path(self, display, c1, c2):
        x1,y1 = c1.center
        x2,y2 = c2.center
        vx,vy = x2-x1,y2-y1
        f = 0.75
        x1,y1 = x1+vx*f,y1+vy*f
        x2,y2 = x2-vx*f,y2-vy*f
        pygame.draw.line(display, BLACK, (x1,y1), (x2,y2), 8)

    def draw(self, display):
        path = self.model.path
        if path is None: return
        count = len(path)
        if count<2: return
        for i in range(count-1):
            c1 = self.circles[path[i]]
            c2 = self.circles[path[i+1]]
            self.draw_path(display, c1, c2)

class Paths:
    def __init__(self, paths_model, circles):
        self.model = paths_model
        self.model.subscribe('update', self.update)
        self.circles = circles
        self.paths = []

    def update(self):
        for mpath in self.model.paths[len(self.paths):]:
            path = Path(mpath, self.circles)
            self.paths.append(path)
            path.draw(display)

    def draw(self, display):
        for p in self.paths:
            p.draw(display)


class Dice:
    def __init__(self, dice_model, pos, color=(255, 255, 255)):
        self.model = dice_model
        self.model.subscribe('update', self.update)
        self.rect = pygame.Rect(0, 0, 64, 64)
        self.rect.move_ip(pos)
        self.color = color
        self.values = {}
        font = pygame.font.Font('freesansbold.ttf', 64)
        #font = pygame.font.SysFont('Comic Sans MS', 64, true)
        for value in range(self.model.min, self.model.max+1):
            text = font.render(str(value), True, BLACK)
            self.values[value] = text

    def collide(self, p):
        return self.rect.collidepoint(p)

    def update(self):
        self.draw(display)

    def draw(self, display):
        pygame.draw.rect(display, self.color, self.rect, border_radius=8)
        if self.model.value is None:
            return
        img = self.values[self.model.value]
        display.blit(img, (self.rect.x+14, self.rect.y+4))
        # for comic  display.blit(img, (self.pos[0]+14, self.pos[1]-12))

class Dices:
    def __init__(self, dices_model):
        self.model = dices_model
        self.yellow = Dice(model.game.dices.yellow, (260,10), pygame.Color('yellow'))
        self.red = Dice(model.game.dices.red, (260+70,10), pygame.Color('red'))

    def collide(self, p):
        return self.yellow.collide(p) or self.red.collide(p)

    def draw(self, display):
        self.yellow.draw(display)
        self.red.draw(display)

class Values:
    def __init__(self, dices_model):
        self.model = dices_model
        self.model.subscribe('update', self.update)
        self.font = pygame.font.Font('freesansbold.ttf', 20)
        self.positions = { }
        self.old_rect = { }
        pos = [410, 28]
        for pair in model.Pair:
            self.positions[pair] = tuple(pos)
            pos[0] += 1
            pos[1] += 22
            self.old_rect[pair] = None

    def update(self):
        self.draw(display)
        
    def draw_pair(self, display, value, pos):
        text = self.font.render(str(value), True, BLACK)
        text = pygame.transform.rotate(text, 2)
        rect = text.get_rect()
        rect.move_ip(pos)
        display.blit(text, pos)
        return rect

    def draw(self, display):
        pairs = self.model.pairing()
        if pairs is None:
            return
        for pair,pos in self.positions.items():
            if self.old_rect[pair] is not None:
                display.blit(background, pos, self.old_rect[pair])
            value = pairs[pair]
            self.old_rect[pair] = self.draw_pair(display, value, pos)

class Choices:
    pos = (470, 25)
    angle = -0.05 # in radian
    size = (20,21)
    
    def __init__(self, choices_model):
        self.model = choices_model
        self.model.subscribe('update', self.update)
    
    def update(self):
        self.draw(display)

    def rotate(self, n, m):
        return (self.pos[0]+n*self.size[0]*math.cos(self.angle)-m*self.size[1]*math.sin(self.angle),
                self.pos[1]+n*self.size[0]*math.sin(self.angle)+m*self.size[1]*math.cos(self.angle))

    def get_pos(self, n, m):
        p1 = self.rotate(n,m)
        p2 = self.rotate(n+1,m)
        p3 = self.rotate(n+1,m+1)
        p4 = self.rotate(n,m+1)
        return (p1, p2, p3, p4)

    def draw_check(self, display, n, m):
        p1, p2, p3, p4 = self.get_pos(n,m)
        pygame.draw.line(display, BLACK, p1, p3, 5)
        pygame.draw.line(display, BLACK, p2, p4, 5)

    def draw(self, display):
        for pair in model.Pair:
            count = self.model.count(pair)
            if count<=0:
                continue
            for n in range(count):
                self.draw_check(display, n, pair)

    def collide_check(self, n, m, p):
        points = self.get_pos(n,m)
        pos = 0 
        neg = 0 
        for i in range(len(points)):
            p1 = points[i]
            i = (i+1) % len(points)
            p2 = points[i]
            cross = (p[0]-p1[0])*(p2[1]-p1[1])-(p[1]-p1[1])*(p2[0]-p1[0])
            if cross>0:
                pos+=1
            if cross<0:
                neg+=1
            if pos>0 and neg>0:
                return False
        return True

    def collide(self, pos):
        for pair in model.Pair:
            count = self.model.max_count()
            for n in range(count):
                if self.collide_check(n, pair, pos):
                    return pair
        return None

pygame.init()

display = pygame.display.set_mode((592, 592))
background = pygame.image.load("dunai.jpg").convert()
display.blit(background, (0,0))

circles = Circles(model.game.circles)
values = Values(model.game.dices)
values.draw(display)
choices = Choices(model.game.choices)
dices = Dices(model.game.dices.yellow)
dices.draw(display)
paths = Paths(model.game.paths, circles.circles)

pygame.display.flip()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            raise SystemExit
        elif event.type == pygame.MOUSEBUTTONUP:
            pos = pygame.mouse.get_pos()
            
            circle = circles.collide(pos)
            if circle is not None:
                model.game.choose(circle)
                pygame.display.flip()
            
            pair = choices.collide(pos)
            if pair is not None:
                model.game.check(pair)
                pygame.display.flip()
                
            if dices.collide(pos):
                model.game.turn()
                pygame.display.flip()

    pygame.time.wait(100)
