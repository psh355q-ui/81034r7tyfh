// Comprehensive Global Market Tickers Database
// Supports: US Stocks, ETFs, Korean Stocks (via Korean names)

// S&P 500 - Top tickers by market cap
export const SP500_TICKERS = [
    'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK.B', 'UNH',
    'XOM', 'JNJ', 'JPM', 'V', 'PG', 'MA', 'CVX', 'HD', 'MRK', 'ABBV',
    'PEP', 'COST', 'KO', 'AVGO', 'WMT', 'TMO', 'MCD', 'ACN', 'CSCO', 'LLY',
    'DHR', 'ABT', 'CRM', 'ADBE', 'VZ', 'NKE', 'DIS', 'WFC', 'NFLX', 'TXN',
    'CMCSA', 'BMY', 'PM', 'ORCL', 'NEE', 'UPS', 'RTX', 'INTC', 'AMD', 'QCOM',
    'HON', 'IBM', 'T', 'BA', 'SBUX', 'INTU', 'COP', 'UNP', 'GE', 'CAT',
    'LOW', 'MDT', 'AMGN', 'GS', 'AXP', 'DE', 'BLK', 'SCHW', 'PLD', 'ELV',
    'SPGI', 'SYK', 'BKNG', 'ADI', 'TJX', 'ADP', 'GILD', 'MDLZ', 'MMC', 'AMT',
    'C', 'LMT', 'VRTX', 'CI', 'ZTS', 'TMUS', 'MO', 'NOC', 'SO', 'EOG',
    'PGR', 'CB', 'DUK', 'MMM', 'TGT', 'USB', 'SLB', 'BDX', 'PNC', 'ICE',
    'BSX', 'CL', 'ITW', 'CME', 'AON', 'WM', 'FIS', 'MCO', 'NSC', 'CCI',
    'GD', 'APD', 'SHW', 'FCX', 'ECL', 'EMR', 'APH', 'PSA', 'MSI', 'REGN',
    'EQIX', 'AJG', 'MCK', 'TFC', 'CNC', 'COF', 'MET', 'HUM', 'SRE', 'AFL',
    'AIG', 'GM', 'PSX', 'ADM', 'KMB', 'ALL', 'TRV', 'PRU', 'D'
];

// Nasdaq 100 - Major tech and growth stocks
export const NASDAQ_100_TICKERS = [
    'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'META', 'NVDA', 'TSLA',
    'AVGO', 'AMD', 'INTC', 'QCOM', 'TXN', 'ADI', 'MRVL', 'KLAC', 'LRCX', 'AMAT', 'NXPI', 'MCHP', 'SNPS', 'CDNS',
    'CRM', 'ORCL', 'ADBE', 'INTU', 'NOW', 'PANW', 'CRWD', 'SNOW', 'TEAM', 'WDAY', 'DDOG', 'ZS', 'FTNT',
    'AMZN', 'BKNG', 'EBAY', 'MELI', 'DASH', 'ABNB',
    'NFLX', 'CMCSA', 'CHTR', 'TMUS', 'PARA',
    'AMGN', 'GILD', 'REGN', 'VRTX', 'BIIB', 'ILMN', 'MRNA', 'SGEN',
    'COST', 'SBUX', 'MNST', 'KDP', 'KHC', 'MDLZ', 'PEP',
    'TSLA', 'RIVN', 'LCID', 'PYPL', 'ADP',
    'CSCO', 'ADSK', 'ANSS', 'CPRT', 'PAYX', 'FAST', 'VRSK', 'CTAS', 'ODFL', 'PCAR', 'ROST',
    'EXC', 'CEG', 'XEL', 'AEP', 'WBA', 'EA', 'ATVI', 'LULU', 'IDXX', 'ALGN', 'CTSH',
    'NTES', 'JD', 'BIDU', 'PDD', 'WBD', 'MAR', 'CSX', 'AZN', 'ASML', 'DXCM', 'ENPH',
    'GEHC', 'FANG', 'ISRG', 'ZM'
];

// NYSE & Other Exchange Popular Stocks (최근 인기 성장주)
export const NYSE_GROWTH_TICKERS = [
    // 핀테크 & 결제
    'PLTR', 'COIN', 'HOOD', 'SOFI', 'SQ', 'AFRM', 'NU',
    // 전기차 & 배터리
    'TSLA', 'RIVN', 'LCID', 'F', 'GM', 'XPEV', 'NIO', 'LI',
    // 우주 & 항공
    'RKLB', 'ASTS', 'SPCE',
    // AI & 데이터
    'PLTR', 'AI', 'PATH', 'SNOW', 'DDOG', 'NET',
    // 바이오텍
    'SAVA', 'RXRX', 'DNA', 'BEAM',
    // 에너지 & 청정에너지
    'ENPH', 'FSLR', 'PLUG', 'BE', 'CHPT',
    // 중국 주식 (NYSE/Nasdaq ADR)
    'BABA', 'JD', 'PDD', 'BIDU', 'NIO', 'XPEV', 'LI', 'BILI',
    // 기타 성장주
    'UBER', 'LYFT', 'SPOT', 'TTD', 'RBLX', 'U', 'DKNG', 'OPEN'
];

// Russell 2000 - Notable small-cap stocks
export const RUSSELL_2000_TICKERS = [
    'KVUE', 'SOLV', 'RGEN', 'TOST', 'RYAN', 'GTLS', 'GKOS', 'LUNR', 'OSCR', 'WING',
    'PLNT', 'CASY', 'TPH', 'BROS', 'SHAK', 'TXRH', 'CHUY', 'BJRI', 'RRGB',
    'UMBF', 'WTFC', 'CBSH', 'SFNC', 'IBOC', 'CATY', 'FFIN', 'UBSI', 'FULT', 'ONB',
    'TMDX', 'NARI', 'OMCL', 'IRTC', 'NEOG', 'TASK', 'PGNY', 'PRVA', 'RDNT', 'TNDM',
    'USLM', 'GMS', 'ROAD', 'UFPT', 'MLI', 'PATK', 'CVCO', 'ATKR', 'HLIO', 'DNOW',
    'TENB', 'EVBG', 'INTA', 'AVPT', 'JAMF', 'PRGS', 'APPF', 'ALRM', 'BL', 'PD',
    'BOOT', 'VSCO', 'ABG', 'HIBB', 'LFUS', 'SGH', 'CHGG', 'CARS', 'SIG', 'ASO'
];

// ETFs - Major Exchange Traded Funds
export const ETF_TICKERS = [
    // Broad Market
    'SPY', 'VOO', 'IVV', 'VTI', 'QQQ', 'DIA', 'IWM', 'VT', 'VEA', 'VWO',
    // Sector ETFs
    'XLK', 'XLF', 'XLV', 'XLE', 'XLI', 'XLP', 'XLY', 'XLU', 'XLB', 'XLRE',
    // Tech
    'SMH', 'SOXX', 'IGV', 'VGT', 'ARKK', 'ARKW', 'ARKG', 'ARKF',
    // Bond ETFs
    'AGG', 'BND', 'TLT', 'IEF', 'SHY', 'LQD', 'HYG', 'JNK',
    // International
    'EFA', 'EEM', 'IEMG', 'VEA', 'VWO', 'FXI', 'EWJ', 'EWZ', 'EWY',
    // Commodity & Gold
    'GLD', 'SLV', 'GDX', 'USO', 'UNG', 'DBA',
    // Leveraged
    'TQQQ', 'SQQQ', 'UPRO', 'SPXU', 'TNA', 'TZA',
    // Dividend
    'VYM', 'SCHD', 'DVY', 'SDY', 'NOBL', 'VIG',
    // Growth/Value
    'VUG', 'IWF', 'VTV', 'IWD', 'MTUM', 'QUAL'
];

// Korean name to ticker mapping (한글 → 티커)
export const KOREAN_NAME_TO_TICKER: Record<string, string> = {
    // === 미국 빅테크 ===
    '애플': 'AAPL',
    '마이크로소프트': 'MSFT',
    'MS': 'MSFT',
    '구글': 'GOOGL',
    '알파벳': 'GOOGL',
    '아마존': 'AMZN',
    '엔비디아': 'NVDA',
    '엔디비아': 'NVDA',
    '메타': 'META',
    '페이스북': 'META',
    '테슬라': 'TSLA',

    // === 반도체 ===
    '인텔': 'INTC',
    'AMD': 'AMD',
    '퀄컴': 'QCOM',
    '브로드컴': 'AVGO',
    '텍사스인스트루먼트': 'TXN',
    '램리서치': 'LRCX',
    '어플라이드머티리얼즈': 'AMAT',

    // === 소프트웨어 ===
    '오라클': 'ORCL',
    '어도비': 'ADBE',
    '세일즈포스': 'CRM',
    '팔란티어': 'PLTR',
    '스노우플레이크': 'SNOW',
    '크라우드스트라이크': 'CRWD',
    '팔로알토': 'PANW',

    // === 전자상거래 ===
    '이베이': 'EBAY',
    '에어비앤비': 'ABNB',

    // === 스트리밍 ===
    '넷플릭스': 'NFLX',
    '디즈니': 'DIS',

    // === 전기차 ===
    '리비안': 'RIVN',
    '루시드': 'LCID',

    // === 금융 ===
    'JP모건': 'JPM',
    '뱅크오브아메리카': 'BAC',
    '골드만삭스': 'GS',
    '씨티그룹': 'C',
    '웰스파고': 'WFC',
    '비자': 'V',
    '마스터카드': 'MA',
    '페이팔': 'PYPL',
    '블랙록': 'BLK',

    // === 바이오/제약 ===
    '화이자': 'PFE',
    '모더나': 'MRNA',
    '존슨앤존슨': 'JNJ',
    '바이오젠': 'BIIB',
    '길리어드': 'GILD',

    // === 소비재 ===
    '코카콜라': 'KO',
    '펩시': 'PEP',
    '스타벅스': 'SBUX',
    '나이키': 'NKE',
    '맥도날드': 'MCD',
    '코스트코': 'COST',
    '월마트': 'WMT',
    '타겟': 'TGT',

    // === 에너지 ===
    '엑슨모빌': 'XOM',
    '셰브론': 'CVX',

    // === 항공우주/방산 ===
    '보잉': 'BA',
    '록히드마틴': 'LMT',

    // === 중국 주식 ===
    '알리바바': 'BABA',
    '바이두': 'BIDU',
    '징동': 'JD',
    '핀둬둬': 'PDD',
    '텐센트': 'TCEHY',

    // === ETF (한글명) ===
    '스파이': 'SPY',
    '큐큐큐': 'QQQ',
    '나스닥': 'QQQ',
    '에스앤피': 'SPY',
    'S&P': 'SPY',
    '러셀': 'IWM',

    // === 한국 주식 (해외상장) ===
    '삼성전자': '005930.KS',
    '삼성': '005930.KS',
    'SK하이닉스': '000660.KS',
    '하이닉스': '000660.KS',
    '현대차': '005380.KS',
    '현대자동차': '005380.KS',
    '기아': '000270.KS',
    'LG에너지솔루션': '373220.KS',
    'LG에너지': '373220.KS',
    '삼성바이오로직스': '207940.KS',
    '삼성바이오': '207940.KS',
    'NAVER': '035420.KS',
    '네이버': '035420.KS',
    '카카오': '035720.KS',
    'SK이노베이션': '096770.KS',
    'LG화학': '051910.KS',
    '포스코홀딩스': '005490.KS',
    '포스코': '005490.KS',
    '삼성SDI': '006400.KS',
    '현대모비스': '012330.KS',
    '셀트리온': '068270.KS',
    'KB금융': '105560.KS',
    '신한금융': '055550.KS',
    '삼성물산': '028260.KS',
    'LG전자': '066570.KS',
    '기아차': '000270.KS',

    // === 기타 ===
    '버크셔해서웨이': 'BRK.B',
    '버크셔': 'BRK.B',
    '워렌버핏': 'BRK.B'
};

// Combined list for autocomplete
export const ALL_TICKERS = [
    ...new Set([
        ...SP500_TICKERS,
        ...NASDAQ_100_TICKERS,
        ...RUSSELL_2000_TICKERS,
        ...ETF_TICKERS
    ])
].sort();

// Valid ticker regex (allows letters, numbers, dots, hyphens)
export const TICKER_REGEX = /^[A-Z0-9.\-]+$/i;

// Check if input contains Korean characters
const hasKorean = (text: string): boolean => {
    return /[ㄱ-ㅎ|ㅏ-ㅣ|가-힣]/.test(text);
};

// Check if ticker is valid format
export const isValidTickerFormat = (ticker: string): boolean => {
    return ticker.length > 0 && ticker.length <= 15 && TICKER_REGEX.test(ticker);
};

// Get autocomplete suggestion for partial ticker input
// Supports: English tickers, Korean company names, ETFs
export const getAutocompleteSuggestion = (input: string): string | null => {
    if (!input) return null;

    // Check for Korean input
    if (hasKorean(input)) {
        // Try exact match first
        const exactMatch = KOREAN_NAME_TO_TICKER[input];
        if (exactMatch) return exactMatch;

        // Try partial match (starts with)
        const partialMatch = Object.keys(KOREAN_NAME_TO_TICKER).find(
            koreanName => koreanName.startsWith(input)
        );
        if (partialMatch) {
            return KOREAN_NAME_TO_TICKER[partialMatch];
        }

        return null;
    }

    // English ticker search (prioritized)
    const upperInput = input.toUpperCase();

    // 1. Try ETFs first (most commonly searched)
    let match = ETF_TICKERS.find(ticker => ticker.startsWith(upperInput));
    if (match) return match;

    // 2. Try S&P500 (most liquid stocks)
    match = SP500_TICKERS.find(ticker => ticker.startsWith(upperInput));
    if (match) return match;

    // 3. Then Nasdaq 100
    match = NASDAQ_100_TICKERS.find(ticker => ticker.startsWith(upperInput));
    if (match) return match;

    // 4. Finally Russell 2000
    match = RUSSELL_2000_TICKERS.find(ticker => ticker.startsWith(upperInput));
    return match || null;
};

// Validate ticker and return error message if invalid
export const validateTicker = (ticker: string): string | null => {
    if (!ticker) return 'Please enter a ticker symbol';

    // Allow Korean names
    if (hasKorean(ticker)) {
        if (KOREAN_NAME_TO_TICKER[ticker]) {
            return null; // Valid Korean name
        }
        return 'Unknown Korean company name';
    }

    if (!isValidTickerFormat(ticker)) return 'Invalid ticker format';
    return null;
};

// Get ticker index info (for display purposes)
export const getTickerIndexInfo = (ticker: string): string[] => {
    const upperTicker = ticker.toUpperCase();
    const indices: string[] = [];

    if (ETF_TICKERS.includes(upperTicker)) indices.push('ETF');
    if (SP500_TICKERS.includes(upperTicker)) indices.push('S&P 500');
    if (NASDAQ_100_TICKERS.includes(upperTicker)) indices.push('Nasdaq 100');
    if (RUSSELL_2000_TICKERS.includes(upperTicker)) indices.push('Russell 2000');

    // Check if Korean stock
    if (upperTicker.endsWith('.KS')) indices.push('KOSPI');

    return indices;
};

// Convert Korean name to ticker if applicable
export const convertKoreanToTicker = (input: string): string => {
    if (hasKorean(input)) {
        return KOREAN_NAME_TO_TICKER[input] || input;
    }
    return input.toUpperCase();
};

// Stats
export const TICKER_STATS = {
    sp500Count: SP500_TICKERS.length,
    nasdaq100Count: NASDAQ_100_TICKERS.length,
    russell2000Count: RUSSELL_2000_TICKERS.length,
    etfCount: ETF_TICKERS.length,
    koreanNamesCount: Object.keys(KOREAN_NAME_TO_TICKER).length,
    totalUnique: ALL_TICKERS.length
};
