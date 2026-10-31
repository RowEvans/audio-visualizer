import sounddevice as sd
import numpy as np
import pygame
import colorsys
import time
from spotify import spotify_now_playing
from monitor import active_on_monitor, cursor_on_monitor, hide_from_alt_tab, hide_window, monitor_of, show_window, set_opacity, hotkey_down

DEVICE = 41
DISPLAY = 1

IDLE_DELAY = 3
FADE_SECONDS = 0.5

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

def pick_color_gray(row):
    t = row / (ROWS - 1)
    v = int(LIGHT_GRAY + (DARK_GRAY - LIGHT_GRAY) * t)
    return (v, v, v)

def draw_grid(screen, levels):
    for col in range(COLS):
        x = MARGIN + col * (CELL_WIDTH + GAP)
        for row in range(ROWS):
            y = HEIGHT - MARGIN - CELL_HEIGHT - row * (CELL_HEIGHT + GAP)
            color = pick_color_gray(row) if row < levels[col] else OFF_COLOR
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
gain_db = 40

hwnd = pygame.display.get_wm_info()["window"]
my_monitor = monitor_of(hwnd)
hide_from_alt_tab(hwnd)
last_user_here = time.time()
opacity = 1.0
enabled = True
hotkey_was_down = False
visible = True

smooth = np.zeros(COLS)
playing = None
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
        hotkey_now = hotkey_down()
        if hotkey_now and not hotkey_was_down:
            enabled = not enabled
        hotkey_was_down = hotkey_now

        now = time.time()
        if now - last_check > 1.0:
            playing = spotify_now_playing()
            last_check = now

        user_here = active_on_monitor(hwnd, my_monitor) or cursor_on_monitor(my_monitor)
        if user_here:
            last_user_here = time.time()
        away_long_enough = time.time() - last_user_here >= IDLE_DELAY
        want_visible = enabled and bool(playing) and away_long_enough      
        if want_visible != visible:
            if want_visible:
                opacity = 0.0
                set_opacity(hwnd, 0)
                show_window(hwnd)
            else:
                hide_window(hwnd)
            visible = want_visible

        if not want_visible:
            smooth[:] = 0
            clock.tick(20)
            continue

        if opacity < 1.0:
            opacity = min(1.0, opacity + 1 / (FPS * FADE_SECONDS))
            set_opacity(hwnd, int(opacity * 255))

        target = compute_levels(band_ranges, window, tilt, gain_db)
        smooth = np.where(target > smooth, target, np.maximum(target, smooth - FALL_SPEED))

        screen.fill(BG_COLOR)
        draw_grid(screen, np.round(smooth).astype(int))
        song_surf = font.render(f"{playing}", True, (150, 150, 150))
        screen.blit(song_surf, song_surf.get_rect(center=(WIDTH // 2, HEIGHT - MARGIN // 2)))
        pygame.display.flip()
        clock.tick(FPS)

pygame.quit()
    
