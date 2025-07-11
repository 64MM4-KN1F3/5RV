#!/usr/bin/env python
import sys
from PIL import Image

def print_palette_section(title, indices, palette):
    """Prints a formatted section for a list of palette indices."""
    print("\n" + "="*60)
    print(title)
    print("="*60)
    if not indices:
        print("  (No indices found for this group)")
    else:
        for index in indices:
            if (index * 3) < len(palette):
                r, g, b = palette[index*3 : index*3+3]
                color_swatch = f"\x1b[48;2;{r};{g};{b}m  \x1b[0m"
                print(f"  Index {index:3}: ({r:3}, {g:3}, {b:3}) {color_swatch}")
    print("="*60 + "\n")

def get_manual_key_indices(image, coordinates):
    """
    Gets palette indices from a list of manually specified coordinates.
    """
    print("Sampling colors from manually specified coordinates...")
    key_indices = []
    y = coordinates['y']
    for x in coordinates['x']:
        if 0 <= x < image.width and 0 <= y < image.height:
            index = image.getpixel((x, y))
            if index not in key_indices:
                key_indices.append(index)
    
    print(f"--> Detected radar key colors at indices: {key_indices}")
    return key_indices

def filter_image(input_path="bom_radar.gif", output_path="bom_radar_filtered.gif"):
    try:
        image = Image.open(input_path)
    except FileNotFoundError:
        print(f"Error: Input file not found at '{input_path}'")
        sys.exit(1)

    if image.mode != 'P':
        print("Error: Image is not a paletted image (mode 'P').")
        sys.exit(1)

    original_palette = image.getpalette()
    if not original_palette:
        print("Error: Could not retrieve palette from image.")
        sys.exit(1)
        
    # --- Manually specified coordinates for the radar key ---
    manual_coords = {
        'y': 428,
        'x': [104, 125, 143, 163, 184, 203, 224, 243, 264, 283, 303, 322, 343, 362, 383]
    }
    key_indices = get_manual_key_indices(image, manual_coords)
    
    # --- Print Detected Palettes ---
    print_palette_section("MANUALLY SPECIFIED RADAR KEY PALETTE (Left to Right)", key_indices, original_palette)
    print_palette_section("FULL IMAGE PALETTE", list(range(256)), original_palette)

    # --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---
    # CUSTOMIZE YOUR COLOR MAPPING HERE
    # --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---
    GS_BLACK, GS_DARK_GRAY, GS_MID_GRAY, GS_LIGHT_GRAY, GS_WHITE = (0,0,0), (40,40,40), (100,100,100), (180,180,180), (255,255,255)

    color_index_map = {
        # This inverted gradient maps the heaviest rainfall (right side of the key) to white
        # for maximum contrast on an e-ink display.
        'RADAR_KEY': [GS_BLACK, GS_BLACK, GS_BLACK, GS_BLACK, GS_BLACK, GS_DARK_GRAY, GS_DARK_GRAY, GS_MID_GRAY, GS_MID_GRAY, GS_LIGHT_GRAY, GS_LIGHT_GRAY, GS_WHITE, GS_WHITE, GS_WHITE, GS_WHITE],
        # Example of mapping land/sea by range
        # (1, 20): GS_DARK_GRAY,
    }
    # --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---

    new_palette = original_palette[:]

    for key, new_color in color_index_map.items():
        indices_to_map = []
        if key == 'RADAR_KEY':
            if isinstance(new_color, list):
                print(f"Dynamically mapping radar key indices to a list of colors")
                for i, index in enumerate(key_indices):
                    if i < len(new_color) and (index * 3) < len(new_palette):
                        new_palette[index*3 : index*3+3] = new_color[i]
                continue
            else:
                indices_to_map = key_indices
        elif isinstance(key, int):
            indices_to_map = [key]
        elif isinstance(key, tuple) and len(key) == 2:
            indices_to_map = range(key[0], key[1] + 1)

        if indices_to_map:
            print(f"Mapping group '{key}' to {new_color}")
            for index in indices_to_map:
                if (index * 3) < len(new_palette):
                    new_palette[index*3 : index*3+3] = new_color
    
    image.putpalette(new_palette)
    image.save(output_path)
    print(f"\nSuccessfully created filtered image at '{output_path}'")

if __name__ == "__main__":
    filter_image()