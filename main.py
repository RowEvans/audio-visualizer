import random
import pygame
import colorsys

DEVICE = 14

WIDTH, HEIGHT = 800, 480
FPS = 60
BG_COLOR = (0, 0, 0)

COLS = 20
ROWS = 14
MARGIN = 40
GAP = 4

CELL_WIDTH = (WIDTH - 2 * MARGIN - (COLS - 1) * GAP) // COLS
CELL_HEIGHT = (HEIGHT - 2 * MARGIN - (ROWS - 1) * GAP) // ROWS

OFF_COLOR = (20, 20, 20)

def pick_color(row):
    t = row / (ROWS - 1)
    hue = (1 - t) * (120 / 360)
    r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
    return (int(r * 255), int(g * 255), int(b * 255))

def draw_grid(screen, levels):
    for col in range(COLS):
        x = MARGIN + col * (CELL_WIDTH + GAP)
        for row in range(ROWS):
            y = HEIGHT - MARGIN - CELL_HEIGHT - row * (CELL_HEIGHT + GAP)
            color = pick_color(row) if row < levels[col] else OFF_COLOR
            pygame.draw.rect(screen, color, (x, y , CELL_WIDTH, CELL_HEIGHT))


pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Audio Visualizer")
clock = pygame.time.Clock()

levels = [random.randint(1, ROWS) for _ in range(COLS)]

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

    screen.fill(BG_COLOR)
    draw_grid(screen, levels)
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
