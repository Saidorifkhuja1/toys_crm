import json
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from faker import Faker
import requests

# Initialize Faker for generating realistic data
fake = Faker()

# Thread-safe counter for tracking progress
class ThreadSafeCounter:
    def __init__(self):
        self._value = 0
        self._lock = threading.Lock()
    
    def increment(self):
        with self._lock:
            self._value += 1
            return self._value
    
    @property
    def value(self):
        with self._lock:
            return self._value

# Global counter for progress tracking
counter = ThreadSafeCounter()

def load_tokens():
    """Load tokens from user_tokens.json file"""
    try:
        with open('tests/user_tokens.json', 'r') as f:
            data = json.load(f)
            tokens = data.get('tokens', [])
            if not tokens:
                raise ValueError("No tokens found in user_tokens.json")
            print(f"📱 Loaded {len(tokens)} tokens from user_tokens.json")
            return tokens
    except FileNotFoundError:
        print("❌ user_tokens.json file not found!")
        print("Please create user_tokens.json with format: {'tokens': ['token1', 'token2', ...]}")
        raise
    except json.JSONDecodeError:
        print("❌ Invalid JSON format in user_tokens.json")
        raise

def create_supplier(token, supplier_data):
    """Create a single supplier via HTTP request"""
    url = "http://localhost:9000/suppliers/"  # Adjust URL as needed
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    
    try:
        response = requests.post(url, json=supplier_data, headers=headers, timeout=30)
        
        if response.status_code == 201:
            return response.json()
        else:
            print(f"❌ Failed to create supplier: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {str(e)}")
        return None

def create_supplier_batch(batch_number, batch_size, tokens):
    """Create a batch of suppliers in a single thread"""
    suppliers_created = []
    
    try:
        for i in range(batch_size):
            # Select random token for this supplier
            token = random.choice(tokens)
            
            # Generate realistic supplier data
            supplier_data = {
                'full_name': fake.company(),
                'phone_number': fake.phone_number()[:20],  # Limit to 20 chars
            }
            
            # Create supplier via HTTP request
            result = create_supplier(token, supplier_data)
            
            if result:
                suppliers_created.append(result)
                
                # Update counter
                count = counter.increment()
                
                # Print progress every 10 suppliers
                if count % 10 == 0:
                    print(f"✓ Created {count} suppliers so far... (Thread {threading.current_thread().name})")
            else:
                print(f"⚠️  Failed to create supplier: {supplier_data['full_name']}")
        
        print(f"🎉 Batch {batch_number} completed: Created {len(suppliers_created)} suppliers")
        return suppliers_created
        
    except Exception as e:
        print(f"❌ Error in batch {batch_number}: {str(e)}")
        return []

def create_suppliers_threaded(total_suppliers=100, num_threads=10):
    """Create suppliers using multiple threads"""
    print(f"🚀 Starting to create {total_suppliers} suppliers using {num_threads} threads...")
    
    # Load tokens
    tokens = load_tokens()
    
    start_time = time.time()
    
    # Calculate batch size
    batch_size = total_suppliers // num_threads
    remaining = total_suppliers % num_threads
    
    all_suppliers = []
    
    # Use ThreadPoolExecutor for better thread management
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = []
        
        # Submit tasks to thread pool
        for i in range(num_threads):
            current_batch_size = batch_size + (1 if i < remaining else 0)
            if current_batch_size > 0:
                future = executor.submit(create_supplier_batch, i + 1, current_batch_size, tokens)
                futures.append(future)
        
        # Wait for all threads to complete and collect results
        for future in futures:
            try:
                suppliers_batch = future.result(timeout=120)  # 2 minute timeout
                all_suppliers.extend(suppliers_batch)
            except Exception as e:
                print(f"❌ Thread execution failed: {str(e)}")
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    print(f"\n🎊 COMPLETED!")
    print(f"📊 Total suppliers created: {len(all_suppliers)}")
    print(f"⏱️  Execution time: {execution_time:.2f} seconds")
    if execution_time > 0:
        print(f"🚀 Average speed: {len(all_suppliers) / execution_time:.2f} suppliers/second")
    
    return all_suppliers

def verify_suppliers():
    """Verify suppliers by fetching from API"""
    print("\n🔍 Verifying suppliers via API...")
    
    try:
        # Load tokens for verification
        tokens = load_tokens()
        token = random.choice(tokens)
        
        url = "http://localhost:9000/suppliers/"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            suppliers = response.json()
            if isinstance(suppliers, list):
                print(f"📈 Total suppliers retrieved: {len(suppliers)}")
                
                # Show some sample suppliers
                sample_suppliers = suppliers[:5]
                print("\n📋 Sample suppliers:")
                for supplier in sample_suppliers:
                    print(f"  • {supplier.get('full_name', 'N/A')} - {supplier.get('phone_number', 'N/A')}")
            else:
                print(f"📈 API response: {suppliers}")
        else:
            print(f"❌ Failed to fetch suppliers: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error verifying suppliers: {str(e)}")

def test_connection():
    """Test connection to the API"""
    print("🔗 Testing API connection...")
    
    try:
        tokens = load_tokens()
        token = random.choice(tokens)
        
        url = "http://localhost:9000/suppliers/"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code in [200, 401, 403]:
            print("✅ API connection successful")
            return True
        else:
            print(f"⚠️  API connection issue: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Connection test failed: {str(e)}")
        return False

def main():
    """Main function to run the supplier creation process"""
    print("=" * 60)
    print("🏭 SUPPLIER GENERATOR WITH HTTP REQUESTS & RANDOM TOKENS")
    print("=" * 60)
    
    try:
        # Test connection first
        if not test_connection():
            print("❌ Cannot proceed without API connection")
            return
        
        # Create suppliers
        suppliers = create_suppliers_threaded(total_suppliers=100, num_threads=10)
        
        # Verify creation
        verify_suppliers()
        
        print("\n✅ All done! Suppliers created successfully.")
        
    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")

if __name__ == "__main__":
    main()