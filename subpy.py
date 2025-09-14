#!/usr/bin/env python3
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

MAX_THREADS = 50  # Change based on your CPU
status_dict = defaultdict(list)

def get_subdomains(domain):
    try:
        print(f"[+] Running subfinder for: {domain}")
        result = subprocess.run(
            ['subfinder', '-d', domain, '-silent'],
            capture_output=True, text=True
        )
        subdomains = result.stdout.strip().split('\n')
        return list(filter(None, subdomains))
    except FileNotFoundError:
        print("[!] subfinder not found. Install it and ensure it's in your PATH.")
        sys.exit(1)

def get_status(url):
    try:
        curl = subprocess.run(
            ['curl.exe', '-s', '-o', 'NUL', '-w', '%{http_code}',
             '--connect-timeout', '3', '--max-time', '5', '--head', url],
            capture_output=True, text=True
        )
        code = curl.stdout.strip()
        return url, code
    except Exception:
        return url, 'ERR'

def check_all(subdomains):
    print("\n[+] Checking HTTP & HTTPS for each subdomain...\n")
    tasks = []
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        for sub in subdomains:
            for proto in ['http', 'https']:
                url = f"{proto}://{sub}"
                tasks.append(executor.submit(get_status, url))

        for future in as_completed(tasks):
            url, code = future.result()
            status_dict[code].append(url)

def print_ordered():
    # Sort all codes numerically except put '200' last
    codes_sorted = sorted(
        [c for c in status_dict if c != '200'],
        key=lambda x: (x.isdigit(), x)
    ) + (['200'] if '200' in status_dict else [])

    for code in codes_sorted:
        print(f"\n🔹 Status [{code}]")
        for url in sorted(status_dict[code]):
            print(f"{url} [{code}]")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 subpy.py <domain.com>")
        sys.exit(1)
    
    domain = sys.argv[1]
    subdomains = get_subdomains(domain)

    if not subdomains:
        print("[!] No subdomains found.")
        sys.exit(0)
    
    check_all(subdomains)
    print_ordered()
