import win32stuff
from datetime import datetime
import asyncio
import numpy
import cv2
import json
import screenshot
import pytesseract
import threading
import win32api
import win32con
import time
import argparse


def is_blue(pixel):
    return pixel[0] > 200 and pixel[1] < 200 and pixel[1] > 100 and pixel[2] < 100


def is_red(pixel):
    return pixel[0] < 100 and pixel[1] < 100 and pixel[2] > 150


def is_black(gray_pixel):
    return gray_pixel < 60


def is_white(gray_pixel):
    return gray_pixel > 215


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


async def press_enter():
    win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)
    win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
    await asyncio.sleep(0.001)


kernel = numpy.ones([1, 1], numpy.uint8)


def get_char_bbox(im: numpy.ndarray) -> tuple:
    min_x = max_x = min_y = max_y = 0
    defined = False
    for x in range(im.shape[0]):
        for y in range(im.shape[1]):
            if is_blue(im[x][y]) or is_red(im[x][y]):
                # it's blueish (B > 200, 100 < G < 200, R < 100)
                if not defined:
                    min_x = max_x = x
                    min_y = max_y = y
                    defined = True
                else:
                    min_x = min(x, min_x)
                    max_x = max(x, max_x)
                    min_y = min(y, min_y)
                    max_y = max(y, max_y)
    return min_x, max_x, min_y, max_y


def capture_image(screenshotter: screenshot.SectionCapture):
    global kernel
    start_time = datetime.now()
    im = screenshotter.get_screenshot()  # im is bgr
    print(
        f"time taken for sct was {(datetime.now()-start_time).seconds + (datetime.now()-start_time).microseconds/1000000}"
    )
    min_x, max_x, min_y, max_y = get_char_bbox(im)

    # replace blue with white and white w/ black
    if max_x != 0 and max_y != 0:
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                if is_red(im[x][y]) or is_blue(im[x][y]):
                    # so change it to white-ish
                    im[x][y] = numpy.array([220, 220, 220])
                else:
                    # it's white-ish
                    im[x][y] = numpy.array([20, 20, 20])  # slightly less dark black

    im = cv2.resize(im, (0, 0), fx=2.0, fy=2.0)
    im = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)

    im = cv2.dilate(im, kernel)
    im = cv2.erode(im, kernel)

    return im


async def read_monitor_info(output_dict: dict):
    with open("./monitor.json", "r") as file:
        temp = json.load(file)
        for item, key in temp.items():
            output_dict[item] = key
        file.close()


async def read_browser_info(output_dict: dict):
    with open("./browser.json", "r") as file:
        temp = json.load(file)
        for item, key in temp.items():
            output_dict[item] = key
        file.close()


def get_text(screenshotter):
    global text, prev_text, run, prev_im
    iter = 1
    while run:
        im = capture_image(screenshotter)
        prev_im = im.copy()
        text = pytesseract.image_to_string(im)
        text = text.replace("\n", " ")

        iter += 1


prev_im = [[0]]
run = True
text = ""


async def dev_main(speed: int, num_races: int):
    global text, run
    print("starting")
    mon = {}
    browser = {}
    await asyncio.gather(read_browser_info(browser), read_monitor_info(mon))
    win32stuff.focus_window(browser["browser"])

    screenshotter = screenshot.SectionCapture(
        mon["top"], mon["left"], mon["width"], mon["height"]
    )

    a = threading.Thread(None, get_text, args=[screenshotter])
    a.start()

    races = 0

    # wait for the initial blackish screen to pass
    if is_black(prev_im[0][0]):
        await press_enter()
        while not is_white(prev_im[0][0]):
            time.sleep(0.00001)

    try:
        while races < num_races:
            type_string(text, speed)

            # if the race's over
            if is_black(prev_im[0][0]):
                races += 1
                if races < num_races:
                    await press_enter()

                    while not is_white(prev_im[0][0]):
                        time.sleep(0.00001)
        run = False
        a.join()
    except KeyboardInterrupt:
        run = False
        a.join()
    print("finished")


parser = argparse.ArgumentParser(description="Tesseract-based Autotyper")
parser.add_argument(
    "wpm", metavar="WPM", type=int, nargs=1, help="desired wpm to type at"
)
parser.add_argument(
    "num_races",
    metavar="R",
    type=int,
    nargs=1,
    help="number of races to complete",
)

args = parser.parse_args()

wpm = args.wpm[0]
num_races = args.num_races[0]

asyncio.run(dev_main(wpm, num_races))
