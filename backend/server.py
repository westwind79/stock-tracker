from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import time


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class InsiderTransaction(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    executive_name: str
    executive_title: Optional[str] = None
    transaction_date: str
    transaction_type: str  # Sale, Purchase, etc.
    shares: float
    price_per_share: float
    total_value: float
    filing_date: str
    form_type: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ExecutiveSummary(BaseModel):
    name: str
    total_sales: float
    transaction_count: int
    latest_transaction: str


class DashboardStats(BaseModel):
    total_sales_value: float
    total_transactions: int
    unique_executives: int
    last_updated: str


# SEC EDGAR API helper functions
def fetch_sec_filings(cik: str = "0001327811", form_type: str = "4"):
    """
    Fetch recent SEC Form 4 filings for Workday (CIK: 0001327811)
    """
    headers = {
        'User-Agent': 'InsiderTracker contact@example.com',
        'Accept-Encoding': 'gzip, deflate',
        'Host': 'www.sec.gov'
    }
    
    url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type={form_type}&dateb=&owner=include&count=100&search_text="
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logging.error(f"Error fetching SEC filings: {e}")
        return None


def parse_sec_filings_list(html_content: str):
    """
    Parse the SEC filings list page to extract document links
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    filings = []
    
    table = soup.find('table', {'class': 'tableFile2'})
    if not table:
        return filings
    
    rows = table.find_all('tr')[1:]  # Skip header
    
    for row in rows[:20]:  # Limit to recent 20 filings
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
    
    return filings


def parse_form4_xml(xml_content: str, filing_date: str):
    """
    Parse Form 4 XML to extract transaction details
    """
    transactions = []
    
    try:
        root = ET.fromstring(xml_content)
        
        # Extract reporting owner info
        owner = root.find('.//reportingOwner')
        if owner is None:
            return transactions
            
        owner_name_elem = owner.find('.//rptOwnerName')
        if owner_name_elem is None:
            return transactions
            
        owner_name = owner_name_elem.text
        
        # Extract title if available
        title_elem = owner.find('.//reportingOwnerRelationship/officerTitle')
        title = title_elem.text if title_elem is not None else "Executive"
        
        # Parse non-derivative transactions
        for trans in root.findall('.//nonDerivativeTransaction'):
            try:
                trans_date = trans.find('.//transactionDate/value')
                trans_code = trans.find('.//transactionCoding/transactionCode')
                shares = trans.find('.//transactionAmounts/transactionShares/value')
                price = trans.find('.//transactionAmounts/transactionPricePerShare/value')
                acquired_disposed = trans.find('.//transactionAmounts/transactionAcquiredDisposedCode/value')
                
                if all([trans_date is not None, shares is not None, price is not None]):
                    trans_date_str = trans_date.text
                    shares_val = float(shares.text)
                    price_val = float(price.text)
                    total_val = shares_val * price_val
                    
                    code = trans_code.text if trans_code is not None else "S"
                    acq_disp = acquired_disposed.text if acquired_disposed is not None else "D"
                    
                    trans_type = "Sale" if acq_disp == "D" else "Purchase"
                    
                    transactions.append({
                        'executive_name': owner_name,
                        'executive_title': title,
                        'transaction_date': trans_date_str,
                        'transaction_type': trans_type,
                        'shares': shares_val,
                        'price_per_share': price_val,
                        'total_value': total_val,
                        'filing_date': filing_date,
                        'form_type': 'Form 4'
                    })
            except Exception as e:
                logging.error(f"Error parsing transaction: {e}")
                continue
                
    except Exception as e:
        logging.error(f"Error parsing Form 4 XML: {e}")
    
    return transactions


def fetch_and_parse_form4(documents_url: str, filing_date: str):
    """
    Fetch the Form 4 XML from the documents page
    """
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
                time.sleep(0.2)  # Be nice to SEC servers
                xml_response = requests.get(xml_url, headers=headers, timeout=10)
                xml_response.raise_for_status()
                
                return parse_form4_xml(xml_response.text, filing_date)
        
    except Exception as e:
        logging.error(f"Error fetching Form 4 XML: {e}")
    
    return []


# API Routes
@api_router.get("/")
async def root():
    return {"message": "Workday Insider Trading Tracker API"}


@api_router.get("/transactions", response_model=List[InsiderTransaction])
async def get_transactions():
    """
    Get all cached transactions from database
    """
    try:
        transactions = await db.transactions.find({}, {"_id": 0}).to_list(1000)
        
        # Convert ISO string timestamps back to datetime objects
        for trans in transactions:
            if isinstance(trans.get('created_at'), str):
                trans['created_at'] = datetime.fromisoformat(trans['created_at'])
        
        # Sort by transaction date descending
        transactions.sort(key=lambda x: x.get('transaction_date', ''), reverse=True)
        
        return transactions
    except Exception as e:
        logging.error(f"Error fetching transactions: {e}")
        raise HTTPException(status_code=500, detail="Error fetching transactions")


@api_router.post("/transactions/refresh")
async def refresh_transactions():
    """
    Fetch fresh data from SEC EDGAR and update database
    """
    try:
        # Fetch SEC filings list
        html_content = fetch_sec_filings()
        if not html_content:
            raise HTTPException(status_code=500, detail="Failed to fetch SEC data")
        
        filings = parse_sec_filings_list(html_content)
        
        all_transactions = []
        for filing in filings[:15]:  # Process last 15 filings
            transactions = fetch_and_parse_form4(
                filing['documents_url'],
                filing['filing_date']
            )
            all_transactions.extend(transactions)
            time.sleep(0.3)  # Rate limiting
        
        # Clear old data and insert new
        await db.transactions.delete_many({})
        
        if all_transactions:
            # Convert to InsiderTransaction objects
            trans_objects = []
            for trans in all_transactions:
                trans_obj = InsiderTransaction(**trans)
                doc = trans_obj.model_dump()
                doc['created_at'] = doc['created_at'].isoformat()
                trans_objects.append(doc)
            
            await db.transactions.insert_many(trans_objects)
        
        return {
            "success": True,
            "transactions_count": len(all_transactions),
            "message": f"Successfully refreshed {len(all_transactions)} transactions"
        }
        
    except Exception as e:
        logging.error(f"Error refreshing transactions: {e}")
        raise HTTPException(status_code=500, detail=f"Error refreshing data: {str(e)}")


@api_router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    """
    Get dashboard statistics
    """
    try:
        transactions = await db.transactions.find({}, {"_id": 0}).to_list(1000)
        
        if not transactions:
            return DashboardStats(
                total_sales_value=0,
                total_transactions=0,
                unique_executives=0,
                last_updated="Never"
            )
        
        # Calculate stats
        total_sales = sum(
            t['total_value'] for t in transactions 
            if t.get('transaction_type') == 'Sale'
        )
        
        unique_execs = len(set(t['executive_name'] for t in transactions))
        
        # Get most recent update
        latest = max(
            (t.get('created_at') for t in transactions if t.get('created_at')),
            default=None
        )
        
        if isinstance(latest, str):
            latest = datetime.fromisoformat(latest)
        
        last_updated = latest.strftime("%Y-%m-%d %H:%M UTC") if latest else "Unknown"
        
        return DashboardStats(
            total_sales_value=total_sales,
            total_transactions=len(transactions),
            unique_executives=unique_execs,
            last_updated=last_updated
        )
        
    except Exception as e:
        logging.error(f"Error calculating stats: {e}")
        raise HTTPException(status_code=500, detail="Error calculating statistics")


@api_router.get("/executives", response_model=List[ExecutiveSummary])
async def get_executives():
    """
    Get executive-level summary
    """
    try:
        transactions = await db.transactions.find({}, {"_id": 0}).to_list(1000)
        
        # Group by executive
        exec_data = {}
        for trans in transactions:
            name = trans['executive_name']
            if name not in exec_data:
                exec_data[name] = {
                    'name': name,
                    'total_sales': 0,
                    'transaction_count': 0,
                    'latest_date': trans['transaction_date']
                }
            
            if trans.get('transaction_type') == 'Sale':
                exec_data[name]['total_sales'] += trans['total_value']
            
            exec_data[name]['transaction_count'] += 1
            
            if trans['transaction_date'] > exec_data[name]['latest_date']:
                exec_data[name]['latest_date'] = trans['transaction_date']
        
        # Convert to list and sort by total sales
        result = [
            ExecutiveSummary(
                name=data['name'],
                total_sales=data['total_sales'],
                transaction_count=data['transaction_count'],
                latest_transaction=data['latest_date']
            )
            for data in exec_data.values()
        ]
        
        result.sort(key=lambda x: x.total_sales, reverse=True)
        
        return result
        
    except Exception as e:
        logging.error(f"Error fetching executives: {e}")
        raise HTTPException(status_code=500, detail="Error fetching executives")


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
