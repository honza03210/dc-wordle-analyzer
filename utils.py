from PIL import Image
from collections import deque
from math import sqrt

neighbor4 = [(-1, 0), (1, 0), (0, 1), (0, -1)]
IMAGE_MAX = 255
MAX_PLAYERS = 15

def shift(image: Image.Image, offset: int = -1, cut_max = True):
    image = image.copy()
    for y in range(image.height):
        for x in range(image.width):
            image.putpixel((x, y), min(254 if cut_max else 255, max(0, image.getpixel((x, y)) + offset)))

    return image
    

def flood_fill(image: Image.Image, x: int, y: int, expected: int, substitute: int, tolerance: int, background: list[tuple[int, int]]) -> Image.Image | None:
    image = image.copy()
    q = deque()

    if image.getpixel((x, y)) < expected + tolerance and image.getpixel((x, y)) > expected - tolerance:
        q.append((x, y))
        background.append((x, y))
        image.putpixel((x, y), substitute)
    else:
        return None
    
    while len(q) > 0:
        (curr_x, curr_y) = q.pop()
        for (ix, iy) in neighbor4:
            if curr_x + ix < 0 or curr_x + ix >= image.width or curr_y + iy < 0 or curr_y + iy >= image.height:
                continue
            if image.getpixel((curr_x + ix, curr_y + iy)) < expected + tolerance and image.getpixel((curr_x + ix, curr_y + iy)) > expected - tolerance:
                q.append((curr_x + ix, curr_y + iy))
                background.append((curr_x + ix, curr_y + iy))
                image.putpixel((curr_x + ix, curr_y + iy), substitute)
    return image

def erode(image: Image.Image, radius: int):
    image_copy = image.copy()
    for y in range(image.height):
        for x in range(image.width):
            for iy in range(-radius, radius + 1):
                for ix in range(-radius, radius + 1):
                    if sqrt(iy * iy + ix * ix) >= radius:
                        continue
                    if (x + ix) >= 0 and (x + ix) < image.width and (y + iy) < image.height and (y + iy) >= 0 and \
                            image.getpixel((x + ix, y + iy)) == 255:
                        image_copy.putpixel((x, y), 255)
    return image_copy

def analyze_section_bounding_box(image: Image.Image, x: int, y: int, section_index: int) -> tuple[tuple[int, int]]:
    max_x = x
    min_x = x
    max_y = y
    min_y = y
    q = deque()
    q.append((x, y))
    image.putpixel((x, y), section_index)


    while len(q) > 0:
        (curr_x, curr_y) = q.pop()
        for (ix, iy) in neighbor4:
            if curr_x + ix < 0 or curr_x + ix >= image.width or curr_y + iy < 0 or curr_y + iy >= image.height:
                continue
            if image.getpixel((curr_x + ix, curr_y + iy)) != 255 and image.getpixel((curr_x + ix, curr_y + iy)) > MAX_PLAYERS:
                q.append((curr_x + ix, curr_y + iy))
                max_x = max(max_x, curr_x + ix)
                min_x = min(min_x, curr_x + ix)
                max_y = max(max_y, curr_y + iy)
                min_y = min(min_y, curr_y + iy)
                image.putpixel((curr_x + ix, curr_y + iy), section_index)
    return ((min_x, min_y), (max_x, max_y))

def bounding_boxes(image: Image.Image, background: int = 255) -> list[tuple[tuple[int, int]]]:
    image = shift(image, MAX_PLAYERS, False)
    bbs: list[tuple[tuple[int, int]]] = []
    for y in range(image.height):
        for x in range(image.width):
            if (image.getpixel((x, y)) != 255 and image.getpixel((x, y)) > MAX_PLAYERS):
                bbs.append(analyze_section_bounding_box(image, x, y, len(bbs)))
    return bbs

def check_section_win(image: Image.Image, bot_right: tuple[int, int], top_left: tuple[int, int], green_to_grey: int = 115):
    for y in range(bot_right[1], top_left[1] - 1, -1):
        green_chunks = 0
        inside_span = 0
        for x in range(top_left[0], bot_right[0] + 1):
            if image.getpixel((x, y)) == 115:
                inside_span += 1
            else:
                if inside_span > 5:
                    green_chunks += 1
                inside_span = 0
        if green_chunks >= 5:
            return True
    return False


if __name__ == "__main__":
    im = Image.open("1false.png")
    im = im.convert("L")
    background = []
    im = shift(im)
    im = flood_fill(im, 0, 0, 20, 255, 1, background)
    im = erode(im, 5)
    im_copy = im.copy()
    bbs = bounding_boxes(im_copy, 255)
    for bb in bbs:
        print(check_section_win(im, bb[1], bb[0]))