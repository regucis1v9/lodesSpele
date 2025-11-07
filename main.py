import pygame
import random
import os
import math

# --- Initialization ---
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Six Seven")
clock = pygame.time.Clock()
# --- CRT Overlay Definition ---
def create_scanline_overlay(width, height, line_height=2, spacing=2):
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    color = (0, 0, 0, 50)  # semi-transparent black
    y = 0
    while y < height:
        pygame.draw.rect(overlay, color, (0, y, width, line_height))
        y += line_height + spacing
    return overlay

def create_vignette_overlay(width, height, strength=100):
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    for y in range(height):
        for x in range(width):
            dx = x - width / 2
            dy = y - height / 2
            dist = math.sqrt(dx*dx + dy*dy)
            max_dist = math.sqrt((width/2)**2 + (height/2)**2)
            alpha = int(strength * (dist / max_dist))
            overlay.set_at((x, y), (0, 0, 0, min(alpha, 255)))
    return overlay

# Create the overlays once
scanline_overlay = create_scanline_overlay(800, 600)
vignette_overlay = create_vignette_overlay(800, 600)
# --- Global volume variables ---
vfx_volume = 1.0
music_volume = 0.5

# --- Load music ---
pygame.mixer.music.load("assets/Kolonādes princis.mp3")
pygame.mixer.music.set_volume(music_volume)
pygame.mixer.music.play(-1)

# --- Load hand images ---
base_img = pygame.image.load("assets/roka.png").convert_alpha()
base_img = pygame.transform.scale(base_img, (100, 100))
left_hand_img = pygame.transform.rotate(base_img, 8)
right_hand_img = pygame.transform.flip(base_img, True, False)
right_hand_img = pygame.transform.rotate(right_hand_img, -8)
left_hand = left_hand_img.get_rect(center=(300, 500))
right_hand = right_hand_img.get_rect(center=(500, 500))
active_hand = left_hand
left_hand_inactive_img = pygame.transform.scale(left_hand_img, (80, 80))
right_hand_inactive_img = pygame.transform.scale(right_hand_img, (80, 80))
left_hand_inactive_img.set_alpha(128)
right_hand_inactive_img.set_alpha(128)

# --- Load fonts ---
font_small = pygame.font.Font("assets/PressStart2P-Regular.ttf", 16)
font_large = pygame.font.Font("assets/PressStart2P-Regular.ttf", 32)
font_go_small = pygame.font.Font("assets/PressStart2P-Regular.ttf", 22)
font_result_label = pygame.font.Font("assets/PressStart2P-Regular.ttf", 28)

# --- Load life images ---
life_img = pygame.image.load("assets/lode_pixel-removebg-preview.png").convert_alpha()
life_img = pygame.transform.scale(life_img, (40, 40))
life_img_lost = life_img.copy()
life_img_lost.set_alpha(64)

# --- Load damage frames ---
damage_frames_raw = [
    pygame.image.load("assets/frameOne.png").convert_alpha(),
    pygame.image.load("assets/frameTwo.png").convert_alpha(),
    pygame.image.load("assets/frameThree.png").convert_alpha()
]
damage_frames = []
for f in damage_frames_raw:
    scaled = pygame.transform.scale(f, (400, 300))
    rect = scaled.get_rect(center=(400, 300))
    damage_frames.append((scaled, rect))

# --- Load sounds ---
damage_sound = pygame.mixer.Sound("assets/Minecraft Potion Drinking - Sound Effect (HD).mp3")
success_sound_6 = pygame.mixer.Sound("assets/six.mp3")
success_sound_7 = pygame.mixer.Sound("assets/seven.mp3")
success_sound_6.set_volume(vfx_volume)
success_sound_7.set_volume(vfx_volume)
damage_sound.set_volume(vfx_volume)

# --- Load fire frames ---
fire_frames = []
fire_folder = "assets/fireGif"
for filename in sorted(os.listdir(fire_folder)):
    if filename.endswith(".gif"):
        img = pygame.image.load(os.path.join(fire_folder, filename)).convert_alpha()
        fire_frames.append(img)
fire_frame_index = 0
fire_frame_timer = 0.0
FIRE_FRAME_DURATION = 0.1

# --- Combo ---
combo_numbers = ["6","7"]
combo_status = [False,False]
combo_pos = [(350,10),(400,10)]
grey_color = (100,100,100)
full_color = (255,255,255)

# --- Game variables ---
BASE_NUMBER_SPEED = 5
LIFE_SPEED_MULTIPLIER = 1.2
MAX_TILT = 15
TILT_SPEED = 200
spawn_interval = 0.5
numbers_weighted = [0,1,2,3,4,5,6,6,7,7,8,9]

# --- Helper functions ---
def init_game():
    global numbers, score, multiplier, combo_state, elapsed_time, lives, spawn_timer
    global immunity, immunity_timer, hand_tilt_angle, combo_status
    numbers = []
    score = 0.0
    multiplier = 1.0
    combo_state = None
    elapsed_time = 0
    lives = 3
    spawn_timer = 0.0
    immunity = False
    immunity_timer = 0
    hand_tilt_angle = 0.0
    combo_status = [False, False]
    return left_hand, right_hand, active_hand

def play_damage_animation():
    damage_sound.play()
    overlay = pygame.Surface((800,600), pygame.SRCALPHA)
    overlay.fill((0,0,0,128))
    current_screen = screen.copy()
    for img, rect in damage_frames:
        screen.blit(current_screen,(0,0))
        screen.blit(img,rect)
        screen.blit(overlay,(0,0))
        pygame.display.flip()
        pygame.time.delay(200)
    damage_sound.stop()

def show_settings_popup():
    global vfx_volume, music_volume
    popup_rect = pygame.Rect(150,150,500,300)
    slider_width = 300
    slider_height = 20
    vfx_slider_rect = pygame.Rect(250,220,slider_width,slider_height)
    music_slider_rect = pygame.Rect(250,320,slider_width,slider_height)
    close_rect = pygame.Rect(popup_rect.right-50,popup_rect.top+10,40,40)
    dragging_vfx = False
    dragging_music = False
    last_vfx_volume = vfx_volume
    preview_queue = []
    running_popup = True
    while running_popup:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if vfx_slider_rect.collidepoint(mouse_pos): dragging_vfx=True
                if music_slider_rect.collidepoint(mouse_pos): dragging_music=True
                if close_rect.collidepoint(mouse_pos): running_popup=False
            if event.type == pygame.MOUSEBUTTONUP:
                dragging_vfx=False; dragging_music=False
        if dragging_vfx:
            rel_x = mouse_pos[0]-vfx_slider_rect.x
            vfx_volume = max(0,min(1,rel_x/slider_width))
        if dragging_music:
            rel_x = mouse_pos[0]-music_slider_rect.x
            music_volume = max(0,min(1,rel_x/slider_width))
        success_sound_6.set_volume(vfx_volume)
        success_sound_7.set_volume(vfx_volume)
        damage_sound.set_volume(vfx_volume)
        pygame.mixer.music.set_volume(music_volume)
        if vfx_volume!=last_vfx_volume:
            last_vfx_volume=vfx_volume
            preview_queue=[success_sound_6,success_sound_7]
        if preview_queue and not pygame.mixer.get_busy():
            preview_queue.pop(0).play()
        screen.fill((0,0,0))
        pygame.draw.rect(screen,(50,50,50),popup_rect)
        pygame.draw.rect(screen,(150,150,150),vfx_slider_rect)
        pygame.draw.rect(screen,(150,150,150),music_slider_rect)
        pygame.draw.circle(screen,(255,0,0),(vfx_slider_rect.x+int(vfx_volume*slider_width),vfx_slider_rect.centery),10)
        pygame.draw.circle(screen,(0,255,0),(music_slider_rect.x+int(music_volume*slider_width),music_slider_rect.centery),10)
        screen.blit(font_small.render("VFX Volume",True,(255,255,255)),(vfx_slider_rect.x,vfx_slider_rect.y-25))
        screen.blit(font_small.render("Music Volume",True,(255,255,255)),(music_slider_rect.x,music_slider_rect.y-25))
        pygame.draw.rect(screen,(200,0,0),close_rect)
        x_text=font_small.render("X",True,(0,0,0))
        screen.blit(x_text,x_text.get_rect(center=close_rect.center))
        screen.blit(scanline_overlay, (0, 0))
        screen.blit(vignette_overlay, (0, 0))
        pygame.display.flip()
        clock.tick(60)
        screen.blit(scanline_overlay, (0, 0))
        screen.blit(vignette_overlay, (0, 0))

def draw_text_with_outline(surf,text,font,color,outline_color,center):
    base=font.render(text,True,color)
    outline=font.render(text,True,outline_color)
    x,y=center
    for dx,dy in [(-1,-1),(-1,1),(1,-1),(1,1),(0,-1),(-1,0),(1,0),(0,1)]:
        surf.blit(outline,outline.get_rect(center=(x+dx,y+dy)))
    surf.blit(base,base.get_rect(center=center))

# --- Start screen ---
def start_screen():
    left_img = pygame.image.load("assets/shifted_left.png").convert_alpha()
    right_img = pygame.image.load("assets/shifted_right.png").convert_alpha()
    left_img = pygame.transform.scale(left_img,(80,80))
    right_img = pygame.transform.scale(right_img,(80,80))
    buttons = ["Play","Settings","Exit"]
    button_width = 200
    button_height = 50
    spacing = 20
    start_y = 300
    button_rects=[]
    for i,b in enumerate(buttons):
        rect = pygame.Rect((800-button_width)//2,start_y+i*(button_height+spacing),button_width,button_height)
        button_rects.append(rect)
    hover_index=-1
    time_accumulator=0.0
    running_start=True
    while running_start:
        dt=clock.tick(60)/1000.0
        time_accumulator+=dt
        mouse_pos=pygame.mouse.get_pos()
        hover_index=-1
        for i,rect in enumerate(button_rects):
            if rect.collidepoint(mouse_pos):
                hover_index=i
                break
        for event in pygame.event.get():
            if event.type==pygame.QUIT: pygame.quit(); exit()
            if event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
                if hover_index!=-1:
                    if buttons[hover_index]=="Play": running_start=False
                    elif buttons[hover_index]=="Exit": pygame.quit(); exit()
                    elif buttons[hover_index]=="Settings": show_settings_popup()
        screen.fill((54,89,74))
        title_font = pygame.font.Font("assets/PressStart2P-Regular.ttf",64)
        draw_text_with_outline(screen,"Six Seven",title_font,(255,255,255),(0,0,0),(400,150))
        font = pygame.font.Font("assets/PressStart2P-Regular.ttf",32)
        if hover_index!=-1:
            offset = math.sin(time_accumulator*3)*10
            rect=button_rects[hover_index]
            left_hand_pos=(rect.left-left_img.get_width()//2,rect.top-10+offset)
            right_hand_pos=(rect.right-right_img.get_width()//2,rect.top-10-offset)
            screen.blit(left_img,left_hand_pos)
            screen.blit(right_img,right_hand_pos)
        for i,rect in enumerate(button_rects):
            draw_text_with_outline(screen,buttons[i],font,(255,255,255),(0,0,0),rect.center)
        screen.blit(scanline_overlay, (0, 0))
        screen.blit(vignette_overlay, (0, 0))
        pygame.display.flip()

# --- Initialize game ---
start_screen()
left_hand, right_hand, active_hand = init_game()

# --- Game state variables ---
numbers=[]
score=0.0
multiplier=1.0
lives=3
combo_state=None
spawn_timer=0.0
immunity=False
immunity_timer=0
hand_tilt_angle=0.0
elapsed_time=0.0
game_over=False

# --- Main game loop ---
running=True
while running:
    dt=clock.tick(60)/1000.0
    elapsed_time+=dt
    for event in pygame.event.get():
        if event.type==pygame.QUIT: running=False
        if not game_over and event.type==pygame.KEYDOWN and event.key==pygame.K_SPACE:
            active_hand = right_hand if active_hand==left_hand else left_hand

    # --- Game logic ---
    if not game_over:
        score += dt*10*multiplier
        keys = pygame.key.get_pressed()
        target_tilt=0.0
        if keys[pygame.K_a]: active_hand.x-=5; target_tilt=MAX_TILT
        elif keys[pygame.K_d]: active_hand.x+=5; target_tilt=-MAX_TILT
        if hand_tilt_angle<target_tilt:
            hand_tilt_angle+=TILT_SPEED*dt
            if hand_tilt_angle>target_tilt: hand_tilt_angle=target_tilt
        elif hand_tilt_angle>target_tilt:
            hand_tilt_angle-=TILT_SPEED*dt
            if hand_tilt_angle<target_tilt: hand_tilt_angle=target_tilt
        if keys[pygame.K_w]: active_hand.y-=5
        if keys[pygame.K_s]: active_hand.y+=5
        for hand in [left_hand,right_hand]: hand.clamp_ip(pygame.Rect(0,0,800,600))

        # Spawn numbers
        spawn_timer+=dt
        if spawn_timer>=spawn_interval:
            spawn_timer-=spawn_interval
            value=str(random.choice(numbers_weighted))
            text_surface=font_large.render(value,True,(255,255,255))
            rect=text_surface.get_rect(center=(random.randint(30,770),0))
            numbers.append({"surf":text_surface,"rect":rect,"value":value})

        # Move numbers & collision
        for n in numbers[:]:
            speed=BASE_NUMBER_SPEED*(LIFE_SPEED_MULTIPLIER**(3-lives))
            n["rect"].y+=speed
            if n["rect"].colliderect(active_hand):
                caught_value=n["value"]
                numbers.remove(n)
                if not immunity:
                    if caught_value not in ["6","7"]:
                        lives=max(0,lives-1)
                        play_damage_animation()
                        immunity=True
                        immunity_timer=2
                        multiplier=max(1.0,multiplier-0.5)
                        combo_state=None
                    else:
                        if combo_state is None:
                            if caught_value=="6":
                                combo_state="6"
                                success_sound_6.play()
                            elif caught_value=="7":
                                multiplier=max(1.0,multiplier-0.5)
                        elif combo_state=="6":
                            if caught_value=="7":
                                multiplier+=0.1
                                success_sound_7.play()
                            combo_state=None
            elif n["rect"].top>600: numbers.remove(n)

        # Combo indicator
        if combo_state is None: combo_status=[False,False]
        elif combo_state=="6": combo_status=[True,False]

        # Immunity timer
        if immunity:
            immunity_timer-=dt
            if immunity_timer<=0: immunity=False

        if lives<=0: game_over=True

    # --- Drawing ---
    screen.fill((54, 89, 74))
    # Inactive hand
    if active_hand==left_hand:
        screen.blit(right_hand_inactive_img,right_hand_inactive_img.get_rect(center=right_hand.center))
    else:
        screen.blit(left_hand_inactive_img,left_hand_inactive_img.get_rect(center=left_hand.center))
    # Active hand with tilt
    tilt_angle=hand_tilt_angle
    if active_hand==left_hand:
        img=pygame.transform.rotate(left_hand_img,8+tilt_angle)
        rect=img.get_rect(center=left_hand.center)
    else:
        img=pygame.transform.rotate(right_hand_img,-8+tilt_angle)
        rect=img.get_rect(center=right_hand.center)
    if immunity:
        flash=int(elapsed_time*3)%2==0
        if flash: screen.blit(img,rect)
    else: screen.blit(img,rect)

    # Draw numbers
    for n in numbers: screen.blit(n["surf"],n["rect"])

    # Draw score
    score_text=font_small.render(f"SCORE: {int(score)}",True,(255,255,255))
    screen.blit(score_text,(20,20))

    # Multiplier label
    label_text=font_small.render("MULTIPLIER:",True,(255,255,255))
    number_text=font_small.render(f"x{multiplier:.1f}",True,(255,255,255))
    label_pos=(20,50)
    label_rect=label_text.get_rect(topleft=label_pos)
    number_pos=(label_rect.right+5,50)
    number_rect=number_text.get_rect(topleft=number_pos)
    screen.blit(label_text,label_pos)
    screen.blit(number_text,number_pos)

    # Fire animation if multiplier high
    if multiplier>1.5 and fire_frames:
        fire_frame_timer+=dt
        if fire_frame_timer>=FIRE_FRAME_DURATION:
            fire_frame_timer-=FIRE_FRAME_DURATION
            fire_frame_index=(fire_frame_index+1)%len(fire_frames)
        fire_img=fire_frames[fire_frame_index]
        target_width=int(number_rect.width*0.8)
        scale_ratio=target_width/fire_img.get_width()
        fire_img_scaled=pygame.transform.scale(fire_img,(int(fire_img.get_width()*scale_ratio),int(fire_img.get_height()*scale_ratio)))
        fire_img_scaled.set_alpha(180)
        fire_rect=fire_img_scaled.get_rect()
        fire_rect.bottom=number_rect.bottom
        fire_rect.centerx=number_rect.centerx
        screen.blit(fire_img_scaled,fire_rect)

    # Lives
    for i in range(3):
        x=750-i*50; y=20
        screen.blit(life_img if i<lives else life_img_lost,(x,y))

    # Combo display
    for i,number in enumerate(combo_numbers):
        color=full_color if combo_status[i] else grey_color
        surf=font_large.render(number,True,color)
        rect=surf.get_rect(topleft=combo_pos[i])
        screen.blit(surf,rect)

    # Game over overlay
    if game_over:
        overlay=pygame.Surface((800,600))
        overlay.set_alpha(int(255*0.73))
        overlay.fill((115,0,0))
        screen.blit(overlay,(0,0))
        title_text="Lodes iztrūkums"
        font_size=67
        max_width=760
        while True:
            font_go_big=pygame.font.Font("assets/PressStart2P-Regular.ttf",font_size)
            sur=font_go_big.render(title_text,True,(255,255,255))
            if sur.get_width()<=max_width: break
            font_size-=1
        screen.blit(font_go_big.render(title_text,True,(255,255,255)),font_go_big.render(title_text,True,(255,255,255)).get_rect(center=(400,150)))
        y_start=220
        for line in ["Tavu prasmju deficīta dēļ,","Tomam beidzās lodes"]:
            sub_surface=font_go_small.render(line,True,(255,255,255))
            screen.blit(sub_surface,sub_surface.get_rect(center=(400,y_start)))
            y_start+=sub_surface.get_height()+3
        result_surface=font_result_label.render("Tava gala rezultāts:",True,(255,255,255))
        score_surface=font_go_small.render(str(int(score)),True,(255,255,255))
        screen.blit(result_surface,result_surface.get_rect(center=(400,300)))
        screen.blit(score_surface,score_surface.get_rect(center=(400,350)))
        # Buttons
        button_width=140; button_height=50; button_spacing=40
        total_width=3*button_width+2*button_spacing
        start_x=(800-total_width)//2; y_pos=450
        exit_rect=pygame.Rect(start_x+button_width+button_spacing,y_pos,button_width,button_height)
        settings_rect=pygame.Rect(start_x+2*(button_width+button_spacing),y_pos,button_width,button_height)
        retry_rect=pygame.Rect(start_x,y_pos,button_width,button_height)
        pygame.draw.rect(screen,(255,255,255),exit_rect)
        pygame.draw.rect(screen,(255,255,255),settings_rect)
        pygame.draw.rect(screen,(255,255,255),retry_rect)

        screen.blit(font_small.render("Exit", True, (0, 0, 0)),
                    font_small.render("Exit", True, (0, 0, 0)).get_rect(center=exit_rect.center))
        screen.blit(font_small.render("Settings", True, (0, 0, 0)),
                    font_small.render("Settings", True, (0, 0, 0)).get_rect(center=settings_rect.center))
        screen.blit(font_small.render("Retry", True, (0, 0, 0)),
                    font_small.render("Retry", True, (0, 0, 0)).get_rect(center=retry_rect.center))
        mouse_pos=pygame.mouse.get_pos()
        if pygame.mouse.get_pressed()[0]:
            if retry_rect.collidepoint(mouse_pos): left_hand,right_hand,active_hand=init_game(); game_over=False
            elif exit_rect.collidepoint(mouse_pos): running=False
            elif settings_rect.collidepoint(mouse_pos): show_settings_popup()
    screen.blit(scanline_overlay, (0, 0))
    screen.blit(vignette_overlay, (0, 0))
    pygame.display.flip()

pygame.mixer.music.stop()
pygame.quit()
