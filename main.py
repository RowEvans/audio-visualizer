import sounddevice as sd
import numpy as np
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

FFT_SIZE = 2048
MIN_FREQ = 40
MAX_FREQ = 16000
DB_FLOOR = -80
DB_CEIL = -25
TILT_DB = 18
FALL_SPEED = 0.35

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

def compute_levels(band_ranges, window, tilt):
    spectrum = np.abs(np.fft.rfft(buffer*window)) / (FFT_SIZE / 2)
    db = np.zeros(COLS)
    for i, (lo, hi) in enumerate(band_ranges):
        db[i] = 20 * np.log10(spectrum[lo:hi].max() + 1e-10)
    db += tilt
    scaled = (db - DB_FLOOR) / (DB_CEIL - DB_FLOOR)
    return np.clip(scaled, 0, 1) * ROWS

info = sd.query_devices(DEVICE)
rate = int(info["default_samplerate"])
band_ranges = make_band_ranges(rate)
window = np.hanning(FFT_SIZE)
tilt = np.linspace(0, TILT_DB, COLS)


pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Audio Visualizer")
clock = pygame.time.Clock()

smooth = np.zeros(COLS)

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
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        target = compute_levels(band_ranges, window, tilt)
        smooth = np.where(target > smooth, target, np.maximum(target, smooth - FALL_SPEED))

        screen.fill(BG_COLOR)
        draw_grid(screen, np.round(smooth).astype(int))
        pygame.display.flip()
        clock.tick(FPS)

pygame.quit()
    
