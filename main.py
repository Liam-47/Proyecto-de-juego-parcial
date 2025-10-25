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