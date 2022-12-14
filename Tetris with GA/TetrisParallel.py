""" This file runs multiple instances of the Tetris class in synchronization with a PyGame display """

# Imports
import matplotlib.pyplot as plt
import pygame
#from pygame.locals import *
from Tetris import Tetris
import TetrisUtils as TUtils
from TetrisSettings import *
from TetrisAgents import *



# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# Parallel Training Settings

# Parallel Tetris game count
ROW_COUNT = 3 #4
COL_COUNT = 6 #10
GAME_COUNT = ROW_COUNT * COL_COUNT  # no need to modify

# Size of each Tetris display
GAME_WIDTH = 100
GAME_HEIGHT = GAME_WIDTH * 2  # no need to modify
GAME_GRID_SIZE = GAME_WIDTH / GRID_COL_COUNT  # no need to modify

# Size of padding
PADDING = 10
PADDING_STATS = 300

# Screen size (automatically calculated)
SCREEN_WIDTH = GAME_WIDTH * COL_COUNT + PADDING * (COL_COUNT + 1) + PADDING_STATS
SCREEN_HEIGHT = GAME_HEIGHT * ROW_COUNT + PADDING * (ROW_COUNT + 1)

# Mutation Rate
MUTATION_RATE = 0.1  # 10% mutation chance

# End of Settings
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

####################
# Global Variables #
####################
# List of Tetris instances
TETRIS_GAMES = []
# List of agents
AGENTS = []

########################
# Genetics Information #
########################
# Only used when genetic agents are used
gen_generation = 1  # when this is set to -1, genetic agent is not used
gen_previous_best_score = 0.0
gen_top_score = 0.0

# Set a time limit so no forever games
time_elapsed = 0
time_limit = 1000 #1000

my_top_score = []


def update(screen):
    """ Called every frame by the runner, handles updates each frame """
    global GAME_COUNT, AGENTS
    global gen_generation, gen_previous_best_score, gen_top_score
    global time_elapsed, time_limit
    global my_top_score
    time_elapsed += 1

    # Check if all agents have reached game over state
    if all(tetris.game_over for tetris in TETRIS_GAMES) or (time_limit != -1 and time_elapsed % time_limit == 0):
        time_elapsed = 0
        # Everyone "died" or time's up, select best one and cross over
        combos = zip(AGENTS, TETRIS_GAMES)
        parents = sorted(combos, key=lambda combo: combo[1].score, reverse=True)
        # Update generation information
        gen_generation += 1
        my_top_score.append(gen_previous_best_score)
        gen_previous_best_score = parents[0][1].score
        if gen_previous_best_score > gen_top_score:
            gen_top_score = gen_previous_best_score

        # Undo zipping
        parents = [a[0] for a in parents]

        # Discard 50% of population
        parents = parents[:GAME_COUNT // 2]
        # Keep first place agent
        AGENTS = [parents[0]]
        # Randomly breed the rest of the agents
        while len(AGENTS) < GAME_COUNT:
            parent1, parent2 = random.sample(parents, 2)
            AGENTS.append(parent1.cross_over(parent2))

        # Reset games
        for tetris in TETRIS_GAMES:
            tetris.reset_game()

    for a in range(GAME_COUNT):
        # If game over, ignore
        if TETRIS_GAMES[a].game_over:
            continue
        TETRIS_GAMES[a].step(AGENTS[a].get_action(TETRIS_GAMES[a]))

    draw(screen)
    pygame.event.get()


def draw(screen):
    """ Called by the update() function every frame, draws the PyGame GUI """
    # Background layer
    screen.fill(TUtils.get_color_tuple(COLORS.get("BACKGROUND_BLACK")))

    # Draw Tetris boards
    curr_x, curr_y = PADDING, PADDING
    for x in range(ROW_COUNT):
        for y in range(COL_COUNT):
            draw_board(screen, TETRIS_GAMES[x * COL_COUNT + y], curr_x, curr_y)
            curr_x += GAME_WIDTH + PADDING
        curr_x = PADDING
        curr_y += GAME_HEIGHT + PADDING

    # Draw statistics
    # Realign starting point to statistics bar
    curr_x, curr_y = GAME_WIDTH * COL_COUNT + PADDING * (COL_COUNT + 1), PADDING

    # Draw title
    draw_text("Tetris", screen, (curr_x, curr_y), font_size=48)
    curr_y += 60
    # Draw statistics
    best_indexes, best_score = get_high_score()
    draw_text(f"High Score: {best_score:.1f}", screen, (curr_x, curr_y))
    curr_y += 20
    draw_text(f"Best Agent: {SEP.join(map(str, best_indexes))}", screen, (curr_x, curr_y))
    curr_y += 20

    # Draw genetics
    if gen_generation > -1:
        curr_y += 20
        draw_text(f"Generation #{gen_generation}", screen, (curr_x, curr_y), font_size=24)
        curr_y += 35
        draw_text(f"Time Limit: {time_elapsed}/{time_limit}", screen, (curr_x, curr_y))
        curr_y += 20

        survivor = len([a for a in TETRIS_GAMES if not a.game_over])
        draw_text(f"Survivors: {survivor}/{GAME_COUNT} ({survivor / GAME_COUNT * 100:.1f}%)", screen, (curr_x, curr_y))
        curr_y += 20
        draw_text(f"Prev H.Score: {gen_previous_best_score:.1f}", screen, (curr_x, curr_y))
        curr_y += 20
        draw_text(f"All Time H.S: {gen_top_score:.1f}", screen, (curr_x, curr_y))
        curr_y += 40

        # Display selected agent
        mouse_x, mouse_y = pygame.mouse.get_pos()
        grid_x, grid_y = mouse_x // (GAME_WIDTH + PADDING), mouse_y // (GAME_HEIGHT + PADDING)
        selected = grid_y * COL_COUNT + grid_x

        agent_index = -1
        highlight_selected = False
        if selected < GAME_COUNT and mouse_x < (GAME_WIDTH + PADDING) * COL_COUNT:
            agent_index = selected
            highlight_selected = True
        elif len(best_indexes) > 0:
            agent_index = best_indexes[0]

        if agent_index != -1:
            draw_text(f"Agent #{agent_index}:", screen, (curr_x, curr_y), font_size=24)
            curr_y += 35
            draw_text(f">> Agg Height: {AGENTS[agent_index].weight_height:.1f}", screen, (curr_x, curr_y))
            curr_y += 20
            draw_text(f">> Hole Count: {AGENTS[agent_index].weight_holes:.1f}", screen, (curr_x, curr_y))
            curr_y += 20
            draw_text(f">> Bumpiness:  {AGENTS[agent_index].weight_bumpiness:.1f}", screen, (curr_x, curr_y))
            curr_y += 20
            draw_text(f">> Line Clear: {AGENTS[agent_index].weight_line_clear:.1f}", screen, (curr_x, curr_y))
            curr_y += 20
            if highlight_selected:
                highlight(screen, selected, mode=1)
            else:
                # Highlight current best(s)
                for a in best_indexes:
                    highlight(screen, a, mode=0)

        # Update display
        pygame.display.update()


def highlight(screen, index: int, mode: int):
    """
    Highlight a certain Tetris grid

    :param screen: the screen to draw on
    :param index: index of Tetris grid to highlight
    :param mode: 0/1, 0 = best, 1 = previous best
    """
    game_x = index % COL_COUNT
    game_y = index // COL_COUNT
    color = TUtils.get_color_tuple(COLORS.get("HIGHLIGHT_GREEN" if mode == 0 else "HIGHLIGHT_RED"))

    if mode == 1:
        # Draw previous best (thick border)
        temp_x = (GAME_WIDTH + PADDING) * game_x
        temp_y = (GAME_HEIGHT + PADDING) * game_y
        pygame.draw.rect(screen, color, (temp_x, temp_y, GAME_WIDTH + PADDING * 2, PADDING))
        pygame.draw.rect(screen, color, (temp_x, temp_y, PADDING, GAME_HEIGHT + PADDING * 2))
        temp_x = (GAME_WIDTH + PADDING) * (game_x + 1) + PADDING - 1
        temp_y = (GAME_HEIGHT + PADDING) * (game_y + 1) + PADDING - 1
        pygame.draw.rect(screen, color, (temp_x, temp_y, -GAME_WIDTH - PADDING, -PADDING))
        pygame.draw.rect(screen, color, (temp_x, temp_y, -PADDING, -GAME_HEIGHT - PADDING))
    elif mode == 0:
        # Draw current best (thin border)
        temp_x = (GAME_WIDTH + PADDING) * game_x + PADDING / 2
        temp_y = (GAME_HEIGHT + PADDING) * game_y + PADDING / 2
        pygame.draw.rect(screen, color, (temp_x, temp_y, GAME_WIDTH + PADDING, PADDING / 2))
        pygame.draw.rect(screen, color, (temp_x, temp_y, PADDING / 2, GAME_HEIGHT + PADDING))
        temp_x = (GAME_WIDTH + PADDING) * (game_x + 1) + PADDING / 2 - 1
        temp_y = (GAME_HEIGHT + PADDING) * (game_y + 1) + PADDING / 2 - 1
        pygame.draw.rect(screen, color, (temp_x, temp_y, -GAME_WIDTH - PADDING + 2, -PADDING / 2))
        pygame.draw.rect(screen, color, (temp_x, temp_y, -PADDING / 2, -GAME_HEIGHT - PADDING + 2))


def get_high_score():
    best_indexes, best_score = [], 0
    for a in range(GAME_COUNT):
        # Ignore dead games
        if TETRIS_GAMES[a].game_over:
            continue
        # Get score
        score = TETRIS_GAMES[a].score
        if score > best_score:
            best_indexes = [a]
            best_score = score
        elif score == best_score:
            best_indexes.append(a)
    return best_indexes, best_score


def draw_text(message: str, screen, offsets, font_size=16, color="WHITE"):
    """ Draws a line of text at the specified offsets """
    text_image = pygame.font.SysFont(FONT_NAME, font_size).render(message, False, TUtils.get_color_tuple(COLORS.get(color)))
    screen.blit(text_image, offsets)


def draw_board(screen, tetris: Tetris, x_offset: int, y_offset: int):
    """
    Draws one Tetris board with offsets, called by draw() multiple times per frame

    :param screen: the screen to draw on
    :param tetris: Tetris instance
    :param x_offset: X offset (starting X)
    :param y_offset: Y offset (starting Y)
    """
    # [0] Striped background layer
    for a in range(GRID_COL_COUNT):
        color = TUtils.get_color_tuple(COLORS.get("BACKGROUND_DARK" if a % 2 == 0 else "BACKGROUND_LIGHT"))
        pygame.draw.rect(screen, color, (x_offset + a * GAME_GRID_SIZE, y_offset, GAME_GRID_SIZE, GAME_HEIGHT))

    # [1] Board tiles
    draw_tiles(screen, tetris.board, global_offsets=(x_offset, y_offset))
    # [1] Current tile
    draw_tiles(screen, tetris.tile_shape, offsets=(tetris.tile_x, tetris.tile_y), global_offsets=(x_offset, y_offset))

    # [2] Game over graphics
    if tetris.game_over:
        color = TUtils.get_color_tuple(COLORS.get("BACKGROUND_BLACK"))
        ratio = 0.9
        pygame.draw.rect(screen, color, (x_offset, y_offset + (GAME_HEIGHT * ratio) / 2, GAME_WIDTH, GAME_HEIGHT * (1 - ratio)))

        message = "GAME OVER"
        color = TUtils.get_color_tuple(COLORS.get("RED"))
        text_image = pygame.font.SysFont(FONT_NAME, GAME_WIDTH // 6).render(message, False, color)
        rect = text_image.get_rect()
        screen.blit(text_image, (x_offset + (GAME_WIDTH - rect.width) / 2, y_offset + (GAME_HEIGHT - rect.height) / 2))


def draw_tiles(screen, matrix, offsets=(0, 0), global_offsets=(0, 0), outline_only=False):
    """
    Draw tiles from a matrix (utility method)

    :param screen: the screen to draw on
    :param matrix: the matrix to draw
    :param offsets: matrix index offsets
    :param global_offsets: global pixel offsets
    :param outline_only: draw prediction outline only?
    """
    for y, row in enumerate(matrix):
        for x, val in enumerate(row):
            if val == 0:
                continue
            coord_x = global_offsets[0] + (offsets[0] + x) * GAME_GRID_SIZE
            coord_y = global_offsets[1] + (offsets[1] + y) * GAME_GRID_SIZE
            # Draw rectangle
            if not outline_only:
                pygame.draw.rect(screen,
                                 TUtils.get_color_tuple(COLORS.get("TILE_" + TILES[val - 1])),
                                 (coord_x, coord_y, GAME_GRID_SIZE, GAME_GRID_SIZE))
                pygame.draw.rect(screen,
                                 TUtils.get_color_tuple(COLORS.get("BACKGROUND_BLACK")),
                                 (coord_x, coord_y, GAME_GRID_SIZE, GAME_GRID_SIZE), 1)
                # Draw highlight triangle
                offset = int(GAME_GRID_SIZE / 10)
                pygame.draw.polygon(screen, TUtils.get_color_tuple(COLORS.get("TRIANGLE_GRAY")),
                                    ((coord_x + offset, coord_y + offset),
                                     (coord_x + 3 * offset, coord_y + offset),
                                     (coord_x + offset, coord_y + 3 * offset)))
            else:
                # Outline-only for prediction location
                pygame.draw.rect(screen,
                                 TUtils.get_color_tuple(COLORS.get("TILE_" + TILES[val - 1])),
                                 (coord_x + 1, coord_y + 1, GAME_GRID_SIZE - 2, GAME_GRID_SIZE - 2), 1)


if __name__ == "__main__":
    print(f"Hello world!")
    print(f">> Initializing {GAME_COUNT} Tetris games in parallel with a grid of {ROW_COUNT}??{COL_COUNT}...")

    # Initialize PyGame module
    pygame.init()
    pygame.font.init()
    display_screen = pygame.display.set_mode(size=(SCREEN_WIDTH, SCREEN_HEIGHT))
    print(f">> Screen size calculated to {SCREEN_WIDTH}??{SCREEN_HEIGHT}...")

    # Initialize Tetris modules and agents
    print(f">> Initializing {GAME_COUNT} Tetris agent(s)...")
    for _ in range(GAME_COUNT):
        TETRIS_GAMES.append(Tetris())
        AGENTS.append(GeneticAgent())

    print(f">> Initialization complete! Let the show begin!")
    #counterLoop = 0
    while gen_generation != 11:  #True:
        # Each loop iteration is 1 frame
        update(display_screen)
        #counterLoop = counterLoop + 1

    #print(my_top_score)

    plt.plot(my_top_score)
    plt.xlabel("Iteration")
    plt.ylabel("Fitness Function/Score")
    plt.show()

    
