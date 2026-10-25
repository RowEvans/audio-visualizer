import sounddevice as sd
import numpy as np
import pygame
import colorsys
import time
from spotify import spotify_is_playing

DEVICE = 14
DISPLAY = 0

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
LIGHT_GRAY = 140
DARK_GRAY = 40

FFT_SIZE = 2048
MIN_FREQ = 40
MAX_FREQ = 16000
DB_FLOOR = -80
DB_CEIL = -25
TILT_DB = 18
FALL_SPEED = 0.35

def pick_color_rg(row):
    t = row / (ROWS - 1)
    hue = (1 - t) * (120 / 360)
    r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
    return (int(r * 255), int(g * 255), int(b * 255))

def pick_color_gray(row):
    t = row / (ROWS - 1)
    v = int(LIGHT_GRAY + (DARK_GRAY - LIGHT_GRAY) * t)
    return (v, v, v)

COLOR_MODES = [("Gray", pick_color_gray), ("Red/Green", pick_color_rg)]
BUTTON_RECT = pygame.Rect(WIDTH - 20 - 120, 8, 120, 24)

def draw_button(screen, font, label):
    hovered = BUTTON_RECT.collidepoint(pygame.mouse.get_pos())
    bg = (75, 75, 85) if hovered else (50, 50, 58)
    pygame.draw.rect(screen, bg, BUTTON_RECT, border_radius=6)
    text = font.render(label, True, (230, 230, 230))
    screen.blit(text, text.get_rect(center=BUTTON_RECT.center))

def draw_grid(screen, levels, color_fn):
    for col in range(COLS):
        x = MARGIN + col * (CELL_WIDTH + GAP)
        for row in range(ROWS):
            y = HEIGHT - MARGIN - CELL_HEIGHT - row * (CELL_HEIGHT + GAP)
            color = color_fn(row) if row < levels[col] else OFF_COLOR
            pygame.draw.rect(screen, color, (x, y , CELL_WIDTH, CELL_HEIGHT))

buffer = np.zeros(FFT_SIZE, dtype=np.float32)

def audio_callback(indata, frames, time, status):
    mono = indata.mean(axis=1)[-FFT_SIZE:]
    n = len(mono)
    buffer[:-n] = buffer[n:]
    buffer[-n:] = mono

def make_band_ranges(rate):
    freqs = np.fft.rfftfreq(FFT_SIZE, 1 / rate)
    edges = np.geomspace(MIN_FREQ, MAX_FREQ, COLS + 1)
    ranges = []
    for i in range(COLS):
        lo = int(np.searchsorted(freqs, edges[i]))
        hi = int(np.searchsorted(freqs, edges[i+1]))
        ranges.append((lo, max(hi, lo + 1)))
    return ranges

def compute_levels(band_ranges, window, tilt, gain_db):
    spectrum = np.abs(np.fft.rfft(buffer*window)) / (FFT_SIZE / 2)
    db = np.zeros(COLS)
    for i, (lo, hi) in enumerate(band_ranges):
        db[i] = 20 * np.log10(spectrum[lo:hi].max() + 1e-10)
    db += tilt + gain_db
    scaled = (db - DB_FLOOR) / (DB_CEIL - DB_FLOOR)
    return np.clip(scaled, 0, 1) * ROWS

info = sd.query_devices(DEVICE)
rate = int(info["default_samplerate"])
band_ranges = make_band_ranges(rate)
window = np.hanning(FFT_SIZE)
tilt = np.linspace(0, TILT_DB, COLS)


pygame.init()
screen = pygame.display.set_mode(
    (WIDTH, HEIGHT), pygame.SCALED | pygame.FULLSCREEN, display=DISPLAY
)
pygame.display.set_caption("Audio Visualizer")
clock = pygame.time.Clock()
font = pygame.font.SysFont("arial", 16)
mode = 0
gain_db = 0

smooth = np.zeros(COLS)
playing = False
last_check = 0.0

with sd.InputStream(
    device = DEVICE,
    channels = 2,
    samplerate=rate,
    blocksize=1024,
    callback=audio_callback
):
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_UP:
                    gain_db += 2
                if event.key == pygame.K_DOWN:
                    gain_db -= 2
                if event.key == pygame.K_f:
                    pygame.display.toggle_fullscreen()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if BUTTON_RECT.collidepoint(event.pos):
                    mode = (mode + 1) % len(COLOR_MODES)

        now = time.time()
        if now - last_check > 1.0:
            playing = spotify_is_playing()
            last_check = now

        if not playing:
            smooth[:] = 0
            screen.fill((0, 0, 0))
            pygame.display.flip()
            clock.tick(FPS)
            continue

        target = compute_levels(band_ranges, window, tilt, gain_db)
        smooth = np.where(target > smooth, target, np.maximum(target, smooth - FALL_SPEED))

        label, color_fn = COLOR_MODES[mode]
        screen.fill(BG_COLOR)
        draw_grid(screen, np.round(smooth).astype(int), color_fn)
        draw_button(screen, font, label)
        gain_text = font.render(f"Gain: {gain_db:+d} dB", True, (150, 150, 150))
        screen.blit(gain_text, (MARGIN, 10))
        pygame.display.flip()
        clock.tick(FPS)

pygame.quit()
    
