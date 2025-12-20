
import os
import OpenDartReader
import logging
import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class DartCollector:
    """
    Collector for DART (Data Analysis, Retrieval and Transfer System) - Korea.
    Fetches corporate filings to build 'Corporate Memory'.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("DART_API_KEY")
        self.dart = None
        if self.api_key:
            try:
                self.dart = OpenDartReader(self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize OpenDartReader: {e}")
        else:
            logger.warning("DART_API_KEY not set. DartCollector will not function.")

    def fetch_recent_filings(self, corp_code: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        Fetches filings for a specific company code over the last N days.
        Note: corp_code is DART's unique code, not the stock ticker (requires mapping).
        """
        if not self.dart:
            return []

        end_date = datetime.datetime.now().strftime('%Y%m%d')
        start_date = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime('%Y%m%d')
        
        try:
            # list_disclosure: get list of reports
            # Using stock_code (e.g., '005930') is easier if supported, OpenDartReader supports it.
            # actually OpenDartReader can take stock code directly in most methods or via find_corp_code.
            # Let's assume input 'corp_code' is the stock ticker (6 digits).
            
            df = self.dart.list(corp_code, start=start_date, end=end_date)
            
            if df is None or df.empty:
                return []
            
            filings = []
            for _, row in df.iterrows():
                filings.append({
                    "rcept_no": row['rcept_no'],
                    "corp_name": row['corp_name'],
                    "report_nm": row['report_nm'],
                    "flr_nm": row['flr_nm'],
                    "rcept_dt": row['rcept_dt'],
                    "rm": row['rm']  # remarks
                })
            return filings

        except Exception as e:
            logger.error(f"Error fetching filings for {corp_code}: {e}")
            return []

    async def collect_and_store(self, vector_store, tickers: List[str]):
        """
        Orchestrator: Fetch filings for list of tickers -> Store summary
        """
        if not self.dart:
            logger.warning("DartCollector skipped (No API Key).")
            return

        logger.info(f"Collecting DART filings for {len(tickers)} tickers...")
        
        for ticker in tickers:
            filings = self.fetch_recent_filings(ticker)
            
            if not filings:
                continue
                
            # Create a summary document for recent activity
            # We enforce a single "Recent Filings Summary" document per ticker to avoid flooding with small docs
            # In a real system, we might embed individual major reports.
            
            content_lines = [f"# Recent DART Filings for {ticker}"]
            content_lines.append(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d')}")
            content_lines.append(f"Found {len(filings)} filings in last 30 days.\n")
            
            for f in filings:
                content_lines.append(f"- [{f['rcept_dt']}] **{f['report_nm']}** (Filer: {f['flr_nm']})")
                if f['rm']:
                    content_lines.append(f"  - Note: {f['rm']}")
            
            content = "\n".join(content_lines)
            
            # Store in Vector DB
            doc_id = await vector_store.add_document(
                ticker=ticker,
                doc_type="korea_filing",
                content=content,
                metadata={"source": "DART", "filing_count": len(filings)},
                document_date=datetime.datetime.now(),
                auto_tag=True 
            )
            logger.info(f"Stored DART Filing Doc for {ticker} (ID: {doc_id})")

