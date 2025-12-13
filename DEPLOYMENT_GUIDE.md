# Deployment Guide - Workday Insider Trading Tracker

## Option 1: Deploy to Your Own Web Server

### Frontend (React)

#### Build the Frontend
```bash
cd /app/frontend
npm run build
# OR if you have yarn installed:
# yarn build
```

The build creates a `/app/frontend/build` folder with:
- `index.html` - Main HTML file
- `static/` - All JS, CSS, and assets

#### Deploy Frontend
Upload the contents of `/app/frontend/build/` to your web server:

**For Apache/Nginx:**
1. Copy all files from `build/` to your web root (e.g., `/var/www/html/`)
2. Configure your web server to serve `index.html` for all routes

**Nginx Configuration Example:**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /var/www/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to backend
    location /api {
        proxy_pass http://your-backend-server:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Apache Configuration Example (.htaccess):**
```apache
<IfModule mod_rewrite.c>
  RewriteEngine On
  RewriteBase /
  RewriteRule ^index\.html$ - [L]
  RewriteCond %{REQUEST_FILENAME} !-f
  RewriteCond %{REQUEST_FILENAME} !-d
  RewriteRule . /index.html [L]
</IfModule>
```

### Backend (FastAPI)

#### Requirements
- Python 3.11+
- MongoDB database
- All dependencies from `requirements.txt`

#### Setup Backend on Server

1. **Copy backend files:**
```bash
# Upload these files to your server:
/app/backend/server.py
/app/backend/requirements.txt
/app/backend/.env
```

2. **Install dependencies:**
```bash
cd /app/backend
pip install -r requirements.txt
```

3. **Configure environment variables (.env):**
```env
MONGO_URL=mongodb://your-mongodb-host:27017
DB_NAME=workday_insider_trading
CORS_ORIGINS=https://your-frontend-domain.com
```

4. **Run with production server (Gunicorn + Uvicorn):**
```bash
pip install gunicorn

# Run the server
gunicorn server:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8001
```

5. **Or use systemd service (recommended):**

Create `/etc/systemd/system/workday-tracker.service`:
```ini
[Unit]
Description=Workday Insider Trading Tracker API
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/path/to/backend
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn server:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8001

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable workday-tracker
sudo systemctl start workday-tracker
```

### Database (MongoDB)

#### Option A: Self-Hosted MongoDB
```bash
# Install MongoDB
sudo apt update
sudo apt install mongodb-org

# Start MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod
```

#### Option B: MongoDB Atlas (Free Tier)
1. Go to https://www.mongodb.com/cloud/atlas
2. Create free cluster
3. Get connection string
4. Update `MONGO_URL` in `.env`

### Update Frontend Environment

Before building, update `/app/frontend/.env`:
```env
REACT_APP_BACKEND_URL=https://your-backend-domain.com
```

Then rebuild:
```bash
cd /app/frontend
npm run build
```

---

## Option 2: Deploy on Emergent Platform (Easiest)

Simply click the **Deploy** button in the Emergent interface:
- ✅ Automatic infrastructure setup
- ✅ MongoDB included
- ✅ Public URL provided
- ✅ SSL/HTTPS enabled
- ✅ No server management needed
- 💰 50 credits/month

---

## Option 3: Deploy to Other Platforms

### Vercel (Frontend) + Railway (Backend + MongoDB)

**Frontend on Vercel:**
1. Push code to GitHub
2. Import to Vercel
3. Build command: `cd frontend && npm run build`
4. Output directory: `frontend/build`
5. Add environment variable: `REACT_APP_BACKEND_URL`

**Backend on Railway:**
1. Create new project on Railway
2. Add MongoDB service
3. Add Python service
4. Point to `/app/backend`
5. Set environment variables
6. Railway will auto-deploy

### DigitalOcean App Platform

1. Create new app
2. Add two components:
   - Web Service (backend) - Python
   - Static Site (frontend) - Node.js
3. Add MongoDB managed database
4. Configure build commands
5. Set environment variables

### AWS (EC2 + S3 + DocumentDB)

- **Frontend:** S3 + CloudFront
- **Backend:** EC2 with Auto Scaling
- **Database:** DocumentDB (MongoDB-compatible)

---

## Files Ready for Download

All your built files are in:
- **Frontend:** `/app/frontend/build/` (static files ready to upload)
- **Backend:** `/app/backend/` (Python files + requirements.txt)

You can download these and deploy anywhere!

---

## Quick Test Locally

After building, test the static frontend:
```bash
cd /app/frontend/build
python3 -m http.server 8080
```

Visit: http://localhost:8080

---

## Important Notes

1. **API Endpoint:** Make sure your frontend's `REACT_APP_BACKEND_URL` points to your backend
2. **CORS:** Update `CORS_ORIGINS` in backend `.env` to allow your frontend domain
3. **MongoDB:** Ensure MongoDB is accessible from your backend server
4. **SEC API:** No API key needed - it's completely free!
5. **Rate Limiting:** SEC requests have built-in delays (0.2-0.3s) to be respectful

---

## Need Help?

If deploying to your own server seems complex, the Emergent deployment option handles all of this automatically with just one click!
