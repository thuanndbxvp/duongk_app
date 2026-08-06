import os
import urllib.request
import json

base_url = "https://huggingface.co/api/datasets/STBack23/omnivoice-vi/tree/main/voices"
resolve_base = "https://huggingface.co/datasets/STBack23/omnivoice-vi/resolve/main/voices"

def download_voices():
    data = json.loads(urllib.request.urlopen(base_url).read().decode())
    voices_dir = os.path.join("D:\\appDK\\apps\\omnivoice\\voices")
    
    voices = []
    for item in data:
        voice_name = item['path'].split('/')[-1]
        
        # Get files in the directory
        sub_url = f"{base_url}/{voice_name}"
        sub_data = json.loads(urllib.request.urlopen(sub_url).read().decode())
        
        audio_file = None
        for f in sub_data:
            if f['path'].endswith('.mp3') or f['path'].endswith('.wav'):
                audio_file = f['path'].split('/')[-1]
                break
                
        if audio_file:
            voices.append(voice_name)
            audio_url = f"{resolve_base}/{voice_name}/{audio_file}"
            ext = audio_file.split('.')[-1]
            out_path = os.path.join(voices_dir, f"{voice_name}.{ext}")
            
            print(f"Downloading {audio_url} to {out_path}")
            urllib.request.urlretrieve(audio_url, out_path)
        else:
            print(f"No audio file found for {voice_name}")
        
    print(f"Downloaded {len(voices)} voices: {voices}")

if __name__ == "__main__":
    download_voices()
