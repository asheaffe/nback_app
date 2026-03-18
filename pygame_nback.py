# NEW PYGAME NBACK CODE
# USING STARTER CODE FROM https://kidscancode.org/blog/2016/08/pygame_1-1_getting-started/
import pygame
import pygame.freetype
import random
import math
import numpy as np
import time
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--blocks', type=int, default=9, help='number of experimental blocks to run')
parser.add_argument('--debug', type=bool, default=False, help='Activate debug mode for fewer trials per block')
args = parser.parse_args()

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
BLOCK_NUM             = args.blocks      # non-practice block number
# for debugging set REST_TIME shorter
DEBUG                 = args.debug      # debug mode

if DEBUG:
    REST_TIME = 1000
    TRIAL_LEN = 10


# timer event IDs
EV_REST_DONE = pygame.USEREVENT + 1
EV_STIM_DONE = pygame.USEREVENT + 2
EV_RESP_DONE = pygame.USEREVENT + 3


# state machine states
STATE_INSTR = "INSTR"
STATE_LEVEL = "LEVEL_TITLE"
STATE_REST = "REST"
STATE_FIXATION = "FIXATION"
STATE_STIM = "STIM"
STATE_RESPONSE = "RESPONSE"
STATE_DONE = "DONE"
STATE_READY = "READY"
STATE_CORRECT = "CORRECT"
STATE_INCORRECT = "INCORRECT"
STATE_SUMMARY = "SUMMARY"

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
# state machine variables
state = STATE_INSTR         # start on instructions
n_levels = [0, 1, 2]          # tutorial levels
level_idx = 0               # index into levels
n_level = n_levels[level_idx] # current N val
trial_idx = 0               # trial counter within current block
block_len = PRACTICE_LEN    # how many trials per block
shown_symbols = []          # history of symbols shown for later n-back matching
current_symbol = None       # current displayed char
current_is_target = None    # whether current letter is an n-back target
response_made = False       # bool preventing multiple key presses counting in one trial
running = True              
rest_end_ms = None          # used to display countdown during REST state
block_num = 0

# get the experimental block list
if BLOCK_NUM % len(n_levels) != 0:
    print(f"WARNING: {BLOCK_NUM} blocks is not evenly divisible by {len(n_levels)} levels.")

levels = [lvl for lvl in n_levels for _ in range(BLOCK_NUM // len(n_levels))]
print(levels)

# stat variables to show at the end of the block
num_correct = 0             # number of correct responses
num_no_response = 0         # didn't respond when supposed to
num_false_alarm = 0         # responded when not supposed to
num_targets = 0             # for total targets in block

instruction_text = "Welcome to the N-back task! \nYou will be presented with a series of letters. " \
"\nPlease indicate if the letter presented occurred N places back. \nWe will start with a tutorial for all N-back levels (0,1,2). \n\nPress any key to begin."

zero_text = "This is the 0-back task \nPress any button to indicate if the current letter occurred 0 places back in the sequence"
one_text = "This is the 1-back task \nPress any button to indicate if the current letter occurred 1 places back in the sequence"
two_text = "This is the 2-back task \nPress any button to indicate if the current letter occurred 2 places back in the sequence"

block_summary_text = f"BLOCK SUMMARY:\nCorrect Responses: {num_correct}\nFalse Alarms: {num_false_alarm}\nNo Response: {num_no_response}"

rest_text = f"Please rest for 30 seconds before beginning the trial"

prev_state = None
while running:
    if state != prev_state:
        #print("STATE ->", state)
        prev_state = state
    # controls spped of loop
    clock.tick(FPS)

    # event handling
    for event in pygame.event.get():
        # check for closing window
        if event.type == pygame.QUIT:
            running = False
       
        # any key from instruction screen -> go to level title
        elif event.type == pygame.KEYUP and state == STATE_INSTR:
            state = STATE_LEVEL

        # any key from level title -> go to state ready
        elif event.type == pygame.KEYUP and state == STATE_LEVEL:
            # reset summary variables
            num_correct = 0             
            num_no_response = 0         
            num_false_alarm = 0 
            num_targets = 0

            print(f"BLOCK: {block_num}\tNBACK LEVEL: {n_level}")

            state = STATE_READY 

        # any key from summary -> go to state 
        elif event.type == pygame.KEYUP and state == STATE_SUMMARY:
            trial_idx = 0
            shown_symbols = []

            if tutorial:
                #level_idx += 1
                if level_idx < len(n_levels):
                    # more tutorial levels remain
                    n_level = n_levels[level_idx]
                    state = STATE_LEVEL
                else:
                    # all tutorial levels done
                    tutorial = False

                    n_level = random.choice(levels)
                    levels.remove(n_level)

                    #level_idx = 0
                    state = STATE_LEVEL

            elif not tutorial and levels: 
                # randomly choose a level from full list
                n_level = random.choice(levels)
                levels.remove(n_level)
                block_num += 1
                state = STATE_LEVEL

            else:
                # end the program
                state = STATE_DONE

        # any key from ready state -> start rest timer + countdown
        elif event.type == pygame.KEYUP and state == STATE_READY:
            state = STATE_REST
            rest_end_ms = pygame.time.get_ticks() + REST_TIME
            pygame.time.set_timer(EV_REST_DONE, REST_TIME, 1)
        
        # key presses during stimulus or response count as a response only once
        elif event.type == pygame.KEYUP and state in (STATE_STIM, STATE_RESPONSE):
            if not response_made: 
                response_made = True

                # cancel timers?
                pygame.time.set_timer(EV_STIM_DONE, 0)
                pygame.time.set_timer(EV_RESP_DONE, 0)
                pygame.time.set_timer(EV_RESP_DONE, STOP_TIME, 1)

                # if current letter is the target
                if current_is_target:
                    num_correct += 1
                    state = STATE_CORRECT
                elif not current_is_target:
                    num_false_alarm += 1
                    state = STATE_INCORRECT

        # rest timer finished -> fixation begins
        elif event.type == EV_REST_DONE and state == STATE_REST: 
            # get the first stim letter
            current_symbol, current_is_target = pick_nback_symbol(shown_symbols, n_level, SYMBOLS)
            shown_symbols.append(current_symbol)

            # count the number of targets in a block
            if current_is_target:
                num_targets += 1

            state = STATE_STIM
            pygame.time.set_timer(EV_STIM_DONE, STIMULUS_DISPLAY_TIME, 1)

            rest_end_ms = None
            state = STATE_STIM
            pygame.time.set_timer(EV_STIM_DONE, FIXATION_TIME, 1)

        # current phase ended
        elif event.type == EV_STIM_DONE:
            # fixation ended -> show stimulus
            if state == STATE_FIXATION: 
                current_symbol, current_is_target = pick_nback_symbol(shown_symbols, n_level, SYMBOLS)
                shown_symbols.append(current_symbol)
                
                # count the number of total targets
                if current_is_target:
                    num_targets += 1

                state = STATE_STIM
                pygame.time.set_timer(EV_STIM_DONE, STIMULUS_DISPLAY_TIME, 1)
                
            # stimulus ended -> resposne window begins
            elif state == STATE_STIM:
                state = STATE_RESPONSE

                # incorporating jitter to response window
                jitter_time = int(random.uniform(JITTER_RANGE[0], JITTER_RANGE[1]))
                pygame.time.set_timer(EV_RESP_DONE, (RESPONSE_WINDOW_TIME + jitter_time), 1)

        # show correct/incorrect for response window time
        elif event.type == EV_RESP_DONE and state in (STATE_CORRECT, STATE_INCORRECT):
            state = STATE_RESPONSE
            pygame.time.set_timer(EV_RESP_DONE, RESPONSE_WINDOW_TIME - STOP_TIME, 1)

        # response window finished -> either next trial or next level
        elif event.type == EV_RESP_DONE and state == STATE_RESPONSE: 
            # 10 trials for tutorial, 40 trials for actual
            if tutorial:
                block_len = PRACTICE_LEN
            else:
                block_len = TRIAL_LEN
            
            # check if a response was made and the user should've responded
            if not response_made and current_is_target:
                num_no_response += 1

            trial_idx += 1
            response_made = False

            # finished this block -> advance to next level or DONE
            if trial_idx >= block_len: 
                level_idx += 1
                state = STATE_SUMMARY

                # if level_idx >= len(levels): 
                #     state = STATE_DONE
                # else:
                #     n_level = levels[level_idx]
                #     trial_idx = 0
                #     shown_symbols = [] # reset history for next level
                #     state = STATE_LEVEL

            # more trials remain -> start next trial w/ fixation
            else: 
                current_symbol, current_is_target = pick_nback_symbol(shown_symbols, n_level, SYMBOLS)
                shown_symbols.append(current_symbol)

                # count the number of targets in a block
                if current_is_target:
                    num_targets += 1

                state = STATE_STIM
                pygame.time.set_timer(EV_STIM_DONE, STIMULUS_DISPLAY_TIME, 1)

    screen.fill(BLACK)
    # rendering
    if state == STATE_INSTR: 
        blit_text_centered(screen, instruction_text, GAME_FONT, color=WHITE)
    elif state == STATE_LEVEL: 
        if tutorial:
            blit_text_centered(screen, f"{n_level}-Back (tutorial)\nPress any key", GAME_FONT, color=GREEN)
        else:
            blit_text_centered(screen, f"{n_level}-Back\nPress any key", GAME_FONT, color=GREEN)
    elif state == STATE_REST:
        now = pygame.time.get_ticks()
        if rest_end_ms is None:
            remaining_s = math.ceil(REST_TIME / 1000)
        else: 
            remaining_ms = max(0, rest_end_ms - now)
            remaining_s = math.ceil(remaining_ms / 1000)
        
        blit_text_centered(screen, f"+", GAME_FONT, color=WHITE)
        
    elif state == STATE_STIM: 
        blit_text_centered(screen, current_symbol, GAME_FONT, color=WHITE)
    elif state == STATE_DONE:
        blit_text_centered(screen, "Done!", GAME_FONT, color=GREEN)
    elif state == STATE_READY:
        # prompt the user after the fixation cross
        blit_text_centered(screen, 'We will begin a rest period. \nPlease stare at the fixation cross for 30 seconds. \nPress any button to begin', GAME_FONT, color=WHITE)
    elif state == STATE_CORRECT and tutorial:
        # display to the user that they are correct
        blit_text_centered(screen, "Correct!", GAME_FONT, color=GREEN)
    elif state == STATE_INCORRECT and tutorial:
        # display to the user that they are incorrect
        blit_text_centered(screen, "Incorrect", GAME_FONT, color=RED)
    elif state == STATE_SUMMARY:
        percent_correct = (num_correct/num_targets) * 100
        # display stats after block
        blit_text_centered(screen, f"BLOCK SUMMARY:\nCorrect Responses: {percent_correct}%\nFalse Alarms: {num_false_alarm}\nNo Response: {num_no_response}\n\nPress any button to continue", GAME_FONT, color=WHITE)

    pygame.display.update()

pygame.quit()