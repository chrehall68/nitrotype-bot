import win32api
import win32con
import time


def type_string(inp: str, max_chars_per_sec: float = 100) -> None:
    for char in inp:
        char_vk = win32api.VkKeyScan(char)
        if char.isupper():
            win32api.keybd_event(win32con.VK_SHIFT, 0, 0, 0)
            win32api.keybd_event(char_vk, 0, 0, 0)
            win32api.keybd_event(win32con.VK_SHIFT, 0, win32con.KEYEVENTF_KEYUP, 0)
            win32api.keybd_event(char_vk, 0, win32con.KEYEVENTF_KEYUP, 0)
        else:
            win32api.keybd_event(char_vk, 0, 0, 0)
            win32api.keybd_event(char_vk, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(1 / max_chars_per_sec)


time.sleep(2)
type_string("The quick brown fox jumps over the lazy dog.", 25)
