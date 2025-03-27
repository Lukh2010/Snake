import os
os.environ['SDL_VIDEODRIVER'] = 'x11'  # Use X11 driver instead of Wayland
os.environ['PYGAME_DETECT_AVX2'] = '1'
os.environ['GDK_BACKEND'] = 'x11'  # Force GTK to use X11 backend
import pygame
import random
import time
import heapq
import json
import pygame.mixer

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# --- Constants ---
# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
GRAY = (128, 128, 128)
CYAN = (0, 255, 255)
SNAKE_COLORS = {
    'GREEN': (0, 255, 0),
    'BLUE': (0, 0, 255),
    'YELLOW': (255, 255, 0),
    'PURPLE': (128, 0, 128),
    'ORANGE': (255, 165, 0),
    'CYAN': (0, 255, 255),
    'PINK': (255, 192, 203),
    'RED': (255, 0, 0),
}
# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
# Grid dimensions
GRID_SIZE = 20  # Define GRID_SIZE here
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // GRID_SIZE
SNAKE_INITIAL_LENGTH = 3

# Dynamically detect the directory of the script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, 'Assets')

# Load images
try:
    apple_img = pygame.image.load(os.path.join(ASSETS_DIR, 'apple.png'))
    apple_img = pygame.transform.scale(apple_img, (GRID_SIZE, GRID_SIZE))
except (pygame.error, FileNotFoundError):
    apple_img = None  # Fallback to a red block if the image is not found

GAME_STATE_MENU = 0
GAME_STATE_PLAYING = 1
GAME_STATE_PAUSED = 2
GAME_STATE_GAME_OVER = 3
GAME_STATE_GRAPHICS = 4
GAME_STATE_SHOP = 5  # Add GAME_STATE_SHOP
GAME_STATE_CUSTOM_LEVELS = 6  # Add GAME_STATE_CUSTOM_LEVELS
DIFFICULTY_EASY = 10
DIFFICULTY_MEDIUM = 14
DIFFICULTY_HARD = 17
DIFFICULTY_SPEED = 20
font = pygame.font.Font(None, 36)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Snake")
clock = pygame.time.Clock()
# Snake variables
snake = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]
snake_direction = (1, 0)  # Initial direction: right
snake_length = SNAKE_INITIAL_LENGTH
# AI variable
ai_enabled = False
# Global variable to hold multiple food positions
foods = []
current_snake_color = SNAKE_COLORS['GREEN']  # Default color
# Global variable to hold wall wrapping state
wall_wrapping_enabled = True
# Global variable to hold obstacles
obstacles = []
# Global variable to hold power-ups
power_ups = []
# Global variable to hold high score
high_score = 0
# Global variable to hold power-up mode state
power_up_mode_enabled = False
# Global variable to hold obstacle mode state
obstacle_mode_enabled = False
# Difficulty setting
difficulty = DIFFICULTY_EASY # Initialize difficulty
# At the beginning of your script or in an appropriate initialization section
game_state = 0  # Or any other appropriate initial value

# Initialize global game state variables
score = 0  # Add missing score variable
high_score = 0
power_up_mode_enabled = False
obstacle_mode_enabled = False
invincible = False  # Add invincible variable initialization
difficulty = DIFFICULTY_EASY
game_state = GAME_STATE_MENU  # Start in menu state

# Global variable to hold multiplayer state
multiplayer_enabled = False  # Initialize multiplayer_enabled

# Global variable to hold survival mode state
survival_mode_enabled = False  # Initialize survival_mode_enabled

MUSIC_THEMES = {
    'theme1': os.path.join(ASSETS_DIR, 'theme1.wav'),
    'theme2': os.path.join(ASSETS_DIR, 'theme2.wav'),
    'theme3': os.path.join(ASSETS_DIR, 'theme3.wav')
}

SOUND_EFFECTS = {
    'eat': pygame.mixer.Sound(os.path.join(ASSETS_DIR, 'eat.wav')),
    'die': pygame.mixer.Sound(os.path.join(ASSETS_DIR, 'die.wav'))
}

# Load settings
try:
    with open('settings.json', 'r') as f:
        settings = json.load(f)
    current_snake_color = SNAKE_COLORS[settings['snake_color']]
    current_theme = settings['music_theme']
    volume = settings['volume']
except:
    settings = {
        "snake_color": "GREEN",
        "music_theme": "theme1",
        "volume": 0.5
    }
    current_snake_color = SNAKE_COLORS['GREEN']
    current_theme = 'theme1'
    volume = 0.5
    with open('settings.json', 'w') as f:
        json.dump(settings, f, indent=4)

# Set volume for all sounds
pygame.mixer.music.set_volume(volume)
for sound in SOUND_EFFECTS.values():
    sound.set_volume(volume)

def save_settings():
    """Save current settings to file."""
    for color_name, color_value in SNAKE_COLORS.items():
        if color_value == current_snake_color:
            settings['snake_color'] = color_name
            break
    settings['music_theme'] = current_theme
    settings['volume'] = volume
    with open('settings.json', 'w') as f:
        json.dump(settings, f, indent=4)

def play_theme_music():
    """Play the selected theme music."""
    pygame.mixer.music.load(MUSIC_THEMES[current_theme])
    pygame.mixer.music.play(-1)  # -1 means loop indefinitely

def place_food():
    """Places 3 pieces of food at random locations on the grid, avoiding the snake and obstacles."""
    global foods
    attempts = 0
    max_attempts = 100  # Prevent infinite loop
    
    while len(foods) < 3 and attempts < max_attempts:
        food = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
        if (food not in snake and food not in foods and 
            food not in obstacles and food not in power_ups):
            foods.append(food)
        attempts += 1
    
    # If we couldn't place all food, clear some space
    if len(foods) < 3:
        for obstacle in obstacles[:]:
            if len(foods) >= 3:
                break
            obstacles.remove(obstacle)
            food = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
            if food not in snake and food not in foods and food not in obstacles and food not in power_ups:
                foods.append(food)

def place_power_up():
    """Places a power-up at a random location on the grid, avoiding the snake, food, and obstacles."""
    global power_ups
    while len(power_ups) < 1:  # Ensure 1 power-up is placed
        power_up = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
        if power_up not in snake and power_up not in foods and power_up not in obstacles:
            power_ups.append(power_up)
            break

def place_obstacles():
    """Places obstacles at random locations on the grid, avoiding the snake and food."""
    global obstacles
    if not foods:  # Ensure food list is initialized
        place_food()
        if not foods:  # If food placement fails, exit
            return
    
    obstacles = []
    attempts = 0
    max_attempts = 50  # Prevent infinite loop
    
    for _ in range(5):  # Place 5 initial obstacles
        while attempts < max_attempts:
            attempts += 1
            obstacle = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
            if (obstacle not in snake and 
                obstacle not in foods and 
                obstacle not in obstacles):
                obstacles.append(obstacle)
                break
        else:
            # If obstacle placement fails, exit
            return

def draw_grid():
    """Draws the grid on the screen."""
    try:
        for x in range(0, SCREEN_WIDTH, GRID_SIZE):
            pygame.draw.line(screen, GRAY, (x, 0), (x, SCREEN_HEIGHT))
        for y in range(0, SCREEN_HEIGHT, GRID_SIZE):
            pygame.draw.line(screen, GRAY, (0, y), (SCREEN_WIDTH, y))
    except pygame.error:
        pass  # Ignore drawing errors if screen not initialized

def draw_snake(snake_list, color):
    """Draws a snake on the screen."""
    try:
        for segment in snake_list:
            pygame.draw.rect(screen, color, 
                           (segment[0] * GRID_SIZE, 
                            segment[1] * GRID_SIZE, 
                            GRID_SIZE, GRID_SIZE))
    except pygame.error:
        pass  # Ignore drawing errors if screen not initialized

def draw_food():
    """Draws the food on the screen."""
    try:
        for food_pos in foods:
            if apple_img:
                screen.blit(apple_img, (food_pos[0] * GRID_SIZE, food_pos[1] * GRID_SIZE))
            else:
                pygame.draw.rect(screen, RED, (food_pos[0] * GRID_SIZE, food_pos[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE))
    except pygame.error:
        pass  # Ignore drawing errors if screen not initialized

def move_snake(snake_list, direction, grow=False):
    """Moves the snake in the given direction."""
    try:
        head = snake_list[0]
        new_head = (head[0] + direction[0], head[1] + direction[1])
        
        # When invincible, only apply wall wrapping if enabled and not hitting a wall
        if invincible:
            if wall_wrapping_enabled:
                new_head = (new_head[0] % GRID_WIDTH, new_head[1] % GRID_HEIGHT)
            else:
                # Don't move if hitting a wall while invincible
                if (new_head[0] < 0 or new_head[0] >= GRID_WIDTH or 
                    new_head[1] < 0 or new_head[1] >= GRID_HEIGHT):
                    return snake_list
        else:
            if wall_wrapping_enabled:
                new_head = (new_head[0] % GRID_WIDTH, new_head[1] % GRID_HEIGHT)
        
        snake_list.insert(0, new_head)  # Add the new head
        if not grow:
            snake_list.pop()  # Remove the last segment if not growing
        return snake_list
    except Exception as e:
        return snake_list

def check_collision(snake_list):
    """Checks if the snake has collided with itself, the borders, or obstacles."""
    try:
        head = snake_list[0]
        
        if invincible:
            # Only check wall collision when invincible
            if not wall_wrapping_enabled:
                if (head[0] < 0 or head[0] >= GRID_WIDTH or 
                    head[1] < 0 or head[1] >= GRID_HEIGHT):
                    return True
            return False  # Skip all other collision checks when invincible
        
        # Normal collision checks when not invincible
        if head in snake_list[1:]:
            return True
            
        if not wall_wrapping_enabled:
            if (head[0] < 0 or head[0] >= GRID_WIDTH or 
                head[1] < 0 or head[1] >= GRID_HEIGHT):
                return True
                
        if head in obstacles:
            return True
            
        return False
    except Exception as e:
        return True

def display_message(message, color, x, y):
    """Displays a message on the screen."""
    text = font.render(message, True, color)
    text_rect = text.get_rect(center=(x, y))
    screen.blit(text, text_rect)  # Corrected line: blit the text, not the rect

def handle_input(event):
    """Handles user input for the game."""
    global snake_direction, player_2_direction, game_state, wall_wrapping_enabled, power_up_mode_enabled, obstacle_mode_enabled, invincible, ai_enabled, survival_mode_enabled
    if event.type == pygame.KEYDOWN:
        # Player 1 controls (arrow keys)
        if event.key == pygame.K_UP and snake_direction != (0, 1):
            snake_direction = (0, -1)
        elif event.key == pygame.K_DOWN and snake_direction != (0, -1):
            snake_direction = (0, 1)
        elif event.key == pygame.K_LEFT and snake_direction != (1, 0):
            snake_direction = (-1, 0)
        elif event.key == pygame.K_RIGHT and snake_direction != (-1, 0):
            snake_direction = (1, 0)
        
        # Player 2 controls (WASD)
        if multiplayer_enabled and not ai_enabled:
            if event.key == pygame.K_w and player_2_direction != (0, 1):
                player_2_direction = (0, -1)
            elif event.key == pygame.K_s and player_2_direction != (0, -1):
                player_2_direction = (0, 1)
            elif event.key == pygame.K_a and player_2_direction != (1, 0):
                player_2_direction = (-1, 0)
            elif event.key == pygame.K_d and player_2_direction != (-1, 0):
                player_2_direction = (1, 0)
        
        # Other controls
        if event.key == pygame.K_ESCAPE:
            game_state = GAME_STATE_PAUSED
        elif event.key == pygame.K_w:  # 'w' key toggles wall wrapping
            wall_wrapping_enabled = not wall_wrapping_enabled
        elif event.key == pygame.K_p:  # 'p' key toggles power-up mode
            power_up_mode_enabled = not power_up_mode_enabled
        elif event.key == pygame.K_o:  # 'o' key toggles obstacle mode
            obstacle_mode_enabled = not obstacle_mode_enabled
        # Hidden trick
        elif event.key == pygame.K_F8 and pygame.key.get_pressed()[pygame.K_1]:
            invincible = True

def calculate_distance(x1, y1, food_pos):
    """Calculates Manhattan distance to the food (accounts for grid wrapping)."""
    dx = abs(x1 - food_pos[0])
    dy = abs(y1 - food_pos[1])
    dx = min(dx, GRID_WIDTH - dx)
    dy = min(dy, GRID_HEIGHT - dy)
    return dx + dy

def is_safe(snake_list, head, direction):
    """Checks if the next move in the given direction will result in a collision."""
    next_head = (head[0] + direction[0], head[1] + direction[1])
    
    if wall_wrapping_enabled:
        next_head = (next_head[0] % GRID_WIDTH, next_head[1] % GRID_HEIGHT)
    else:
        if (next_head[0] < 0 or next_head[0] >= GRID_WIDTH or
            next_head[1] < 0 or next_head[1] >= GRID_HEIGHT):
            return False

    return next_head not in snake_list[1:]

def check_food_collision(snake_head):
    """Checks if the snake's head has collided with any food."""
    global score, snake_length, foods, obstacles
    for food_pos in foods[:]:
        if snake_head == food_pos:
            SOUND_EFFECTS['eat'].play()
            score += 1  # Increase score by 1 for each apple
            snake_length += 1
            foods.remove(food_pos)  # Remove the eaten food from the list
            place_new_food()  # Place new food to replace the eaten one
            if obstacle_mode_enabled:
                add_random_obstacle()  # Add a random obstacle
            return True  # Indicate that food was eaten
    return False

def place_new_food():
    """Places a new piece of food at a random location on the grid, avoiding the snake and existing foods."""
    global foods
    attempts = 0
    max_attempts = 100  # Prevent infinite loop
    
    while attempts < max_attempts:
        food = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
        if (food not in snake and food not in foods and 
            food not in obstacles and food not in power_ups):
            foods.append(food)
            break
        attempts += 1

def reset_game():
    """Resets the game to its initial state."""
    global snake, snake_direction, snake_length, score, foods, game_state, obstacles, power_ups, difficulty, invincible, player_2_snake, player_2_direction, player_2_length
    snake = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]
    snake_direction = (1, 0)
    snake_length = SNAKE_INITIAL_LENGTH
    score = 0
    foods = []
    obstacles = []
    power_ups = []
    invincible = False

    if multiplayer_enabled:
        # Spawn Player 2 (or AI) a bit away from the middle
        player_2_snake = [(GRID_WIDTH // 2 - 5, GRID_HEIGHT // 2 + 3)]
        player_2_direction = (-1, 0)  # Initial direction: left
        player_2_length = SNAKE_INITIAL_LENGTH

    place_food()  # Always place food first
    if obstacle_mode_enabled:
        place_obstacles()  # Then place obstacles if enabled
    if power_up_mode_enabled:
        place_power_up()
    game_state = GAME_STATE_MENU  # Return to menu after reset

def astar(snake_list, start, end):
    """A* pathfinding algorithm."""
    grid = create_grid(snake_list)
    start_node = (start[0], start[1])
    end_node = (end[0], end[1])

    open_list = [(0, start_node, [])]  # (f_score, node, path)
    closed_set = set()

    while open_list:
        f_score, current_node, path = heapq.heappop(open_list)

        if current_node == end_node:
            return path + [current_node]

        if current_node in closed_set:
            continue
        closed_set.add(current_node)

        for neighbor in get_neighbors(current_node, grid):
            if grid[neighbor[1]][neighbor[0]] == 1:  # Obstacle
                continue
            new_path = path + [current_node]
            g_score = len(new_path)
            h_score = calculate_distance(neighbor[0], neighbor[1], end_node)  # Manhattan distance
            f_score = g_score + h_score

            heapq.heappush(open_list, (f_score, neighbor, new_path))
    return None  # No path found

def create_grid(snake_list):
    """Creates a grid representation of the game board."""
    grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
    
    # Mark snake as obstacles
    for segment in snake_list:
        if 0 <= segment[0] < GRID_WIDTH and 0 <= segment[1] < GRID_HEIGHT:
            grid[segment[1]][segment[0]] = 1
    
    # Mark game obstacles as obstacles
    for obstacle in obstacles:
        if 0 <= obstacle[0] < GRID_WIDTH and 0 <= obstacle[1] < GRID_HEIGHT:
            grid[obstacle[1]][obstacle[0]] = 1
    
    # Add buffer zone around obstacles for safer pathfinding
    buffer_grid = [row[:] for row in grid]
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            if grid[y][x] == 1:
                for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                        buffer_grid[ny][nx] = 0.5  # Mark cells next to obstacles as risky
    
    return buffer_grid

def get_neighbors(node, grid):
    """Gets valid neighbors for a given node."""
    x, y = node
    neighbors = []
    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
        new_x, new_y = x + dx, y + dy
        if 0 <= new_x < GRID_WIDTH and 0 <= new_y < GRID_HEIGHT:
            neighbors.append((new_x, new_y))
    return neighbors

def flood_fill(grid, start_node):
    """Performs a flood fill to count reachable cells."""
    x, y = start_node
    if x < 0 or x >= GRID_WIDTH or y < 0 or y >= GRID_HEIGHT or grid[y][x] == 1:
        return 0

    q = [(x, y)]
    grid[y][x] = 1  # Mark as visited
    count = 1

    while q:
        cx, cy = q.pop(0)
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT and grid[ny][nx] == 0:
                grid[ny][nx] = 1  # Mark as visited
                q.append((nx, ny))
                count += 1
    return count

def is_path_safe(snake_list, path):
    """Checks if a given path is safe for the snake."""
    future_snake = snake_list[:]
    for move in path:
        future_snake.insert(0, move)
        future_snake.pop()
        if future_snake[0] in future_snake[1:]:
            return False
    return True

def ai_move(snake_list, foods):
    """Advanced AI algorithm with improved pathfinding and collision avoidance."""
    head = snake_list[0]
    
    if not foods:
        return find_safe_direction(snake_list)

    best_path = None
    min_distance = float('inf')
    target_food = None

    # Create grid with obstacles and risk zones
    grid = create_grid(snake_list)

    for food in foods:
        path = astar(snake_list, head, food)
        if path and len(path) > 1:
            # Calculate path risk (accounting for nearby obstacles)
            path_risk = 0
            for pos in path:
                if grid[pos[1]][pos[0]] == 0.5:  # Cell next to obstacle
                    path_risk += 1
            
            # Calculate effective distance (including risk penalty)
            distance = len(path) + path_risk * 2

            if distance < min_distance:
                temp_snake = snake_list[:]
                safe = True
                for pos in path[1:]:
                    temp_snake.insert(0, pos)
                    temp_snake.pop()
                    if temp_snake[0] in temp_snake[1:] or temp_snake[0] in obstacles:
                        safe = False
                        break
                
                if safe:
                    min_distance = distance
                    best_path = path
                    target_food = food

    # If we have a safe path to food, use it
    if best_path and len(best_path) > 1:
        next_pos = best_path[1]
        move = (next_pos[0] - head[0], next_pos[1] - head[1])
        return move

    # No safe path to food, find safest direction
    return find_safe_direction(snake_list)

def find_safe_direction(snake_list):
    """Helper function to find a safe direction when no food is available."""
    head = snake_list[0]
    possible_moves = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    best_move = None
    max_space = 0

    for move in possible_moves:
        if is_safe(snake_list, head, move):
            new_head = (head[0] + move[0], head[1] + move[1])
            temp_snake = [new_head] + snake_list[:-1]
            temp_grid = create_grid(temp_snake)
            space = flood_fill(temp_grid.copy(), new_head)
            
            if space > max_space:
                max_space = space
                best_move = move
    return best_move if best_move else snake_direction

def draw_menu():
    """Draws the menu screen with all options."""
    title_font = pygame.font.Font(None, 72)
    text = title_font.render("Snake", True, WHITE)
    text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 50))
    screen.blit(text, text_rect)
    
    # Difficulty buttons
    button_width = 150
    button_height = 70
    x_start = SCREEN_WIDTH // 2 - (2 * button_width + 10)
    y_pos = 150
    spacing = button_width + 10

    pygame.draw.rect(screen, WHITE, (x_start, y_pos, button_width, button_height), 2)
    display_message("Easy", WHITE, x_start + button_width // 2, y_pos + button_height // 2)
    x_start += spacing
    pygame.draw.rect(screen, WHITE, (x_start, y_pos, button_width, button_height), 2)
    display_message("Medium", WHITE, x_start + button_width // 2, y_pos + button_height // 2)
    x_start += spacing
    pygame.draw.rect(screen, WHITE, (x_start, y_pos, button_width, button_height), 2)
    display_message("Hard", WHITE, x_start + button_width // 2, y_pos + button_height // 2)
    x_start += spacing
    pygame.draw.rect(screen, WHITE, (x_start, y_pos, button_width, button_height), 2)
    display_message("Speed", WHITE, x_start + button_width // 2, y_pos + button_height // 2)
    
    # Bottom buttons
    button_width = 180
    button_height = 60
    bottom_y = 350
    power_up_y = 420
    settings_y = 490

    # AI button
    ai_x = SCREEN_WIDTH // 6 - button_width // 2
    pygame.draw.rect(screen, WHITE, (ai_x, bottom_y, button_width, button_height), 2)
    ai_status = "AI: " + ("ON" if ai_enabled else "OFF")
    display_message(ai_status, WHITE, ai_x + button_width // 2, bottom_y + button_height // 2)
    
    # Power-Up Mode button
    power_up_x = SCREEN_WIDTH // 6 - button_width // 2
    pygame.draw.rect(screen, WHITE, (power_up_x, power_up_y, button_width, button_height), 2)
    power_up_status = "Power-Up: " + ("ON" if power_up_mode_enabled else "OFF")
    display_message(power_up_status, WHITE, power_up_x + button_width // 2, power_up_y + button_height // 2)
    
    # Wall button
    wall_x = SCREEN_WIDTH // 2 - button_width // 2
    pygame.draw.rect(screen, WHITE, (wall_x, bottom_y, button_width, button_height), 2)
    wall_status = "Wall: " + ("ON" if wall_wrapping_enabled else "OFF")
    display_message(wall_status, WHITE, wall_x + button_width // 2, bottom_y + button_height // 2)
    
    # Multiplayer button
    multiplayer_x = SCREEN_WIDTH // 2 - button_width // 2
    pygame.draw.rect(screen, WHITE, (multiplayer_x, power_up_y, button_width, button_height), 2)
    multiplayer_status = "Multiplayer: " + ("ON" if multiplayer_enabled else "OFF")
    multiplayer_font = pygame.font.Font(None, 28)  # Smaller font for better fit
    multiplayer_text = multiplayer_font.render(multiplayer_status, True, WHITE)
    multiplayer_text_rect = multiplayer_text.get_rect(center=(multiplayer_x + button_width // 2, power_up_y + button_height // 2))
    screen.blit(multiplayer_text, multiplayer_text_rect)
    
    # Obstacle Mode button
    obstacle_x = 5 * SCREEN_WIDTH // 6 - button_width // 2
    pygame.draw.rect(screen, WHITE, (obstacle_x, bottom_y, button_width, button_height), 2)
    obstacle_status = "Obstacle: " + ("ON" if obstacle_mode_enabled else "OFF")
    display_message(obstacle_status, WHITE, obstacle_x + button_width // 2, bottom_y + button_height // 2)
    
    # Settings button
    settings_x = 5 * SCREEN_WIDTH // 6 - button_width // 2
    pygame.draw.rect(screen, WHITE, (settings_x, settings_y, button_width, button_height), 2)
    display_message("Settings", WHITE, settings_x + button_width // 2, settings_y + button_height // 2)

def handle_menu_click(mouse_pos):
    """Handles mouse clicks in the menu state."""
    global difficulty, wall_wrapping_enabled, power_up_mode_enabled, multiplayer_enabled, obstacle_mode_enabled, game_state, ai_enabled
    
    # Difficulty buttons
    button_width = 150
    button_height = 70
    x_start = SCREEN_WIDTH // 2 - (2 * button_width + 10)
    y_pos = 150
    spacing = button_width + 10

    # Handle difficulty button clicks
    for i, diff in enumerate([DIFFICULTY_EASY, DIFFICULTY_MEDIUM, DIFFICULTY_HARD, DIFFICULTY_SPEED]):
        button_x = SCREEN_WIDTH // 2 - (2 * button_width + 10) + i * spacing
        if (button_x <= mouse_pos[0] <= button_x + button_width and 
            y_pos <= mouse_pos[1] <= y_pos + button_height):
            difficulty = diff
            reset_game()
            break

    # Bottom buttons
    button_width = 180
    button_height = 60
    bottom_y = 350
    power_up_y = 420
    settings_y = 490
    
    # AI button
    ai_x = SCREEN_WIDTH // 6 - button_width // 2
    if (ai_x <= mouse_pos[0] <= ai_x + button_width and 
        bottom_y <= mouse_pos[1] <= bottom_y + button_height):
        ai_enabled = not ai_enabled
        save_settings()
    
    # Power-Up Mode button
    power_up_x = SCREEN_WIDTH // 6 - button_width // 2
    if (power_up_x <= mouse_pos[0] <= power_up_x + button_width and 
        power_up_y <= mouse_pos[1] <= power_up_y + button_height):
        power_up_mode_enabled = not power_up_mode_enabled
        save_settings()

    # Wall button
    wall_x = SCREEN_WIDTH // 2 - button_width // 2
    if (wall_x <= mouse_pos[0] <= wall_x + button_width and 
        bottom_y <= mouse_pos[1] <= bottom_y + button_height):
        wall_wrapping_enabled = not wall_wrapping_enabled
        save_settings()

    # Multiplayer button
    multiplayer_x = SCREEN_WIDTH // 2 - button_width // 2
    if (multiplayer_x <= mouse_pos[0] <= multiplayer_x + button_width and 
        power_up_y <= mouse_pos[1] <= power_up_y + button_height):
        multiplayer_enabled = not multiplayer_enabled
        save_settings()

    # Obstacle Mode button
    obstacle_x = 5 * SCREEN_WIDTH // 6 - button_width // 2
    if (obstacle_x <= mouse_pos[0] <= obstacle_x + button_width and 
        bottom_y <= mouse_pos[1] <= bottom_y + button_height):
        obstacle_mode_enabled = not obstacle_mode_enabled
        save_settings()

    # Settings button
    settings_x = 5 * SCREEN_WIDTH // 6 - button_width // 2
    if (settings_x <= mouse_pos[0] <= settings_x + button_width and 
        settings_y <= mouse_pos[1] <= settings_y + button_height):
        game_state = GAME_STATE_GRAPHICS

def draw_game_over():
    """Draws the game over screen with clickable buttons."""
    global high_score
    if score > high_score:
        high_score = score
    display_message("Game Over", WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100)
    if multiplayer_enabled and winner:  # Only show winner message in multiplayer mode
        display_message(f"{winner} won!", WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50)
    else:
        display_message(f"Final Score: {score}", WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50)
    display_message(f"High Score: {high_score}", WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    
    # Restart button
    pygame.draw.rect(screen, WHITE, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 + 30, 100, 40), 2)
    display_message("Restart", WHITE, SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 50)
    
    # Menu button
    pygame.draw.rect(screen, WHITE, (SCREEN_WIDTH // 2 + 50, SCREEN_HEIGHT // 2 + 30, 100, 40), 2)
    display_message("Menu", WHITE, SCREEN_WIDTH // 2 + 100, SCREEN_HEIGHT // 2 + 50)

def draw_pause_menu():
    """Draws the pause menu with clickable buttons."""
    display_message("Paused", WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100)
    
    # Button dimensions and spacing
    button_width = 100
    button_height = 40
    button_spacing = 20  # Small spacing between buttons
    
    # Calculate total width and starting x position to center buttons horizontally
    total_width = 3 * button_width + 2 * button_spacing
    start_x = SCREEN_WIDTH // 2 - total_width // 2
    y_pos = SCREEN_HEIGHT // 2 - button_height // 2  # Vertically centered
    
    # Resume button
    resume_x = start_x
    pygame.draw.rect(screen, WHITE, (resume_x, y_pos, button_width, button_height), 2)
    display_message("Resume", WHITE, resume_x + button_width // 2, y_pos + button_height // 2)
    
    # Restart button
    restart_x = resume_x + button_width + button_spacing
    pygame.draw.rect(screen, WHITE, (restart_x, y_pos, button_width, button_height), 2)
    display_message("Restart", WHITE, restart_x + button_width // 2, y_pos + button_height // 2)
    
    # Menu button
    menu_x = restart_x + button_width + button_spacing
    pygame.draw.rect(screen, WHITE, (menu_x, y_pos, button_width, button_height), 2)
    display_message("Menu", WHITE, menu_x + button_width // 2, y_pos + button_height // 2)

def handle_graphics_menu_click(mouse_pos):
    """Handles mouse clicks in the graphics menu."""
    global current_snake_color, current_theme, volume, game_state
    
    # Snake color selection
    x_start = SCREEN_WIDTH // 2 - (len(SNAKE_COLORS) * 70) // 2
    y_pos = 150
    spacing = 70
    color_size = 60
    for i, (color_name, color_value) in enumerate(SNAKE_COLORS.items()):
        x_pos = x_start + i * spacing
        if x_pos <= mouse_pos[0] <= x_pos + color_size and y_pos <= mouse_pos[1] <= y_pos + color_size:
            current_snake_color = color_value
            save_settings()
            break
    
    # Music theme selection
    x_start = 200
    spacing = 150
    y_pos = 300
    for i, theme in enumerate(MUSIC_THEMES.keys()):
        x_pos = x_start + i * spacing
        if x_pos <= mouse_pos[0] <= x_pos + 100 and y_pos <= mouse_pos[1] <= y_pos + 40:
            current_theme = theme
            play_theme_music()
            save_settings()
            break
    
    # Volume control
    if 250 <= mouse_pos[0] <= 550 and 440 <= mouse_pos[1] <= 480:
        volume = (mouse_pos[0] - 250) / 300
        volume = max(0, min(1, volume))
        pygame.mixer.music.set_volume(volume)
        for sound in SOUND_EFFECTS.values():
            sound.set_volume(volume)
            save_settings()
    
    # Back button
    back_button_y = 520
    if SCREEN_WIDTH // 2 - 50 <= mouse_pos[0] <= SCREEN_WIDTH // 2 + 50 and back_button_y <= mouse_pos[1] <= back_button_y + 40:
        game_state = GAME_STATE_MENU

def add_random_obstacle():
    """Adds a single obstacle at a random location, avoiding the snake and food."""
    global obstacles
    if not foods:  # Skip if no food exists
        return
        
    attempts = 0
    max_attempts = 20
    
    while attempts < max_attempts:
        attempts += 1
        obstacle = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
        if (obstacle not in snake and 
            obstacle not in foods and 
            obstacle not in obstacles and 
            obstacle not in power_ups):  # Ensure obstacle does not spawn inside the snake or other game elements
            obstacles.append(obstacle)
            break

def draw_obstacles():
    """Draws the obstacles on the screen."""
    if not obstacles:
        return
    for obstacle in obstacles:
        pygame.draw.rect(screen, GRAY, (obstacle[0] * GRID_SIZE, obstacle[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE))

def place_gambler():
    """Places a gambler at a random location on the grid, avoiding the snake, food, and obstacles."""
    global power_ups
    while len(power_ups) < 1:  # Ensure 1 gambler is placed
        power_up = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
        if power_up not in snake and power_up not in foods and power_up not in obstacles:
            power_ups.append(power_up)
            break

def draw_gamblers():
    """Draws the gamblers on the screen."""
    for power_up in power_ups:
        pygame.draw.rect(screen, CYAN, (power_up[0] * GRID_SIZE, power_up[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE))

def check_gambler_collision(snake_head):
    """Checks if the snake's head has collided with any gambler."""
    global score, snake_length, power_ups
    for power_up in power_ups[:]:
        if snake_head == power_up:
            score += 50  # Increase score by 50 for gambler
            if random.choice([True, False]):
                snake_length += 1  # Increase snake length by 1
            else:
                snake_length = max(snake_length - 1, 1)  # Decrease snake length by 1, but not below 1
            power_ups.remove(power_up)  # Remove the collected gambler
            place_gambler()  # Place a new gambler
            return True  # Indicate that gambler was collected
    return False

def draw_graphics_menu():
    """Draws the graphics menu screen."""
    global current_snake_color, current_theme, volume
    
    display_message("Graphics Settings", WHITE, SCREEN_WIDTH // 2, 50)
    
    # Snake color selection
    display_message("Snake Color:", WHITE, SCREEN_WIDTH // 2, 100)
    x_start = SCREEN_WIDTH // 2 - (len(SNAKE_COLORS) * 70) // 2  # Center the colors
    y_pos = 150
    spacing = 70  # Increased spacing
    color_size = 60 # Increased color size
    
    for i, (color_name, color_value) in enumerate(SNAKE_COLORS.items()):
        x_pos = x_start + i * spacing
        pygame.draw.rect(screen, color_value, (x_pos, y_pos, color_size, color_size))
        if color_value == current_snake_color:
            pygame.draw.rect(screen, WHITE, (x_pos-2, y_pos-2, color_size+4, color_size+4), 2)
        #display_message(color_name, WHITE, x_pos + 25, y_pos + 60) # Removed color names
    
    # Music theme selection
    display_message("Music Theme:", WHITE, SCREEN_WIDTH // 2, 250) # Moved up
    x_start = 200
    spacing = 150
    y_pos = 300 # Moved up
    for i, theme in enumerate(MUSIC_THEMES.keys()):
        x_pos = x_start + i * spacing
        pygame.draw.rect(screen, WHITE, (x_pos, y_pos, 100, 40), 2)
        display_message(theme, WHITE, x_pos + 50, y_pos + 20)
        if theme == current_theme:
            pygame.draw.rect(screen, WHITE, (x_pos-2, y_pos-2, 104, 44), 2)
    
    # Volume control
    display_message("Volume:", WHITE, SCREEN_WIDTH // 2, 400) # Moved up
    pygame.draw.rect(screen, WHITE, (250, 450, 300, 20), 2) # Moved up
    pygame.draw.rect(screen, WHITE, (250 + volume * 300 - 10, 440, 20, 40)) # Moved up
    
    # Back button
    back_button_y = 520 # Moved back button up
    pygame.draw.rect(screen, WHITE, (SCREEN_WIDTH // 2 - 50, back_button_y, 100, 40), 2)
    display_message("Back", WHITE, SCREEN_WIDTH // 2, back_button_y + 20)

# Multiplayer variables
player_2_snake = [(GRID_WIDTH // 2 - 5, GRID_HEIGHT // 2)]
player_2_direction = (-1, 0)  # Initial direction: left
player_2_length = SNAKE_INITIAL_LENGTH

# Power-up effects
power_up_effects = [
    "slow_time", "double_score", "shrink_snake", "double_size", "add_length", "reverse_controls"
]

# Global variable to track active power-up effects and their durations
active_power_ups = {}  # Format: {"effect_name": remaining_duration_in_seconds}

def apply_power_up_effect(effect):
    """Applies a random power-up effect."""
    global difficulty, score, snake_length, invincible, active_power_ups
    duration = 10  # Default duration for power-ups in seconds
    active_power_ups[effect] = duration  # Add the effect to the active list

    if effect == "slow_time":
        difficulty = max(5, difficulty - 5)  # Slow down the game
    elif effect == "double_score":
        score += 10  # Add a noticeable score boost
    elif effect == "shrink_snake":
        snake_length = max(1, snake_length - 5)  # Shrink the snake
    elif effect == "double_size":
        snake_length += 5  # Temporarily increase size
    elif effect == "add_length":
        snake_length += 10  # Add 10 length
    elif effect == "reverse_controls":
        invincible = True  # Reverse controls temporarily

def update_power_up_effects():
    """Updates the durations of active power-up effects and removes expired ones."""
    global difficulty, invincible, active_power_ups
    expired_effects = []

    for effect, duration in active_power_ups.items():
        active_power_ups[effect] -= 1 / clock.get_fps()  # Decrease duration based on frame rate
        if active_power_ups[effect] <= 0:
            expired_effects.append(effect)

    for effect in expired_effects:
        del active_power_ups[effect]
        # Reset any effects that expire
        if effect == "slow_time":
            difficulty = DIFFICULTY_EASY  # Reset difficulty to default
        elif effect == "reverse_controls":
            invincible = False  # Reset invincibility

def draw_active_power_ups():
    """Draws the active power-up effects and their remaining durations on the screen."""
    y_offset = 20
    for effect, duration in active_power_ups.items():
        text = f"{effect}: {int(duration)}s"
        display_message(text, WHITE, SCREEN_WIDTH - 150, y_offset)
        y_offset += 20

def check_power_up_collision(snake_head):
    """Checks if the snake's head has collided with any power-up."""
    global power_ups, active_power_ups
    for power_up in power_ups[:]:
        if snake_head == power_up:
            effect = random.choice(power_up_effects)  # Randomly select a power-up effect
            apply_power_up_effect(effect)  # Apply the selected effect
            power_ups.remove(power_up)  # Remove the collected power-up
            place_power_up()  # Place a new power-up
            return True  # Indicate that a power-up was collected
    return False

def move_snake_multiplayer(snake_list, direction, grow=False):
    """Moves the snake for multiplayer mode."""
    head = snake_list[0]
    new_head = (head[0] + direction[0], head[1] + direction[1])
    new_head = (new_head[0] % GRID_WIDTH, new_head[1] % GRID_HEIGHT)  # Wall wrapping
    snake_list.insert(0, new_head)
    if not grow:
        snake_list.pop()
    return snake_list

def check_multiplayer_collision():
    """Checks for collisions between the two players."""
    global game_state, winner
    # Check if Player 1 collides with Player 2
    if snake[0] in player_2_snake:
        winner = "Player 2" if not ai_enabled else "AI"
        game_state = GAME_STATE_GAME_OVER
    # Check if Player 2 collides with Player 1
    elif player_2_snake[0] in snake:
        winner = "Player 1"
        game_state = GAME_STATE_GAME_OVER

def apply_power_up_effect(effect):
    """Applies a random power-up effect."""
    global difficulty, score, snake_length, player_2_length, invincible
    if effect == "slow_time":
        difficulty = max(5, difficulty - 5)  # Slow down the game
    elif effect == "double_score":
        score *= 2  # Double the score
    elif effect == "shrink_snake":
        snake_length = max(1, snake_length - 5)  # Shrink the snake
    elif effect == "double_size":
        snake_length += 5  # Temporarily increase size
    elif effect == "add_length":
        snake_length += 10  # Add 10 length
    elif effect == "reverse_controls":
        invincible = True  # Reverse controls temporarily (can be implemented further)

def check_power_up_collision(snake_head):
    """Checks if the snake's head has collided with any power-up."""
    global power_ups, active_power_ups
    for power_up in power_ups[:]:
        if snake_head == power_up:
            effect = random.choice(power_up_effects)  # Randomly select a power-up effect
            apply_power_up_effect(effect)  # Apply the selected effect
            power_ups.remove(power_up)  # Remove the collected power-up
            place_power_up()  # Place a new power-up
            return True  # Indicate that a power-up was collected
    return False

def draw_power_ups():
    """Draws the power-ups on the screen."""
    for power_up in power_ups:
        pygame.draw.rect(screen, CYAN, (power_up[0] * GRID_SIZE, power_up[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE))

def draw_shop():
    """Draws the shop screen."""
    display_message("Shop (Coming Soon)", WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50)
    pygame.draw.rect(screen, WHITE, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 2, 100, 40), 2)
    display_message("Back", WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20)

def draw_custom_levels():
    """Draws the custom levels screen."""
    display_message("Custom Levels (Coming Soon)", WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50)
    pygame.draw.rect(screen, WHITE, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 2, 100, 40), 2)
    display_message("Back", WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20)

def handle_shop_or_custom_click(mouse_pos):
    """Handles clicks in Shop or Custom Levels screens."""
    global game_state
    if (SCREEN_WIDTH // 2 - 50 <= mouse_pos[0] <= SCREEN_WIDTH // 2 + 50 and 
        SCREEN_HEIGHT // 2 <= mouse_pos[1] <= SCREEN_HEIGHT // 2 + 40):
        game_state = GAME_STATE_MENU

# Global variable to hold the winner
winner = None  # Initialize winner variable

# Separate high scores for each mode
high_scores = {
    "normal": 0,
    "obstacle": 0,
    "power_up": 0,
    "multiplayer": 0
}

def update_high_score():
    """Updates the high score for the current mode."""
    global high_scores, score
    mode = "normal"
    if obstacle_mode_enabled:
        mode = "obstacle"
    elif power_up_mode_enabled:
        mode = "power_up"
    elif multiplayer_enabled:
        mode = "multiplayer"
    if score > high_scores[mode]:
        high_scores[mode] = score

# --- Game Loop ---
running = True
play_theme_music()
try:
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if game_state == GAME_STATE_PLAYING:
                handle_input(event)
            elif game_state == GAME_STATE_PAUSED:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:  # Resume
                        game_state = GAME_STATE_PLAYING
                    elif event.key == pygame.K_q:  # Quit to menu
                        game_state = GAME_STATE_MENU
                    elif event.key == pygame.K_SPACE:  # Restart
                        reset_game()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    
                    # Button dimensions and spacing
                    button_width = 100
                    button_height = 40
                    button_spacing = 20  # Small spacing between buttons
                    
                    # Calculate total width and starting x position to center buttons horizontally
                    total_width = 3 * button_width + 2 * button_spacing
                    start_x = SCREEN_WIDTH // 2 - total_width // 2
                    y_pos = SCREEN_HEIGHT // 2 - button_height // 2  # Vertically centered
                    
                    # Resume button
                    resume_x = start_x
                    if (resume_x <= mouse_pos[0] <= resume_x + button_width and
                        y_pos <= mouse_pos[1] <= y_pos + button_height):
                        game_state = GAME_STATE_PLAYING
                
                    # Restart button
                    restart_x = resume_x + button_width + button_spacing
                    if (restart_x <= mouse_pos[0] <= restart_x + button_width and
                        y_pos <= mouse_pos[1] <= y_pos + button_height):
                        reset_game()
                
                    # Menu button
                    menu_x = restart_x + button_width + button_spacing
                    if (menu_x <= mouse_pos[0] <= menu_x + button_width and
                        y_pos <= mouse_pos[1] <= y_pos + button_height):
                        game_state = GAME_STATE_MENU
            elif game_state == GAME_STATE_MENU:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    handle_menu_click(pygame.mouse.get_pos())
            elif game_state == GAME_STATE_GAME_OVER:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:  # Restart
                        reset_game()
                    elif event.key == pygame.K_q:  # Quit to menu
                        game_state = GAME_STATE_MENU
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    # Restart button
                    if SCREEN_WIDTH // 2 - 150 <= mouse_pos[0] <= SCREEN_WIDTH // 2 - 50 and SCREEN_HEIGHT // 2 + 30 <= mouse_pos[1] <= SCREEN_HEIGHT // 2 + 70:
                        reset_game()
                    # Menu button
                    elif SCREEN_WIDTH // 2 + 50 <= mouse_pos[0] <= SCREEN_WIDTH // 2 + 150 and SCREEN_HEIGHT // 2 + 30 <= mouse_pos[1] <= SCREEN_HEIGHT // 2 + 70:
                        game_state = GAME_STATE_MENU
            elif game_state == GAME_STATE_GRAPHICS:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    handle_graphics_menu_click(pygame.mouse.get_pos())
            elif game_state in [GAME_STATE_SHOP, GAME_STATE_CUSTOM_LEVELS]:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    handle_shop_or_custom_click(pygame.mouse.get_pos())

        # --- Game Logic ---
        if game_state == GAME_STATE_PLAYING:
            update_power_up_effects()  # Update power-up durations
            if ai_enabled and multiplayer_enabled:
                player_2_grow = check_food_collision(player_2_snake[0])  # Check if AI eats food
                player_2_snake = move_snake_multiplayer(player_2_snake, ai_move(player_2_snake, foods), player_2_grow)

            grow = check_food_collision(snake[0])  # Check food collision for Player 1
            power_up_collected = check_power_up_collision(snake[0])  # Check power-up collision
            snake = move_snake(snake, snake_direction, grow or power_up_collected)  # Move Player 1 snake

            if multiplayer_enabled:
                # Check for collisions between the two snakes
                check_multiplayer_collision()

            # Check for collisions with walls, self, or obstacles
            if check_collision(snake) or (multiplayer_enabled and check_collision(player_2_snake)):
                SOUND_EFFECTS['die'].play()
                if not winner:  # If no winner yet, Player 1 loses
                    winner = "Player 2" if not ai_enabled else "AI"
                game_state = GAME_STATE_GAME_OVER

        # --- Drawing ---
        screen.fill(BLACK)  # Clear the screen
        if game_state == GAME_STATE_MENU:
            draw_menu()
        elif game_state == GAME_STATE_PLAYING:
            draw_snake(snake, current_snake_color)
            if multiplayer_enabled:
                draw_snake(player_2_snake, SNAKE_COLORS['BLUE'])
            draw_food()
            draw_obstacles()
            draw_power_ups()
            draw_active_power_ups()  # Draw active power-ups
            display_message(f"Score: {score}", WHITE, 50, 20)
        elif game_state == GAME_STATE_PAUSED:
            draw_pause_menu()
        elif game_state == GAME_STATE_GAME_OVER:
            update_high_score()  # Update high score when the game ends
            draw_game_over()
        elif game_state == GAME_STATE_GRAPHICS:
            draw_graphics_menu()
        elif game_state == GAME_STATE_SHOP:
            draw_shop()
        elif game_state == GAME_STATE_CUSTOM_LEVELS:
            draw_custom_levels()

        pygame.display.flip()  # Update the display
        clock.tick(difficulty * 2 if ai_enabled else difficulty)  # Control the game speed

except Exception as e:
    print(f"An error occurred: {e}")
    pygame.quit()
    running = False

# Quit Pygame
pygame.quit()
