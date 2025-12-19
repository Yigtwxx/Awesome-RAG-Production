import requests
from bs4 import BeautifulSoup
import datetime

def run_discovery():
    """
    Scrapes GitHub topics to find trending RAG projects.
    Outputs a formatted markdown list for easy integration.
    """
    URL = "https://github.com/topics/rag"
    HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    print(f"[*] Initiating discovery at: {URL}")
    try:
        response = requests.get(URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"[-] Critical Error: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    projects = soup.find_all('article', class_='border rounded color-shadow-small color-bg-subtle my-4')

    with open("../PROPOSED_UPDATES.md", "w", encoding="utf-8") as f:
        f.write(f"# Proposed RAG Updates - {datetime.date.today()}\n")
        f.write("> Review these resources before adding them to the main README.\n\n")
        
        for project in projects:
            title_tag = project.find('a', class_='text-bold')
            if not title_tag: continue
            
            path = title_tag.get('href').strip()
            link = f"https://github.com{path}"
            name = path.split('/')[-1]

            desc_tag = project.find('p', class_='color-fg-muted')
            desc = desc_tag.text.strip() if desc_tag else "No description provided."

            star_tag = project.find('span', id='repo-stars-counter-star')
            stars = star_tag.text.strip() if star_tag else "0"

            f.write(f"* **[{name}]({link})** - {desc} (⭐ {stars})\n")
            print(f"[+] Discovered: {name}")

    print("\n[!] Success! Check 'PROPOSED_UPDATES.md' for the results.")

if __name__ == "__main__":
    run_discovery()