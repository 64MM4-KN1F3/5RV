#!/usr/bin/env python
import os
import sys
import requests

def scrape_radar_gif():
    print(f"Executing script from: {os.getcwd()}")
    print(f"Using Python interpreter: {sys.executable}")
    """
    Downloads the BOM radar GIF and saves it.
    """
    url = "http://www.bom.gov.au/radar/IDR024.gif"
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes
        with open("bom_radar.gif", "wb") as f:
            f.write(response.content)
        print("Successfully saved image to bom_radar.gif")
        return 0

    except requests.exceptions.RequestException as e:
        print(f"Error copying image: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(scrape_radar_gif())