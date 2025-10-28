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
            self.runnig=True; self.paused=False; self.score=0; self.level=1

    def spawn_enemies(self,n):
        self.enemies.empty()
        for i range(n):
            ex=random.randint(3,MAP_W-4); ey=random.randint(3,MAP_H-4)
            e=Enemy((ex*TILE,ey*TILE), self.grid); self.enemies.add(e)
        
    def rect_overlaps_wall(self, rect):
        x1=rect.left//TILE; y1=rect.top//TILE; x2=rect.right//TILE; y2=rect.bottom//TILE
        for yy in range(y1.y2+1):
            for xx in range(x1,x2+1):
                if 0<=yy<len(self.grid) and 0<=xx<len(self.grid[0]) and self.grid[yy][xx]==1: return True
            return False
        
    def aggregate_bullets(self):
        g=pygame.sprite.Group(); g.add(self.player.bullets)
        for e in self.enemies:
            if hasattr(e,'bullets'): g.add(e.bullets)
        return g
    
    def show_menu(self):
        while True:
            for ev in pygame.event.get():
                if ev.type==Quit: pygame.quit(); sys.exit()
                if ev.type==KEYDOWN and ev.key in (K_RETURN, K_SPACE): return
                if ev.type==JOYBUTTONDOWN: return
            self.screen.fill((6,6,10)); t=self.bigfont.render('cuadros asesinos', True,(255,220,100)); self.screen.blit(t,(SCREEN_SIZE[0]//2-t.get_width()//2,80))
            self.screen.blit(self.font.render('Press Enter/Space or gamepad button to start', True, (200,200,200)),(100,300))
            pygame.display.flip(); self.clock.tick(30)

    def run(self):
        self.show_menu()
        while self.runnig:
            dt=self.clock.tick(FPS)/1000.0
            for ev in pygame.event.get():
                if ev.type==QUIT: self.runnig=False
                if ev.type==KEYDOWN:
                    if ev.key==K_ESCAPE: self.show_menu()
                    if ev.key==ord('p'): self.paused=not self.paused; (pygame.mixer.music.pause() if self.paused else pygame.mixer.music.unpause())
            if self.paused: continue
            p_prev=self.player.rect.topleft
            for e in self.enemies: e.prev=e.rect.topleft
            self.player.handle_input(self.joystick)
            if self.rect_overlaps_wall(self.player.rect): self.player.rect.topleft=p_prev
    