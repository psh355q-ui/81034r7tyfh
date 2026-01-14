# 🚨 Real Trading Migration Guide

You are about to switch from **Paper Trading (Mock)** to **Real Trading (Live Money)**.
This process carries financial risk. Please follow these steps carefully to ensure your system is configured correctly and safely.

## 1. Safety Checklist (Pre-Flight)
- [ ] **Account Number**: Ensure you have your 8-digit KIS Account Number ready.
- [ ] **Capital Limit**: Decide on a maximum capital allocation (e.g., $1,000 for testing).
- [ ] **Stop Loss**: The system has a built-in daily stop loss (Default: -2%), but you should monitor it manually for the first few days.

## 2. Configuration (`.env` file)
Open your `.env` file and update the following variables:

```ini
# --- KIS Broker Configuration ---

# 1. Switch to Real Mode
KIS_IS_VIRTUAL=false

# 2. Set Real Account Number (Format: 12345678-01 or just 12345678)
KIS_ACCOUNT_NUMBER=YOUR_REAL_ACCOUNT_NUMBER
KIS_PRODUCT_CODE=01

# 3. Real Server Keys (Different from Virtual Keys!)
# Make sure these match your "Real Investment" API keys from KIS website
KIS_APP_KEY=YOUR_REAL_APP_KEY
KIS_APP_SECRET=YOUR_REAL_APP_SECRET
```

## 3. Execution (Running the Engine)
Use `run_live_trading.py` to start the engine. We recommend starting with strict limits.

### Recommended Command for First Run
```bash
python backend/run_live_trading.py --mode live --account YOUR_ACC_NUM --max-position-size 1000 --max-positions 2 --interval 300
```

- `--mode live`: Enables real order execution.
- `--max-position-size 1000`: Limits each trade to max $1,000.
- `--max-positions 2`: Only allows holding 2 positions at once.
- `--interval 300`: Checks for trades every 5 minutes.

## 4. Emergency Procedures
If the system behaves unexpectedly:
1.  **Ctrl+C**: Stop the script immediately in the terminal.
2.  **MTS/HTS**: Open your KIS Mobile/Desktop app and manually cancel orders or close positions.
3.  **Kill Switch**: The system will auto-stop if Daily P&L < -2%.

## 5. Verification
When you first run the script:
1.  It will display a **"LIVE TRADING MODE ENABLED"** warning.
2.  It will ask you to type **"YES I UNDERSTAND"** to proceed.
3.  On the first trade signal, it will ask for **Confirmation (y/n)** before sending the order (unless `--no-confirm` is used).

---
**Disclaimer**: This software is for educational and research purposes. The user assumes all responsibility for any financial losses incurred.
