"""
S&P 500 Universe - 전체 종목 및 섹터 정의

11개 GICS 섹터별 종목 분류
Last Updated: 2024-12
"""

from typing import Dict, List, Set


# S&P 500 11개 GICS 섹터
SP500_SECTORS: Dict[str, List[str]] = {
    "Technology": [
        "AAPL", "MSFT", "NVDA", "AVGO", "ORCL", "CRM", "ADBE", "AMD", "CSCO", "ACN",
        "INTC", "IBM", "INTU", "NOW", "QCOM", "TXN", "AMAT", "ADI", "LRCX", "MU",
        "SNPS", "CDNS", "KLAC", "MCHP", "MSI", "HPQ", "HPE", "KEYS", "FTNT", "ANSS",
        "IT", "MPWR", "NXPI", "ON", "ENPH", "SEDG", "TER", "ZBRA", "EPAM", "FSLR",
        "GEN", "JNPR", "AKAM", "WDC", "STX", "NTAP", "SWKS", "QRVO", "FFIV", "GLW"
    ],
    "Healthcare": [
        "UNH", "JNJ", "LLY", "ABBV", "MRK", "PFE", "TMO", "ABT", "DHR", "BMY",
        "AMGN", "MDT", "GILD", "ISRG", "CVS", "ELV", "SYK", "VRTX", "REGN", "CI",
        "ZTS", "BDX", "BSX", "MCK", "HUM", "HCA", "IDXX", "MRNA", "DXCM", "IQV",
        "EW", "A", "MTD", "BIIB", "CNC", "WAT", "ALGN", "HOLX", "MOH", "RMD",
        "WST", "ILMN", "CAH", "DGX", "VTRS", "CRL", "XRAY", "HSIC", "LH", "TFX"
    ],
    "Financials": [
        "BRK-B", "JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "SPGI", "BLK",
        "AXP", "C", "SCHW", "CB", "MMC", "PGR", "ICE", "CME", "AON", "MET",
        "USB", "AJG", "PNC", "TRV", "AIG", "AFL", "PRU", "MCO", "BK", "ALL",
        "MSCI", "TROW", "STT", "FITB", "HIG", "MTB", "WRB", "CINF", "COF", "DFS",
        "CFG", "RF", "KEY", "HBAN", "NTRS", "SYF", "RJF", "FDS", "NDAQ", "IVZ"
    ],
    "Consumer Discretionary": [
        "AMZN", "TSLA", "HD", "MCD", "NKE", "SBUX", "LOW", "TJX", "BKNG", "MAR",
        "CMG", "ORLY", "AZO", "ROST", "YUM", "HLT", "DHI", "LEN", "F", "GM",
        "APTV", "EBAY", "LVS", "WYNN", "MGM", "CCL", "RCL", "NCLH", "DPZ", "POOL",
        "BBY", "GRMN", "DRI", "ULTA", "ETSY", "BWA", "LKQ", "TPR", "RL", "PVH",
        "VFC", "HAS", "WHR", "NVR", "PHM", "KMX", "AAP", "GPC", "EXPE", "CZR"
    ],
    "Communication Services": [
        "META", "GOOGL", "GOOG", "NFLX", "DIS", "CMCSA", "VZ", "T", "TMUS", "CHTR",
        "EA", "WBD", "TTWO", "OMC", "IPG", "LYV", "MTCH", "FOXA", "FOX", "NWS",
        "NWSA", "PARA", "DISH"
    ],
    "Industrials": [
        "CAT", "UNP", "RTX", "HON", "BA", "GE", "DE", "LMT", "UPS", "ADP",
        "ETN", "NOC", "WM", "ITW", "EMR", "FDX", "GD", "NSC", "CSX", "JCI",
        "PH", "PCAR", "TT", "CMI", "CARR", "CTAS", "ROK", "AME", "FAST", "ODFL",
        "LHX", "RSG", "VRSK", "PWR", "IR", "OTIS", "DOV", "CPRT", "J", "HWG",
        "EXPD", "XYL", "FTV", "GWW", "WAB", "IEX", "JBHT", "MAS", "SNA", "NDSN"
    ],
    "Consumer Staples": [
        "PG", "KO", "PEP", "COST", "WMT", "PM", "MO", "MDLZ", "CL", "KMB",
        "GIS", "STZ", "ADM", "SYY", "HSY", "K", "KHC", "EL", "MKC", "CHD",
        "CLX", "HRL", "SJM", "CAG", "BG", "CPB", "TAP", "KR", "WBA", "TGT"
    ],
    "Energy": [
        "XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PXD", "PSX", "VLO", "OXY",
        "WMB", "KMI", "HES", "HAL", "DVN", "FANG", "BKR", "TRGP", "OKE", "CTRA",
        "MRO", "APA"
    ],
    "Utilities": [
        "NEE", "DUK", "SO", "D", "SRE", "AEP", "XEL", "EXC", "ED", "WEC",
        "AWK", "PEG", "ES", "EIX", "DTE", "FE", "CMS", "AEE", "PPL", "ETR",
        "CEG", "CNP", "EVRG", "ATO", "LNT", "NI", "NRG", "PNW"
    ],
    "Real Estate": [
        "PLD", "AMT", "EQIX", "CCI", "PSA", "O", "WELL", "SPG", "DLR", "VICI",
        "SBAC", "AVB", "ARE", "EQR", "CBRE", "MAA", "WY", "INVH", "ESS", "VTR",
        "EXR", "IRM", "UDR", "KIM", "REG", "HST", "CPT", "PEAK", "BXP", "FRT"
    ],
    "Materials": [
        "LIN", "APD", "SHW", "ECL", "FCX", "NEM", "NUE", "DD", "DOW", "CTVA",
        "PPG", "VMC", "MLM", "ALB", "IFF", "FMC", "CE", "CF", "MOS", "LYB",
        "EMN", "IP", "PKG", "WRK", "SEE", "AVY", "BALL", "AMCR"
    ],
}

# 전체 S&P 500 종목 리스트
SP500_TICKERS: List[str] = []
for sector_tickers in SP500_SECTORS.values():
    SP500_TICKERS.extend(sector_tickers)

SP500_SET: Set[str] = set(SP500_TICKERS)

# 종목 → 섹터 매핑
TICKER_TO_SECTOR: Dict[str, str] = {}
for sector, tickers in SP500_SECTORS.items():
    for ticker in tickers:
        TICKER_TO_SECTOR[ticker] = sector


def get_sector(ticker: str) -> str:
    """종목의 섹터 반환"""
    return TICKER_TO_SECTOR.get(ticker, "Unknown")


def get_sector_tickers(sector: str) -> List[str]:
    """섹터의 모든 종목 반환"""
    return SP500_SECTORS.get(sector, [])


def get_all_sectors() -> List[str]:
    """모든 섹터 이름 반환"""
    return list(SP500_SECTORS.keys())


def is_sp500(ticker: str) -> bool:
    """S&P500 종목 여부"""
    return ticker in SP500_SET


# 편의 상수
TOTAL_STOCKS = len(SP500_TICKERS)
TOTAL_SECTORS = len(SP500_SECTORS)

# 섹터별 종목 수
SECTOR_COUNTS = {sector: len(tickers) for sector, tickers in SP500_SECTORS.items()}


if __name__ == "__main__":
    print(f"S&P 500 Universe: {TOTAL_STOCKS} stocks in {TOTAL_SECTORS} sectors")
    print("\nSector breakdown:")
    for sector, count in sorted(SECTOR_COUNTS.items(), key=lambda x: -x[1]):
        print(f"  {sector}: {count}")
