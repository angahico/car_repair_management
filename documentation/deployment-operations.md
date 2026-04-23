# Deployment & Operations

## Production Deployment

### Prerequisites
- Frappe Bench with ERPNext v15+
- Python 3.11+
- Node.js 18+
- MariaDB 10.6+
- Redis 6+
- Nginx (reverse proxy)
- Supervisor (process management)

### Installation

```bash
bench get-app https://github.com/selfmadecs/car_repair_management.git
bench --site your-site.com install-app car_repair_management
bench --site your-site.com migrate
```

### Frontend Build

```bash
cd apps/car_repair_management/frontend
yarn install
yarn build
```

Build output goes to `car_repair_management/public/frontend/` and is served statically via Nginx.

## Restart Procedures

### ⚠️ Gunicorn with --preload

This deployment uses gunicorn with `--preload` flag. This means:
- **`kill -HUP` is NOT sufficient** for Python changes — the preloaded app module won't reload
- Must kill the master PID and let supervisor restart it

### After Python/Backend Changes

```bash
# Kill all gunicorn processes
pkill -9 -f "gunicorn.*frappe"

# Wait for supervisor to restart (10-15 seconds)
sleep 12

# Verify restart
pgrep -a "gunicorn.*frappe" | head -3
```

### After Frontend Changes

```bash
cd apps/car_repair_management/frontend
yarn build

# No gunicorn restart needed for frontend-only changes
# Nginx serves static files directly
```

### After Python + Frontend Changes

```bash
# Build frontend first
cd apps/car_repair_management/frontend && yarn build

# Then restart gunicorn
pkill -9 -f "gunicorn.*frappe"
sleep 12
pgrep -a "gunicorn.*frappe" | head -3
```

### After DocType Schema Changes

```bash
bench --site your-site.com migrate
pkill -9 -f "gunicorn.*frappe"
sleep 12
```

## Process Architecture

### Supervisor Configuration

```
[program:frappe-bench-frappe-web]
command=gunicorn -b 127.0.0.1:8000 -w 9 --max-requests 5000
        --max-requests-jitter 500 -t 120 --graceful-timeout 30
        frappe.app:application --preload
```

### Services

| Service | Port | Purpose |
|---|---|---|
| Gunicorn | 8000 | Web server (9 workers) |
| Redis Cache | 13000 | Caching, Socket.IO pub/sub |
| Redis Queue | 11000 | Background job queue |
| Socket.IO | 9000 | Real-time updates |
| MariaDB | 3306 | Database |

## Scheduled Tasks

| Frequency | Task | Description |
|---|---|---|
| Hourly | `execute_scheduled_reports` | Run due Workshop Report Schedules |
| Daily | `update_job_costing_snapshots` | Refresh Job Costing for all Repair Orders |

Verify scheduler is running:
```bash
bench --site your-site.com doctor
```

## Monitoring

### Logs

```bash
# Web server logs
tail -f logs/web.*.log

# Worker logs
tail -f logs/worker.*.log

# Frappe error logs
bench --site your-site.com console
>>> frappe.get_all("Error Log", limit=5, order_by="creation desc")
```

### Health Checks

```bash
# Check all processes
pgrep -a "gunicorn\|redis\|node.*socketio"

# Check site status
curl -s http://127.0.0.1:8000/api/method/frappe.ping

# Check database
bench --site your-site.com mariadb -e "SELECT 1"
```

## Cache Management

```bash
# Clear cache
bench --site your-site.com clear-cache

# Clear website cache
bench --site your-site.com clear-website-cache

# Build assets
bench build --app car_repair_management
```

## Database Operations

```bash
# Run migrations
bench --site your-site.com migrate

# Database console
bench --site your-site.com mariadb

# Python console with Frappe context
bench --site your-site.com console

# Backup
bench --site your-site.com backup
```

## Testing

```bash
# Enable tests (required first)
bench --site your-site.com set-config allow_tests true

# Run all app tests
bench --site your-site.com run-tests --app car_repair_management

# Single test file
bench --site your-site.com run-tests --app car_repair_management \
  --test apps/car_repair_management/car_repair_management/tests/test_file.py
```

## Debugging

Create a debug script:

```python
# apps/car_repair_management/car_repair_management/debug.py
def execute():
    import frappe
    # Your debug code here
    print(frappe.db.get_all("Repair Order", limit=5))
```

Run it:
```bash
bench --site your-site.com execute car_repair_management.debug.execute
```

**Important**: Delete the debug file after use.
