import os.path
import math
from PIL import Image

# todo: better tile sort for easier reuse
# todo: command line interface
# todo: output time needed

img_path = r"tom_c16_map.gif"
# img_path = r"850_gamemap2.png"
# img_path = r"894_gamemap3.png"
# img_path = r"894_gamemap5.png"
tiles = (8, 8)
color = "ff00ff"


def extract_tiles(str_img_path, tile_size, transparent_color="ff00ff"):
    str_path = os.path.dirname(str_img_path)
    str_filename = os.path.basename(str_img_path)
    str_suffix = str_filename[str_filename.find("."):]
    str_subject = str_filename.replace(str_suffix, "")

    img = Image.open(str_img_path)
    print(img.format, img.size, img.mode)
    print("image size: " + str(img.size))
    print("tile size:  " + str(tile_size))
    print("atlas  size:" + str((img.width // tile_size[0], img.height // tile_size[1])))

    all_tile_img, tile_atlas = deduplicate_tiles(img, tile_size)

    catalog_size, tile_set = assemble_tileset(all_tile_img, img, tile_size)

    catalog_filename = os.path.join(str_path, str_subject + "_catalog" + str_suffix)
    tile_set.save(catalog_filename, palette=img.getpalette())
    print("Number of unique tiles:" + str(len(all_tile_img)))

    tiles_per_column = img.width // tile_size[0]
    tiles_per_row = img.height // tile_size[1]
    tilemap_data = generate_tilemap_data(tile_atlas, (tiles_per_row,tiles_per_column))

    tiled_file = """<?xml version="1.0" encoding="UTF-8"?>
<map version="1.2" tiledversion="1.3.3" orientation="orthogonal" renderorder="right-down" 
width="%(width)i" height="%(height)i" tilewidth="%(tilewidth)i" tileheight="%(tileheight)i" 
infinite="0" nextlayerid="2" nextobjectid="1">
 <tileset firstgid="1" name="%(tileset_name)s" tilewidth="%(tilewidth)i" tileheight="%(tileheight)i" 
  tilecount="%(tilecount)i" columns="%(columns)i" backgroundcolor="#000000">
  <image source="%(catalog_file)s" trans="%(transparent)s" width="%(catalog_width)i" height="%(catalog_height)i"/>
 </tileset>
 <layer id="1" name="Tile Layer 1" width="%(width)i" height="%(height)i">
  <data encoding="csv">
%(atlas_data)s
</data>
 </layer>
</map>
""" % {"width": img.width // tile_size[0],
       "height": img.height // tile_size[1],
       "tilewidth": tile_size[0],
       "tileheight": tile_size[1],
       "tileset_name": str_subject,
       "tilecount": len(all_tile_img),
       "columns": catalog_size,
       "catalog_file": catalog_filename,
       "transparent": transparent_color,
       "catalog_width": catalog_size * tile_size[0],
       "catalog_height": catalog_size * tile_size[1],
       "atlas_data": tilemap_data}
    map_filename = os.path.join(str_path, str_subject + ".tmx")
    f = open(map_filename, "w")
    f.write(tiled_file)
    f.close()


def generate_tilemap_data(tile_atlas, tile_count):
    atlas_data = ""
    for row in range(tile_count[0]):
        accu_row = ""
        for col in range(tile_count[1]):
            index = row * tile_count[1] + col
            accu_row += format("%d, " % tile_atlas[index])
        atlas_data += accu_row + "\n"
    atlas_data = atlas_data[:-3]
    return atlas_data


def assemble_tileset(all_tile_img, img, tile_size):
    catalog_size = math.ceil(math.sqrt(len(all_tile_img)))
    tile_catalog = Image.new(img.mode, (catalog_size * tile_size[0], catalog_size * tile_size[1]))
    index = 0
    for tile_img in all_tile_img:
        tmp = tile_img.copy()
        tile_catalog.paste(tmp,
                           ((index % catalog_size) * tile_size[0],
                            (index // catalog_size) * tile_size[1]))
        index += 1
    return catalog_size, tile_catalog


def deduplicate_tiles(img, tile_size):
    all_tiles = {}  # hashmap of (str(tile) -> index)
    all_tiles_imgs = []  # list of tiles
    tile_atlas = []  # indexes to tiles
    imgdata = img.getdata()
    for ty in range(img.height // tile_size[1]):
        for tx in range(img.width // tile_size[0]):
            tile_data = []
            for py in range(tile_size[1]):
                for px in range(tile_size[0]):
                    abs_x = tx * tile_size[0] + px
                    abs_y = ty * tile_size[1] + py
                    # a += imgdata[abs_x+abs_y*img.width]
                    pixel = img.getpixel((abs_x, abs_y))
                    tile_data.append(pixel)
            str_tile_data = str(tile_data)
            if str_tile_data not in all_tiles:
                all_tiles_imgs.append(img.crop((tx * tile_size[0],
                                                ty * tile_size[1],
                                                tx * tile_size[0] + tile_size[0],
                                                ty * tile_size[1] + tile_size[1])))
                all_tiles[str_tile_data] = len(all_tiles_imgs)
            tile_atlas.append(all_tiles[str_tile_data])
    return all_tiles_imgs, tile_atlas


extract_tiles(img_path, tiles, color)
