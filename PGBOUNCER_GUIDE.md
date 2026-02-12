# PgBouncer Setup & Load Testing Guide

## 🔧 PgBouncer Installation

### Windows
Since you're on Windows, you have two options:

#### Option 1: Docker (Recommended)
```powershell
# Create docker-compose.yml with PgBouncer service
docker-compose up -d pgbouncer
```

#### Option 2: WSL2 + Ubuntu
```bash
# In WSL2 Ubuntu terminal
sudo apt update
sudo apt install pgbouncer -y

# Copy config files
sudo cp pgbouncer.ini /etc/pgbouncer/
sudo cp userlist.txt /etc/pgbouncer/

# Generate MD5 hash for userlist.txt
echo -n "changeme corpuslio_user" | md5sum
# Replace <YOUR_MD5_HASH_HERE> in userlist.txt with output

# Start PgBouncer
sudo systemctl start pgbouncer
sudo systemctl enable pgbouncer
sudo systemctl status pgbouncer
```

## 📝 Django Settings Update

Update `settings.py` to use PgBouncer:

```python
# Before (Direct PostgreSQL):
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': 'localhost',
        'PORT': '5432',  # PostgreSQL port
        'NAME': 'corpuslio_db',
        'USER': 'corpuslio_user',
        'PASSWORD': 'changeme',
        'CONN_MAX_AGE': 600,
    }
}

# After (Through PgBouncer):
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': 'localhost',
        'PORT': '6432',  # PgBouncer port
        'NAME': 'corpuslio_db',
        'USER': 'corpuslio_user',
        'PASSWORD': 'changeme',
        'CONN_MAX_AGE': 0,  # Important: Disable Django connection pooling
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}
```

**Critical:** Set `CONN_MAX_AGE=0` to disable Django's connection pooling since PgBouncer handles it.

## 🚀 Load Testing with Locust

### Installation
```powershell
pip install locust
```

### Running Tests

#### 1. Basic Test (50 users)
```powershell
cd C:\Users\user\OneDrive\Belgeler\GitHub\corpuslio
locust -f locustfile.py --host=http://localhost:8000 --users 50 --spawn-rate 5
```

Then open: http://localhost:8089

#### 2. Headless Stress Test (100 users, 5 minutes)
```powershell
locust -f locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 10 --run-time 5m --headless
```

#### 3. Progressive Load Test
```powershell
# Start with 20 users
locust -f locustfile.py --host=http://localhost:8000 --users 20 --spawn-rate 2 --run-time 2m --headless

# Then 50 users
locust -f locustfile.py --host=http://localhost:8000 --users 50 --spawn-rate 5 --run-time 3m --headless

# Then 100 users
locust -f locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 10 --run-time 5m --headless
```

## 📊 Performance Baseline Metrics

### Target Metrics (After PgBouncer)
- **Response Time (p95)**: <500ms for search
- **Requests/sec**: >50 RPS
- **Error Rate**: <1%
- **Concurrency**: 50+ users without connection errors

### What to Monitor

#### 1. Django Dev Server
```powershell
# Terminal 1: Run Django
python manage.py runserver
```

#### 2. PostgreSQL Connections
```sql
-- Check active connections
SELECT count(*) FROM pg_stat_activity WHERE datname = 'corpuslio_db';

-- Should stay under 50 with PgBouncer
```

#### 3. PgBouncer Stats
```bash
# Connect to PgBouncer admin console
psql -h 127.0.0.1 -p 6432 -U corpuslio_user pgbouncer

# Check pool stats
SHOW POOLS;
SHOW STATS;
SHOW SERVERS;
```

## 🐛 Troubleshooting

### PgBouncer Connection Errors
```bash
# Check PgBouncer logs
sudo tail -f /var/log/pgbouncer/pgbouncer.log

# Test direct connection
psql -h 127.0.0.1 -p 6432 -U corpuslio_user corpuslio_db
```

### Django Connection Issues
```python
# Verify Django can connect through PgBouncer
python manage.py dbshell
```

### Rate Limiting
If you get 429 errors, temporarily disable rate limiting:
```python
# settings.py
RATELIMIT_ENABLE = False
```

## 📈 Expected Results

### Without PgBouncer (Baseline)
- 20 users: OK
- 50 users: Connection exhaustion
- 100 users: FAIL (too many connections)

### With PgBouncer
- 20 users: <200ms avg
- 50 users: <300ms avg
- 100 users: <500ms avg
- Connection pooling prevents exhaustion

## 🎯 Success Criteria

- ✅ PgBouncer running and accepting connections
- ✅ Django connects through port 6432
- ✅ 50 concurrent users with <500ms p95 response time
- ✅ No connection exhaustion errors
- ✅ Database connections stay under 50
- ✅ Requests/sec > 50 RPS

## 📁 Files Created
- `pgbouncer.ini` - PgBouncer configuration
- `userlist.txt` - Authentication file
- `locustfile.py` - Load test scenarios
- `PGBOUNCER_GUIDE.md` - This guide

## Next Steps
1. Install PgBouncer
2. Configure userlist.txt with MD5 hashes
3. Update Django settings.py (PORT: 6432, CONN_MAX_AGE: 0)
4. Restart Django
5. Run load tests
6. Document baseline metrics
