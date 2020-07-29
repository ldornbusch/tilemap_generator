import os.path
import math
import timeit
from PIL import Image
from PIL import ImageDraw

# progress: better tile sort for easier reuse
# todo: command line interface

img_path = r"tom_c16_map.gif"
# img_path = r"850_gamemap2.png"
# img_path = r"894_gamemap7.png"
# img_path = r"894_gamemap5.png"
# img_path = r"894_gamemap3.png"
# img_path = r"894_gamemap14.png"
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
    print("map  size:" + str((img.width // tile_size[0], img.height // tile_size[1])))

    tileset_size = [img.width // tile_size[0], img.height // tile_size[1]]

    all_tile_img, tile_atlas, tileset_map = deduplicate_tiles(img, tile_size)

    del_lines = []
    for y in reversed(range(tileset_size[1])):
        accu = 0
        for x in range(tileset_size[0]):
            accu += tileset_map[y*tileset_size[0]+x]
        if accu == 0:
            del_lines.append(y)

    del_cols = []
    for x in reversed(range(tileset_size[0])):
        accu = 0
        for y in reversed(range(tileset_size[1])):
            accu += tileset_map[y*tileset_size[0]+x]
        if accu == 0:
            del_cols.append(x)

    for y in del_lines:
        for x in reversed(range(tileset_size[0])):
            tileset_map.pop(y*tileset_size[0]+x)
        tileset_size[1] = tileset_size[1] - 1

    for x in del_cols:
        for y in reversed(range(tileset_size[1])):
            tileset_map.pop(y*tileset_size[0]+x)
        tileset_size[0] = tileset_size[0] - 1
    print("optimized tileset_size:"+str(tileset_size))

    catalog_size, tile_set, tile_mapping = assemble_tileset(all_tile_img, img, tile_size, tileset_map, tileset_size)

    catalog_filename = os.path.join(str_path, str_subject + "_catalog" + str_suffix)
    # tile_set.save(catalog_filename, palette=img.getpalette())
    tile_set.save(catalog_filename, palette=img.getpalette())
    print("Number of unique tiles:" + str(len(all_tile_img)))

    tiles_per_column = img.width // tile_size[0]
    tiles_per_row = img.height // tile_size[1]
    tilemap_data = generate_tilemap_data(tile_atlas, tile_mapping, (tiles_per_row, tiles_per_column))

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
       "columns": catalog_size[0],
       "catalog_file": catalog_filename,
       "transparent": transparent_color,
       "catalog_width": catalog_size[0] * tile_size[0],
       "catalog_height": catalog_size[1] * tile_size[1],
       "atlas_data": tilemap_data}
    map_filename = os.path.join(str_path, str_subject + ".tmx")
    f = open(map_filename, "w")
    f.write(tiled_file)
    f.close()


def generate_tilemap_data(tile_atlas, tile_mapping, tile_count):
    atlas_data = ""
    for row in range(tile_count[0]):
        accu_row = ""
        for col in range(tile_count[1]):
            index = row * tile_count[1] + col
            accu_row += format("%d, " % (tile_mapping[tile_atlas[index]]+1))
        atlas_data += accu_row + "\n"
    atlas_data = atlas_data[:-3]
    return atlas_data


def assemble_tileset(all_tile_img, img, tile_size, tileset_map, tileset_size):
    tile_mapping = {}
    tile_catalog = Image.new(img.mode, (tileset_size[0] * tile_size[0], tileset_size[1] * tile_size[1]))
    for y in range(tileset_size[1]):
        for x in range(tileset_size[0]):
            img_id = tileset_map[y * tileset_size[0] + x]
            if img_id != 0:
                tile_mapping[img_id] = y * tileset_size[0] + x
                tmp = all_tile_img[img_id - 1].copy()
                tile_catalog.paste(tmp, (x * tile_size[0], y * tile_size[1]))

    return tileset_size, tile_catalog, tile_mapping


def deduplicate_tiles(img, tile_size):
    all_tiles = {}  # hashmap of (str(tile) -> index)
    all_tiles_imgs = []  # list of tiles
    tile_atlas = []  # indexes to tiles
    img_tile_atlas = []  # indexes to tiles in secondary image atlas (for better reordering)
    imgdata = img.getdata()
    for ty in range(img.height // tile_size[1]):
        for tx in range(img.width // tile_size[0]):
            tile_data = []
            for py in range(tile_size[1]):
                for px in range(tile_size[0]):
                    abs_x = tx * tile_size[0] + px
                    abs_y = ty * tile_size[1] + py
                    pixel = imgdata[abs_x+abs_y*img.width]
                    tile_data.append(pixel)
            str_tile_data = str(tile_data)
            if str_tile_data not in all_tiles:
                all_tiles_imgs.append(img.crop((tx * tile_size[0],
                                                ty * tile_size[1],
                                                tx * tile_size[0] + tile_size[0],
                                                ty * tile_size[1] + tile_size[1])))
                all_tiles[str_tile_data] = len(all_tiles_imgs)
                img_tile_atlas.append(len(all_tiles_imgs))
            else:
                img_tile_atlas.append(0)
            tile_atlas.append(all_tiles[str_tile_data])
    return all_tiles_imgs, tile_atlas, img_tile_atlas


start = timeit.default_timer()
extract_tiles(img_path, tiles, color)
end = timeit.default_timer()
print("%.2f sec." % (end - start))
