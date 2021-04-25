from colormath.color_objects import HSLColor, ColorBase, sRGBColor
from colormath.color_conversions import convert_color
from PIL import ImageColor


def relative_rgb_field(rgb: float):
    """https://www.w3.org/TR/WCAG20/#relativeluminancedef"""
    if rgb <= 0.03928:
        return rgb / 12.92
    else:
        return ((rgb + 0.055) / 1.055) ^ 2.4


def get_relative_luminosity(color: ColorBase) -> float:
    """https://www.w3.org/TR/WCAG20/#relativeluminancedef"""
    rgb_color: sRGBColor = convert_color(color, sRGBColor)
    return 0.2126 * rgb_color.rgb_r + 0.7152 * rgb_color.rgb_g + 0.0722 * rgb_color.rgb_b


def contrast(color1: ColorBase, color2: ColorBase):
    """http://www.w3.org/TR/WCAG20/#contrast-ratiodef"""
    lum1 = get_relative_luminosity(color1)
    lum2 = get_relative_luminosity(color2)
    if lum1 > lum2:
        return (lum1 + 0.05) / (lum2 + 0.05)

    return (lum2 + 0.05) / (lum1 + 0.05)


def from_hex_color_string(hex_color_string: str) -> sRGBColor:
    return sRGBColor(*[x / 255.0 for x in ImageColor.getcolor(hex_color_string, "RGB")])


ColorBase.contrast = contrast
ColorBase.from_hex_color_string = from_hex_color_string
