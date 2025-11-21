#!/usr/bin/env python
import os
import sys
import requests
import argparse
import re
from PIL import Image, ImageSequence
from io import BytesIO

def get_image_urls(page_url, base_url="https://reg.bom.gov.au"):
    """
    Fetches the radar loop page and extracts the background image and list of radar frame URLs.
    Returns a dictionary with URLs: background, topography, locations, range, frames.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
        }
        print(f"Fetching page: {page_url}")
        response = requests.get(page_url, headers=headers, timeout=10)
        response.raise_for_status()
        content = response.text

        product_id = re.search(r'(IDR\d+)', page_url).group(1)
        
        # Define URLs for all potential layers
        urls = {
            'background': f"{base_url}/products/radar_transparencies/{product_id}.background.png",
            'topography': f"{base_url}/products/radar_transparencies/{product_id}.topography.png",
            'locations': f"{base_url}/products/radar_transparencies/{product_id}.locations.png",
            'range': f"{base_url}/products/radar_transparencies/{product_id}.range.png",
            'frames': []
        }
        
        # Extract frame URLs from JS variable: theImageNames[i] = "/radar/..."
        frame_matches = re.findall(r'theImageNames\[\d+\]\s*=\s*"([^"]+)"', content)
        if not frame_matches:
            print(f"Error: Could not find radar frames in {page_url}")
            return None
            
        urls['frames'] = [f"{base_url}{url}" for url in frame_matches]
        
        return urls

    except Exception as e:
        print(f"Error fetching details from {page_url}: {e}")
        return None

def fetch_image(url, name="image"):
    """Fetches an image from a URL and returns a PIL Image object (RGBA), or None if failed."""
    try:
        # print(f"Downloading {name}: {url}")
        resp = requests.get(url)
        if resp.status_code == 200:
            return Image.open(BytesIO(resp.content)).convert("RGBA")
        else:
            # print(f"Failed to fetch {name} (Status {resp.status_code})")
            return None
    except Exception as e:
        print(f"Error downloading {name}: {e}")
        return None

def create_animated_radar(page_url, output_gif_path):
    """
    Downloads frames and layers, composites them, and saves as an animated GIF.
    Returns True on success.
    """
    urls = get_image_urls(page_url)
    if not urls or not urls['frames']:
        return False

    try:
        # Download static layers
        print("Downloading static layers...")
        background = fetch_image(urls['background'], "background")
        topography = fetch_image(urls['topography'], "topography")
        locations = fetch_image(urls['locations'], "locations")
        range_overlay = fetch_image(urls['range'], "range")
        
        if not background:
            print("Critical: Background not found. Using black placeholder.")
            background = Image.new('RGBA', (512, 512), (0, 0, 0, 255))

        # Helper to crop image
        crop_pixels = 16
        def crop_img(img):
            if img and img.height > crop_pixels:
                return img.crop((0, crop_pixels, img.width, img.height))
            return img

        # Crop static layers
        background = crop_img(background)
        topography = crop_img(topography)
        locations = crop_img(locations)
        range_overlay = crop_img(range_overlay)

        frames = []
        for i, frame_url in enumerate(urls['frames']):
            print(f"Downloading frame {i+1}/{len(urls['frames'])}: {frame_url}")
            radar_layer = fetch_image(frame_url, f"frame {i+1}")
            
            if not radar_layer:
                print(f"Skipping failed frame: {frame_url}")
                continue

            radar_layer = crop_img(radar_layer)

            # Composite: Background -> Topography -> Radar -> Locations -> Range
            composite = Image.new('RGBA', background.size)
            composite.paste(background, (0,0))
            
            if topography:
                composite.alpha_composite(topography)
                
            if radar_layer:
                composite.alpha_composite(radar_layer)
                
            if locations:
                composite.alpha_composite(locations)
                
            if range_overlay:
                composite.alpha_composite(range_overlay)
            
            # Convert to RGB for GIF
            frame_img = composite.convert("RGB").quantize(colors=256, method=Image.MAXCOVERAGE, dither=Image.NONE)
            frames.append(frame_img)

        if frames:
            # Save as animated GIF
            # Duration is in milliseconds. 500ms = 0.5s per frame is standardish
            frames[0].save(
                output_gif_path,
                save_all=True,
                append_images=frames[1:],
                duration=500,
                loop=0
            )
            print(f"Saved animated GIF to {output_gif_path}")
            return True
        else:
            return False

    except Exception as e:
        print(f"Error creating animated radar for {page_url}: {e}")
        return False

def join_animated_gifs(gif1_path, gif2_path, output_path, orientation='horizontal'):
    """
    Joins two animated GIFs side-by-side or vertically.
    Preserves animation by processing frame by frame.
    """
    try:
        gif1 = Image.open(gif1_path)
        gif2 = Image.open(gif2_path)

        # Ensure they have the same number of frames or handle mismatch
        # We'll loop over the minimum number of frames
        n_frames = min(gif1.n_frames, gif2.n_frames)
        
        frames = []
        for i in range(n_frames):
            gif1.seek(i)
            gif2.seek(i)
            
            img1 = gif1.convert("RGBA")
            img2 = gif2.convert("RGBA")
            
            separator_size = 1
            
            if orientation == 'vertical':
                total_width = max(img1.width, img2.width)
                total_height = img1.height + img2.height + separator_size
                # Using black background for separator
                new_img = Image.new('RGBA', (total_width, total_height), (0, 0, 0, 255))
                new_img.paste(img1, (0, 0))
                new_img.paste(img2, (0, img1.height + separator_size))
            else: # horizontal
                total_width = img1.width + img2.width + separator_size
                total_height = max(img1.height, img2.height)
                # Using black background for separator
                new_img = Image.new('RGBA', (total_width, total_height), (0, 0, 0, 255))
                new_img.paste(img1, (0, 0))
                new_img.paste(img2, (img1.width + separator_size, 0))

            # Quantize
            frame_img = new_img.convert("RGB").quantize(colors=256, method=Image.MAXCOVERAGE, dither=Image.NONE)
            frames.append(frame_img)

        if frames:
            frames[0].save(
                output_path,
                save_all=True,
                append_images=frames[1:],
                duration=gif1.info.get('duration', 500),
                loop=0
            )
            print(f"Successfully joined animated GIFs to {output_path}")
            return True
        return False

    except Exception as e:
        print(f"Error joining animated GIFs: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape and process BOM radar animated images.")
    parser.add_argument("--dev", action="store_true", help="Run in development mode (skip scraping, just join existing temp files if they exist).")
    parser.add_argument("-a", "--arrangement", choices=['v', 'vertical', 'h', 'horizontal'], default='horizontal', help="Arrangement of the joined images (v/vertical or h/horizontal).")
    args = parser.parse_args()

    orientation = 'vertical' if args.arrangement in ['v', 'vertical'] else 'horizontal'
    
    radar_64_url = "https://reg.bom.gov.au/products/IDR024.loop.shtml"
    radar_128_url = "https://reg.bom.gov.au/products/IDR023.loop.shtml"
    
    # Temp filenames for the individual animated gifs
    gif_64_path = "temp_radar_64km.gif"
    gif_128_path = "temp_radar_128km.gif"
    output_file = f"bom_radar_{orientation}_animated.gif"

    if not args.dev:
        success_64 = create_animated_radar(radar_64_url, gif_64_path)
        success_128 = create_animated_radar(radar_128_url, gif_128_path)
        
        if not (success_64 and success_128):
            print("Failed to create one or both radar GIFs.")
            sys.exit(1)
    else:
        print("Dev mode: Using existing temporary GIF files if available.")
        if not os.path.exists(gif_64_path) or not os.path.exists(gif_128_path):
            print("Error: Temporary GIF files not found for dev mode.")
            # For dev testing without files, we could generate dummy ones, but better to fail.
            sys.exit(1)

    join_success = join_animated_gifs(gif_64_path, gif_128_path, output_file, orientation=orientation)
    
    if join_success:
        # Cleanup temp files? Maybe keep them for debugging or if user wants them.
        # For now, let's keep them or maybe delete them. The prompt didn't specify.
        # Usually scripts should clean up, but dev mode relies on them.
        # We'll leave them.
        sys.exit(0)
    else:
        sys.exit(1)