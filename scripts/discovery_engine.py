import requests
import datetime
import os

def run_discovery():
    """
    Fetches trending RAG projects from GitHub API with quality filters.
    Filters:
    - Topic: RAG
    - Stars: > 100 (Quality threshold)
    - Last Push: Within last 90 days (Freshness threshold)
    """
    # Configuration
    MIN_STARS = 100
    DAYS_LIMIT = 90
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") # Optional, increases rate limits
    
    # Calculate date threshold
    cutoff_date = (datetime.datetime.now() - datetime.timedelta(days=DAYS_LIMIT)).strftime("%Y-%m-%d")
    
    # Construct API Query: topic:rag + stars:>=100 + pushed:>=2024-XX-XX
    query = f"topic:rag stars:>={MIN_STARS} pushed:>={cutoff_date}"
    URL = "https://api.github.com/search/repositories"
    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": 15  # Get top 15 results
    }
    
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    print(f"[*] Initiating Smart Discovery...")
    print(f"    - Filter: Stars >= {MIN_STARS}")
    print(f"    - Filter: Updated after {cutoff_date}")

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_file = os.path.join(repo_root, ".github", "PROPOSED_UPDATES.md")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    try:
        response = requests.get(URL, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        projects = data.get("items", [])
    except Exception as e:
        print(f"[-] Critical Error impacting discovery: {e}")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"# Smart RAG Discovery - {datetime.date.today()}\n\n")
            f.write(f"> Discovery failed this run: {e}\n")
        return

    # Write results
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"# 🚀 Smart RAG Discovery - {datetime.date.today()}\n")
        f.write(f"> **Filters Applied:** Stars >= {MIN_STARS}, Updated in last {DAYS_LIMIT} days.\n\n")
        f.write("| Project | Stars | Description | Last Update |\n")
        f.write("| :--- | :--- | :--- | :--- |\n")
        
        count = 0
        for p in projects:
            name = p['name']
            url = p['html_url']
            desc = p['description'] or "No description provided."
            stars = p['stargazers_count']
            updated_at = p['updated_at'].split("T")[0]
            
            # Clean description for markdown table (remove pipes)
            desc = desc.replace("|", "-").replace("\n", " ")
            if len(desc) > 100: desc = desc[:97] + "..."

            f.write(f"| **[{name}]({url})** | ⭐ {stars} | {desc} | {updated_at} |\n")
            print(f"[+] Found: {name} ({stars} stars) - Updated: {updated_at}")
            count += 1

    print(f"\n[!] Success! found {count} high-quality RAG projects.")
    print(f"    Results written to '{output_file}'")

if __name__ == "__main__":
    run_discovery()