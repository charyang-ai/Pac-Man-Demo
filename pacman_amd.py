import pygame
import random
import math
import os
import numpy as np
import wave

# Initialize Pygame
pygame.init()
pygame.mixer.init()
pygame.key.set_repeat(0) 

# Sound file paths
SOUND_DIR = "sounds"
SOUND_FILES = {
    'waka1': 'waka1.wav',
    'waka2': 'waka2.wav',
    'siren': 'siren.wav',
    'power_pellet': 'power_pellet.wav',
    'ghost_eaten': 'ghost_eaten.wav',
    'death': 'death.wav',
    'start': 'game_start.wav'

}

# Create sounds directory if not exists
if not os.path.exists(SOUND_DIR):
    os.makedirs(SOUND_DIR)

def generate_sound(frequency, duration=0.1, wave_type='square'):
    sample_rate = 44100
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    
    if wave_type == 'square':
        wave_data = 0.5 * np.sign(np.sin(2 * np.pi * frequency * t))
    else:  # sine
        wave_data = 0.5 * np.sin(2 * np.pi * frequency * t)
    
    # Convert to 16-bit integers
    wave_data = np.int16(wave_data * 32767)
    
    # Convert to stereo (duplicate mono to both channels)
    stereo_wave = np.column_stack((wave_data, wave_data))
    return stereo_wave

# Generate and save missing sounds
for name, params in [
    ('waka1', (440, 0.08, 'square')),
    ('waka2', (660, 0.08, 'square')),
    ('power_pellet', (1000, 0.8, 'sine')),
    ('ghost_eaten', (1600, 0.3, 'square')),
    ('death', (200, 1.5, 'sine'))
]:
    path = os.path.join(SOUND_DIR, SOUND_FILES[name])
    if not os.path.exists(path):
        wave_data = generate_sound(*params)
        
        # Save using wave module
        with wave.open(path, 'w') as wav_file:
            wav_file.setnchannels(2)       # Stereo
            wav_file.setsampwidth(2)       # 2 bytes per sample
            wav_file.setframerate(44100)
            wav_file.writeframes(wave_data.tobytes())


# Load sounds
sounds = {name: pygame.mixer.Sound(os.path.join(SOUND_DIR, path)) 
          for name, path in SOUND_FILES.items()}



# Game constants
CELL_SIZE = 20
COLS = 28
ROWS = 31
WIDTH = COLS * CELL_SIZE
HEIGHT = ROWS * CELL_SIZE + 80  # Extra space for UI
FPS = 10

# Colors
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
PINK = (255, 184, 255)
CYAN = (0, 255, 255)
ORANGE = (255, 184, 82)
BLUE = (33, 33, 255)
WHITE = (255, 255, 255)

# Ghost colors
GHOST_COLORS = [RED, PINK, CYAN, ORANGE]

# Maze layout
maze = [
    "############################",
    "#O...........##...........O#",
    "#.####.#####.##.#####.####.#",
    "#.####.#####.##.#####.####.#",
    "#.####.#####.##.#####.####.#",
    "#..........................#",
    "#.####.##.########.##.####.#",
    "#.####.##.########.##.####.#",
    "#......##....##....##......#",
    "######.##### ## #####.######",
    "######.##### ## #####.######",
    "######.##          ##.######",
    "######.## ###--### ##.######",
    "######.## #      # ##.######",
    "          #      #          ",
    "######.## #      # ##.######",
    "######.## ######## ##.######",
    "######.##          ##.######",
    "######.## ######## ##.######",
    "######.## ######## ##.######",
    "#O...........##...........O#",
    "#.####.#####.##.#####.####.#",
    "#.####.#####.##.#####.####.#",
    "#...##................##...#",
    "### ##.## ######## ##.## ###",
    "### ##.## ######## ##.## ###",
    "#......##....##....##......#",
    "#.##########.##.##########.#",
    "#.##########.##.##########.#",
    "#..........................#",
    "############################"
]

class PacMan:
    def __init__(self):
        self.x = 14
        self.y = 23
        self.direction = (0, 0)
        self.animation_frame = 0
        self.animation_speed = 0.4
        self.animation_counter = 0
        self.lives = 4
        self.mouth_phases = [
            (45, 315), (30, 330), (15, 345),
            (0, 360), (15, 345), (30, 330)
        ]
        self.waka_toggle = False

    def move(self):
        new_x = self.x + self.direction[0]
        new_y = self.y + self.direction[1]

        if new_y == 14:
            if new_x < 0 and maze[14][COLS-1] != '#':
                self.x = COLS-1
                return
            if new_x >= COLS and maze[14][0] != '#':
                self.x = 0
                return

        if 0 <= new_x < COLS and 0 <= new_y < ROWS:
            if maze[new_y][new_x] != '#':
                self.x, self.y = new_x, new_y

    def update_animation(self):
        if self.direction != (0, 0):
            self.animation_counter += 1
            if self.animation_counter >= self.animation_speed * FPS:
                self.animation_frame = (self.animation_frame + 1) % len(self.mouth_phases)
                self.animation_counter = 0

    def get_mouth_angles(self):
        base = self.mouth_phases[self.animation_frame]
        if self.direction == (1,0): return base
        if self.direction == (-1,0): return (180+base[0], 180+base[1])
        if self.direction == (0,1): return (90+base[0], 90+base[1])
        if self.direction == (0,-1): return (270+base[0], 270+base[1])
        return (45, 315)

class Ghost:
    def __init__(self, x, y, color):
        self.x, self.y = x, y
        self.color = self.original_color = color
        self.directions = [(0,1),(0,-1),(1,0),(-1,0)]
        self.direction = random.choice(self.directions)

    def move(self, frightened=False):
        new_x = self.x + self.direction[0]
        new_y = self.y + self.direction[1]

        if new_y == 14:
            if new_x < 0 and maze[14][COLS-1] != '#':
                self.x = COLS-1
                return
            if new_x >= COLS and maze[14][0] != '#':
                self.x = 0
                return

        if 0 <= new_x < COLS and 0 <= new_y < ROWS and maze[new_y][new_x] != '#':
            self.x, self.y = new_x, new_y
        else:
            valid = []
            for dx, dy in self.directions:
                nx, ny = self.x+dx, self.y+dy
                if ny == 14 and (nx<0 or nx>=COLS):
                    valid.append((dx, dy))
                elif 0<=nx<COLS and 0<=ny<ROWS and maze[ny][nx]!='#':
                    valid.append((dx, dy))
            if valid:
                if frightened:
                    reverse_dir = (-self.direction[0], -self.direction[1])
                    if reverse_dir in valid:
                        self.direction = reverse_dir
                    else:
                        self.direction = random.choice(valid)
                else:
                    self.direction = random.choice(valid)

def draw_maze(screen):
    for y in range(ROWS):
        for x in range(COLS):
            if maze[y][x] == '#':
                pygame.draw.rect(screen, BLUE, (x*CELL_SIZE, y*CELL_SIZE+40, CELL_SIZE, CELL_SIZE))
            elif maze[y][x] == '.':
                pygame.draw.circle(screen, WHITE, (x*CELL_SIZE+10, y*CELL_SIZE+40+10), 2)
            elif maze[y][x] == 'O':
                pygame.draw.circle(screen, WHITE, (x*CELL_SIZE+10, y*CELL_SIZE+40+10), 6)

def draw_pacman(screen, pacman):
    cx = pacman.x*CELL_SIZE + CELL_SIZE//2
    cy = pacman.y*CELL_SIZE + 40 + CELL_SIZE//2
    r = CELL_SIZE//2
    start, end = pacman.get_mouth_angles()
    start %= 360
    end %= 360
    
    pygame.draw.circle(screen, YELLOW, (cx, cy), r)
    if start != end:
        points = [(cx, cy),
                  (cx + r*math.cos(math.radians(start)), cy + r*math.sin(math.radians(start))),
                  (cx + r*math.cos(math.radians(end)), cy + r*math.sin(math.radians(end)))]
        pygame.draw.polygon(screen, BLACK, points)
    
    if pacman.direction != (0,0):
        eye_angle = (start + end)/2
        ex = cx + (r//2)*math.cos(math.radians(eye_angle))
        ey = cy + (r//2)*math.sin(math.radians(eye_angle))
        pygame.draw.circle(screen, BLACK, (ex, ey), r//4)

def draw_ghost(screen, x, y, color, direction):
    body = pygame.Rect(x*CELL_SIZE, y*CELL_SIZE+40, CELL_SIZE, CELL_SIZE)
    pygame.draw.rect(screen, color, body, border_radius=10)
    
    points = []
    for i in range(7):
        px = x*CELL_SIZE + (i*CELL_SIZE)//6
        py = y*CELL_SIZE+40 + CELL_SIZE - (CELL_SIZE//6 if i%2 else 0)
        points.append((px, py))
    points += [(x*CELL_SIZE+CELL_SIZE, y*CELL_SIZE+40+CELL_SIZE),
               (x*CELL_SIZE, y*CELL_SIZE+40+CELL_SIZE)]
    pygame.draw.polygon(screen, color, points)
    
    eye_pos = []
    pupil_offset = (0, 0)
    if direction == (1,0):
        eye_pos = [(x*CELL_SIZE+7, y*CELL_SIZE+47),
                   (x*CELL_SIZE+13, y*CELL_SIZE+47)]
        pupil_offset = (3, 0)
    elif direction == (-1,0):
        eye_pos = [(x*CELL_SIZE+7, y*CELL_SIZE+47),
                   (x*CELL_SIZE+13, y*CELL_SIZE+47)]
        pupil_offset = (-3, 0)
    elif direction == (0,-1):
        eye_pos = [(x*CELL_SIZE+7, y*CELL_SIZE+43),
                   (x*CELL_SIZE+13, y*CELL_SIZE+43)]
        pupil_offset = (0, -3)
    else:
        eye_pos = [(x*CELL_SIZE+7, y*CELL_SIZE+47),
                   (x*CELL_SIZE+13, y*CELL_SIZE+47)]
        pupil_offset = (0, 3)

    for ex, ey in eye_pos:
        pygame.draw.circle(screen, WHITE, (ex, ey), 3)
        pygame.draw.circle(screen, BLACK, (ex+pupil_offset[0], ey+pupil_offset[1]), 2)

def draw_lives(screen, lives):
    for i in range(lives):
        x = 20 + i * 40
        y = HEIGHT - 30
        pygame.draw.circle(screen, YELLOW, (x, y), 12)
        start_angle = math.radians(45)
        end_angle = math.radians(315)
        points = [
            (x, y),
            (x + 12 * math.cos(start_angle), y + 12 * math.sin(start_angle)),
            (x + 12 * math.cos(end_angle), y + 12 * math.sin(end_angle))
        ]
        pygame.draw.polygon(screen, BLACK, points)

class Game:
    def __init__(self):
        self.siren_channel = pygame.mixer.Channel(0)
        self.effect_channel = pygame.mixer.Channel(1)
        self.waka_channel = pygame.mixer.Channel(2)
        self.waka_toggle = pygame.mixer.Channel(3)
        
    def play_start(self):
        sounds['start'].play()
        
    def play_waka(self):
        if not self.waka_channel.get_busy():
            sound = sounds['waka1'] if self.waka_toggle else sounds['waka2']
            self.waka_toggle = not self.waka_toggle
            self.waka_channel.play(sound)

    def play_siren(self):
        if not self.siren_channel.get_busy():
            self.siren_channel.play(sounds['siren'], loops=-1)        
            
    def stop_siren(self):
        self.siren_channel.stop()
        
    def play_power_pellet(self):
        self.effect_channel.play(sounds['power_pellet'])
        
    def play_ghost_eaten(self):
        self.effect_channel.play(sounds['ghost_eaten'])
        
    def play_death(self):
        self.siren_channel.stop()
        self.waka_channel.stop()
        self.effect_channel.play(sounds['death'])


def main():

    game = Game()
    game.play_start()


    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)
    
    pacman = PacMan()
    ghosts = [Ghost(13,9,RED), Ghost(14,11,PINK),
              Ghost(13,9,CYAN), Ghost(14,11,ORANGE)]
    
    dots = sum(row.count('.') for row in maze)
    super_pellets = sum(row.count('O') for row in maze)
    score = 0
    frightened_mode = False
    frightened_timer = 0
    running = True
    game_over = False
    win = False

    sounds['start'].play()

    while running:
        screen.fill(BLACK)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP: pacman.direction = (0,-1)
                elif event.key == pygame.K_DOWN: pacman.direction = (0,1)
                elif event.key == pygame.K_LEFT: pacman.direction = (-1,0)
                elif event.key == pygame.K_RIGHT: pacman.direction = (1,0)
        
        pacman.update_animation()
        pacman.move()
        
        cell = maze[pacman.y][pacman.x]
        if cell == '.':
            maze[pacman.y] = maze[pacman.y][:pacman.x] + ' ' + maze[pacman.y][pacman.x+1:]
            dots -= 1
            score += 10
            #sound
            game.play_waka()
            if not frightened_mode:
                game.play_siren()

        elif cell == 'O':
            maze[pacman.y] = maze[pacman.y][:pacman.x] + ' ' + maze[pacman.y][pacman.x+1:]
            super_pellets -= 1
            score += 50
            frightened_mode = True
            frightened_timer = pygame.time.get_ticks()
            for g in ghosts:
                g.color = BLUE
                reverse_dir = (-g.direction[0], -g.direction[1])
                if (0 <= g.x + reverse_dir[0] < COLS and
                    0 <= g.y + reverse_dir[1] < ROWS and
                    maze[g.y + reverse_dir[1]][g.x + reverse_dir[0]] != '#'):
                    g.direction = reverse_dir
            game.play_power_pellet()
            game.stop_siren()

        if frightened_mode and pygame.time.get_ticks() - frightened_timer > 10000:
            frightened_mode = False
            for ghost in ghosts:
                ghost.color = ghost.original_color
        
        for ghost in ghosts:
            ghost.move(frightened_mode)
        
        collision = False
        if len(ghosts)!=0:
            for ghost in ghosts:
                if (pacman.x, pacman.y) == (ghost.x, ghost.y):
                    if frightened_mode:
                        score += 200
                        ghosts.remove(ghost)
                        # ghost.x = 13 if ghost.x==14 else 14
                        # ghost.y = 14 if ghost.y==15 else 15
                        # Ghost eaten
                        game.play_ghost_eaten()

                    else:
                        collision = True
        else:
            win=True
            game_over=True
            # running=False

        if collision:
            pacman.lives -= 1
            if pacman.lives <= 0:
                game_over = True
                win=False
            else:
                pacman.x, pacman.y = 14, 23
                pacman.direction = (0,0)
                for i, ghost in enumerate(ghosts):
                    ghost.x = [13,14,13,14][i]
                    ghost.y = [9,9,11,11][i]
                    ghost.direction = random.choice(ghost.directions)
            #sound
            game.play_death()
            pygame.time.wait(2000)  # Pause for death sound

        if dots == 0 and super_pellets == 0:
            running = False
        


        draw_maze(screen)
        draw_pacman(screen, pacman)
        for ghost in ghosts:
            draw_ghost(screen, ghost.x, ghost.y, ghost.color, ghost.direction)
        
        draw_lives(screen, pacman.lives)
        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (WIDTH//2 - score_text.get_width()//2, 10))
        
        if game_over:
            text = "You Win!" if win else "Game Over!"
            font = pygame.font.SysFont(None, 72)
            text_surface = font.render(text, True, YELLOW)
            text_rect = text_surface.get_rect(center=(WIDTH//2, HEIGHT//2))
            screen.blit(text_surface, text_rect)

        if game_over and win:

            pygame.time.wait(2000) 
            # running=False

        if game_over and not win:

            pygame.time.wait(2000) 
            running=False

        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()

if __name__ == "__main__":
    main()