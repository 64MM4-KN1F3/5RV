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
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes
        with open(output_filename, "wb") as f:
            f.write(response.content)
        print("Successfully saved image to " + output_filename)
        return True

    except requests.exceptions.RequestException as e:
        print(f"Error copying image: {e}")
        return False

def join_and_resize_images(image1_path, image2_path, output_path, target_width, target_height):
    try:
        img1 = Image.open(image1_path)
        img2 = Image.open(image2_path)

        # Create a new image with the combined width
        total_width = img1.width + img2.width
        max_height = max(img1.height, img2.height)
        
        # Create a new image with a black background
        new_img = Image.new('RGB', (total_width, max_height), (0, 0, 0))
        
        # Paste the two images side-by-side
        new_img.paste(img1, (0, 0))
        new_img.paste(img2, (img1.width, 0))

        # Calculate aspect ratio
        aspect_ratio = new_img.width / new_img.height
        target_aspect_ratio = target_width / target_height

        if aspect_ratio > target_aspect_ratio:
            # Fit to width
            new_width = target_width
            new_height = int(target_width / aspect_ratio)
        else:
            # Fit to height
            new_height = target_height
            new_width = int(target_height * aspect_ratio)

        # Resize the image
        resized_img = new_img.resize((new_width, new_height), Image.LANCZOS)

        # Create a black background for the final image
        final_img = Image.new('RGB', (target_width, target_height), (0, 0, 0))

        # Paste the resized image onto the black background
        paste_x = (target_width - new_width) // 2
        paste_y = (target_height - new_height) // 2
        final_img.paste(resized_img, (paste_x, paste_y))

        final_img.save(output_path)
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

    if not args.dev:
        radar_64_url = "http://www.bom.gov.au/radar/IDR024.gif"
        radar_256_url = "http://www.bom.gov.au/radar/IDR022.gif"
        scrape_success = scrape_radar_gif(radar_64_url, radar_64_file) and scrape_radar_gif(radar_256_url, radar_256_file)
        if not scrape_success:
            sys.exit(1)

    join_success = join_and_resize_images(radar_64_file, radar_256_file, output_file, 800, 480)
    
    if join_success:
        sys.exit(0)
    else:
        sys.exit(1)