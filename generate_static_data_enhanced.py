"""
Enhanced Static JSON Generator for Workday Insider Trading Tracker
Scrapes SEC EDGAR and generates JSON files with MORE historical data
"""

import requests
import json
import time
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Configuration
CIK = "0001327811"  # Workday Inc.
OUTPUT_DIR = Path("./public_data")
OUTPUT_DIR.mkdir(exist_ok=True)

# Increased from 15 to 50 for better historical data
NUM_FILINGS_TO_FETCH = 50

def fetch_sec_filings(cik=CIK, form_type="4"):
    """Fetch recent SEC Form 4 filings"""
    headers = {
        'User-Agent': 'InsiderTracker contact@example.com',
        'Accept-Encoding': 'gzip, deflate',
        'Host': 'www.sec.gov'
    }
    
    url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type={form_type}&dateb=&owner=include&count=100&search_text="
    
    print(f"Fetching SEC filings from: {url}")
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response.text


def parse_sec_filings_list(html_content):
    """Parse SEC filings list to extract document links"""
    soup = BeautifulSoup(html_content, 'html.parser')
    filings = []
    
    table = soup.find('table', {'class': 'tableFile2'})
    if not table:
        return filings
    
    rows = table.find_all('tr')[1:]  # Skip header
    
    for row in rows[:100]:  # Get up to 100 filings
        cols = row.find_all('td')
        if len(cols) >= 4:
            filing_type = cols[0].text.strip()
            filing_date = cols[3].text.strip()
            documents_link = cols[1].find('a')
            
            if documents_link and filing_type == '4':
                doc_url = "https://www.sec.gov" + documents_link['href']
                filings.append({
                    'filing_date': filing_date,
                    'documents_url': doc_url
                })
    
    print(f"Found {len(filings)} Form 4 filings")
    return filings


def parse_form4_xml(xml_content, filing_date):
    """Parse Form 4 XML to extract transactions"""
    transactions = []
    
    try:
        root = ET.fromstring(xml_content)
        
        # Extract owner info
        owner = root.find('.//reportingOwner')
        if owner is None:
            return transactions
            
        owner_name_elem = owner.find('.//rptOwnerName')
        if owner_name_elem is None:
            return transactions
            
        owner_name = owner_name_elem.text
        
        # Extract title
        title_elem = owner.find('.//reportingOwnerRelationship/officerTitle')
        title = title_elem.text if title_elem is not None else "Executive"
        
        # Parse transactions
        for trans in root.findall('.//nonDerivativeTransaction'):
            try:
                trans_date = trans.find('.//transactionDate/value')
                shares = trans.find('.//transactionAmounts/transactionShares/value')
                price = trans.find('.//transactionAmounts/transactionPricePerShare/value')
                acquired_disposed = trans.find('.//transactionAmounts/transactionAcquiredDisposedCode/value')
                
                if all([trans_date is not None, shares is not None, price is not None]):
                    trans_date_str = trans_date.text
                    shares_val = float(shares.text)
                    price_val = float(price.text)
                    total_val = shares_val * price_val
                    
                    acq_disp = acquired_disposed.text if acquired_disposed is not None else "D"
                    trans_type = "Sale" if acq_disp == "D" else "Purchase"
                    
                    transactions.append({
                        'id': f"{owner_name}_{trans_date_str}_{shares_val}",
                        'executive_name': owner_name,
                        'executive_title': title,
                        'transaction_date': trans_date_str,
                        'transaction_type': trans_type,
                        'shares': shares_val,
                        'price_per_share': price_val,
                        'total_value': total_val,
                        'filing_date': filing_date,
                        'form_type': 'Form 4',
                        'created_at': datetime.now().isoformat()
                    })
            except Exception as e:
                print(f"  Error parsing transaction: {e}")
                continue
                
    except Exception as e:
        print(f"  Error parsing XML: {e}")
    
    return transactions


def fetch_and_parse_form4(documents_url, filing_date):
    """Fetch Form 4 XML and parse it"""
    headers = {
        'User-Agent': 'InsiderTracker contact@example.com',
        'Accept-Encoding': 'gzip, deflate',
        'Host': 'www.sec.gov'
    }
    
    try:
        # Fetch documents page
        response = requests.get(documents_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find XML link
        for link in soup.find_all('a'):
            href = link.get('href', '')
            if '.xml' in href and 'xslF345X' not in href:
                xml_url = "https://www.sec.gov" + href if href.startswith('/') else href
                
                # Fetch XML
                time.sleep(0.3)  # Rate limiting
                xml_response = requests.get(xml_url, headers=headers, timeout=10)
                xml_response.raise_for_status()
                
                return parse_form4_xml(xml_response.text, filing_date)
        
    except Exception as e:
        print(f"  Error fetching XML: {e}")
    
    return []


def generate_stats(transactions):
    """Calculate dashboard statistics"""
    if not transactions:
        return {
            'total_sales_value': 0,
            'total_transactions': 0,
            'unique_executives': 0,
            'last_updated': 'Never'
        }
    
    total_sales = sum(
        t['total_value'] for t in transactions 
        if t.get('transaction_type') == 'Sale'
    )
    
    unique_execs = len(set(t['executive_name'] for t in transactions))
    
    return {
        'total_sales_value': total_sales,
        'total_transactions': len(transactions),
        'unique_executives': unique_execs,
        'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    }


def generate_executives_summary(transactions):
    """Generate executive-level summary"""
    exec_data = {}
    
    for trans in transactions:
        name = trans['executive_name']
        if name not in exec_data:
            exec_data[name] = {
                'name': name,
                'total_sales': 0,
                'transaction_count': 0,
                'latest_transaction': trans['transaction_date']
            }
        
        if trans.get('transaction_type') == 'Sale':
            exec_data[name]['total_sales'] += trans['total_value']
        
        exec_data[name]['transaction_count'] += 1
        
        if trans['transaction_date'] > exec_data[name]['latest_transaction']:
            exec_data[name]['latest_transaction'] = trans['transaction_date']
    
    # Convert to list and sort
    result = list(exec_data.values())
    result.sort(key=lambda x: x['total_sales'], reverse=True)
    
    return result


def generate_price_history(transactions):
    """Generate price history data for Chart.js"""
    # Filter only sales with valid prices
    sales = [t for t in transactions if t.get('transaction_type') == 'Sale' and t.get('price_per_share', 0) > 0]
    
    if not sales:
        return []
    
    # Group by date and calculate average price
    by_date = defaultdict(list)
    for sale in sales:
        by_date[sale['transaction_date']].append(sale['price_per_share'])
    
    # Calculate daily averages
    price_history = []
    for date, prices in sorted(by_date.items()):
        avg_price = sum(prices) / len(prices)
        price_history.append({
            'date': date,
            'price': round(avg_price, 2),
            'transactions': len(prices)
        })
    
    return price_history


def main():
    """Main execution"""
    print("=" * 60)
    print("SEC EDGAR Data Scraper - Workday Insider Trading")
    print("ENHANCED VERSION - Fetching more historical data")
    print("=" * 60)
    
    # Step 1: Fetch filings list
    print("\n[1/5] Fetching SEC filings list...")
    html_content = fetch_sec_filings()
    if not html_content:
        print("ERROR: Failed to fetch SEC data")
        return
    
    # Step 2: Parse filings
    print("\n[2/5] Parsing filings list...")
    filings = parse_sec_filings_list(html_content)
    
    # Step 3: Fetch and parse each Form 4
    print(f"\n[3/5] Processing {min(NUM_FILINGS_TO_FETCH, len(filings))} Form 4 documents...")
    all_transactions = []
    
    for i, filing in enumerate(filings[:NUM_FILINGS_TO_FETCH], 1):
        print(f"  Processing filing {i}/{min(NUM_FILINGS_TO_FETCH, len(filings))}... ", end="")
        transactions = fetch_and_parse_form4(
            filing['documents_url'],
            filing['filing_date']
        )
        all_transactions.extend(transactions)
        print(f"Found {len(transactions)} transactions")
        time.sleep(0.3)  # Rate limiting
    
    # Sort by transaction date
    all_transactions.sort(key=lambda x: x.get('transaction_date', ''), reverse=True)
    
    # Step 4: Generate price history
    print(f"\n[4/5] Generating price history chart data...")
    price_history = generate_price_history(all_transactions)
    print(f"  Created {len(price_history)} historical price points")
    
    # Step 5: Generate JSON files
    print(f"\n[5/5] Generating JSON files...")
    
    # transactions.json
    transactions_file = OUTPUT_DIR / "transactions.json"
    with open(transactions_file, 'w') as f:
        json.dump(all_transactions, f, indent=2)
    print(f"  ✓ Created {transactions_file} ({len(all_transactions)} transactions)")
    
    # stats.json
    stats = generate_stats(all_transactions)
    stats_file = OUTPUT_DIR / "stats.json"
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"  ✓ Created {stats_file}")
    
    # executives.json
    executives = generate_executives_summary(all_transactions)
    executives_file = OUTPUT_DIR / "executives.json"
    with open(executives_file, 'w') as f:
        json.dump(executives, f, indent=2)
    print(f"  ✓ Created {executives_file} ({len(executives)} executives)")
    
    # price_history.json (NEW)
    price_file = OUTPUT_DIR / "price_history.json"
    with open(price_file, 'w') as f:
        json.dump(price_history, f, indent=2)
    print(f"  ✓ Created {price_file} ({len(price_history)} price points)")
    
    print("\n" + "=" * 60)
    print("SUCCESS! JSON files ready for upload")
    print("=" * 60)
    print(f"\nGenerated files in: {OUTPUT_DIR.absolute()}")
    print(f"\nData Summary:")
    print(f"  - Total transactions: {len(all_transactions)}")
    print(f"  - Date range: {price_history[-1]['date'] if price_history else 'N/A'} to {price_history[0]['date'] if price_history else 'N/A'}")
    print(f"  - Total sales value: ${stats['total_sales_value']:,.2f}")
    print("\nNext steps:")
    print("1. Upload these files to: /public_html/workday/data/")
    print("2. The app will now show a price history chart!")


if __name__ == "__main__":
    main()