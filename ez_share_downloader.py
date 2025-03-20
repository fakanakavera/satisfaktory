import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin, unquote
import time
import re

class EzShareDownloader:
    def __init__(self, base_url="http://ezshare.card"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Host': 'ezshare.card'
        })
        self.download_folder = "downloaded_images"
        
        if not os.path.exists(self.download_folder):
            os.makedirs(self.download_folder)

    def get_file_list(self):
        """Get list of files from the SD card"""
        try:
            # Get the photo gallery page
            params = {
                'vtype': '0',
                'fdir': '100MEDIA',
                'ftype': '0',
                'devw': '320',
                'devh': '356',
                'folderFlag': '0'
            }
            response = self.session.get(f"{self.base_url}/photo", params=params)
            print(f"Response status code: {response.status_code}")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            files = []
            
            # Find all image entries in the gallery
            for checkbox in soup.find_all('input', {'name': 'checkimg'}):
                value = checkbox.get('value', '')
                # Extract fname and fdir from the checkbox value
                fname_match = re.search(r'fname=(.*?)&', value)
                fdir_match = re.search(r'fdir=(.*?)(?:&|$)', value)
                
                if fname_match and fdir_match:
                    fname = fname_match.group(1)
                    fdir = fdir_match.group(1)
                    files.append({
                        'fname': fname,
                        'fdir': fdir,
                        'folderFlag': '0'
                    })
            
            print("\nFound files:", files)
            return files
            
        except requests.exceptions.RequestException as e:
            print(f"Error accessing the ez Share card: {e}")
            return []

    def download_file(self, file_info):
        """Download a single file"""
        try:
            # Construct the download URL with parameters
            params = {
                'fname': file_info['fname'],
                'fdir': file_info['fdir'],
                'folderFlag': file_info['folderFlag']
            }
            
            filename = file_info['fname']
            save_path = os.path.join(self.download_folder, filename)

            print(f"Downloading {filename}...")
            
            # Use the download endpoint
            response = self.session.get(f"{self.base_url}/download", params=params, stream=True)
            response.raise_for_status()

            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            print(f"Successfully downloaded {filename}")
            return True

        except requests.exceptions.RequestException as e:
            print(f"Error downloading {filename}: {e}")
            return False

    def download_all_images(self):
        """Download all images from the SD card"""
        files = self.get_file_list()
        
        if not files:
            print("No image files found or couldn't access the SD card")
            return

        print(f"Found {len(files)} image files")
        
        for file_info in files:
            self.download_file(file_info)
            time.sleep(0.5)

def main():
    # Create downloader instance
    downloader = EzShareDownloader()
    
    # Start downloading
    print("Starting download of all images...")
    downloader.download_all_images()
    print("Download process completed!")

if __name__ == "__main__":
    main() 