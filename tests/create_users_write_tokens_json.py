import requests
import json
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock


class UserRegistrationBot:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.register_url = f"{base_url}/auth/register/"
        self.token_url = f"{base_url}/auth/token/"
        self.tokens = []
        self.lock = Lock()
        self.successful_registrations = 0
        self.failed_registrations = 0

    def generate_user_data(self, index):
        """Generate user data for registration"""
        return {
            "username": f"user{index:04d}",
            "password": f"password{index:04d}",
            "full_name": f"User {index:04d}",
            "phone_number": f"+998{90000000 + index:08d}",  # Uzbekistan phone format
        }

    def register_user(self, user_data):
        """Register a single user"""
        try:
            response = requests.post(
                self.register_url,
                json=user_data,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )

            if response.status_code == 201:
                print(f"✓ User {user_data['username']} registered successfully")
                return True, user_data
            else:
                print(
                    f"✗ Failed to register {user_data['username']}: {response.status_code} - {response.text}"
                )
                return False, None

        except requests.exceptions.RequestException as e:
            print(f"✗ Network error registering {user_data['username']}: {str(e)}")
            return False, None

    def get_token(self, user_data):
        """Get authentication token for a user"""
        try:
            login_data = {
                "username": user_data["username"],
                "password": user_data["password"],
            }

            response = requests.post(
                self.token_url,
                json=login_data,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )

            if response.status_code == 200:
                token_data = response.json()
                # Extract access token (assuming JWT response format)
                access_token = token_data.get("access")
                if access_token:
                    print(f"✓ Token obtained for {user_data['username']}")
                    return access_token
                else:
                    print(f"✗ No access token in response for {user_data['username']}")
                    return None
            else:
                print(
                    f"✗ Failed to get token for {user_data['username']}: {response.status_code} - {response.text}"
                )
                return None

        except requests.exceptions.RequestException as e:
            print(
                f"✗ Network error getting token for {user_data['username']}: {str(e)}"
            )
            return None

    def process_user(self, index):
        """Process a single user: register and get token"""
        user_data = self.generate_user_data(index)

        # Register user
        success, registered_user = self.register_user(user_data)
        if not success:
            with self.lock:
                self.failed_registrations += 1
            return None

        # Reduced delay for faster processing in parallel mode
        time.sleep(0.05)

        # Get token
        token = self.get_token(registered_user)
        if token:
            with self.lock:
                self.tokens.append(token)
                self.successful_registrations += 1
            return token
        else:
            with self.lock:
                self.failed_registrations += 1
            return None

    def create_users_sequential(self, count=1000):
        """Create users sequentially (slower but more reliable)"""
        print(f"Starting sequential user creation for {count} users...")

        for i in range(1, count + 1):
            print(f"Processing user {i}/{count}")
            self.process_user(i)

            # Progress update every 50 users
            if i % 50 == 0:
                print(
                    f"Progress: {i}/{count} users processed. Success: {self.successful_registrations}, Failed: {self.failed_registrations}"
                )

    def create_users_parallel(self, count=1000, max_workers=20):
        """Create users in parallel with optimized threading"""
        print(
            f"Starting simultaneous user creation for {count} users with {max_workers} worker threads..."
        )

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks simultaneously
            futures = [
                executor.submit(self.process_user, i) for i in range(1, count + 1)
            ]

            # Process completed tasks as they finish
            completed_count = 0
            for future in as_completed(futures):
                completed_count += 1
                try:
                    result = future.result()
                    # More frequent progress updates for better visibility
                    if completed_count % 25 == 0 or completed_count == count:
                        print(
                            f"Progress: {completed_count}/{count} users processed. Success: {self.successful_registrations}, Failed: {self.failed_registrations}"
                        )
                except Exception as e:
                    print(f"Error processing user: {str(e)}")
                    with self.lock:
                        self.failed_registrations += 1

    def save_tokens_to_file(self, filename="user_tokens.json"):
        """Save tokens to JSON file"""
        try:
            data = {
                "tokens": self.tokens,
                "total_tokens": len(self.tokens),
                "successful_registrations": self.successful_registrations,
                "failed_registrations": self.failed_registrations,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            }

            with open(filename, "w") as f:
                json.dump(data, f, indent=2)

            print(f"✓ Tokens saved to {filename}")
            print(f"Total tokens saved: {len(self.tokens)}")

        except Exception as e:
            print(f"✗ Error saving tokens to file: {str(e)}")

    def run(self, count=1000, parallel=True, max_workers=20):
        """Main method to run the bot - now optimized for simultaneous threading"""
        print(f"Starting user registration bot...")
        print(f"Target: {count} users")
        print(f"Base URL: {self.base_url}")
        print(f"Mode: {'Simultaneous Threading' if parallel else 'Sequential'}")
        print(f"Worker Threads: {max_workers if parallel else 1}")
        print("-" * 50)

        start_time = time.time()

        try:
            if parallel:
                self.create_users_parallel(count, max_workers)
            else:
                self.create_users_sequential(count)

            end_time = time.time()
            duration = end_time - start_time

            print("-" * 50)
            print(f"Registration completed in {duration:.2f} seconds")
            print(f"Average time per user: {duration/count:.3f} seconds")
            print(f"Successful registrations: {self.successful_registrations}")
            print(f"Failed registrations: {self.failed_registrations}")
            print(f"Success rate: {(self.successful_registrations/count)*100:.1f}%")
            print(f"Total tokens collected: {len(self.tokens)}")

            # Save tokens to file
            self.save_tokens_to_file()

        except KeyboardInterrupt:
            print("\n⚠ Process interrupted by user")
            print(
                f"Partial results: {self.successful_registrations} successful, {self.failed_registrations} failed"
            )
            if self.tokens:
                self.save_tokens_to_file("partial_tokens.json")

        except Exception as e:
            print(f"✗ Unexpected error: {str(e)}")
            if self.tokens:
                self.save_tokens_to_file("error_tokens.json")


def main():
    # Configuration
    BASE_URL = "http://localhost:9000"  # Change this to your server URL
    USER_COUNT = 100
    PARALLEL_MODE = True  # Now defaults to True for simultaneous threading
    MAX_WORKERS = (
        20  # Increased for better parallelism (adjust based on server capacity)
    )

    # Create and run the bot
    bot = UserRegistrationBot(BASE_URL)
    bot.run(count=USER_COUNT, parallel=PARALLEL_MODE, max_workers=MAX_WORKERS)


if __name__ == "__main__":
    main()
