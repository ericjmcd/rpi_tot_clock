# -*- coding: utf-8 -*-
import pygame
from MenuSystem import MenuSystem
import time
import glob
import os
import random
from datetime import datetime, time as dt_time
pygame.init()

DEBUG=False
SONG_REPEATS=3
SLEEPING_COLOR=pygame.Color(0,50,255,80) # blueish
WAKING_COLOR=pygame.Color(0,150,255,80) # light blueish
AWAKE_COLOR=pygame.Color(255,200,0,80) #yellowish
BEDTIME_COLOR=pygame.Color(200,100,0,80) # orangish
STATE_COLORS={0:WAKING_COLOR,
              1:AWAKE_COLOR,
              2:BEDTIME_COLOR,
              3:SLEEPING_COLOR,
              }

cur_dir = os.path.dirname(os.path.abspath(__file__))

infoObject = pygame.display.Info()
window_size=(infoObject.current_w, infoObject.current_h)
window_size=(800,640)
#scr=pygame.display.set_mode(window_size,pygame.FULLSCREEN)
scr=pygame.display.set_mode(window_size)

window_size=scr.get_rect()[2:]

def create_image(filename):
    # Convenience function to load image file into image object
    try: 
        image=pygame.image.load(filename)
        image=pygame.transform.scale(image, window_size)
        image=image.convert()
    except:
        print('Cannot load image: %s'%filename)
        image=None
    return image

def fill_gradient(surface, color, gradient, rect=None, vertical=True, forward=True):
    """fill a surface with a gradient pattern
    Parameters:
    color -> starting color
    gradient -> final color
    rect -> area to fill; default is surface's rect
    vertical -> True=vertical; False=horizontal
    forward -> True=forward; False=reverse
    
    Pygame recipe: http://www.pygame.org/wiki/GradientCode
    """
    if rect is None: rect = surface.get_rect()
    x1,x2 = rect.left, rect.right
    y1,y2 = rect.top, rect.bottom
    if vertical: h = y2-y1
    else:        h = x2-x1
    if forward: a, b = color, gradient
    else:       b, a = color, gradient
    rate = (
        float(b[0]-a[0])/h,
        float(b[1]-a[1])/h,
        float(b[2]-a[2])/h
    )
    fn_line = pygame.draw.line
    if vertical:
        for line in range(y1,y2):
            color = (
                min(max(a[0]+(rate[0]*(line-y1)),0),255),
                min(max(a[1]+(rate[1]*(line-y1)),0),255),
                min(max(a[2]+(rate[2]*(line-y1)),0),255)
            )
            fn_line(surface, color, (x1,line), (x2,line))
    else:
        for col in range(x1,x2):
            color = (
                min(max(a[0]+(rate[0]*(col-x1)),0),255),
                min(max(a[1]+(rate[1]*(col-x1)),0),255),
                min(max(a[2]+(rate[2]*(col-x1)),0),255)
            )
            fn_line(surface, color, (col,y1), (col,y2))

    
scr.fill((0,0,0)) # wipe screen (to black)
bg=None
scrrect = scr.get_rect()
pygame.display.flip()

# Hour, Minute for transition times
# (assumes: transition to wakeup, wakeup, transition to sleep, asleep) 
state_times=[(6,15),(6,30),(18,45),(19,0)] # 24 hour times to start state
state_times=[dt_time(*i) for i in state_times]

MenuSystem.init()
MenuSystem.BGCOLOR = pygame.Color(200,200,200,80)
MenuSystem.FGCOLOR = pygame.Color(200,200,200,255)
MenuSystem.BGHIGHTLIGHT = pygame.Color(0,0,0,180)
MenuSystem.BORDER_HL = pygame.Color(200,200,200,180)

mode_menu  = MenuSystem.Menu('Mode',  ('Sleeping','Awake'))
audio_menu = MenuSystem.Menu('Audio', ('Silence','Rain','Ocean')) # Fixme - make selection
song_menu  = MenuSystem.Menu('Song', ('No Song','Aquarium1','Aquarium2','Aquarium3','Lullaby'))

audio=('Silence','Not Playing')
song=('No Song','Not Playing') # song and status (Not Playing, Playing, Played) 

mode_choice = MenuSystem.MenuChoice()
mode_choice.set(mode_menu,(10,10),w=150)
pygame.display.update(mode_choice)

audio_choice = MenuSystem.MenuChoice()
audio_choice.set(audio_menu,(210,10),w=150)
pygame.display.update(audio_choice)

song_choice = MenuSystem.MenuChoice()
song_choice.set(song_menu,(410,10),w=150)
pygame.display.update(song_choice)

exit = MenuSystem.Button('EXIT',100,30)
exit.bottomright =  scrrect.w-10,scrrect.h-10
exit.set()

done=False
clock = pygame.time.Clock()
FPS=10
alpha=255
BG_SWAP_DURATION_SECS=3.0
alpha_delta=255.0/(BG_SWAP_DURATION_SECS*FPS)
last_motion = time.time()
menu_hide_delay=3

refresh_bg_delay=10
last_bg_refresh=time.time()
state=0
force_state=False # for manual
forced_state=0
one_shot_bg = True

def add_top_bot_colors(screen,color):
    window_size=screen.get_rect()[2:]
    height=100
    rect_size=(window_size[0],height)
    BLACK=(0,0,0)
    surf = pygame.Surface(rect_size)
    fill_gradient(surf, color,BLACK)
    screen.blit(surf, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
    surf = pygame.Surface(rect_size)
    fill_gradient(surf, color,BLACK,forward=False)
    screen.blit(surf, (0, window_size[1]-rect_size[1]), special_flags=pygame.BLEND_RGB_ADD)     

if DEBUG:
    now=datetime.now()
    state_times=[(now.hour+(now.minute+x)/60,(now.minute+x)%60) for x in range(4)]
    state_times=[dt_time(*i) for i in state_times]    

#print 'Now',now.hour,':',now.minute
#print 'Times',state_times
while not done:
    # FIXME
    # Hack to get the menus to work since they don't play well with
    # blitting the background
    clock.tick(FPS)    
    show_menus=time.time()-last_motion<menu_hide_delay # hide after no input    
    pygame.mouse.set_visible(show_menus) # show menus first
    if not show_menus or one_shot_bg: # don't update bg if menus are up
        now=datetime.now().time()
        next_state=len(state_times)-1 # default if now>all
        for i in range(len(state_times)):
            if now<state_times[i]:
                next_state=(i-1)%len(state_times)
                break        
        new_state=False
        if next_state != state:
            print 'Cur state',state,'New state',next_state
            new_state=True
            state=next_state
            if state in [0,2]: # awake or sleeping, clear forced_state
                force_state=False
    
    if show_menus and not one_shot_bg:
        exit.draw()
        mode_choice.draw()
        audio_choice.draw()
        song_choice.draw()
    else:
        if bg !=None:
            scr.blit(bg,(0,0))
        if (alpha==255 and time.time()-last_bg_refresh>refresh_bg_delay) or new_state or one_shot_bg:
            alpha=0
            last_bg_refresh=time.time()
            _state = forced_state if force_state else state
            
#             if _state==3: # sleeping
#                 dir="./sleeping/*"
#             elif _state==1: # awake
#                 dir="./awake/*"
#             else: # transitions
#                 dir="./transitions/*"
            dir="./images/*" # just use one directory now with color banners
            dir=os.path.join(cur_dir,dir)
            files=glob.glob(dir)                
            #print(files)
            #fname=os.path.join('sleeping',files[random.randint(0,len(files)-1)])
            fname=files[random.randint(0,len(files)-1)]
            #print(fname)
            bg2=create_image(fname)
        
        alpha = min(255,alpha+alpha_delta)
        if alpha==255: # done blending, so update image
            bg=bg2
        if one_shot_bg:
            alpha=255
            bg=bg2
        bg2.set_alpha(int(alpha))
        scr.blit(bg2,(0,0))
        one_shot_bg=False
        bar_color = STATE_COLORS[state]
        add_top_bot_colors(scr,bar_color)
                             
    # Display time
    dt_now = datetime.now()
    time_str='%02d:%02d:%02d'%(dt_now.hour%12,dt_now.minute,dt_now.second)
    font = MenuSystem.FONT#pygame.font.Font(None, 72)
    gray = (50,50,50)    
    text = font.render(time_str, 1, gray)
    textpos = text.get_rect()
    textpos.left = int(window_size[0]*0)
    textpos.bottom = int(window_size[1])
    pygame.draw.rect(scr, (0,0,0),textpos,0)    
    scr.blit(text, textpos)        
        
    for ev in pygame.event.get():
        if ev.type == pygame.MOUSEMOTION:
            last_motion = time.time()
                
        #print('evals',bar,audio_choice,song_choice)
        if mode_choice.update(ev):
            if mode_choice.choice:
                mode = mode_choice.choice_label[0]
                forced_state = 0 if mode=='Sleeping' else 2 #Awake
                force_state = True
                one_shot_bg = True # refresh background
        if song_choice.update(ev):
            if song_choice.choice:
                _song = song_choice.choice_label[0]
                if song[0] != _song: # new select so update
                    song = (_song, 'Not Playing')                

        if audio_choice.update(ev):
            if audio_choice.choice:
                _audio = audio_choice.choice_label[0]
                if audio[0] != _audio:
                    audio=(_audio,'Not Playing')
        
        #print song,audio
        if audio=='Silence' and song[0]=='No Song':
            pygame.mixer.music.stop() # ensure nothing playing
        if song[0]!='No Song':
            if song[1]=='Playing' and pygame.mixer.music.get_busy()==0: # Song is over
                song=(song[0],'Played')
            elif song[1]=='Not Playing': # start new song
                pygame.mixer.music.stop()
                pygame.mixer.music.load(os.path.join(cur_dir,'sounds',song[0]+'.mp3'))
                if song[0]=='Lullaby': # Lullaby is 10 minutes long so don't repeat
                    pygame.mixer.music.play(0)
                else:
                    pygame.mixer.music.play(SONG_REPEATS)                
                song=(song[0],'Playing')
        
        if song[1]!='Playing' and audio[0]!='Silence' and audio[1]=='Not Playing':
            pygame.mixer.music.stop()
            pygame.mixer.music.load(os.path.join(cur_dir,'sounds',audio[0]+'.mp3'))
            audio=(audio[0],'Playing')
            pygame.mixer.music.play(-1) # loop indefinitely
        
        if exit.update(ev):
            if exit.clicked:
                done=True#break       
        if ev.type==12: # catch "X" close
            done=True
            
    pygame.display.flip()
        
pygame.quit()

        