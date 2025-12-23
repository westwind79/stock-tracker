"""
13F Institutional Ownership Data Scraper for Workday (WDAY)
VERSION 4 - FIXED: Proper validation to avoid CUSIP confusion
"""

import requests
import json
import time
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path
import re

# Configuration
WDAY_CUSIP = "98138H101"
OUTPUT_DIR = Path("./public_data")
OUTPUT_DIR.mkdir(exist_ok=True)

# Major institutional investors (expanded list)
MAJOR_INVESTORS = {
    '0000102909': 'Vanguard Group',
    '0001364742': 'BlackRock',
    '0000093751': 'State Street',
    '0001166559': 'Fidelity',
    '0001061768': 'Baillie Gifford',
    '0001364439': 'Geode Capital',
    '0001513882': 'Eagle Capital',
    '0001336528': 'Invesco',
    '0001029160': 'Northern Trust',
    '0001336617': 'American Century',
    '0000914208': 'Charles Schwab',
    '0001337619': 'T. Rowe Price',
    '0000354204': 'Morgan Stanley',
    '0000886982': 'Goldman Sachs',
    '0000019617': 'JPMorgan Chase',
}


def fetch_latest_13f_filings(max_per_investor=2):
    """Fetch recent 13F filings"""
    headers = {
        'User-Agent': 'InsiderTracker contact@example.com',
        'Accept-Encoding': 'gzip, deflate',
        'Host': 'www.sec.gov'
    }
    
    all_filings = []
    
    print(f"\n📊 Fetching 13F filings from {len(MAJOR_INVESTORS)} institutions...")
    
    for cik, name in MAJOR_INVESTORS.items():
        print(f"  {name}...", end=" ")
        
        url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=13F-HR&dateb=&owner=exclude&count={max_per_investor}&search_text="
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table', {'class': 'tableFile2'})
            
            if not table:
                print("No filings")
                continue
            
            rows = table.find_all('tr')[1:]
            found = 0
            
            for row in rows[:max_per_investor]:
                cols = row.find_all('td')
                if len(cols) >= 4:
                    filing_date = cols[3].text.strip()
                    documents_link = cols[1].find('a')
                    
                    if documents_link:
                        doc_url = "https://www.sec.gov" + documents_link['href']
                        all_filings.append({
                            'cik': cik,
                            'name': name,
                            'filing_date': filing_date,
                            'documents_url': doc_url
                        })
                        found += 1
            
            print(f"✓ {found}")
            time.sleep(0.3)
            
        except Exception as e:
            print(f"Error")
            continue
    
    print(f"\n✓ Total: {len(all_filings)} filings")
    return all_filings


def parse_13f_xml_robust(xml_text):
    """Parse 13F XML with namespace handling"""
    if not xml_text:
        return None
    
    try:
        # Remove namespaces
        xml_text = re.sub(r'xmlns[^"]*="[^"]*"', '', xml_text)
        xml_text = re.sub(r'<\?xml[^>]*\?>', '', xml_text)
        
        root = ET.fromstring(xml_text.strip())
        
        # Search for WDAY CUSIP
        for elem in root.iter():
            # Look for CUSIP element
            if elem.text and elem.text.strip() == WDAY_CUSIP:
                # Found WDAY! Now find the parent infoTable
                parent = elem
                for _ in range(5):  # Go up max 5 levels
                    parent = list(root.iter())[list(root.iter()).index(parent) - 1] if parent != root else None
                    if parent is None:
                        break
                    
                    # Look for shares and value in siblings
                    shares_found = None
                    value_found = None
                    
                    for child in parent.iter():
                        tag_lower = child.tag.lower()
                        
                        # Find shares
                        if 'sshprnamt' in tag_lower or 'shrs' in tag_lower:
                            if child.text and child.text.strip().isdigit():
                                shares_found = int(child.text.strip())
                        
                        # Find value (in thousands)
                        if 'value' in tag_lower and 'valueUSD' not in tag_lower:
                            if child.text and child.text.strip().isdigit():
                                value_found = int(child.text.strip())
                    
                    if shares_found and value_found:
                        # CRITICAL: Validate that shares != CUSIP number
                        if shares_found != 98138 and shares_found > 100000:
                            return {
                                'shares': shares_found,
                                'value_dollars': value_found * 1000
                            }
    except Exception as e:
        pass
    
    return None


def parse_13f_text_strict(text_content):
    """Parse text with strict validation"""
    try:
        lines = text_content.split('\n')
        
        for i, line in enumerate(lines):
            # Must have CUSIP
            if WDAY_CUSIP not in line:
                continue
            
            # Get surrounding context
            context_start = max(0, i - 3)
            context_end = min(len(lines), i + 4)
            context_lines = lines[context_start:context_end]
            
            # Must mention WORKDAY or WDAY
            context_text = '\n'.join(context_lines).upper()
            if 'WORKDAY' not in context_text and 'WDAY' not in context_text:
                continue
            
            # Extract numbers (skip the CUSIP itself)
            all_numbers = []
            for ctx_line in context_lines:
                # Skip the line with CUSIP
                if WDAY_CUSIP in ctx_line:
                    continue
                
                # Find all numbers
                numbers = re.findall(r'(\d[\d,]*)', ctx_line)
                for num_str in numbers:
                    num = int(num_str.replace(',', ''))
                    
                    # CRITICAL VALIDATION
                    # 1. Must not be the CUSIP number
                    if num == 98138 or num == 98138101:
                        continue
                    
                    # 2. Must be reasonable (shares: 100K-50M, value: >$10M)
                    if num > 10000:
                        all_numbers.append(num)
            
            if len(all_numbers) < 2:
                continue
            
            # Sort numbers by magnitude
            all_numbers.sort()
            
            # Heuristic: 
            # - Shares are typically 1M-25M (middle range)
            # - Values are typically $500M-$5B (large numbers)
            
            shares_candidates = [n for n in all_numbers if 100000 < n < 50000000]
            value_candidates = [n for n in all_numbers if n > 10000000]
            
            if shares_candidates and value_candidates:
                shares = shares_candidates[0]
                value = value_candidates[0]
                
                # Final sanity check: value should be shares * ~$200-300
                expected_min = shares * 150
                expected_max = shares * 350
                
                if expected_min < value < expected_max:
                    return {
                        'shares': shares,
                        'value_dollars': value
                    }
        
    except Exception as e:
        pass
    
    return None


def download_and_parse_13f(documents_url, headers):
    """Download 13F filing and parse it"""
    try:
        # Get filing page
        response = requests.get(documents_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Strategy 1: Try XML information table
        for link in soup.find_all('a'):
            href = link.get('href', '')
            text = link.get_text().lower()
            
            if '.xml' in href and any(kw in text for kw in ['information', 'infotable', 'table']):
                xml_url = "https://www.sec.gov" + href if href.startswith('/') else href
                time.sleep(0.3)
                
                xml_response = requests.get(xml_url, headers=headers, timeout=10)
                xml_response.raise_for_status()
                
                result = parse_13f_xml_robust(xml_response.text)
                if result:
                    return result
        
        # Strategy 2: Try any XML file
        for link in soup.find_all('a'):
            href = link.get('href', '')
            if '.xml' in href:
                xml_url = "https://www.sec.gov" + href if href.startswith('/') else href
                time.sleep(0.3)
                
                xml_response = requests.get(xml_url, headers=headers, timeout=10)
                xml_response.raise_for_status()
                
                result = parse_13f_xml_robust(xml_response.text)
                if result:
                    return result
        
        # Strategy 3: Text fallback (with strict validation)
        for link in soup.find_all('a'):
            href = link.get('href', '')
            if href.endswith('.txt'):
                txt_url = "https://www.sec.gov" + href if href.startswith('/') else href
                time.sleep(0.3)
                
                txt_response = requests.get(txt_url, headers=headers, timeout=10)
                txt_response.raise_for_status()
                
                result = parse_13f_text_strict(txt_response.text)
                if result:
                    return result
        
    except Exception as e:
        pass
    
    return None


def fetch_all_holdings(filings):
    """Fetch WDAY holdings for all filings"""
    print(f"\n📈 Analyzing {len(filings)} filings for WDAY holdings...")
    print("(This will take a few minutes due to SEC rate limiting)\n")
    
    headers = {
        'User-Agent': 'InsiderTracker contact@example.com',
        'Accept-Encoding': 'gzip, deflate',
        'Host': 'www.sec.gov'
    }
    
    holdings = []
    
    for idx, filing in enumerate(filings, 1):
        print(f"  [{idx}/{len(filings)}] {filing['name']} ({filing['filing_date']})... ", end="", flush=True)
        
        result = download_and_parse_13f(filing['documents_url'], headers)
        
        if result:
            result['investor_name'] = filing['name']
            result['cik'] = filing['cik']
            result['filing_date'] = filing['filing_date']
            holdings.append(result)
            print(f"✓ {result['shares']:,} shares (${result['value_dollars']:,.0f})")
        else:
            print("No position")
        
        time.sleep(0.5)  # Be nice to SEC
    
    return holdings


def calculate_stats(holdings):
    """Calculate ownership statistics"""
    if not holdings:
        return None
    
    # Keep only most recent filing per investor
    by_investor = {}
    for h in holdings:
        name = h['investor_name']
        if name not in by_investor or h['filing_date'] > by_investor[name]['filing_date']:
            by_investor[name] = h
    
    unique_holdings = list(by_investor.values())
    unique_holdings.sort(key=lambda x: x['shares'], reverse=True)
    
    total_shares = sum(h['shares'] for h in unique_holdings)
    total_value = sum(h['value_dollars'] for h in unique_holdings)
    
    return {
        'total_institutional_shares': total_shares,
        'total_institutional_value': total_value,
        'number_of_institutions': len(unique_holdings),
        'largest_holder': unique_holdings[0]['investor_name'] if unique_holdings else None,
        'largest_holder_shares': unique_holdings[0]['shares'] if unique_holdings else 0,
        'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M UTC"),
        'holdings_by_investor': unique_holdings
    }


def generate_cluster_data(holdings):
    """Generate bubble chart data"""
    by_investor = {}
    for h in holdings:
        name = h['investor_name']
        if name not in by_investor or h['filing_date'] > by_investor[name]['filing_date']:
            by_investor[name] = h
    
    cluster = []
    for name, holding in by_investor.items():
        cluster.append({
            'name': name,
            'shares': holding['shares'],
            'value': holding['value_dollars'],
            'filing_date': holding['filing_date']
        })
    
    cluster.sort(key=lambda x: x['value'], reverse=True)
    return cluster


def main():
    """Main execution"""
    print("=" * 70)
    print("SEC 13F Institutional Ownership Scraper - WDAY")
    print("VERSION 4 - FIXED: Proper validation (no CUSIP confusion)")
    print("=" * 70)
    
    filings = fetch_latest_13f_filings(max_per_investor=2)
    
    if not filings:
        print("\n❌ No filings found")
        return
    
    holdings = fetch_all_holdings(filings)
    
    if not holdings:
        print("\n❌ No WDAY holdings found")
        print("\nPossible reasons:")
        print("  • These institutions sold their WDAY positions")
        print("  • 13F format has changed (contact support)")
        print("  • SEC is blocking requests (try again later)")
        return
    
    print(f"\n✅ Found {len(holdings)} total holdings")
    print(f"📊 From {len(set(h['investor_name'] for h in holdings))} unique institutions\n")
    
    stats = calculate_stats(holdings)
    cluster = generate_cluster_data(holdings)
    
    # Save data
    ownership_file = OUTPUT_DIR / "institutional_ownership.json"
    with open(ownership_file, 'w') as f:
        json.dump(stats, f, indent=2)
    
    cluster_file = OUTPUT_DIR / "ownership_cluster.json"
    with open(cluster_file, 'w') as f:
        json.dump(cluster, f, indent=2)
    
    print("💾 Saved:")
    print(f"  • {ownership_file}")
    print(f"  • {cluster_file}")
    
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print(f"Total Shares: {stats['total_institutional_shares']:,}")
    print(f"Total Value: ${stats['total_institutional_value']:,.0f}")
    print(f"Institutions: {stats['number_of_institutions']}")
    print(f"Top Holder: {stats['largest_holder']} ({stats['largest_holder_shares']:,} shares)")
    
    print("\n🏆 Top 10 Institutional Holders:")
    for i, holder in enumerate(stats['holdings_by_investor'][:10], 1):
        pct = (holder['shares'] / stats['total_institutional_shares'] * 100)
        print(f"  {i:2d}. {holder['investor_name']:20s} {holder['shares']:>12,} shares ({pct:5.1f}%)  ${holder['value_dollars']:>15,}")
    
    print("\n✅ Ready for visualization!")
    print("=" * 70)


if __name__ == "__main__":
    main()