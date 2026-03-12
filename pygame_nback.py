# NEW PYGAME NBACK CODE
# USING STARTER CODE FROM https://kidscancode.org/blog/2016/08/pygame_1-1_getting-started/
import pygame
import pygame.freetype
import random
import math
import numpy as np
import time

# globals
SIZE = WIDTH, HEIGHT = (1024, 720)
FPS = 30
SYMBOLS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

# experimental constants
PRACTICE_LEN = 10   # number of letters shown in a practice block
TRIAL_LEN = 40      # number of letters shown in a real block

FIXATION_TIME         = 500
STIMULUS_DISPLAY_TIME = 500
RESPONSE_WINDOW_TIME  = 2000
JITTER_RANGE          = (100, 500)
STOP_TIME             = 500
REST_TIME             = 30000

# colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

# initialize and create window
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("NBACK")
clock = pygame.time.Clock()

TEXT_SIZE = 30

# font module
pygame.font.init()
GAME_FONT = pygame.font.SysFont('Arial', TEXT_SIZE)

# set tutorial to true to start tutorial at the beginning
tutorial = True
instruction = True

instruction_text = "Welcome to the N-back task! \nYou will be presented with a series of letters. " \
"\nPlease indicate if the letter presented occurred N places back. \nWe will start with a tutorial for all N-back levels (0,1,2). \n\nPress any key to begin."

zero_text = "This is the 0-back task \nPress any button to indicate if the current letter occurred 0 places back in the sequence"
one_text = "This is the 1-back task \nPress any button to indicate if the current letter occurred 1 places back in the sequence"
two_text = "This is the 2-back task \nPress any button to indicate if the current letter occurred 2 places back in the sequence"

rest_text = f"Please rest for 30 seconds before beginning the trial"

#### CREDIT: https://gist.github.com/galatolofederico/aa43e0d3bfce5fd6173fb25c8b48e8f3
def blit_text(surface, text, pos, font, color=pygame.Color('black')):
    words = [word.split(' ') for word in text.splitlines()] 
    space = font.size(' ')[0]
    max_width, max_height = surface.get_size()
    x, y = pos
    rects = []
    row_rects = []
    for line in words:
        for word in line:
            word_surface = font.render(word, 0, color)
            word_width, word_height = word_surface.get_size()
            if x + word_width >= max_width:
                x = pos[0]
                rects.append(row_rects)
                row_rects = []
            row_rects.append(word)
            x += word_width + space
        x = pos[0]
        rects.append(row_rects)
        row_rects = []

    max_vertical_rects = math.floor(max_height / font.size(' ')[1])
    printable_rects = rects[-max_vertical_rects:]
    for line in printable_rects:
        for word in line:
            word_surface = font.render(word, 0, color)
            word_width, word_height = word_surface.get_size()
            surface.blit(word_surface, (x, y))
            x += word_width + space
        x = pos[0]
        y += word_height

### Claude wrote this so use with caution
def blit_text_centered(surface, text, font, color=pygame.Color('black')):
    words = [word.split(' ') for word in text.splitlines()]
    space = font.size(' ')[0]
    max_width, max_height = surface.get_size()
    word_height = font.size(' ')[1]

    # First pass: build lines as lists of words (respecting word wrap)
    lines = []
    for line in words:
        row = []
        x = 0
        for word in line:
            word_width = font.size(word)[0]
            if x + word_width >= max_width:
                lines.append(row)
                row = []
                x = 0
            row.append(word)
            x += word_width + space
        lines.append(row)

    # Calculate total text block height and start y so block is vertically centered
    total_height = len(lines) * word_height
    y = (max_height - total_height) // 2

    # Second pass: render each line centered horizontally
    for line in lines:
        # Calculate this line's total width
        line_width = sum(font.size(word)[0] for word in line) + space * (len(line) - 1)
        x = (max_width - line_width) // 2  # center this line

        for word in line:
            word_surface = font.render(word, 0, color)
            word_width = font.size(word)[0]
            surface.blit(word_surface, (x, y))
            x += word_width + space

        y += word_height

def pick_nback_symbol(shown_symbols, n_level, symbols, TARGET_RATIO=0.33):
    rng = np.random.default_rng()

    if n_level == 0:
        symbol = random.choice(symbols)
        is_target = True
    elif len(shown_symbols) < n_level: 
        symbol = random.choice(symbols)
        is_target = False
    elif rng.random() < TARGET_RATIO:
        symbol = shown_symbols[-n_level]
        is_target = True
    else:
        is_target = False
        symbol = random.choice([s for s in symbols if s != shown_symbols[-n_level]])
    
    return symbol, is_target

# game loop 
running = True
while running:
    # controls spped of loop
    clock.tick(FPS)

    for event in pygame.event.get():
        # check for closing window
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYUP:
            print(event.unicode)
            instruction = False
        

    screen.fill(BLACK)

    if instruction:
        # show instruction
        blit_text_centered(screen, instruction_text, GAME_FONT, color=WHITE)
        pygame.display.update()
    elif tutorial:
        # list of n-back levels
        levels = ["0-Back", "1-Back", "2-Back"]

        for i in range(len(levels)):
            blit_text_centered(screen, levels[i], GAME_FONT, color=GREEN)
            pygame.display.update()

            # wait for a key press
            pygame.event.wait()
            screen.fill(BLACK)
            pygame.display.update()

            blit_text_centered(screen, rest_text, GAME_FONT, color=WHITE)
            pygame.display.update()
            
            # wait for a key press
            pygame.event.wait()
            screen.fill(BLACK)
            pygame.display.update()

            blit_text_centered(screen, '+', GAME_FONT, color=WHITE)
            pygame.display.update()
            pygame.time.set_timer(pygame.USEREVENT+1, REST_TIME, 1)

            shown_symbols = []
            for trial in range(PRACTICE_LEN):
                symbol, is_target = pick_nback_symbol(shown_symbols=shown_symbols, n_level=i, symbols=SYMBOLS)
                
                # https://www.pygame.org/docs/ref/time.html
                blit_text_centered(screen, symbol, GAME_FONT, color=WHITE)
                pygame.display.update()

                # participant should be able respond during this time in addition to response window
                pygame.time.set_timer(pygame.USEREVENT+2, STIMULUS_DISPLAY_TIME, 1)

                screen.fill(BLACK)
                pygame.display.update()

                pygame.time.set_timer(pygame.USEREVENT+3, RESPONSE_WINDOW_TIME, 1)

            # practice: go through each nback level once
            # after practice, randomize nback levels for number of blocks


pygame.quit()