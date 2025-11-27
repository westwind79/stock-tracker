import requests
import sys
import json
from datetime import datetime

class WorkdayInsiderTradingTester:
    def __init__(self, base_url="https://executive-selloff.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def test_api_root(self):
        """Test API root endpoint"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                expected_message = "Workday Insider Trading Tracker API"
                success = data.get("message") == expected_message
                details = f"Status: {response.status_code}, Message: {data.get('message', 'N/A')}"
            else:
                details = f"Status: {response.status_code}"
                
            self.log_test("API Root Endpoint", success, details)
            return success
            
        except Exception as e:
            self.log_test("API Root Endpoint", False, str(e))
            return False

    def test_get_transactions(self):
        """Test GET /api/transactions endpoint"""
        try:
            response = requests.get(f"{self.api_url}/transactions", timeout=15)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = isinstance(data, list)
                details = f"Status: {response.status_code}, Transactions count: {len(data)}"
                
                # Check transaction structure if data exists
                if data and len(data) > 0:
                    first_trans = data[0]
                    required_fields = ['id', 'executive_name', 'transaction_date', 'transaction_type', 
                                     'shares', 'price_per_share', 'total_value', 'filing_date']
                    missing_fields = [field for field in required_fields if field not in first_trans]
                    if missing_fields:
                        success = False
                        details += f", Missing fields: {missing_fields}"
                    else:
                        details += f", Sample transaction: {first_trans['executive_name']} - {first_trans['transaction_type']}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
                
            self.log_test("GET Transactions", success, details)
            return success, response.json() if success else []
            
        except Exception as e:
            self.log_test("GET Transactions", False, str(e))
            return False, []

    def test_get_stats(self):
        """Test GET /api/stats endpoint"""
        try:
            response = requests.get(f"{self.api_url}/stats", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                required_fields = ['total_sales_value', 'total_transactions', 'unique_executives', 'last_updated']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    success = False
                    details = f"Missing fields: {missing_fields}"
                else:
                    details = f"Sales: ${data['total_sales_value']:,.0f}, Transactions: {data['total_transactions']}, Executives: {data['unique_executives']}, Updated: {data['last_updated']}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
                
            self.log_test("GET Stats", success, details)
            return success, response.json() if success else {}
            
        except Exception as e:
            self.log_test("GET Stats", False, str(e))
            return False, {}

    def test_get_executives(self):
        """Test GET /api/executives endpoint"""
        try:
            response = requests.get(f"{self.api_url}/executives", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = isinstance(data, list)
                details = f"Status: {response.status_code}, Executives count: {len(data)}"
                
                # Check executive structure if data exists
                if data and len(data) > 0:
                    first_exec = data[0]
                    required_fields = ['name', 'total_sales', 'transaction_count', 'latest_transaction']
                    missing_fields = [field for field in required_fields if field not in first_exec]
                    if missing_fields:
                        success = False
                        details += f", Missing fields: {missing_fields}"
                    else:
                        details += f", Top executive: {first_exec['name']} - ${first_exec['total_sales']:,.0f} in sales"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
                
            self.log_test("GET Executives", success, details)
            return success, response.json() if success else []
            
        except Exception as e:
            self.log_test("GET Executives", False, str(e))
            return False, []

    def test_refresh_transactions(self):
        """Test POST /api/transactions/refresh endpoint"""
        try:
            print("🔄 Testing data refresh (this may take 30-60 seconds)...")
            response = requests.post(f"{self.api_url}/transactions/refresh", timeout=90)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                expected_fields = ['success', 'transactions_count', 'message']
                missing_fields = [field for field in expected_fields if field not in data]
                
                if missing_fields:
                    success = False
                    details = f"Missing fields: {missing_fields}"
                else:
                    details = f"Success: {data['success']}, Count: {data['transactions_count']}, Message: {data['message']}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:300]}"
                
            self.log_test("POST Refresh Transactions", success, details)
            return success, response.json() if success else {}
            
        except Exception as e:
            self.log_test("POST Refresh Transactions", False, str(e))
            return False, {}

    def run_all_tests(self):
        """Run all backend API tests"""
        print("🚀 Starting Workday Insider Trading API Tests")
        print(f"📍 Testing against: {self.api_url}")
        print("=" * 60)
        
        # Test API root
        self.test_api_root()
        
        # Test GET endpoints first
        transactions_success, transactions_data = self.test_get_transactions()
        stats_success, stats_data = self.test_get_stats()
        executives_success, executives_data = self.test_get_executives()
        
        # Test refresh endpoint (this might take time)
        refresh_success, refresh_data = self.test_refresh_transactions()
        
        # If refresh worked, test GET endpoints again to verify data was updated
        if refresh_success:
            print("\n🔄 Re-testing GET endpoints after refresh...")
            self.test_get_transactions()
            self.test_get_stats()
            self.test_get_executives()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print("⚠️  Some tests failed. Check the details above.")
            return 1

def main():
    tester = WorkdayInsiderTradingTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())