"""
Update existing WDAY JSON files with accurate institutional ownership and current price
Modifies files in place - run this in the same directory as your JSON files
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

def get_current_price():
    """Fetch current WDAY stock price from Yahoo Finance"""
    try:
        url = "https://finance.yahoo.com/quote/WDAY/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Try to find price element
        price_element = soup.find('fin-streamer', {'data-symbol': 'WDAY', 'data-field': 'regularMarketPrice'})
        if price_element:
            price_value = price_element.get('data-value')
            if price_value:
                return float(price_value)
            else:
                return float(price_element.text.strip())
        
        print("Warning: Could not fetch current price from Yahoo Finance")
        return None
    except Exception as e:
        print(f"Error fetching price: {e}")
        return None

def get_institutional_ownership():
    """Fetch institutional ownership from Yahoo Finance holders page"""
    try:
        url = "https://finance.yahoo.com/quote/WDAY/holders/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        holders = []
        
        # Find all tables on the page
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            
            # Look for institutional holder data
            for row in rows[1:]:  # Skip header row
                cols = row.find_all('td')
                
                if len(cols) >= 4:
                    try:
                        # Extract data from columns
                        name = cols[0].text.strip()
                        shares_text = cols[1].text.strip().replace(',', '')
                        date_text = cols[2].text.strip()
                        percent_text = cols[3].text.strip().replace('%', '')
                        value_text = cols[4].text.strip().replace(',', '') if len(cols) > 4 else '0'
                        
                        # Skip if this looks like a header row
                        if 'Holder' in name or not shares_text:
                            continue
                        
                        # Parse shares (handle M, B suffixes)
                        shares = 0
                        if 'M' in shares_text:
                            shares = int(float(shares_text.replace('M', '')) * 1_000_000)
                        elif 'B' in shares_text:
                            shares = int(float(shares_text.replace('B', '')) * 1_000_000_000)
                        else:
                            try:
                                shares = int(float(shares_text))
                            except:
                                continue
                        
                        # Parse value (handle M, B suffixes)
                        value = 0
                        if 'M' in value_text:
                            value = int(float(value_text.replace('M', '')) * 1_000_000)
                        elif 'B' in value_text:
                            value = int(float(value_text.replace('B', '')) * 1_000_000_000)
                        else:
                            try:
                                value = int(float(value_text))
                            except:
                                value = 0
                        
                        # Parse percentage
                        try:
                            percent = float(percent_text)
                        except:
                            percent = 0.0
                        
                        # Parse date (format: "Sep 30, 2025")
                        try:
                            filing_date = datetime.strptime(date_text, '%b %d, %Y').strftime('%Y-%m-%d')
                        except:
                            filing_date = date_text
                        
                        holders.append({
                            'name': name,
                            'shares': shares,
                            'value': value,
                            'percent': percent,
                            'filing_date': filing_date
                        })
                        
                        # Get top 10 holders
                        if len(holders) >= 10:
                            break
                            
                    except Exception as e:
                        print(f"Error parsing row: {e}")
                        continue
                
                if len(holders) >= 10:
                    break
            
            if len(holders) >= 10:
                break
        
        return holders
        
    except Exception as e:
        print(f"Error fetching institutional ownership: {e}")
        return []

def update_json_files():
    """Update all JSON files with fresh data"""
    
    print("=" * 60)
    print("WDAY Data Updater")
    print("=" * 60)
    print()
    
    # Get fresh data
    print("[1/3] Fetching current stock price...")
    current_price = get_current_price()
    if current_price:
        print(f"✓ Current WDAY price: ${current_price:.2f}")
    else:
        print("✗ Could not fetch current price")
    print()
    
    print("[2/3] Fetching institutional ownership data...")
    institutional_holders = get_institutional_ownership()
    if institutional_holders:
        print(f"✓ Found {len(institutional_holders)} institutional holders")
        print(f"   Top holder: {institutional_holders[0]['name']} with {institutional_holders[0]['shares']:,} shares")
    else:
        print("✗ Could not fetch institutional ownership data")
    print()
    
    # Update stats.json with current price
    print("[3/3] Updating JSON files...")
    try:
        with open('stats.json', 'r') as f:
            stats = json.load(f)
        
        if current_price:
            stats['current_price'] = current_price
        stats['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M UTC')
        
        with open('stats.json', 'w') as f:
            json.dump(stats, f, indent=2)
        print("✓ Updated stats.json with current price")
    except Exception as e:
        print(f"✗ Error updating stats.json: {e}")
    
    # Update institutional_ownership.json
    if institutional_holders:
        try:
            total_shares = sum(h['shares'] for h in institutional_holders)
            total_value = sum(h['value'] for h in institutional_holders)
            
            institutional_data = {
                'total_institutional_shares': total_shares,
                'total_institutional_value': total_value,
                'number_of_institutions': len(institutional_holders),
                'largest_holder': institutional_holders[0]['name'],
                'largest_holder_shares': institutional_holders[0]['shares'],
                'largest_holder_percent': institutional_holders[0]['percent'],
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M UTC'),
                'holdings_by_investor': [
                    {
                        'investor_name': h['name'],
                        'shares': h['shares'],
                        'value_dollars': h['value'],
                        'percent_outstanding': h['percent'],
                        'filing_date': h['filing_date']
                    }
                    for h in institutional_holders
                ]
            }
            
            with open('institutional_ownership.json', 'w') as f:
                json.dump(institutional_data, f, indent=2)
            print("✓ Updated institutional_ownership.json with accurate data")
            
        except Exception as e:
            print(f"✗ Error updating institutional_ownership.json: {e}")
        
        # Update ownership_cluster.json (top 5 for charts)
        try:
            ownership_cluster = [
                {
                    'name': h['name'],
                    'shares': h['shares'],
                    'value': h['value'],
                    'percent': h['percent'],
                    'filing_date': h['filing_date']
                }
                for h in institutional_holders[:5]
            ]
            
            with open('ownership_cluster.json', 'w') as f:
                json.dump(ownership_cluster, f, indent=2)
            print("✓ Updated ownership_cluster.json with top 5 holders")
            
        except Exception as e:
            print(f"✗ Error updating ownership_cluster.json: {e}")
    
    print()
    print("=" * 60)
    print("Update Complete!")
    print("=" * 60)
    print()
    
    # Show summary
    if current_price:
        print(f"Current Stock Price: ${current_price:.2f}")
    if institutional_holders:
        print(f"Institutional Holders: {len(institutional_holders)}")
        print(f"Total Institutional Value: ${total_value:,.0f}")
        print(f"Top Holder: {institutional_holders[0]['name']} ({institutional_holders[0]['percent']}%)")
    print()
    print("Files updated:")
    print("  ✓ stats.json")
    if institutional_holders:
        print("  ✓ institutional_ownership.json")
        print("  ✓ ownership_cluster.json")
    print()
    print("Your existing files (transactions.json, executives.json, price_history.json)")
    print("remain unchanged.")
    print()

if __name__ == '__main__':
    update_json_files()