"""
무료 프록시 서버 설정 및 테스트 스크립트

Usage:
    python backend/services/setup_free_proxy.py
"""

import asyncio
import httpx
from bs4 import BeautifulSoup
import logging
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FreeProxyManager:
    """무료 프록시 서버 관리자"""
    
    def __init__(self):
        self.proxy_sources = [
            'https://free-proxy-list.net/',
            'https://www.sslproxies.org/',
            'https://www.us-proxy.org/',
        ]
        self.test_url = 'https://kr.investing.com/economic-calendar/'
        self.timeout = 10
        self.max_retries = 3
    
    async def fetch_proxies(self, source_url: str) -> List[Dict[str, str]]:
        """
        프록시 소스에서 프록시 목록 추출
        
        Args:
            source_url: 프록시 소스 URL
            
        Returns:
            프록시 리스트 [{'ip': '1.2.3.4', 'port': '8080', 'protocol': 'http', 'country': 'US'}, ...]
        """
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(source_url)
                response.raise_for_status()
                
                html = response.text
                soup = BeautifulSoup(html, 'html.parser')
                
                # 프록시 테이블 찾기
                table = soup.find('table', {'id': 'proxylisttable'})
                if not table:
                    logger.warning(f"No proxy table found in {source_url}")
                    return []
                
                proxies = []
                rows = table.find_all('tr')
                
                for row in rows[1:]:  # 헤더 제외
                    cells = row.find_all('td')
                    if len(cells) < 7:
                        continue
                    
                    ip = cells[0].get_text(strip=True)
                    port = cells[1].get_text(strip=True)
                    country = cells[2].get_text(strip=True)
                    anonymity = cells[4].get_text(strip=True)
                    https = cells[6].get_text(strip=True)
                    
                    # HTTPS 지원 프록시만 필터링
                    if 'yes' in https.lower():
                        protocol = 'https'
                    else:
                        protocol = 'http'
                    
                    # 익명성 필터링 (elite 또는 anonymous)
                    if 'elite' in anonymity.lower() or 'anonymous' in anonymity.lower():
                        proxies.append({
                            'ip': ip,
                            'port': port,
                            'protocol': protocol,
                            'country': country
                        })
                
                logger.info(f"Fetched {len(proxies)} proxies from {source_url}")
                return proxies
                
        except Exception as e:
            logger.error(f"Error fetching proxies from {source_url}: {e}")
            return []
    
    async def test_proxy(self, proxy: Dict[str, str]) -> bool:
        """
        프록시 연결 테스트
        
        Args:
            proxy: 프록시 정보
            
        Returns:
            성공 여부
        """
        try:
            proxy_url = f"{proxy['protocol']}://{proxy['ip']}:{proxy['port']}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            async with httpx.AsyncClient(
                timeout=self.timeout,
                headers=headers,
                proxies={'http://': proxy_url, 'https://': proxy_url}
            ) as client:
                response = await client.get(self.test_url)
                
                if response.status_code == 200:
                    logger.info(f"✓ Proxy {proxy['ip']}:{proxy['port']} ({proxy['country']}) works!")
                    return True
                else:
                    logger.warning(f"✗ Proxy {proxy['ip']}:{proxy['port']} returned status {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.warning(f"✗ Proxy {proxy['ip']}:{proxy['port']} failed: {e}")
            return False
    
    async def find_working_proxy(self, max_proxies: int = 20) -> Optional[Dict[str, str]]:
        """
        작동하는 프록시 찾기
        
        Args:
            max_proxies: 테스트할 최대 프록시 수
            
        Returns:
            작동하는 프록시 정보
        """
        all_proxies = []
        
        # 모든 소스에서 프록시 수집
        for source in self.proxy_sources:
            proxies = await self.fetch_proxies(source)
            all_proxies.extend(proxies)
        
        if not all_proxies:
            logger.error("No proxies found")
            return None
        
        logger.info(f"Total proxies fetched: {len(all_proxies)}")
        
        # 테스트할 프록시 수 제한
        test_proxies = all_proxies[:max_proxies]
        
        # 프록시 테스트
        for proxy in test_proxies:
            logger.info(f"Testing proxy {proxy['ip']}:{proxy['port']} ({proxy['country']})...")
            if await self.test_proxy(proxy):
                return proxy
        
        logger.error("No working proxy found")
        return None
    
    def generate_proxy_config(self, proxy: Dict[str, str]) -> str:
        """
        프록시 설정 문자열 생성
        
        Args:
            proxy: 프록시 정보
            
        Returns:
            프록시 설정 문자열
        """
        return f"{proxy['protocol']}://{proxy['ip']}:{proxy['port']}"


async def main():
    """메인 함수"""
    manager = FreeProxyManager()
    
    print("=" * 60)
    print("무료 프록시 서버 검색 및 테스트")
    print("=" * 60)
    print()
    
    # 작동하는 프록시 찾기
    print("프록시 검색 중...")
    working_proxy = await manager.find_working_proxy(max_proxies=20)
    
    if working_proxy:
        print()
        print("=" * 60)
        print("✓ 작동하는 프록시를 찾았습니다!")
        print("=" * 60)
        print(f"IP: {working_proxy['ip']}")
        print(f"Port: {working_proxy['port']}")
        print(f"Protocol: {working_proxy['protocol']}")
        print(f"Country: {working_proxy['country']}")
        print()
        
        proxy_url = manager.generate_proxy_config(working_proxy)
        print(f"Proxy URL: {proxy_url}")
        print()
        
        print("EconomicCalendarFetcher에 설정하는 방법:")
        print("-" * 60)
        print("```python")
        print("fetcher = EconomicCalendarFetcher()")
        print(f"fetcher.use_proxy = True")
        print(f"fetcher.proxies = '{proxy_url}'")
        print("```")
        print()
        
        print("또는 .env 파일에 추가:")
        print("-" * 60)
        print(f"PROXY_URL={proxy_url}")
        print()
        
    else:
        print()
        print("=" * 60)
        print("✗ 작동하는 프록시를 찾지 못했습니다.")
        print("=" * 60)
        print()
        print("다른 옵션을 고려해주세요:")
        print("1. 유료 프록시 서버 사용")
        print("2. VPN 사용")
        print("3. 다른 경제 캘더 API 사용 (FMP API 등)")
        print()


if __name__ == "__main__":
    asyncio.run(main())
