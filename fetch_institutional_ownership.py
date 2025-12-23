"""
Quick fix script to correct the institutional ownership values
The text parser is extracting wrong numbers - let's use current stock price
Run this in: C:\MAMP\htdocs\stock-tracker\
"""

import json
from pathlib import Path

# Current WDAY stock price (approximate - update this!)
WDAY_PRICE = 241.50  # Check current price at finance.yahoo.com/quote/WDAY

def fix_values():
    """Fix the dollar values using share count * current price"""
    
    data_file = Path("public_data/institutional_ownership.json")
    cluster_file = Path("public_data/ownership_cluster.json")
    
    if not data_file.exists():
        print("❌ institutional_ownership.json not found")
        print(f"Looking in: {data_file.absolute()}")
        return
    
    # Load existing data
    with open(data_file, 'r') as f:
        stats = json.load(f)
    
    with open(cluster_file, 'r') as f:
        cluster = json.load(f)
    
    print(f"🔧 Fixing values using WDAY price: ${WDAY_PRICE}")
    print("\nBefore:")
    print(f"  Total Value: ${stats['total_institutional_value']:,.0f}")
    
    # Fix values in holdings_by_investor
    for holder in stats['holdings_by_investor']:
        correct_value = holder['shares'] * WDAY_PRICE
        old_value = holder.get('value_dollars', 0)
        holder['value_dollars'] = correct_value
        print(f"  {holder['investor_name']}: {holder['shares']:,} shares × ${WDAY_PRICE} = ${correct_value:,.2f}")
    
    # Recalculate totals
    stats['total_institutional_value'] = sum(h['value_dollars'] for h in stats['holdings_by_investor'])
    
    # Fix cluster data
    for item in cluster:
        item['value'] = item['shares'] * WDAY_PRICE
    
    print("\nAfter:")
    print(f"  Total Value: ${stats['total_institutional_value']:,.2f}")
    print(f"\nBreakdown:")
    for holder in stats['holdings_by_investor']:
        pct = (holder['shares'] / stats['total_institutional_shares'] * 100)
        print(f"  {holder['investor_name']}: ${holder['value_dollars']:,.0f} ({pct:.1f}%)")
    
    # Save corrected data
    with open(data_file, 'w') as f:
        json.dump(stats, f, indent=2)
    
    with open(cluster_file, 'w') as f:
        json.dump(cluster, f, indent=2)
    
    print(f"\n✅ Fixed values saved!")
    print(f"  - {data_file}")
    print(f"  - {cluster_file}")
    print("\n🎯 Now you can copy these files to frontend and build!")

if __name__ == "__main__":
    fix_values()