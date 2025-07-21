from PIL import Image
from collections import deque
from math import sqrt
import os

neighbor4 = [(-1, 0), (1, 0), (0, 1), (0, -1)]
IMAGE_MAX = 255
MAX_PLAYERS = 15


GIF_IMAGES = []

"""
Shifts all pixels in the image by offset (new = old + offset)
"""


def shift(image: Image.Image, offset: int = -1, cut_max=True) -> Image.Image:
    image = image.copy()
    for y in range(image.height):
        for x in range(image.width):
            image.putpixel(
                (x, y),
                min(
                    254 if cut_max else IMAGE_MAX,
                    max(0, image.getpixel((x, y)) + offset),
                ),
            )

    return image


"""
Fills all the pixels of color 'expected' (with a +- 'tolerance') with 'substitute' color, adds all filled pixels into 'background' list
"""


def flood_fill(
    image: Image.Image,
    x: int,
    y: int,
    expected: int,
    substitute: int,
    tolerance: int,
    background: list[tuple[int, int]],
) -> Image.Image | None:
    image = image.copy()
    q = deque()

    if (
        image.getpixel((x, y)) >= expected + tolerance
        or image.getpixel((x, y)) <= expected - tolerance
    ):
        expected = image.getpixel((x, y))

    if expected <= substitute + tolerance and expected >= substitute - tolerance:
        return image

    q.append((x, y))
    background.append((x, y))
    image.putpixel((x, y), substitute)

    while len(q) > 0:
        (curr_x, curr_y) = q.pop()
        for ix, iy in neighbor4:
            if (
                curr_x + ix < 0
                or curr_x + ix >= image.width
                or curr_y + iy < 0
                or curr_y + iy >= image.height
            ):
                continue
            p_val = image.getpixel((curr_x + ix, curr_y + iy))
            if (
                p_val < expected + tolerance
                and p_val > expected - tolerance
                and p_val != substitute
            ):
                q.append((curr_x + ix, curr_y + iy))
                background.append((curr_x + ix, curr_y + iy))
                image.putpixel((curr_x + ix, curr_y + iy), substitute)
    return image


"""
Erosion operation with circular convolution kernel of 'radius'
"""


def erode(
    image: Image.Image,
    radius: int,
    top_left: tuple[int, int] | None = None,
    bot_right: tuple[int, int] | None = None,
) -> Image.Image:
    image_copy = image.copy()
    if not top_left or not bot_right:
        top_left = (0, 0)
        bot_right = (image.width - 1, image.height - 1)
    for y in range(top_left[1], bot_right[1]):
        for x in range(top_left[0], bot_right[0]):
            for iy in range(-radius, radius + 1):
                for ix in range(-radius, radius + 1):
                    if sqrt(iy * iy + ix * ix) >= radius:
                        continue
                    if (
                        (x + ix) >= 0
                        and (x + ix) < image.width
                        and (y + iy) < image.height
                        and (y + iy) >= 0
                        and image.getpixel((x + ix, y + iy)) == IMAGE_MAX
                    ):
                        image_copy.putpixel((x, y), IMAGE_MAX)
    return image_copy


"""
Close operation with circular convolution kernel of 'radius'
"""


def morf_close(
    image: Image.Image,
    radius: int,
    top_left: tuple[int, int] | None = None,
    bot_right: tuple[int, int] | None = None,
) -> Image.Image:
    image_copy = image.copy()
    if not top_left or not bot_right:
        top_left = (0, 0)
        bot_right = (image.width - 1, image.height - 1)
    for y in range(top_left[1], bot_right[1]):
        for x in range(top_left[0], bot_right[0]):
            min_pix_val = IMAGE_MAX
            for iy in range(-radius, radius + 1):
                for ix in range(-radius, radius + 1):
                    if sqrt(iy * iy + ix * ix) >= radius:
                        continue
                    if (
                        (x + ix) >= 0
                        and (x + ix) < image.width
                        and (y + iy) < image.height
                        and (y + iy) >= 0
                    ):
                        min_pix_val = min(image.getpixel((x + ix, y + iy)), min_pix_val)
            image_copy.putpixel((x, y), min_pix_val)
    return image_copy


"""
floods a 4-connected section, returns bounding box
"""


def analyze_section_bounding_box(
    image: Image.Image, x: int, y: int, section_index: int
) -> tuple[tuple[int, int]]:
    max_x = x
    min_x = x
    max_y = y
    min_y = y
    q = deque()
    q.append((x, y))
    image.putpixel((x, y), section_index)
    while len(q) > 0:
        (curr_x, curr_y) = q.pop()
        for ix, iy in neighbor4:
            if (
                curr_x + ix < 0
                or curr_x + ix >= image.width
                or curr_y + iy < 0
                or curr_y + iy >= image.height
            ):
                continue
            if (
                image.getpixel((curr_x + ix, curr_y + iy)) != IMAGE_MAX
                and image.getpixel((curr_x + ix, curr_y + iy)) > MAX_PLAYERS
            ):
                q.append((curr_x + ix, curr_y + iy))
                max_x = max(max_x, curr_x + ix)
                min_x = min(min_x, curr_x + ix)
                max_y = max(max_y, curr_y + iy)
                min_y = min(min_y, curr_y + iy)
                image.putpixel((curr_x + ix, curr_y + iy), section_index)
    return ((min_x, min_y), (max_x, max_y))


"""
Explores the whole image, looking for unexplored sections, returns list of bounding boxes
"""


def bounding_boxes(
    image: Image.Image,
    top_left: tuple[int, int] = (0, 0),
    bottom_right: tuple[int, int] | None = None,
    background: int = IMAGE_MAX,
) -> list[tuple[tuple[int, int]]]:
    if not bottom_right:
        bottom_right = (image.width - 1, image.height - 1)
    image = shift(image, MAX_PLAYERS, False)
    bbs: list[tuple[tuple[int, int]]] = []
    for y in range(top_left[1], bottom_right[1]):
        for x in range(top_left[0], bottom_right[0]):
            if (
                image.getpixel((x, y)) != background
                and image.getpixel((x, y)) > MAX_PLAYERS
            ):
                bbs.append(analyze_section_bounding_box(image, x, y, len(bbs)))
                # will pop if the bb is around a small artifact
                if (
                    abs(bbs[-1][0][0] - bbs[-1][1][0])
                    * abs(bbs[-1][0][1] - bbs[-1][1][1])
                    < 30
                ):
                    bbs.pop()
    return bbs


"""
Checks whether there is a winning configuration (5 green squares) in a section
"""


def check_section_win(
    image: Image.Image,
    bot_right: tuple[int, int],
    top_left: tuple[int, int],
    green_to_grey: int = 115,
) -> bool:
    for y in range(bot_right[1], top_left[1] - 1, -1):
        green_chunks = 0
        inside_span = 0
        for x in range(top_left[0], bot_right[0] + 1):
            if image.getpixel((x, y)) == green_to_grey:
                inside_span += 1
            else:
                if inside_span > 5:
                    green_chunks += 1
                inside_span = 0
        if green_chunks >= 5:
            return True
    return False


"""
gets the center of an object, then finds an edge pixel closest and furthest from it, returns min_dist / max_dist
"""


def roundness(
    image: Image.Image, bot_right: tuple[int, int], top_left: tuple[int, int]
) -> float:
    sum_x = 0
    sum_y = 0
    count = 0
    edges = []
    for y in range(bot_right[1], top_left[1] - 1, -1):
        for x in range(top_left[0], bot_right[0] + 1):
            if image.getpixel((x, y)) != IMAGE_MAX:
                sum_x += x
                sum_y += y
                count += 1
                edge = False
                for ix, iy in neighbor4:
                    if (
                        x + ix < 0
                        or x + ix >= image.width
                        or y + iy < 0
                        or y + iy >= image.height
                    ):
                        continue
                    if image.getpixel((x + ix, y + iy)) != image.getpixel((x, y)):
                        edge = True
                if edge:
                    edges.append((x, y))

    center = (sum_x / count, sum_y / count)

    max_dist = 0
    min_dist = 10000
    for edge_pixel in edges:
        dist = (edge_pixel[0] - center[0]) ** 2 + (edge_pixel[1] - center[1]) ** 2
        max_dist = max(max_dist, dist)
        min_dist = min(min_dist, dist)

    return min_dist / max_dist


"""
computes r, g, b average values for the given pixels
"""


def get_pixel_stats(
    image: Image.Image, pixels: list[tuple[int, int]]
) -> tuple[int, int, int]:
    red = 0
    green = 0
    blue = 0
    im: Image.Image = image.convert("RGB")
    for pixel in pixels:
        r, g, b = im.getpixel(pixel)
        red += r
        green += g
        blue += b
    red /= len(pixels)
    green /= len(pixels)
    blue /= len(pixels)

    return red, green, blue


"""
Flood fills the background of the single segment, erodes small artifacts, closes all the gaps (makes a single object
from the squares of the playthrough), creates a mask, then decides what mask is rounder => the pfp location
returns the pixels of the pfp mask
"""


def get_pfp_pixels(
    image: Image.Image, bot_right: tuple[int, int], top_left: tuple[int, int]
) -> list[tuple[int, int]]:
    image = image.copy()
    GIF_IMAGES.append(image.copy())
    image = flood_fill(image, bot_right[0] - 20, bot_right[1] - 2, 30, IMAGE_MAX, 1, [])
    GIF_IMAGES.append(image.copy())
    image = erode(image, 3, top_left, bot_right)
    GIF_IMAGES.append(image.copy())
    image = morf_close(image, 5, top_left, bot_right)
    GIF_IMAGES.append(image.copy())
    for y in range(image.height):
        for x in range(image.width):
            if image.getpixel((x, y)) != IMAGE_MAX:
                image.putpixel((x, y), 100)
    GIF_IMAGES.append(image.copy())
    bbs = bounding_boxes(image, top_left, bot_right)
    max_round = (0, bbs[0])
    for bb in bbs:
        r = roundness(image, bb[1], bb[0])
        if r > max_round[0]:
            max_round = (r, bb)
    pfp_pixels = []
    for y in range(max_round[1][0][1], max_round[1][1][1] + 1):
        for x in range(max_round[1][0][0], max_round[1][1][0] + 1):
            if image.getpixel((x, y)) != IMAGE_MAX:
                pfp_pixels.append((x, y))

    return pfp_pixels


"""
computes color averages for pfps saved in ./players/
"""


def get_players_pixel_stats():
    player_pfp_stats: dict[str : tuple[float, float, float]] = {}
    path = "./players/"
    files = os.listdir(path)

    # Print the files
    for file in files:
        # print(f"started {file}")
        im_orig = Image.open(path + file)
        im = im_orig.convert("L")
        im = shift(im)
        im = flood_fill(im, 0, 0, 20, IMAGE_MAX, 1, [])
        im_copy = im.copy()
        bbs = bounding_boxes(im_copy)
        player_pfp_stats[file] = get_pixel_stats(
            im_orig, get_pfp_pixels(im, bbs[0][1], bbs[0][0])
        )
        print(f"'{file}': {player_pfp_stats[file]},")
    return player_pfp_stats


"""
Finds the closest match to given color average
"""


def match_similar_pfp(
    players_pfp_stats: dict[str : tuple[float, float, float]],
    to_match: tuple[float, float, float],
):
    best_guess = ("Unknown", 999999999)
    for name, (r, g, b) in players_pfp_stats.items():
        # print(f"'{name}'= ({r}, {g}, {b})")
        diff = (to_match[0] - r) ** 2 + (to_match[1] - g) ** 2 + (to_match[2] - b) ** 2
        if diff < best_guess[1]:
            best_guess = name, diff
    return best_guess


if __name__ == "__main__":
    # computes the color characteristics of pfps in players dir
    # players_pfp_stats = get_players_pixel_stats()

    # precomputed to save time
    players_pfp_stats = {
        "vojto.png": (133.94788506157417, 147.28466892736034, 132.4917008745315),
        "dart.png": (90.25311475409836, 85.65803278688524, 84.5583606557377),
        "kalista.png": (68.59580224645404, 60.30564893006477, 60.482413708288924),
        "codee.png": (128.39014813492773, 100.0146350169552, 47.477244333392825),
        "honza.png": (6.854538956397427, 4.610257326661902, 23.32880629020729),
        "dacia.png": (162.96234160271283, 161.2764590398001, 138.93842584329823),
        "alien.png": (37.858724772280766, 26.381496695838543, 17.59385604572245),
        "techno.png": (127.09064830751578, 174.90549954921727, 186.597983771822),
        "joy.png": (210.96698197394252, 183.62216669641265, 181.03551668748884),
    }

    im_orig = Image.open("./tests/9players.png")
    GIF_IMAGES.append(im_orig.copy())
    im = im_orig.convert("L")
    GIF_IMAGES.append(im.copy())
    im = shift(im)  # makes space for IMAGE_MAX to be unique value as the background
    im = flood_fill(im, 0, 0, 20, IMAGE_MAX, 1, [])  # fills the background
    GIF_IMAGES.append(im.copy())
    im = erode(im, 3)  # removes smaller artifacts (floating title text)
    im_copy = im.copy()
    GIF_IMAGES.append(im.copy())
    bbs = bounding_boxes(
        im_copy
    )  # these are the bounding boxes of segments with pfp and playthrough
    for bb in bbs:
        win = check_section_win(
            im, bb[1], bb[0]
        )  # checks for 5 green squares in the bounding box
        stats = get_pixel_stats(
            im_orig, get_pfp_pixels(im, bb[1], bb[0])
        )  # separates pixels of the pfp and analysis average colors
        print(
            f"{match_similar_pfp(players_pfp_stats, stats)[0][:-4]} "
            + ("SOLVED" if win else "NOT solved")
        )

    GIF_IMAGES[0].save(
        "wow.gif",
        save_all=True,
        append_images=GIF_IMAGES[1:],
        optimize=False,
        duration=1000,
        loop=0,
    )
