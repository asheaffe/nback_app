from collections import deque
from psychopy import visual, core, event, gui, prefs
from psychopy.hardware import joystick
from datetime import datetime
import csv
import random
import sys
import argparse
import os
import numpy as np
import pandas as pd
import asyncio
from datetime import datetime

# TODO: don't use psychopy what the freak
# TODO: remove stupidass python multithreading shit


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

async def Nback(n_level=0, 
                block_num=1,                                              
                pid=None, 
                practice=True,
                marker_stream=None, 
                win=None, 
                DEBUG_MODE=False,
                DRT_socket=None, 
                walking=False):                        
    
    walking = walking.upper()

    save_path = "nback_2025/results"
                
    joystick.backend = 'pyglet'
    joy = joystick.Joystick(0)
    
    SYMBOLS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    TRIALS_PER_BLOCK      = 5 if DEBUG_MODE else 40
    FIXATION_TIME         = 0.5
    STIMULUS_DISPLAY_TIME = 0.5
    RESPONSE_WINDOW_TIME  = 2
    JITTER_RANGE          = (0.1, 0.5)
    STOP_TIME             = 0.5
    REST_TIME             = 0.5 if DEBUG_MODE else 30.0
    DRT_TIME              = 5
    DRT_JITTER_RANGE      = (0.0, 5.0)


    # joystick indices
    B_BUTTON = 1
    A_BUTTON = 2
    TRIGGER = 6
            
    stim_text        = visual.TextStim(win, text='',  height=0.20, color='white', units='height')
    stop_text        = visual.TextStim(win, text='',  height=0.20, color='white')
    fixation_cross   = visual.TextStim(win, text='+', height=0.10, color='white')
    summary_text     = visual.TextStim(win, text='',  height=0.05, color='white', pos=(0, 0))                
    
    correct_text     = visual.TextStim(win, text='CORRECT',   height=0.20, color='green')
    incorrect_text   = visual.TextStim(win, text='INCORRECT', height=0.20, color='red')
    
    rest_text = visual.TextStim(
        win,
        text = f"""Please rest for {REST_TIME} seconds before beginning the trial""",
        height=0.05,
        color='white',
        pos = (0, -0.1)
    )
    
    stim_text.draw()
    win.flip()
    marker_stream.send_sample(f"{n_level}/{walking}/REST", is_practice=practice)
    timer = core.Clock()
    while timer.getTime() < REST_TIME:
        if timer.getTime() < 3:
            rest_text.draw()
        else:
            fixation_cross.draw()
        win.flip()
    
    win.flip()
    
    
    if practice:
        practice_message = 'This is a series of practice trials. You will be shown if your answers are correct or incorrect'
    else:
        practice_message = 'You will NOT be shown the correctness of your trials during this task.'

    nback_text = visual.TextStim(
        win, 
        text = f"""{n_level}-Back {walking} Task""",
        height = 0.1,
        color = 'white',
        pos = (0, 0.3)
    )
    
    instruction_text = visual.TextStim(
        win,
        text = f"""You will see a series of letters on the screen. For each letter:\n\nPress A if the current letter matches the letter seen {n_level} letters previously.\nPress B otherwise.\n\n{practice_message}            
        """,
        height=0.05,
        color='white',
        pos = (0, -0.1)
    )
    
    marker_stream.send_sample(f"{n_level}/{walking}/INSTRUCTION", is_practice=practice)
    nback_text.draw()
    instruction_text.draw()
    win.flip()
    
    # experimenter presses key to start
    event.waitKeys(keyList=['return', 'space'])

    # one fixation cross
    fixation_cross.draw()
    win.flip()
    core.wait(FIXATION_TIME)
    win.flip()
        
    vibe_time = core.getTime() + DRT_TIME + random.uniform(*DRT_JITTER_RANGE)
            
    # block start
    marker_stream.send_sample(f"{n_level}/{walking}/START_BLOCK", is_practice=practice)
    results, shown_symbols = [], []            
    for trial_num in range(TRIALS_PER_BLOCK): 

        symbol, is_target = pick_nback_symbol(shown_symbols, n_level, SYMBOLS) 
        jitter_time       = random.uniform(*JITTER_RANGE)
        stim_text.text    = symbol
        pressed           = {
                                'response': {'button': None, 'rt': None}, 
                                'drt':      {'pressed': False, 'time': None}
                            }
        timer             = core.Clock()        

        while timer.getTime() < (RESPONSE_WINDOW_TIME + jitter_time):

            if timer.getTime() < STIMULUS_DISPLAY_TIME:
                stim_text.draw()
                        
            win.flip()          

            if vibe_time != None and core.getTime() >= vibe_time:                
                DRT_socket.send("EXECUTE_VIBRATION")
                vibe_rt_timer = core.Clock()
                marker_stream.send_sample(f"{n_level}/{walking}/DRT_STIM", is_practice=practice)
                if trial_num >= TRIALS_PER_BLOCK - 2:
                    vibe_time = None
                else:
                    vibe_time = core.getTime() + DRT_TIME + random.uniform(*DRT_JITTER_RANGE)
                
                        
            marker_stream.send_sample(f"{n_level}/{walking}/{'IS_TARGET' if is_target else 'NOT_TARGET'}", is_practice=practice)
            
            if not pressed['response']['button'] and ((joy.getButton(A_BUTTON) or joy.getButton(B_BUTTON)) or (joy.getButton(A_BUTTON) and joy.getButton(B_BUTTON))):
                rt = timer.getTime()

                if joy.getButton(A_BUTTON) and joy.getButton(B_BUTTON):
                    button = "BOTH"                        
                elif joy.getButton(A_BUTTON):
                    button = "A"
                elif joy.getButton(B_BUTTON):
                    button = "B"
                
                marker_stream.send_sample(f"{n_level}/{walking}/RESPONSE/{button}", is_practice=practice)
                pressed['response']['button'] = button 
                pressed['response']['rt']     = rt

            if not pressed['drt']['pressed'] and joy.getButton(TRIGGER):
                marker_stream.send_sample(f"{n_level}/{walking}/DRT_RESPONSE", is_practice=practice)
                pressed['drt']['pressed'] = True
                pressed['drt']['time']    = vibe_rt_timer.getTime()                
                                                                                    
        shown_symbols.append(symbol)


        correct =     is_target and pressed['response']['button'] == "A" or \
                    not is_target and pressed['response']['button'] == "B"

        if practice:
            if correct:
                correct_text.draw()
            else:
                incorrect_text.draw()
            
            win.flip()
            core.wait(STIMULUS_DISPLAY_TIME)
            win.flip()
            
        results.append({
            'pid': pid,
            'block': block_num,
            'trial': trial_num, 
            'n_level': n_level, 
            'symbol': symbol,
            'ascii_symbol': ord(symbol),
            'is_target': is_target,
            'response': pressed['response']['button'],                
            'rt': pressed['response']['rt'],
            'correct': correct,
            'drt': pressed['drt']['pressed'],
            'drt_time': pressed['drt']['time'],
            'raw_time': core.getTime(),                
            'jitter_time': jitter_time
        })

    stop_text.text = "STOP"
    stop_text.draw()
    win.flip()
    core.wait(STOP_TIME)
    win.flip()
    
    results = pd.DataFrame(results)
    
    print(f"Percentage of correct trials for this block: {results.correct.sum() / results.shape[0]}")

    results.to_csv(f"{save_path}/{block_num}_{n_level}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", index=False)
    win.close()

        #core.quit()                