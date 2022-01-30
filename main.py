from datetime import datetime
import os
import time

import cv2
import mss
import numpy
import pytesseract

import win32api
import win32con

import argparse
import json

# os.system("$PYTHONPATH='C:/Program Files/Tesseract-OCR/'")
os.system("set PATH=%PATH%;C:/Program Files/Tesseract-OCR/")

CHARS_PER_WORD = 5
SECONDS_PER_MINUTE = 60


def get_acc(inp, out):
    mistakes = 0
    try:
        for i in range(len(out)):
            if inp[i] != out[i]:
                mistakes += 1
        print(f"accuracy is {(len(out)-mistakes)/len(out)}")
    except:
        pass


def get_blue_bbox(im: numpy.ndarray) -> tuple:
    min_x = max_x = min_y = max_y = 0
    defined = False
    for x in range(im.shape[0]):
        for y in range(im.shape[1]):
            if (
                im[x][y][0] > 200
                and im[x][y][1] < 200
                and im[x][y][1] > 100
                and im[x][y][2] < 100
            ):
                # it's blueish (B > 200, 100 < G < 200, R < 100)
                if not defined:
                    minx = max_x = x
                    min_y = max_y = y
                    defined = True
                else:
                    min_x = min(x, min_x)
                    max_x = max(x, max_x)
                    min_y = min(y, min_y)
                    max_y = max(y, max_y)
    return min_x, max_x, min_y, max_y


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


kernel = numpy.ones([1, 1], numpy.uint8)


def capture_image(monitor: dict):
    global kernel
    with mss.mss() as sct:
        im = numpy.asarray(sct.grab(monitor))  # im is bgr
        min_x, max_x, min_y, max_y = get_blue_bbox(im)

        # replace blue with white and white w/ black
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                if (
                    im[x][y][0] > 200
                    and im[x][y][1] < 200
                    and im[x][y][1] > 100
                    and im[x][y][2] < 100
                ):
                    # it's blueish (B > 200, 100 < G < 200, R < 100)
                    # so change it to white-ish
                    im[x][y] = im[0][0]  # the first one should be white-ish
                else:
                    # it's white-ish
                    im[x][y] = numpy.array(
                        [30, 30, 30, 255]
                    )  # slightly less dark black

        im = cv2.resize(im, (0, 0), fx=2.0, fy=2.0)

        im = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)

        im = cv2.dilate(im, kernel)
        im = cv2.erode(im, kernel)

        return im


def main(wpm: int, time_limit: int = -1):
    with open("./monitor.json", "r") as file:
        mon = json.load(file)
    start_time = datetime.now()

    while (time_limit == -1) or (datetime.now() - start_time).seconds < time_limit:
        im = capture_image(mon)
        cv2.imshow("live", im)
        text = pytesseract.image_to_string(im)

        text = text.replace("\n", " ")
        print(text)
        if cv2.waitKey(5) > 0:
            break

        # One screenshot per second
        time.sleep(1)
        type_string(text, wpm * CHARS_PER_WORD / SECONDS_PER_MINUTE)


parser = argparse.ArgumentParser(description="Tesseract-based Autotyper")
parser.add_argument(
    "wpm", metavar="WPM", type=int, nargs=1, help="desired wpm to type at"
)
parser.add_argument(
    "time_limit",
    metavar="T",
    type=int,
    nargs=1,
    help="max time to type; -1 to type forever",
)

args = parser.parse_args()

wpm = args.wpm[0]
time_limit = args.time_limit[0]
main(wpm, time_limit)
