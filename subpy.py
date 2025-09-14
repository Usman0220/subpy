import subprocess
import requests
import sys
import urllib3
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def run_subfinder(domain):
    """Run subfinder and return a list of subdomains."""
    try:
        result = subprocess.run(
            ["subfinder", "-silent", "-d", domain],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.splitlines()
    except subprocess.CalledProcessError as e:
        print("[!] Error running subfinder:", e)
        return []

def check_status(url):
    """Check HTTP status code of a given URL."""
    try:
        r = requests.get(url, timeout=10, verify=False, allow_redirects=False)
        return url, r.status_code
    except requests.exceptions.RequestException:
        return url, 0  # [000] for failed

def main(domain):
    print(f"[+] Running subfinder for: {domain}\n")
    subdomains = run_subfinder(domain)

    print("[+] Checking HTTP & HTTPS for each subdomain...\n")

    results = defaultdict(list)

    urls = [f"{scheme}://{sub}" for sub in subdomains for scheme in ["http", "https"]]

    # Run checks in parallel (50 threads like xargs -P 50)
    with ThreadPoolExecutor(max_workers=50) as executor:
        future_to_url = {executor.submit(check_status, url): url for url in urls}
        for future in as_completed(future_to_url):
            url, code = future.result()
            results[code].append(url)

    # Print all codes except 200 first, then 200 at the end
    for code in sorted(results.keys()):
        if code != 200:
            print(f"\n🔹 Status [{code:03}]")
            for u in results[code]:
                print(u)

    # Print 200 last if exists
    if 200 in results:
        print(f"\n🔹 Status [200]")
        for u in results[200]:
            print(u)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <domain>")
    else:
        main(sys.argv[1])
