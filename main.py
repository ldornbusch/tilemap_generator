import argparse
import timeit
import tile_converter


# todo: provide existing tile_set file(add new tiles to it?)


def tilesize(value):
    if value.lower().find("x") == -1:
        raise argparse.ArgumentTypeError("'{}': You need to separate width and height with an 'x' ".format(value))
    if len(value.lower().split("x")) != 2:
        raise argparse.ArgumentTypeError("'{}': please specify only 2 values separated by an 'x' ".format(value))
    try:
        test = value.lower().split("x")
        test = list(map(int, test))
    except ValueError:
        raise argparse.ArgumentTypeError("'{}': please specify  2 integer values separated by an 'x' ".format(value))
    return value


def hexcolor(value):
    if not len(value) in [3, 6]:
        raise argparse.ArgumentTypeError(
            "'{}' is not a valid hex color. "
            "Please use a 3 or 6 digit hexadecimal [0-9A-F] number ".format(value))
    try:
        test = int(value, 16)
    except ValueError:
        raise argparse.ArgumentTypeError(
            "'{}' is not a valid hex color."
            " Please use only hexadecimal  [0-9A-Fa-f] characters ".format(value))
    return test


parser = argparse.ArgumentParser(description='create atilemap from an image by cutting it into equal spaced tiles.'
                                             'Tileset and .tmx map file for Tiled will be stored on same path '
                                             'as the input image.')
parser.add_argument('image_path', help='The Image(path) to be tiled')
parser.add_argument('--tiles', '-t', dest='tiles', type=tilesize, default="16x16",
                    help='Tilesize to be used (eg 8x8, 16x4, etc) for'
                         ' tiling the image (default is \'16x16\').')
parser.add_argument('--color', '-c', dest='color', type=hexcolor, default="ff00ff",
                    help='the color (in 3 or 6 digit hexcode) which is regarded as transparent(default is \'ff00ff\').')
args = parser.parse_args()

img_path = args.image_path
tile_spec = args.tiles
color = args.color

start = timeit.default_timer()
tiles = tile_spec.lower().split("x")
tiles = list(map(int, tiles))
tile_converter.extract_tiles(img_path, tiles, color)
end = timeit.default_timer()
print("%.2f sec." % (end - start))
