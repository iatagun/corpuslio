"""Locust load testing scenarios for CorpusLIO corpus search.

Usage:
    # Test with 50 concurrent users
    locust -f locustfile.py --host=http://localhost:8000 --users 50 --spawn-rate 5

    # Headless mode (no web UI)
    locust -f locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 10 --run-time 5m --headless
"""

from locust import HttpUser, task, between, events
import random
import json


class CorpusSearchUser(HttpUser):
    """Simulates a user performing corpus searches and analysis."""
    
    # Wait 1-3 seconds between tasks
    wait_time = between(1, 3)
    
    # Sample queries for realistic load testing
    search_queries = [
        "git", "gel", "yap", "ol", "et", "ver", "al", "gör", "bil", "çık",
        "çalış", "oku", "yaz", "konuş", "anla", "düşün", "iste", "söyle", "bul", "kullan"
    ]
    
    def on_start(self):
        """Login before starting tasks (if authentication required)."""
        # For anonymous access, skip login
        # For authenticated tests, uncomment:
        # self.client.post("/accounts/login/", {
        #     "username": "testuser",
        #     "password": "testpass"
        # })
        pass
    
    @task(5)
    def search_concordance(self):
        """Test KWIC concordance search (most common operation)."""
        query = random.choice(self.search_queries)
        with self.client.get(
            "/tr/corpus-search/",
            params={
                "q": query,
                "type": "form",
                "context": 5,
                "limit": 100
            },
            catch_response=True,
            name="/tr/corpus-search/ [concordance]"
        ) as response:
            if response.status_code == 200:
                if "results" in response.text or "Sonuç" in response.text:
                    response.success()
                else:
                    response.failure("No results in response")
            elif response.status_code == 429:
                response.failure("Rate limited")
            else:
                response.failure(f"Status {response.status_code}")
    
    @task(3)
    def search_with_regex(self):
        """Test regex pattern search."""
        patterns = [".*mak", ".*mek", "git.*", "gel.*", "^çık.*"]
        pattern = random.choice(patterns)
        
        with self.client.get(
            "/tr/corpus-search/",
            params={
                "q": pattern,
                "type": "lemma",
                "regex": "true",
                "limit": 50
            },
            catch_response=True,
            name="/tr/corpus-search/ [regex]"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                response.failure("Rate limited")
            else:
                response.failure(f"Status {response.status_code}")
    
    @task(2)
    def collocation_analysis(self):
        """Test collocation analysis."""
        keyword = random.choice(self.search_queries)
        
        with self.client.get(
            "/tr/collocation/",
            params={
                "keyword": keyword,
                "window": 5,
                "min_freq": 2
            },
            catch_response=True,
            name="/tr/collocation/"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                response.failure("Rate limited")
            else:
                response.failure(f"Status {response.status_code}")
    
    @task(2)
    def ngram_analysis(self):
        """Test n-gram extraction."""
        n = random.choice([2, 3])
        
        with self.client.get(
            "/tr/ngram-analysis/",
            params={
                "n": n,
                "min_freq": 2,
                "use_lemma": "true",
                "analyze": "1",
                "limit": 100
            },
            catch_response=True,
            name=f"/tr/ngram-analysis/ [n={n}]"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                response.failure("Rate limited")
            else:
                response.failure(f"Status {response.status_code}")
    
    @task(2)
    def frequency_analysis(self):
        """Test word frequency analysis."""
        with self.client.get(
            "/tr/frequency/",
            params={
                "use_lemma": "true",
                "min_length": 2,
                "analyze": "1",
                "limit": 100
            },
            catch_response=True,
            name="/tr/frequency/"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                response.failure("Rate limited")
            else:
                response.failure(f"Status {response.status_code}")
    
    @task(1)
    def library_view(self):
        """Test corpus library browsing."""
        with self.client.get(
            "/tr/library/",
            catch_response=True,
            name="/tr/library/"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")
    
    @task(1)
    def api_concordance(self):
        """Test JSON API endpoint."""
        query = random.choice(self.search_queries)
        
        with self.client.get(
            "/tr/api/concordance/",
            params={
                "q": query,
                "type": "form",
                "limit": 50
            },
            catch_response=True,
            name="/tr/api/concordance/"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "results" in data:
                        response.success()
                    else:
                        response.failure("No results in JSON")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON")
            else:
                response.failure(f"Status {response.status_code}")


class StressTestUser(HttpUser):
    """Stress test with heavy queries."""
    
    wait_time = between(0.5, 1.5)
    
    @task(1)
    def heavy_ngram(self):
        """Test large n-gram extraction (stress test)."""
        with self.client.get(
            "/tr/ngram-analysis/",
            params={
                "n": 3,
                "min_freq": 1,
                "analyze": "1",
                "limit": 500
            },
            catch_response=True,
            name="/tr/ngram-analysis/ [STRESS]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")
    
    @task(1)
    def heavy_frequency(self):
        """Test large frequency analysis (stress test)."""
        with self.client.get(
            "/tr/frequency/",
            params={
                "use_lemma": "false",
                "min_length": 1,
                "analyze": "1",
                "limit": 1000
            },
            catch_response=True,
            name="/tr/frequency/ [STRESS]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Print test configuration."""
    print("\n" + "="*60)
    print("🚀 CorpusLIO Load Test Starting")
    print("="*60)
    print(f"Target: {environment.host}")
    print(f"Users: {environment.runner.target_user_count if hasattr(environment.runner, 'target_user_count') else 'N/A'}")
    print("="*60 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print test summary."""
    print("\n" + "="*60)
    print("✅ CorpusLIO Load Test Complete")
    print("="*60)
    
    stats = environment.stats
    print(f"\nTotal Requests: {stats.total.num_requests}")
    print(f"Total Failures: {stats.total.num_failures}")
    print(f"Average Response Time: {stats.total.avg_response_time:.0f}ms")
    print(f"95th Percentile: {stats.total.get_response_time_percentile(0.95):.0f}ms")
    print(f"Requests/sec: {stats.total.total_rps:.2f}")
    print("="*60 + "\n")
