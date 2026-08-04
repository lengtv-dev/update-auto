import urllib.request
import re
import json

# รายชื่อ URL ทั้งหมดที่ต้องการดึงข้อมูล
URL_LIST = [
    "https://3bb-test.thanathon-zank.workers.dev/?ch=NopZ5gjkGmE",
    "https://3bb-test.thanathon-zank.workers.dev/?ch=nQlqONGyoa4",
    "https://3bb-test.thanathon-zank.workers.dev/?ch=NopZ5gjkGmE"
]

def fetch_url_content(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"[-] Error fetching {url}: {e}")
        return None

def extract_mpd_and_key(content):
    if not content:
        return None, None

    mpd_url = None
    license_key = None

    # สกัดจาก M3U Format
    m3u_key_match = re.search(r'#KODIPROP:inputstream\.adaptive\.license_key=([^\s\n]+)', content)
    m3u_mpd_match = re.search(r'(https?://[^\s\n]+\.mpd[^\s\n]*)', content)
    
    if m3u_mpd_match:
        mpd_url = m3u_mpd_match.group(1).strip()
    if m3u_key_match:
        license_key = m3u_key_match.group(1).strip()

    # สกัดจาก JSON Format
    if not mpd_url:
        try:
            data = json.loads(content)
            if isinstance(data, dict):
                mpd_url = data.get('url') or data.get('mpd') or data.get('stream')
                license_key = data.get('key') or data.get('license_key') or data.get('clear_key')
        except json.JSONDecodeError:
            pass

    # Regex Scan
    if not mpd_url:
        mpd_matches = re.findall(r'https?://[^\s"\']+\.mpd[^\s"\']*', content)
        key_matches = re.findall(r'(?:key|license_key|keyid)=([a-fA-F0-9:]+)', content, re.IGNORECASE)
        
        if mpd_matches:
            mpd_url = mpd_matches[0]
        if key_matches:
            license_key = key_matches[0]

    return mpd_url, license_key

def generate_multi_m3u(urls, output_file="playlist.m3u"):
    playlist_entries = []

    for index, url in enumerate(urls, start=1):
        content = fetch_url_content(url)
        mpd_url, license_key = extract_mpd_and_key(content)

        if mpd_url:
            lic_key_val = license_key if license_key else "keyid"
            entry = f"#EXTINF:-1, CH{index}\n"
            entry += "#KODIPROP:inputstream.adaptive.license_type=com.widevine.alpha\n"
            entry += f"#KODIPROP:inputstream.adaptive.license_key={lic_key_val}\n"
            entry += f"{mpd_url}"
            playlist_entries.append(entry)

    if playlist_entries:
        full_m3u_content = "#EXTM3U\n" + "\n\n".join(playlist_entries)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(full_m3u_content)
        print(f"[+] Successfully generated {output_file}")

if __name__ == "__main__":
    generate_multi_m3u(URL_LIST)
