import win32gui
import win32process as wproc
import win32api


def winEnumHandler(hwnd, windows):
    if win32gui.IsWindowVisible(hwnd):
        print(hwnd, win32gui.GetWindowText(hwnd))
        windows[win32gui.GetWindowText(hwnd)] = hwnd


def focus_window(window_title: str):
    windows = {}
    win32gui.EnumWindows(winEnumHandler, windows)

    words = window_title.split()
    for title, hwnd in windows.items():
        valid = all([word in title for word in words])
        if valid:
            # it's microsoft edge

            # attach the current process to the thread
            remote_thread, _ = wproc.GetWindowThreadProcessId(hwnd)
            wproc.AttachThreadInput(win32api.GetCurrentThreadId(), remote_thread, True)

            # finally, set focus to the desired window
            win32gui.SetFocus(hwnd)
            break
