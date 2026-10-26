import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32

SW_HIDE = 0
SW_SHOWNOACTIVATE = 4
MONITOR_DEFAULTTONEAREST = 2

user32.GetForegroundWindow.restype = wintypes.HWND
user32.MonitorFromWindow.argtypes = [wintypes.HWND, wintypes.DWORD]
user32.MonitorFromWindow.restype = wintypes.HANDLE


def hide_window(hwnd):
    user32.ShowWindow(hwnd, SW_HIDE)


HWND_TOPMOST = wintypes.HWND(-1)
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010

user32.SetWindowPos.argtypes = [
    wintypes.HWND, wintypes.HWND,
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    wintypes.UINT,
]


def show_window(hwnd):
    user32.ShowWindow(hwnd, SW_SHOWNOACTIVATE)
    user32.SetWindowPos(
        hwnd, HWND_TOPMOST, 0, 0, 0, 0,
        SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE,
    )


def monitor_of(hwnd):
    return user32.MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST)


def active_on_monitor(my_hwnd, my_monitor):
    fg = user32.GetForegroundWindow()
    if not fg or fg == my_hwnd:
        return False
    return monitor_of(fg) == my_monitor