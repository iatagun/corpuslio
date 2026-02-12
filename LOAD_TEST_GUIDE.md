# Load Test Execution Guide

## Problem Found
❌ **Django server wasn't running** → 100% request failures (4100ms timeout)

## Solution: Run Tests Properly

### Step 1: Start Django Server
```powershell
# Terminal 1 - Keep this running
cd corpuslio_django
python manage.py runserver
```

### Step 2: Run Load Test
```powershell
# Terminal 2 - In a NEW terminal window
cd C:\Users\user\OneDrive\Belgeler\GitHub\corpuslio
locust -f locustfile.py --host=http://localhost:8000 --users 20 --spawn-rate 2 --run-time 2m --headless
```

## Expected Results (working system)

### Good Results:
- ✅ **0-1% failure rate** (not 100%!)
- ✅ **Response time <500ms** for p95
- ✅ **RPS: 10-50+** depending on data
- ✅ **No connection errors**

### Current Results (broken):
- ❌ 100% failure rate
- ❌ 4100ms timeout (Django not responding)
- ❌ RPS: 3.5 (because all fail)

## Quick Test Command

After starting Django server, run this:

```powershell
# Small test (20 users, 1 minute)
locust -f locustfile.py --host=http://localhost:8000 --users 20 --spawn-rate 5 --run-time 1m --headless
```

You should see:
- Request count increasing
- Failures near 0%
- Response times around 100-300ms

## Next: Full Test Suite

Once Django is running:

```powershell
# Progressive tests
locust -f locustfile.py --host=http://localhost:8000 --users 20 --spawn-rate 2 --run-time 2m --headless
locust -f locustfile.py --host=http://localhost:8000 --users 50 --spawn-rate 5 --run-time 3m --headless
locust -f locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 10 --run-time 5m --headless
```
