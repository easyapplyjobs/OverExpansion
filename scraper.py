"""
OverExpansion Rate Scraper
Runs daily via GitHub Actions. Fetches:
  1. FDIC national average rates (official weekly data)
  2. Per-bank APY from each bank's public rate page
Outputs: rates.json consumed by index.html
"""

import json
import time
import re
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Optional

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def fetch(url: str, timeout: int = 10) -> Optional[str]:
    """Fetch a URL and return text, or None on failure."""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  WARN: fetch failed for {url}: {e}")
        return None


def first_float(pattern: str, text: str) -> Optional[float]:
    """Return first regex match as float, or None."""
    m = re.search(pattern, text)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    return None


# ── FDIC NATIONAL AVERAGES ────────────────────────────────────────────────────

def fetch_fdic_national_averages() -> dict:
    """
    FDIC publishes weekly national deposit rate averages via their Statistics API.
    Endpoint: https://banks.data.fdic.gov/api/deposits
    Fields: REPDTE, INTDEPSAV (savings rate), INTDEP (total interest on deposits)
    
    The FDIC 'rates' endpoint gives the national average APY published weekly.
    """
    print("Fetching FDIC national averages...")
    averages = {}

    # FDIC national rate averages endpoint
    # SAVRATJUM = national avg savings APY
    # MMRATJUM  = national avg money market APY
    # SDRATJUM  = national avg 12-month CD APY
    url = (
        "https://banks.data.fdic.gov/api/summary?"
        "filters=REPDTE%3A[2025-01-01+TO+*]"
        "&fields=REPDTE,SAVRATJUM,MMRATJUM,SDRATJUM,INTDEP"
        "&limit=1&sort_by=REPDTE&sort_order=DESC"
        "&output=json"
    )
    text = fetch(url)
    if text:
        try:
            data = json.loads(text)
            rows = data.get("data", [])
            if rows:
                row = rows[0].get("data", rows[0])
                averages["savings_national_avg"] = round(float(row.get("SAVRATJUM", 0.38)), 2)
                averages["mma_national_avg"]     = round(float(row.get("MMRATJUM", 0.55)), 2)
                averages["cd_1yr_national_avg"]  = round(float(row.get("SDRATJUM", 1.96)), 2)
                averages["fdic_report_date"]     = row.get("REPDTE", "")
                print(f"  FDIC savings avg: {averages['savings_national_avg']}%")
        except Exception as e:
            print(f"  WARN: FDIC parse error: {e}")

    # Fallback to known values if API fails
    if "savings_national_avg" not in averages:
        averages = {
            "savings_national_avg": 0.38,
            "mma_national_avg": 0.55,
            "cd_1yr_national_avg": 1.96,
            "fdic_report_date": "",
            "source": "fallback"
        }

    return averages


# ── PER-BANK SCRAPERS ─────────────────────────────────────────────────────────
# Each function fetches the bank's public rate page and extracts the APY.
# Returns dict of product -> APY float, or empty dict on failure.

def scrape_ally() -> dict:
    text = fetch("https://www.ally.com/bank/online-savings-account/")
    if not text:
        return {}
    rates = {}
    # Ally publishes APY in pattern like "4.00% APY"
    m = first_float(r'(\d+\.\d+)\s*%\s*APY', text)
    if m:
        rates["savings"] = m
    return rates


def scrape_marcus() -> dict:
    text = fetch("https://www.marcus.com/us/en/savings/high-yield-savings")
    if not text:
        return {}
    rates = {}
    m = first_float(r'(\d+\.\d+)\s*%\s*(?:APY|Annual Percentage Yield)', text)
    if m:
        rates["savings"] = m
    return rates


def scrape_sofi() -> dict:
    text = fetch("https://www.sofi.com/banking/")
    if not text:
        return {}
    rates = {}
    m = first_float(r'(\d+\.\d+)\s*%\s*APY', text)
    if m:
        rates["savings"] = m
    return rates


def scrape_discover() -> dict:
    text = fetch("https://www.discover.com/online-banking/savings/")
    if not text:
        return {}
    rates = {}
    m = first_float(r'(\d+\.\d+)\s*%\s*APY', text)
    if m:
        rates["savings"] = m
    return rates


def scrape_synchrony() -> dict:
    text = fetch("https://www.synchronybank.com/banking/high-yield-savings/")
    if not text:
        return {}
    rates = {}
    m = first_float(r'(\d+\.\d+)\s*%\s*APY', text)
    if m:
        rates["savings"] = m
    return rates


def scrape_capital_one() -> dict:
    text = fetch("https://www.capitalone.com/bank/savings-accounts/online-performance-savings-account/")
    if not text:
        return {}
    rates = {}
    m = first_float(r'(\d+\.\d+)\s*%\s*APY', text)
    if m:
        rates["savings"] = m
    return rates


def scrape_cit() -> dict:
    text = fetch("https://www.cit.com/cit-bank/banking/savings/")
    if not text:
        return {}
    rates = {}
    m = first_float(r'(\d+\.\d+)\s*%\s*APY', text)
    if m:
        rates["savings"] = m
    return rates


def scrape_axos() -> dict:
    text = fetch("https://www.axosbank.com/Banking/Savings-Accounts/High-Yield-Savings")
    if not text:
        return {}
    rates = {}
    m = first_float(r'(\d+\.\d+)\s*%\s*APY', text)
    if m:
        rates["savings"] = m
    return rates


def scrape_american_express() -> dict:
    text = fetch("https://www.americanexpress.com/en-us/banking/online-savings/")
    if not text:
        return {}
    rates = {}
    m = first_float(r'(\d+\.\d+)\s*%\s*APY', text)
    if m:
        rates["savings"] = m
    return rates


def scrape_ufb() -> dict:
    text = fetch("https://www.ufbdirect.com/")
    if not text:
        return {}
    rates = {}
    m = first_float(r'(\d+\.\d+)\s*%\s*APY', text)
    if m:
        rates["savings"] = m
    return rates


def scrape_barclays() -> dict:
    text = fetch("https://www.banking.barclaysus.com/tiered-savings.html")
    if not text:
        return {}
    rates = {}
    m = first_float(r'(\d+\.\d+)\s*%\s*APY', text)
    if m:
        rates["savings"] = m
    return rates


def scrape_everbank() -> dict:
    text = fetch("https://www.everbank.com/banking/savings")
    if not text:
        return {}
    rates = {}
    m = first_float(r'(\d+\.\d+)\s*%\s*APY', text)
    if m:
        rates["savings"] = m
    return rates


def scrape_bread() -> dict:
    text = fetch("https://www.breadsavings.com/")
    if not text:
        return {}
    rates = {}
    m = first_float(r'(\d+\.\d+)\s*%\s*APY', text)
    if m:
        rates["savings"] = m
    return rates


def scrape_western_alliance() -> dict:
    text = fetch("https://www.westernalliancebancorporation.com/personal-banking/savings")
    if not text:
        return {}
    rates = {}
    m = first_float(r'(\d+\.\d+)\s*%\s*APY', text)
    if m:
        rates["savings"] = m
    return rates


def scrape_varo() -> dict:
    text = fetch("https://www.varomoney.com/bank/savings-account/")
    if not text:
        return {}
    rates = {}
    m = first_float(r'(\d+\.\d+)\s*%\s*APY', text)
    if m:
        rates["savings"] = m
    return rates


def scrape_bask() -> dict:
    text = fetch("https://www.baskbank.com/interest-savings-account")
    if not text:
        return {}
    rates = {}
    m = first_float(r'(\d+\.\d+)\s*%\s*APY', text)
    if m:
        rates["savings"] = m
    return rates


def scrape_lendingclub() -> dict:
    text = fetch("https://www.lendingclub.com/savings/high-yield-savings-account")
    if not text:
        return {}
    rates = {}
    m = first_float(r'(\d+\.\d+)\s*%\s*APY', text)
    if m:
        rates["savings"] = m
    return rates


def scrape_forbright() -> dict:
    text = fetch("https://www.forbrightbank.com/savings")
    if not text:
        return {}
    rates = {}
    m = first_float(r'(\d+\.\d+)\s*%\s*APY', text)
    if m:
        rates["savings"] = m
    return rates


def scrape_alliant() -> dict:
    text = fetch("https://www.alliantcreditunion.org/bank/high-rate-savings")
    if not text:
        return {}
    rates = {}
    m = first_float(r'(\d+\.\d+)\s*%\s*APY', text)
    if m:
        rates["savings"] = m
    return rates


def scrape_vio() -> dict:
    text = fetch("https://www.viobank.com/online-savings-account")
    if not text:
        return {}
    rates = {}
    m = first_float(r'(\d+\.\d+)\s*%\s*APY', text)
    if m:
        rates["savings"] = m
    return rates


# Map bank name -> scraper function
SCRAPERS = {
    "Ally Bank":                    scrape_ally,
    "Marcus by Goldman Sachs":      scrape_marcus,
    "SoFi Bank":                    scrape_sofi,
    "Discover Bank":                scrape_discover,
    "Synchrony Bank":               scrape_synchrony,
    "Capital One 360":              scrape_capital_one,
    "CIT Bank":                     scrape_cit,
    "Axos Bank":                    scrape_axos,
    "American Express HYSA":        scrape_american_express,
    "UFB Direct":                   scrape_ufb,
    "Barclays US":                  scrape_barclays,
    "EverBank":                     scrape_everbank,
    "Bread Savings":                scrape_bread,
    "Western Alliance Bank":        scrape_western_alliance,
    "Varo Bank":                    scrape_varo,
    "Bask Bank":                    scrape_bask,
    "LendingClub Bank":             scrape_lendingclub,
    "Forbright Bank":               scrape_forbright,
    "Alliant Credit Union":         scrape_alliant,
    "Vio Bank":                     scrape_vio,
}


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print(f"\n{'='*60}")
    print(f"OverExpansion Scraper — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*60}\n")

    results = {
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "national_averages": {},
        "banks": {},
        "errors": []
    }

    # 1. FDIC national averages
    results["national_averages"] = fetch_fdic_national_averages()
    time.sleep(1)

    # 2. Per-bank scraping
    print(f"\nScraping {len(SCRAPERS)} banks...")
    succeeded = 0
    for bank_name, scraper_fn in SCRAPERS.items():
        print(f"  → {bank_name}...")
        try:
            rates = scraper_fn()
            if rates:
                results["banks"][bank_name] = rates
                print(f"     ✓ savings: {rates.get('savings', 'n/a')}%")
                succeeded += 1
            else:
                print(f"     ✗ no rates extracted")
                results["errors"].append(f"{bank_name}: no rates extracted")
        except Exception as e:
            print(f"     ✗ error: {e}")
            results["errors"].append(f"{bank_name}: {str(e)}")
        time.sleep(0.8)  # polite delay between requests

    print(f"\n{'='*60}")
    print(f"Done: {succeeded}/{len(SCRAPERS)} banks scraped successfully")
    print(f"Errors: {len(results['errors'])}")

    # 3. Write output
    with open("rates.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"Written: rates.json")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
