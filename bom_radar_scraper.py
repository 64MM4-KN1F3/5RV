#!/usr/bin/env python
import os
import sys
import requests

def scrape_radar_gif():
    print(f"Executing script from: {os.getcwd()}")
    print(f"Using Python interpreter: {sys.executable}")
    """
    Checks if the BOM radar GIF can be downloaded.
    """
    url = "http://www.bom.gov.au/radar/IDR024.gif"
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes
        print("Successfully connected to BOM radar URL.")
        return 0

    except requests.exceptions.RequestException as e:
        print(f"Error connecting to BOM radar URL: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(scrape_radar_gif())