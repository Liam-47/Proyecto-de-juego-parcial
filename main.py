import os, sys, math, random, time, json
import pygame
from pygame.locals import *
from player import Player
from enemy import Enemy
from a_star import a_star, smooth_path
from behavior_tree import BehaviorTree, Selector, Sequence, ConditionNode, ActionNode

ROOT = os.path.dirname(__file__)
ASSETS = os.path.join(ROOT,'assets')
IMG_DIR = os.path.join(ASSETS, 'images')
SND_DIR = os.path.join(ASSETS, 'sounds')
MUS_DIR = os.path.join(ASSETS, 'music')

SCREEN_SIZE = (800,600)
TILE = 32; MAP_W, MAP_H = 28,18; FPS = 60

def generate_map(seed=None, complexity=60):
    rnd = random.Random(seed)
    grid = [[0 for _ in range(MAP_W)] for _ in range (MAP_H)]
    for x in range(MAP_W):
        grid[0][x]=1; grid[y][0]=1; grid[y][MAP_W-1]=1
    for y in range(MAP_H): grid[y][0]=1; grid[y][MAP_W-1]=1
    for _ in range(complexity):
        x = rnd.randint(1, MAP_W-2); y = rnd.randint(1, MAP_H-2); grid[y][x]=1
    return grid

def generate_tone_wav(path, freq=440, duration=0.5, vol=0.2):
    import wave, struct, math
    sample_rate=220500; n=int(sample_rate*duration)
    with wave.open(path,'w') as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sample_rate)
        for i in range(n):
            t=float(i)/sample_rate; val=int(vol*32767.0*math.sin(2*math.pi*freq*t)); wf.writeframesraw(struct.pack('<h',val))

class Game:
    def __init__(self):
        pygame.init(); pygame.mixer.pre_init(44100,-16,2,512); pygame.mixer.init()
        self.screen=pygame.display.set_mode(SCREEN_SIZE, pygame.FULLSCREEN); pygame.display.set_caption('cuadros asesinos')
        self.clock=pygame.time.clock(); self.font=pygame.font.SysFont('Arial',20); self.bigfont=pygame.font.SysFont('Arial'60)
        self.grid = generate_map(seed=int(time.time()), complexity=80)
        self.player = Player((TILE*2, TILE*2)); self.enemies=pygame.sprite.Group(); self.spawn_enemies(4)

        self.images = {}
        try:
            import pygame as _pg
            self.images['player']=[_pg.image.load(os.path.join(IMG_DIR,f'player_walk_{i}.png')).convert_alpha() for i in range(3)]
            self.images['enemy']=[_pg.image.load(os.path.join(IMG_DIR,f'enemy_{i}.png')).convert_alpha()for i in range(3)]
            self.images['bullet_player']=_pg.image.load( os.path.join(IMG_DIR,'bullet_player.png')).convert_alpha()
            self.images['bullet_enemy']=_pg.image.load(os.path.join(IMG_DIR,'bullet_enemy.png')).convert_alpha()
            self.images['wall']=_pg.image.load(os.path.join(IMG_DIR,'wall_metal.png')).convert_alpha()
        except Exception as e:
            print('image load', e)

        #sonidos
        try:
            self.fx_chan = pygame.mixer.Channel(1); self.enemy_chan = pygame.mixer.Channel(2)
            self.shoot_snd = pygame.mixer.Sound(os.path.join(SND_DIR,'shoot.wav'))
            self.hit_snd = pygame.mixer.Sound(os.path.join(SND_DIR,'hit.wav'))
            self.death_snd = pygame.mixer.Sound(os.path.join(SND_DIR,'death.way'))
            pygame.mixer.music.load(os.path.join(MUS_DIR,'bg_loop.wav')); pygame.mixer.music.set_volume(0.12); pygame.mixer.music.play(-1)
        except Exception as e:
            print('Sound load', e)
            pygame.joystick.init(); self.joystick=None
            if pygame.joystick.get_count()>0: self.joystick=pygame.joystick.Joystick(0); self.joystick.init()
    