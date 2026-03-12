from collections import deque
from datetime import datetime
# from lsl_app.device_layers.nback_layer import NbackLayer
# from lsl_app.device_layers.drt_layer import DRT_layer
import csv
import random
import sys
import argparse
import os
import numpy as np
import pandas as pd


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Force basic OpenGL
# prefs.hardware['openGL'] = 'legacy'
# prefs.general['winType'] = 'pygame'

# os.environ['MESA_GL_VERSION_OVERRIDE'] = '3.3'
# os.environ['LIBGL_ALWAYS_SOFTWARE'] = '1'
# os.environ['PSYCHOPY_FORCE_OPENGL'] = '0'


class Nback():
    def __init__(self, marker_stream=None, n_level=0, block_num=1, win=None):
        self.marker = marker_stream
        self.nback_level = n_level
        self.blocks = block_num
        self.DEBUG_MODE = True

        self.YES_BUTTON = 'a'
        self.NO_BUTTON = 'b'

        # joystick button indices
        B_BUTTON = 1
        A_BUTTON = 2

        self.INSTRUCTIONS = lambda n_level: visual.TextStim(
            win,
            text=f"{n_level}-Back Task\n\nPress A if current letter matches {n_level} back.\nPress B otherwise.\n\nPress any button to begin.",
            height=0.05,
            color='white'
        )

        self.FIXATION_TIME = 0.5
        self.STIMULUS_DISPLAY_TIME = 0.5
        self.RESPONSE_WINDOW_TIME = 1.5
        self.JITTER_RANGE = (0.1, 0.5)
        self.STOP_TIME = 0.5
        self.REST_TIME = 0.5 if self.DEBUG_MODE else 30.0

def connect_joystick():
    joystick.backend = 'pyglet'
    # print(joystick.getAllJoysticks())
    print(joystick)
    return joystick.Joystick(0)
    # joys = joystick.getNumJoysticks()
    # joy_connected = False
    # if joys > 0:
    #     print("Joystick connected!")
    #     joy_connected = True

    # if joy_connected:
    #     joy = joystick.Joystick(0)
    
    # return joy

def pick_nback_symbol(nback_level, shown_symbols):
    if nback_level == 0:
        symbol = random.choice(shown_symbols)
        is_target = True
    elif len(shown_symbols) < nback_level: 
        symbol = random.choice(shown_symbols)
        is_target = False
    elif np.random.rand() < TARGET_RATIO:
        symbol = shown_symbols[-nback_level]
        is_target = True
    else:
        is_target = False
        symbol = random.choice([s for s in shown_symbols if s != shown_symbols[-nback_level]])
    
    return symbol, is_target

def run_nback_block(nback_level, block_num):

    # nback_layer = NbackLayer()
    joy = connect_joystick()

    INSTRUCTIONS(nback_level).draw()
    win.flip() 
    
    event.waitKeys(keyList=['return', 'space'])
    
    fixation_cross.draw()
    win.flip()
    core.wait(FIXATION_TIME)
    win.flip()
  
    results = []
    
    # nback_layer.send_sample(f"{nback_level}/START")

    for trial_num in range(TRIALS_PER_BLOCK): 
        stim_text.text, is_target = pick_nback_symbol(nback_level, shown_symbols)
       
        jitter_time = random.uniform(*JITTER_RANGE)
        
        DRT = None
        pressed = {'response': None, 'drt': None}
        
        timer = core.Clock()
        
        while timer.getTime() < (RESPONSE_WINDOW_TIME + jitter_time):

            if timer.getTime() < STIMULUS_DISPLAY_TIME:
                stim_text.draw()
            
            win.flip()
            # nback_layer.send_sample(f"{nback_level}/{is_target}")

            if not pressed['response'] and joy.getButton(A_BUTTON):
                pressed['response'] = {'button': A_BUTTON, 'rt': timer.getTime()}
                # nback_layer.send_sample(f"{nback_level}/RESPONSE/A")
            elif not pressed['response'] and joy.getButton(B_BUTTON):
                pressed['response'] = {'button': B_BUTTON, 'rt': timer.getTime()}
                # nback_layer.send_sample(f"{nback_level}/RESPONSE/B")
            
            if not pressed['drt'] and joy.getButton(6):  # Assuming 6 is the trigger button index
                pressed['drt'] = True
                # DRT_layer.send_sample(core.Clock())

        results.append({
            'block': block_num,
            'trial': trial_num, 
            'symbol': stim_text.text,
            'ascii_symbol': ord(symbol),
            'is_target': is_target,
            'response': pressed['response']['button'] if pressed['response'] else None,
            'correct': is_target and pressed['response']['button'] == B_BUTTON or \
                      not is_target and pressed['response']['button'] == A_BUTTON,
            'rt': pressed['response']['rt'] if pressed['response'] else None,
            'raw_time': core.getTime(),
            'nback_level': nback_level, 
            'jitter_time': jitter_time
        })


    def pick_nback_symbol(self, shown_symbols):
        if self.nback_level == 0:
            symbol = random.choice(self.shown_symbols)
            is_target = True
        elif len(shown_symbols) < self.nback_level: 
            symbol = random.choice(self.shown_symbols)
            is_target = False
        elif np.random.rand() < self.TARGET_RATIO:
            symbol = shown_symbols[-self.nback_level]
            is_target = True
        else:
            is_target = False
            symbol = random.choice([s for s in self.shown_symbols if s != shown_symbols[-self.nback_level]])
        
        return symbol, is_target

    def run_nback_block(self, block_num):
        # initialize nback layer and drt layer
        #nback_layer = NbackLayer()

        joy = self.connect_joystick()
        print(":/")
        self.INSTRUCTIONS(self.nback_level).draw()
        self.win.flip() 
        self.get_user_input()

        # any_button = self.get_user_input(joy, self.INSTRUCTIONS(self.nback_level))
        # while True not in any_button:   
        #     any_button = self.get_user_input(joy, self.INSTRUCTIONS(self.nback_level))
        
        self.fixation_cross.draw()
        self.win.flip()
        core.wait(self.FIXATION_TIME)
        self.win.flip()
    
        results = []
        shown_symbols = []

        # start trial marker
        self.marker.send_sample(f"{self.nback_level}/START")

        for trial_num in range(self.TRIALS_PER_BLOCK): 
            symbol, is_target = self.pick_nback_symbol(self.nback_level, shown_symbols)
            shown_symbols.append(symbol)
            ASCII_symbol = ord(symbol)
            
            self.stim_text.text = symbol
            self.stim_text.draw()
            self.win.flip()
            stim_shown = True
            
            key_pressed = False
            response = None
            rt = None
            
            timer = core.Clock()
            jitter_time = random.uniform(*self.JITTER_RANGE)
            
            while timer.getTime() < (self.RESPONSE_WINDOW_TIME + jitter_time):
                if stim_shown and timer.getTime() >= self.STIMULUS_DISPLAY_TIME:
                    self.win.flip()
                    stim_shown = False
                
                #keys = event.getKeys(timeStamped=timer)
                if stim_shown:
                    buttons = self.get_joy_input(joy, self.stim_text)
                else:
                    buttons = self.get_joy_input(joy)

                if True in buttons and not key_pressed:
                    key_pressed = True
                    rt = timer.getTime()
                    
                    if buttons[self.A_BUTTON]:
                        print(f"{self.nback_level}/YES")
                        self.marker.send_sample(f"{self.nback_level}/YES")
                        response = True
                        
                    elif buttons[self.B_BUTTON]:
                        print(f"{self.nback_level}/NO")
                        self.marker.send_sample(f"{self.nback_level}/NO")
                        response = False
                        
                    
                #     # response marker
                #     if response == YES_BUTTON:
                #         rstr = "YES"
                #     elif response == NO_BUTTON:
                #         rstr = "NO"
                #     # if for some reason the response isn't yes or no, keep going
                #     else:
                #         continue
                #     nback_layer.send_sample(f"{nback_level}/{rstr}")

            if is_target == response:
                correct = True
            else:
                correct = False

            results.append({
                'block': block_num,
                'trial': trial_num, 
                'symbol': symbol,
                'ascii_symbol': ASCII_symbol,
                'is_target': is_target,
                'response': response,
                'correct': correct,
                'response_time': rt,
                'raw_time': core.getTime(),
                'nback_level': self.nback_level, 
                'jitter_time': jitter_time
            })

        self.stop_text.text = "STOP"
        self.stop_text.draw()
        self.win.flip()
        self.core.wait(self.STOP_TIME)
        self.win.flip()

        self.fixation_cross.draw()
        self.win.flip()
        core.wait(self.REST_TIME)
        self.win.flip()
        
        results = pd.DataFrame(results)
        results.to_csv(self.SAVE_FILE, index=False)
        self.win.close()
        core.quit() 

def parse_arguments():
    parser = argparse.ArgumentParser(description='N-Back Task')
    parser.add_argument('-n', '--nback', type=int, default=2,
                    help='N-back level (default: 2)')
    parser.add_argument('-b', '--block', type=int, default=40,
                    help='Sequence trial length (default: 40)')
    
    return parser.parse_args()  

if __name__ == "__main__":
    args = parse_arguments()
    nback_num = args.nback
    block = args.block

    nback = Nback(n_level=nback_num, block_num=block)
    results = nback.run_nback_block(block_num=block)
    