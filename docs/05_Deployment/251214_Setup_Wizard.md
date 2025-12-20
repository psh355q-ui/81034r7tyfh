# AI Trading System - Setup Wizard

**Date**: 2025-12-14
**Author**: Development Team
**Version**: 1.0
**Difficulty**: Beginner-friendly

## Welcome! 🎯

This step-by-step guide will help you set up the AI Trading System from scratch. No prior experience with Docker or trading systems required. Just follow the steps carefully, and you'll have a fully functional system running in about 30-45 minutes.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Step 1: Install Required Software](#step-1-install-required-software)
3. [Step 2: Get KIS API Credentials](#step-2-get-kis-api-credentials)
4. [Step 3: Download the Project](#step-3-download-the-project)
5. [Step 4: Configure Environment Variables](#step-4-configure-environment-variables)
6. [Step 5: Start the System](#step-5-start-the-system)
7. [Step 6: Verify Everything Works](#step-6-verify-everything-works)
8. [Step 7: Access the Application](#step-7-access-the-application)
9. [Optional: Advanced Setup](#optional-advanced-setup)
10. [Next Steps](#next-steps)

---

## 1. Prerequisites

### What You Need

- **Computer**: Windows 10/11, macOS, or Linux
- **RAM**: At least 8GB (16GB recommended)
- **Disk Space**: At least 10GB free
- **Internet**: Stable connection for downloading and API access
- **Time**: 30-45 minutes for first-time setup

### What You'll Install

- Git (for downloading code)
- Docker Desktop (runs all services)
- Python 3.11+ (for backend)
- Node.js 18+ (for frontend)

Don't worry if you don't have these yet - we'll install them together!

---

## Step 1: Install Required Software

### 1.1 Install Git

**Windows**:
1. Download: https://git-scm.com/download/win
2. Run installer with default settings
3. Verify installation:
```bash
git --version
# Should show: git version 2.x.x
```

**macOS**:
```bash
# Using Homebrew
brew install git

# Or download from: https://git-scm.com/download/mac
```

**Linux (Ubuntu/Debian)**:
```bash
sudo apt update
sudo apt install git
```

### 1.2 Install Docker Desktop

**Windows**:
1. Download: https://www.docker.com/products/docker-desktop/
2. Run installer
3. Restart computer when prompted
4. Start Docker Desktop
5. Verify installation:
```bash
docker --version
docker-compose --version
```

**macOS**:
1. Download Docker Desktop for Mac
2. Drag to Applications folder
3. Launch Docker Desktop
4. Grant permissions when requested

**Linux**:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install docker.io docker-compose

# Add your user to docker group
sudo usermod -aG docker $USER

# Log out and log back in
```

**Troubleshooting Docker**:
- If Docker Desktop won't start, enable virtualization in BIOS
- Windows: Enable WSL 2 if prompted
- macOS: Grant disk access in System Preferences → Privacy

### 1.3 Install Python 3.11+

**Windows**:
1. Download: https://www.python.org/downloads/
2. Run installer
3. ⚠️ **IMPORTANT**: Check "Add Python to PATH"
4. Click "Install Now"
5. Verify:
```bash
python --version
# Should show: Python 3.11.x or higher
```

**macOS**:
```bash
# Using Homebrew
brew install python@3.11
```

**Linux**:
```bash
sudo apt update
sudo apt install python3.11 python3-pip
```

### 1.4 Install Node.js 18+

**Windows**:
1. Download: https://nodejs.org/ (LTS version)
2. Run installer with default settings
3. Verify:
```bash
node --version
npm --version
```

**macOS**:
```bash
# Using Homebrew
brew install node@18
```

**Linux**:
```bash
# Using NodeSource repository
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

✅ **Checkpoint**: Verify all installations
```bash
git --version
docker --version
python --version
node --version
```

All commands should show version numbers without errors.

---

## Step 2: Get KIS API Credentials

### 2.1 Create KIS Developer Account

1. **Go to KIS Developer Portal**:
   - Visit: https://apiportal.koreainvestment.com/

2. **Sign Up**:
   - Click "회원가입" (Sign Up)
   - Fill in your information
   - Verify your email

3. **Login**:
   - Use your new credentials to login

### 2.2 Create Application

1. **Navigate to "My Applications"**:
   - Click "나의 애플리케이션" in the menu

2. **Create New Application**:
   - Click "신규 등록" (New Registration)
   - Application Name: "AI Trading System"
   - Description: "Personal AI trading system"
   - Submit

3. **Get Your Credentials**:
   You'll receive:
   - **APP_KEY**: Starts with "PS" (e.g., PSxxxxxx...)
   - **APP_SECRET**: 36-character string

   ⚠️ **IMPORTANT**: Save these somewhere safe! You'll need them soon.

### 2.3 Get Account Information

You also need your trading account details:

1. **Account Number**:
   - Format: XXXXXXXX-XX
   - Find in your KIS trading app

2. **Account Code**:
   - `01` for real trading account
   - `02` for virtual/paper trading account

### 2.4 Choose Trading Mode

**For Beginners** (Recommended):
- Use **Virtual Trading** (모의투자)
- Base URL: `https://openapivts.koreainvestment.com:29443`
- No real money involved
- Perfect for testing

**For Experienced Users**:
- Use **Real Trading** (실전투자)
- Base URL: `https://openapi.koreainvestment.com:9443`
- Uses real money
- Requires account verification

📝 **Note Down**:
```
APP_KEY: PS________________________
APP_SECRET: ____________________________
ACCOUNT_NUMBER: ________-__
ACCOUNT_CODE: 01 or 02
BASE_URL: (virtual or real)
```

---

## Step 3: Download the Project

### 3.1 Choose Installation Location

Pick a folder for the project. For example:
- Windows: `C:\Users\YourName\Projects\`
- macOS/Linux: `~/projects/`

### 3.2 Clone Repository

Open terminal/command prompt and run:

```bash
# Navigate to your chosen folder
cd C:\Users\YourName\Projects  # Windows
# or
cd ~/projects  # macOS/Linux

# Clone the repository
git clone https://github.com/your-org/ai-trading-system.git

# Enter project folder
cd ai-trading-system
```

### 3.3 Verify Project Structure

```bash
# List files
dir  # Windows
ls   # macOS/Linux
```

You should see:
```
backend/
frontend/
docker-compose.yml
.env.example
README.md
```

---

## Step 4: Configure Environment Variables

### 4.1 Create .env File

**Windows**:
```bash
copy .env.example .env
```

**macOS/Linux**:
```bash
cp .env.example .env
```

### 4.2 Edit .env File

Open `.env` in any text editor (Notepad, VS Code, etc.)

### 4.3 Configure KIS Credentials

Find these lines and replace with your actual values:

```env
# KIS API Configuration (REQUIRED)
KIS_APP_KEY=PSxxxxxxxxxxxxxxxxxxxxxx  # Replace with your APP_KEY
KIS_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  # Replace with your APP_SECRET
KIS_ACCOUNT_NUMBER=12345678-01  # Replace with your account number
KIS_ACCOUNT_CODE=02  # 01 for real, 02 for virtual

# For Virtual Trading (Recommended for beginners)
KIS_BASE_URL=https://openapivts.koreainvestment.com:29443

# For Real Trading (Comment out the above, use this instead)
# KIS_BASE_URL=https://openapi.koreainvestment.com:9443
```

### 4.4 Configure Database (Use Defaults or Customize)

**Option A: Use Defaults** (Easiest)
- Just leave these as-is:
```env
DB_USER=trading_user
DB_PASSWORD=secure_password_123
DB_NAME=trading_db
```

**Option B: Customize** (More Secure)
- Change password to something strong:
```env
DB_PASSWORD=YourStrongPassword123!@#
```

### 4.5 Configure Optional Features

**Gemini AI** (Optional - for AI analysis):
```env
# Get free API key from: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=AIzaSy...

# Leave blank if you don't want AI features
# GEMINI_API_KEY=
```

**Redis Cache** (Optional - improves performance):
```env
# Enable caching (recommended)
REDIS_ENABLED=true

# Or disable
# REDIS_ENABLED=false
```

**Log Level**:
```env
# For beginners: INFO (less verbose)
APP_LOG_LEVEL=INFO

# For debugging: DEBUG (very verbose)
# APP_LOG_LEVEL=DEBUG
```

### 4.6 Save and Verify

1. Save the `.env` file
2. Verify it exists:

```bash
# Windows
dir .env

# macOS/Linux
ls -la .env
```

✅ **Checkpoint**: Your `.env` file should have:
- KIS_APP_KEY (starts with PS)
- KIS_APP_SECRET (36 characters)
- KIS_ACCOUNT_NUMBER (format: XXXXXXXX-XX)
- KIS_BASE_URL (virtual or real)

---

## Step 5: Start the System

### 5.1 Start Docker Services

```bash
# Make sure Docker Desktop is running first!

# Start all services
docker-compose up -d
```

This will:
- Download required images (first time only - takes 5-10 minutes)
- Start PostgreSQL database
- Start Redis cache
- Start Elasticsearch, Logstash, Kibana (ELK Stack)
- Start backend and frontend

You'll see output like:
```
Creating ai-trading-postgres ... done
Creating ai-trading-redis ... done
Creating ai-trading-elasticsearch ... done
...
```

### 5.2 Wait for Services to Start

Services need time to initialize (about 1-2 minutes):

```bash
# Check status
docker-compose ps

# Wait until all show "Up (healthy)" or "Up"
```

**Expected Output**:
```
Name                    State          Ports
---------------------------------------------------------
ai-trading-backend      Up             0.0.0.0:8001->8001/tcp
ai-trading-frontend     Up             0.0.0.0:3002->3000/tcp
ai-trading-postgres     Up (healthy)   0.0.0.0:5432->5432/tcp
ai-trading-redis        Up             0.0.0.0:6379->6379/tcp
ai-trading-elasticsearch Up            0.0.0.0:9200->9200/tcp
...
```

### 5.3 Initialize Database

```bash
# Enter backend directory
cd backend

# Run database migrations
alembic upgrade head
```

You should see:
```
INFO  [alembic.runtime.migration] Running upgrade -> xxxx, Initial schema
INFO  [alembic.runtime.migration] Running upgrade xxxx -> yyyy, Add indexes
```

### 5.4 Verify Services

**Check Backend**:
```bash
curl http://localhost:8001/api/health
```

Expected response:
```json
{"status":"healthy","timestamp":"2025-12-14T..."}
```

**Check Frontend** (open in browser):
```
http://localhost:3002
```

You should see the login page.

**Check Database**:
```bash
docker exec -it ai-trading-postgres psql -U trading_user -d trading_db -c "\dt"
```

Should list database tables.

✅ **Checkpoint**: All services should be running and responding.

---

## Step 6: Verify Everything Works

### 6.1 Test KIS Connection

```bash
# Test KIS authentication
curl http://localhost:8001/api/kis/status
```

**Expected Response**:
```json
{
  "authenticated": true,
  "account_number": "12345678-01",
  "api_mode": "virtual"
}
```

**If You See Errors**:
- Check your KIS credentials in `.env`
- Verify BASE_URL matches your account type (virtual vs real)
- Make sure APP_KEY starts with "PS"

### 6.2 Test Account Balance

```bash
curl http://localhost:8001/api/kis/balance
```

Should show your account balance and holdings.

### 6.3 Test Stock Quote

```bash
# Get Samsung Electronics stock price
curl http://localhost:8001/api/market/quote/005930
```

Should return current price data.

### 6.4 View Logs

**All Logs**:
```bash
docker-compose logs --tail=50
```

**Backend Only**:
```bash
docker-compose logs backend --tail=50
```

**Follow Logs Live**:
```bash
docker-compose logs -f backend
```

Press `Ctrl+C` to stop following.

**Look for**:
- ✅ "Logging initialized"
- ✅ "Application startup complete"
- ✅ "KIS client initialized"
- ❌ No error messages

---

## Step 7: Access the Application

### 7.1 Open Frontend

1. **Open browser** (Chrome, Firefox, Safari)
2. **Go to**: http://localhost:3002
3. **You should see**: Login/Registration page

### 7.2 Create Account

1. Click "Sign Up" or "Register"
2. Fill in:
   - Username
   - Email
   - Password
3. Click "Register"

### 7.3 Login

1. Enter your credentials
2. Click "Login"
3. You should see the dashboard

### 7.4 Explore Features

**Dashboard**:
- Account balance
- Holdings
- Recent trades

**Market Data**:
- Search for stocks (try "005930" for Samsung)
- View real-time prices
- See charts

**Trading** (Virtual Mode Only for Testing):
- Place test orders
- View order history
- Monitor positions

### 7.5 Access Additional Tools

**Kibana (Logs & Monitoring)**:
- URL: http://localhost:5601
- Username: (none required initially)
- Navigate to "Discover" to see logs

**API Documentation**:
- URL: http://localhost:8001/docs
- Interactive API testing interface

**Database Admin** (Optional):
```bash
docker exec -it ai-trading-postgres psql -U trading_user -d trading_db
```

---

## Optional: Advanced Setup

### Enable AI Features

If you have a Gemini API key:

1. **Get API Key**:
   - Visit: https://makersuite.google.com/app/apikey
   - Sign in with Google
   - Create API key

2. **Add to .env**:
```env
GEMINI_API_KEY=AIzaSy...
```

3. **Restart Backend**:
```bash
docker-compose restart backend
```

4. **Test AI**:
```bash
curl http://localhost:8001/api/ai/analyze/005930
```

### Setup Email Notifications

```env
# SMTP Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Enable notifications
EMAIL_NOTIFICATIONS=true
```

**Gmail App Password**:
1. Go to Google Account settings
2. Security → 2-Step Verification
3. App passwords → Generate
4. Use generated password in SMTP_PASSWORD

### Configure Trading Limits

```env
# Risk Management
MAX_POSITION_SIZE=1000000  # Maximum 1M KRW per position
MAX_DAILY_LOSS=100000      # Stop trading if daily loss exceeds 100K KRW
MAX_DAILY_TRADES=50        # Maximum trades per day
```

### Enable Trading Bots

⚠️ **CAUTION**: Only use bots in virtual trading mode until you're confident!

```env
# Trading Bot Configuration
TRADING_BOT_ENABLED=false  # Set to true to enable

# Strategy
TRADING_STRATEGY=momentum  # Options: momentum, mean_reversion, ml_based

# Bot Settings
BOT_CHECK_INTERVAL=60      # Check every 60 seconds
BOT_MIN_CONFIDENCE=0.7     # Only trade when confidence > 70%
```

---

## Next Steps

### For Beginners

1. **Learn the Interface**:
   - Explore all dashboard features
   - Try searching different stocks
   - View charts and market data

2. **Test Trading (Virtual Mode)**:
   - Place small virtual trades
   - Monitor your positions
   - Review trade history

3. **Study the Logs**:
   - Open Kibana (http://localhost:5601)
   - Watch logs as you use the system
   - Learn what's happening behind the scenes

4. **Read Documentation**:
   - [Performance Tuning Guide](./251214_Performance_Tuning.md)
   - [Security Best Practices](./251214_Security_Best_Practices.md)
   - [Troubleshooting Guide](./251214_Troubleshooting_Guide.md)

### For Advanced Users

1. **Customize Strategy**:
   - Edit `backend/ai/strategies/*.py`
   - Implement your own trading logic
   - Backtest before deploying

2. **Set Up CI/CD**:
   - Configure GitHub Actions
   - Automated testing
   - Deployment pipeline

3. **Production Deployment**:
   - Set up cloud hosting (AWS, GCP, Azure)
   - Configure SSL/TLS
   - Implement monitoring and alerts

4. **Integrate Additional Data Sources**:
   - News APIs
   - Social sentiment
   - Alternative data

### Learning Resources

**Korean Stock Market**:
- Trading hours: 09:00-15:30 KST
- After-hours: 15:40-16:00 KST
- Settlement: T+2 (trade day + 2 days)

**KIS API Documentation**:
- https://apiportal.koreainvestment.com/
- API reference guides
- Sample code

**System Architecture**:
- Review `docs/01_Architecture/`
- Understand component interactions
- Study data flow diagrams

---

## Maintenance

### Daily Checks

```bash
# Check system health
docker-compose ps

# View recent logs
docker-compose logs --tail=100

# Check disk space
docker system df
```

### Weekly Tasks

```bash
# Update dependencies
cd backend
pip install --upgrade -r requirements.txt

cd ../frontend
npm update

# Cleanup old logs
docker-compose logs --tail=0 > /dev/null
```

### Backup

**Database Backup**:
```bash
# Backup database
docker exec ai-trading-postgres pg_dump -U trading_user trading_db > backup_$(date +%Y%m%d).sql

# Restore from backup
docker exec -i ai-trading-postgres psql -U trading_user trading_db < backup_20251214.sql
```

**Environment Backup**:
```bash
# Backup .env file (remove sensitive data before sharing!)
cp .env .env.backup
```

### Updates

```bash
# Pull latest code
git pull origin main

# Rebuild containers
docker-compose down
docker-compose build
docker-compose up -d

# Run migrations
cd backend
alembic upgrade head
```

---

## Stopping the System

### Stop Services (Temporary)

```bash
# Stop all services but keep data
docker-compose stop
```

### Stop and Remove (but keep data)

```bash
# Stop and remove containers, but volumes (data) remain
docker-compose down
```

### Complete Cleanup (⚠️ Deletes ALL Data)

```bash
# Remove everything including database data
docker-compose down -v
```

### Restart Services

```bash
# After stopping
docker-compose start

# Or restart everything
docker-compose restart
```

---

## Getting Help

### Check Logs First

Most problems show up in logs:
```bash
docker-compose logs backend --tail=100
```

### Use Troubleshooting Guide

See [Troubleshooting Guide](./251214_Troubleshooting_Guide.md) for:
- Common errors and solutions
- Debugging techniques
- FAQ

### Search Documentation

All guides are in `docs/` folder:
- `01_Architecture/` - System design
- `02_Phase_Reports/` - Development history
- `05_Deployment/` - Setup and operations

### Test Individual Components

```bash
# Test database
docker exec -it ai-trading-postgres psql -U trading_user -d trading_db -c "SELECT 1;"

# Test backend
curl http://localhost:8001/api/health

# Test frontend
curl http://localhost:3002
```

---

## Success Checklist

✅ All software installed (Git, Docker, Python, Node.js)
✅ KIS API credentials obtained
✅ Project downloaded and configured
✅ All Docker services running
✅ Database initialized
✅ Backend health check passes
✅ Frontend accessible in browser
✅ KIS connection successful
✅ Can view stock quotes
✅ Can place virtual trades
✅ Logs visible in Kibana

If you've checked all these items - **Congratulations!** 🎉

Your AI Trading System is fully operational!

---

## Appendix

### Environment Variables Reference

```env
# KIS API (Required)
KIS_APP_KEY=              # Your APP KEY from KIS
KIS_APP_SECRET=           # Your APP SECRET from KIS
KIS_ACCOUNT_NUMBER=       # Format: XXXXXXXX-XX
KIS_ACCOUNT_CODE=         # 01=real, 02=virtual
KIS_BASE_URL=             # API endpoint URL

# Database (Required)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=trading_db
DB_USER=trading_user
DB_PASSWORD=              # Change to secure password

# Redis (Optional)
REDIS_ENABLED=true
REDIS_HOST=localhost
REDIS_PORT=6379

# AI Features (Optional)
GEMINI_API_KEY=           # For AI analysis

# Application
APP_ENV=development       # or production
APP_LOG_LEVEL=INFO        # or DEBUG
APP_SECRET_KEY=           # Auto-generated

# Frontend
FRONTEND_URL=http://localhost:3002

# Email (Optional)
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
EMAIL_NOTIFICATIONS=false
```

### Port Reference

| Service | Port | URL |
|---------|------|-----|
| Backend API | 8001 | http://localhost:8001 |
| Frontend | 3002 | http://localhost:3002 |
| PostgreSQL | 5432 | localhost:5432 |
| Redis | 6379 | localhost:6379 |
| Elasticsearch | 9200 | http://localhost:9200 |
| Kibana | 5601 | http://localhost:5601 |
| Logstash | 5044 | localhost:5044 |

### Useful Commands

```bash
# Docker
docker-compose ps                  # List containers
docker-compose logs -f backend     # Follow backend logs
docker-compose restart backend     # Restart backend
docker-compose down -v             # Remove everything

# Database
docker exec -it ai-trading-postgres psql -U trading_user -d trading_db

# Backend
cd backend
uvicorn main:app --reload          # Run backend directly
pytest tests/                       # Run tests
alembic upgrade head               # Run migrations

# Frontend
cd frontend
npm run dev                        # Run frontend directly
npm run build                      # Build for production
```

---

**Congratulations on setting up your AI Trading System!**

Remember:
- Start with **virtual trading** to learn the system
- Monitor logs regularly
- Keep credentials secure
- Test thoroughly before using real money

Happy trading! 📈

---

**Last Updated**: 2025-12-14
**Version**: 1.0
