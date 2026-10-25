import ctypes
from ctypes import wintypes

import psutil

user32 = ctypes.windll.user32
WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

IDLE_TITLES = ("spotify", "spotify free", "spotify premium")

def spotify_titles():
    titles = []

    def callback(hwnd, lparam):
        length = user32.GetWindowTextLengthW(hwnd)
        if length:
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            try:
                if psutil.Process(pid.value).name().lower() == "spotify.exe":
                    titles.append(buf.value)
            except psutil.Error:
                pass

        return True

    user32.EnumWindows(WNDENUMPROC(callback), 0)
    return titles


def spotify_now_playing():
    for title in spotify_titles():
        if title.lower() not in IDLE_TITLES and " - " in title:
            return title

    return None

if __name__ == "__main__":
    import time

    while True:
        print(spotify_titles(), "->", spotify_now_playing())
        time.sleep(1)