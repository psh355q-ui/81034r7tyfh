
import sys
import os
import logging
import sys
import os
import logging
from pprint import pprint, pformat

# Add project root to path
sys.path.insert(0, os.getcwd())

import backend.trading.kis_client as kc
import backend.trading.overseas_stock as osf
from dotenv import load_dotenv

# Load env
load_dotenv()

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.FileHandler("logs/debug/debug_log.txt", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Redirect print to logger for consistency
def print(*args, **kwargs):
    logger.info(" ".join(map(str, args)))

def debug_balance():
    print("=== Debugging KIS Overseas Balance ===")
    
    # Check credentials
    key = os.getenv("KIS_APP_KEY")
    secret = os.getenv("KIS_APP_SECRET")
    acc = os.getenv("KIS_ACCOUNT_NUMBER")
    
    print(f"Account: {acc}")
    print(f"Key exists: {bool(key)}")
    print(f"Secret exists: {bool(secret)}")
    
    if not (key and secret and acc):
        print("Missing credentials in .env")
        return

    # Parse Account Number
    # KIS requires CANO (8 digits) and PRDT_CD (2 digits)
    if '-' in acc:
        cano, prdt = acc.split('-')
    else:
        cano = acc
        prdt = "01"
        
    print(f"Using CANO={cano}, PRDT={prdt}")

    # Authenticate (Real Server)
    print("\n[1] Authenticating (PROD)...")
    if kc.auth(svr="prod"):
        print("Authentication Successful")
    else:
        print("Authentication Failed")
        return

    # Try main US exchanges
    exchanges = ["NASD", "NYSE", "AMEX"] 
    
    found_any = False
    for exc in exchanges:
        print(f"\n[2] Querying Balance for Exchange: '{exc}' ...")
        try:
            res = osf.get_balance(
                cano=cano,
                acnt_prdt_cd=prdt,
                ovrs_excg_cd=exc
            )
            
            output1 = res.get('output1', [])
            
            if output1:
                print(f"✅ FOUND {len(output1)} positions in {exc}:")
                found_any = True
                for i, item in enumerate(output1):
                    # KIS often returns strings for numbers
                    qty = item.get('ovrs_cblc_qty', item.get('hldg_qty', '0'))
                    code = item.get('pdno', item.get('ovrs_pdno', 'UNKNOWN'))
                    name = item.get('prdt_name', item.get('ovrs_item_name', 'UNKNOWN'))
                    print(f"  [{i+1}] {code} ({name}): Qty={qty}")
                    if i == 0:
                        print("  First Item Details:")
                        print(pformat(item))
            else:
                print(f"  No positions found in {exc}.")
            
            # Print output2 for Cash Balance
            output2 = res.get('output2', {})
            if output2:
                print(f"  [Cash Details for {exc}]:")
                print(pformat(output2))
            else:
                print(f"  No Cash Details (output2) for {exc}")
                
        except Exception as e:
            print(f"  Error querying {exc}: {e}")
            
    # [3] Debug Present Balance (Cash)
    print("\n[3] Querying Present Balance (Cash Info) ...")
    try:
        # Use get_present_balance
        res_bal = osf.get_present_balance(cano, prdt)
        print("  [Present Balance Result]:")
        
        # Check output2 (usually where the cash/assets detail is)
        out2 = res_bal.get('output2', [])
        
        # output2 might be a list or object, usually object for balance summary
        if out2:
            print("  Output2 (Asset/Cash Details):")
            if hasattr(out2, '__dict__'):
                print(pformat(vars(out2)))
            else:
                print(pformat(out2))
        
        # Check output1 just in case
        out1 = res_bal.get('output1', [])
        if out1:
            print("  Output1 (Stock/Summary?):")
            if hasattr(out1, '__dict__'):
                print(pformat(vars(out1)))
            else:
                print(pformat(out1))
                
    except Exception as e:
        print(f"  Error querying present balance: {e}")

    # [4] Debug Price Detail (for Daily P&L)
    print("\n[4] Querying Price Detail for 'INTC' (NASD) ...")
    try:
        # Test get_price
        res_price = osf.get_price("NASD", "INTC")
        if res_price:
            print("  [Price Detail Result]:")
            # Usually get_price returns a list of wrappers or a wrapper
            if isinstance(res_price, list):
                item = res_price[0]
            else:
                item = res_price
                
            print(f"  Type: {type(item)}")
            if hasattr(item, '__dict__'):
                print(pformat(vars(item)))
            else:
                print(pformat(item))
        else:
            print("  No price data returned.")
            
    except Exception as e:
        print(f"  Error querying price: {e}")

    except Exception as e:
        print(f"  Error querying price: {e}")

    # [5] Debug Price Detail (New API)
    print("\n[5] Querying Price Detail (HHDFS76200200) for 'INTC' ...")
    try:
        # Test NAS
        print("  Testing EXCD='NAS':")
        res_detail_nas = osf.get_price_detail("NAS", "INTC")
        if res_detail_nas:
             # Check for valid data (e.g. if 'last' is not empty)
             data_nas = getattr(res_detail_nas, '_data', res_detail_nas)
             print(pformat(data_nas))
        else:
            print("  NAS returned empty.")

        # Test NASD
        print("  Testing EXCD='NASD':")
        res_detail_nasd = osf.get_price_detail("NASD", "INTC")
        if res_detail_nasd:
             data_nasd = getattr(res_detail_nasd, '_data', res_detail_nasd)
             print(pformat(data_nasd))
        else:
            print("  NASD returned empty.")
            
    except Exception as e:
        print(f"  Error querying price detail: {e}")

    if not found_any:
        print("\n❌ No positions found in any exchange.")



if __name__ == "__main__":
    debug_balance()
