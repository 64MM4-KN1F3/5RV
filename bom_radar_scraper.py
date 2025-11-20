#!/usr/bin/env python
import os
import sys
import requests
import argparse
from PIL import Image

def scrape_radar_gif(url, output_filename):
    print(f"Executing script from: {os.getcwd()}")
    print(f"Using Python interpreter: {sys.executable}")
    """
    Downloads the BOM radar GIF and saves it.
    Returns a tuple (success, last_modified_timestamp).
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes
        last_modified = response.headers.get("Last-Modified")
        with open(output_filename, "wb") as f:
            f.write(response.content)
        print("Successfully saved image to " + output_filename)
        return True, last_modified

    except requests.exceptions.RequestException as e:
        print(f"Error copying image: {e}")
        return False, None

def join_and_resize_images(image1_path, image2_path, output_path, target_width, target_height, orientation='horizontal'):
    try:
        img1 = Image.open(image1_path).convert("RGBA")
        img2 = Image.open(image2_path).convert("RGBA")

        if orientation == 'vertical':
            # Create a new image with the combined height
            total_width = max(img1.width, img2.width)
            total_height = img1.height + img2.height

            # Create a new transparent image
            new_img = Image.new('RGBA', (total_width, total_height), (0, 0, 0, 0))

            # Paste the two images stacked vertically
            new_img.paste(img1, (0, 0))
            new_img.paste(img2, (0, img1.height))
        else:
            # Create a new image with the combined width
            total_width = img1.width + img2.width
            max_height = max(img1.height, img2.height)

            # Create a new transparent image
            new_img = Image.new('RGBA', (total_width, max_height), (0, 0, 0, 0))

            # Paste the two images side-by-side
            new_img.paste(img1, (0, 0))
            new_img.paste(img2, (img1.width, 0))

        # --- Resize with aspect ratio preservation ---
        aspect_ratio = new_img.width / new_img.height
        target_aspect_ratio = target_width / target_height

        if aspect_ratio > target_aspect_ratio:
            new_width = target_width
            new_height = int(target_width / aspect_ratio)
        else:
            new_height = target_height
            new_width = int(target_height * aspect_ratio)

        # Use the NEAREST resampling filter to preserve sharp edges and prevent
        # the creation of new colors, which is ideal for this type of graphic
        # and avoids the artifacting seen with anti-aliasing filters like LANCZOS.
        resized_img = new_img.resize((new_width, new_height), Image.NEAREST)

        # --- Create final image with black background and center the resized image ---
        final_img_with_bg = Image.new('RGB', (target_width, target_height), (0, 0, 0))
        paste_x = (target_width - new_width) // 2
        paste_y = (target_height - new_height) // 2
        
        # Paste the resized image (which has an alpha channel) onto the RGB background
        final_img_with_bg.paste(resized_img, (paste_x, paste_y), resized_img)

        # --- Quantize back to a paletted image for GIF format ---
        # By disabling dithering, we prevent the noisy artifacts that can appear
        # when reducing the color palette, resulting in a cleaner image.
        final_paletted_img = final_img_with_bg.quantize(colors=256, method=Image.MAXCOVERAGE, dither=Image.NONE)
        
        final_paletted_img.save(output_path, "GIF")
        print(f"Successfully joined and resized images to {output_path}")
        return True
    except Exception as e:
        print(f"Error joining and resizing images: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape and process BOM radar images.")
    parser.add_argument("--dev", action="store_true", help="Run in development mode (skip scraping).")
    args = parser.parse_args()

    radar_64_file = "bom_radar_64km.gif"
    radar_256_file = "bom_radar_256km.gif"
    output_file = "bom_radar.gif"
    output_file_vertical = "bom_radar_vertical.gif"
    timestamp_file = "timestamp.txt"

    if not args.dev:
        radar_64_url = "http://www.bom.gov.au/radar/IDR024.gif"
        radar_256_url = "http://www.bom.gov.au/radar/IDR022.gif"
        
        scrape_64_success, last_modified_64 = scrape_radar_gif(radar_64_url, radar_64_file)
        scrape_256_success, _ = scrape_radar_gif(radar_256_url, radar_256_file)
        
        scrape_success = scrape_64_success and scrape_256_success

        if not scrape_success:
            sys.exit(1)
        
        if last_modified_64:
            with open(timestamp_file, "w") as f:
                f.write(last_modified_64)
            print(f"Timestamp '{last_modified_64}' saved to {timestamp_file}")

    join_success_horizontal = join_and_resize_images(radar_64_file, radar_256_file, output_file, 800, 480, orientation='horizontal')
    join_success_vertical = join_and_resize_images(radar_64_file, radar_256_file, output_file_vertical, 480, 800, orientation='vertical')
    
    if join_success_horizontal and join_success_vertical:
        sys.exit(0)
    else:
        sys.exit(1)