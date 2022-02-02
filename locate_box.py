import json
from time import sleep
import tkinter
import numpy
from tqdm import tqdm

from screenshot import SectionCapture
from win32stuff import focus_window


def get_full_monitor():
    root = tkinter.Tk()
    max_width = root.winfo_screenwidth()
    max_height = root.winfo_screenheight()
    del root

    mon = {"top": 0, "left": 0, "width": max_width, "height": max_height}
    return mon


def is_white(pixel):
    return pixel[0] > 220 and pixel[1] > 220 and pixel[2] > 220


def get_typing_screen(im):
    SKIP_SIZE = 2
    top_x = top_y = 0
    span_x = span_y = 0

    y = 0
    for x in tqdm(range(im.shape[0])):
        y = 0
        while y < im.shape[1]:
            if is_white(im[x][y]):
                temp_span_x = 0
                temp_span_y = 0
                while x + SKIP_SIZE < im.shape[0] and is_white(im[x + SKIP_SIZE][y]):
                    x += SKIP_SIZE
                    temp_span_x += SKIP_SIZE
                while y + SKIP_SIZE < im.shape[1] and is_white(im[x][y + SKIP_SIZE]):
                    y += SKIP_SIZE
                    temp_span_y += SKIP_SIZE
                if (
                    temp_span_x * temp_span_y > span_x * span_y
                    and temp_span_y < im.shape[1] * 0.75
                    and temp_span_x > 100
                ):
                    # the text box can't be more than 75% of the screen's width
                    # the text box must be at least 50 px tall
                    span_x, span_y = temp_span_x, temp_span_y
                    top_x, top_y = x - temp_span_x, y - temp_span_y
            y += 1

    if span_x < 100:
        return None
    return top_x, top_y, span_x, span_y


print(
    "Starting to locate the typing box. Please be on your Nitro-Type screen"
    " and have the white typing area visible."
)

full_monitor = get_full_monitor()
sct = SectionCapture(
    full_monitor["top"],
    full_monitor["left"],
    full_monitor["width"],
    full_monitor["height"],
)
with open("./browser.json", "r") as file:
    browser = json.load(file)
    focus_window(browser['browser'])
    file.close()
while True:
    im = numpy.asarray(sct.get_screenshot())
    new_mon = get_typing_screen(im)
    if new_mon is not None:
        break
    print("Please be on your nitro-type screen!")
    print("will try to locate the text box again in 3 seconds.")
    sleep(3)

with open("./monitor.json", "w") as file:
    monitor_settings = {
        "top": new_mon[0],
        "left": new_mon[1],
        "height": new_mon[2],
        "width": new_mon[3],
    }
    json.dump(monitor_settings, file)
    file.close()

print(
    "Finished locating box. Don't move the nitrotype window without re-running"
    " locate_box.py"
)
