from PIL import Image
import importlib.resources as resources
import pyautogui
from .properties import *

arrow_icons = []
arrow_subicons = []
properties = Properties()


def load_textures(resolution: str) -> None:
    assets_root = resources.files(__package__).joinpath("assets")
    for arrow in Arrow:
        arrow_texture = Image.open(assets_root / resolution / f"{arrow.name}.png")
        arrow_icons.append(arrow_texture)


def generate_icon_subregions(icon_index) -> Image:
    icon_size = arrow_icons[icon_index].size
    # Pair of number of columns and rows to split into
    x_sub_regions, y_sub_regions = 3, 3
    sub_region_width = icon_size[0] / x_sub_regions
    sub_region_height = icon_size[1] / y_sub_regions

    for x in range(0, x_sub_regions):
        for y in range(0, y_sub_regions):
            # Area of new subicon
            bounds = (
                x * sub_region_width,
                y * sub_region_height,
                (x * sub_region_width) + sub_region_width,
                (y * sub_region_height) + sub_region_width
            )
            yield arrow_icons[icon_index].crop(bounds)


def generate_subicons() -> None:
    for arrow in Arrow:
        sub_icons = []
        for sub_icon in generate_icon_subregions(arrow.value):
            # Allows for reading color data from each pixel
            sub_icon = sub_icon.convert("RGBA")

            for pixel in Image.Image.getdata(sub_icon):
                # Pixel is empty if its alpha component is zero
                if pixel[3] == 0:
                    break
            else:
                # Adds sub icon to array if doesn't contain transparent pixels
                sub_icons.append(sub_icon)
        if sub_icons:
            arrow_subicons.append(sub_icons)


def remove_duplicate_subicons() -> None:
    for arrow1 in Arrow:
        for arrow2 in Arrow:
            # Ensures same arrow icons aren't being compared
            if arrow1.value == arrow2.value:
                continue

            for i, sub_icon in enumerate(arrow_subicons[arrow2.value]):
                icon_bounds = locate(sub_icon, arrow_icons[arrow1.value])

                # Removes subicon if it can be found in a different character
                if icon_bounds is not None:
                    arrow_subicons[arrow2.value].pop(i)


def get_screenshot() -> Image:
    screenshot = pyautogui.screenshot(region=properties.screen)
    size = screenshot.size
    scale = properties.screen_scale

    # Scales image to match original size
    return screenshot.resize((int(size[0]) / scale, int(size[1]) / scale), Image.NEAREST)


def locate(sub_image, base_image, confidence=0.95):
    return pyautogui.locate(sub_image, base_image, confidence=confidence)
