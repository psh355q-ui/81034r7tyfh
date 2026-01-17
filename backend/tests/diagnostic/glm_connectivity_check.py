"""
GLM API Connectivity Diagnostic Script

Phase: Network Diagnostics
Date: 2026-01-17

Purpose:
    Check GLM API connectivity and network settings
    - Network connectivity to API endpoints
    - DNS resolution
    - Proxy settings
    - API authentication test
"""

import os
import asyncio
import socket
import logging
from typing import Dict, Any
from pathlib import Path
import aiohttp
import json

# Load .env file
try:
    from dotenv import load_dotenv
    # Find project root and load .env
    project_root = Path(__file__).parent.parent.parent.parent
    env_file = project_root / '.env'
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ Loaded .env from: {env_file}")
    else:
        print(f"⚠️  .env file not found at: {env_file}")
except ImportError:
    print("⚠️  python-dotenv not installed, using system environment variables only")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class GLMConnectivityChecker:
    """GLM API connectivity diagnostic tool"""

    def __init__(self):
        self.api_key = os.getenv('GLM_API_KEY')
        self.api_base = os.getenv('GLM_API_BASE', 'https://open.bigmodel.cn/api/paas/v4')
        self.timeout = 10

    def check_env_vars(self) -> Dict[str, Any]:
        """Check environment variables"""
        logger.info("\n=== Environment Variables ===")

        result = {
            'has_api_key': bool(self.api_key),
            'api_base': self.api_base,
            'api_key_prefix': self.api_key[:8] + '...' if self.api_key else None,
            'model': os.getenv('GLM_MODEL', 'glm-4.7')
        }

        logger.info(f"API Key Present: {result['has_api_key']}")
        logger.info(f"API Base: {result['api_base']}")
        logger.info(f"API Key Prefix: {result['api_key_prefix']}")
        logger.info(f"Model: {result['model']}")

        return result

    def check_dns_resolution(self) -> Dict[str, Any]:
        """Check DNS resolution for GLM API endpoint"""
        logger.info("\n=== DNS Resolution ===")

        hostname = "open.bigmodel.cn"
        result = {
            'hostname': hostname,
            'resolved': False,
            'ip_addresses': [],
            'error': None
        }

        try:
            # Get address info
            addr_info = socket.getaddrinfo(hostname, 443, socket.AF_UNSPEC, socket.SOCK_STREAM)

            ips = set()
            for info in addr_info:
                ip = info[4][0]
                ips.add(ip)

            result['resolved'] = True
            result['ip_addresses'] = list(ips)

            logger.info(f"✅ DNS Resolution Successful")
            logger.info(f"  Hostname: {hostname}")
            logger.info(f"  IP Addresses: {', '.join(ips)}")

        except socket.gaierror as e:
            result['error'] = str(e)
            logger.error(f"❌ DNS Resolution Failed: {e}")
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"❌ Unexpected DNS Error: {e}")

        return result

    def check_proxy_settings(self) -> Dict[str, Any]:
        """Check system proxy settings"""
        logger.info("\n=== Proxy Settings ===")

        result = {
            'http_proxy': os.getenv('HTTP_PROXY') or os.getenv('http_proxy'),
            'https_proxy': os.getenv('HTTPS_PROXY') or os.getenv('https_proxy'),
            'no_proxy': os.getenv('NO_PROXY') or os.getenv('no_proxy'),
        }

        has_proxy = any(result.values())
        logger.info(f"HTTP Proxy: {result['http_proxy'] or 'Not set'}")
        logger.info(f"HTTPS Proxy: {result['https_proxy'] or 'Not set'}")
        logger.info(f"No Proxy: {result['no_proxy'] or 'Not set'}")
        logger.info(f"Proxy Configured: {has_proxy}")

        return result

    async def check_tcp_connection(self) -> Dict[str, Any]:
        """Check TCP connection to GLM API"""
        logger.info("\n=== TCP Connection ===")

        hostname = "open.bigmodel.cn"
        port = 443

        result = {
            'hostname': hostname,
            'port': port,
            'connected': False,
            'error': None,
            'duration_ms': None
        }

        try:
            import time
            start_time = time.time()

            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(hostname, port),
                timeout=self.timeout
            )

            duration = (time.time() - start_time) * 1000

            writer.close()
            await writer.wait_closed()

            result['connected'] = True
            result['duration_ms'] = round(duration, 2)

            logger.info(f"✅ TCP Connection Successful")
            logger.info(f"  Hostname: {hostname}:{port}")
            logger.info(f"  Duration: {duration:.2f}ms")

        except asyncio.TimeoutError:
            result['error'] = f'Connection timeout after {self.timeout}s'
            logger.error(f"❌ TCP Connection Timeout ({self.timeout}s)")
        except ConnectionRefusedError:
            result['error'] = 'Connection refused'
            logger.error(f"❌ TCP Connection Refused")
        except OSError as e:
            result['error'] = str(e)
            logger.error(f"❌ TCP Connection Error: {e}")
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"❌ Unexpected TCP Error: {e}")

        return result

    async def check_api_authentication(self) -> Dict[str, Any]:
        """Check GLM API authentication with minimal test call"""
        logger.info("\n=== API Authentication Test ===")

        if not self.api_key:
            logger.error("❌ No API key found - skipping authentication test")
            return {
                'tested': False,
                'authenticated': False,
                'error': 'No API key'
            }

        url = f"{self.api_base}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Minimal test payload
        payload = {
            "model": os.getenv('GLM_MODEL', 'glm-4.7'),
            "messages": [
                {"role": "user", "content": "Hello"}
            ],
            "max_tokens": 10,
            "temperature": 0.1
        }

        result = {
            'url': url,
            'tested': True,
            'authenticated': False,
            'status_code': None,
            'error': None,
            'duration_ms': None
        }

        try:
            import time
            start_time = time.time()

            timeout = aiohttp.ClientTimeout(total=self.timeout)

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    duration = (time.time() - start_time) * 1000
                    result['duration_ms'] = round(duration, 2)
                    result['status_code'] = response.status

                    if response.status == 200:
                        result['authenticated'] = True
                        data = await response.json()
                        logger.info(f"✅ API Authentication Successful")
                        logger.info(f"  Status: {response.status}")
                        logger.info(f"  Duration: {duration:.2f}ms")
                        logger.info(f"  Model: {data.get('model', 'unknown')}")
                    elif response.status == 401:
                        result['error'] = 'Unauthorized - Invalid API key'
                        logger.error(f"❌ API Authentication Failed - Invalid API key (401)")
                    elif response.status == 429:
                        result['error'] = 'Rate limit exceeded'
                        logger.error(f"❌ API Authentication Failed - Rate limit (429)")
                    else:
                        text = await response.text()
                        result['error'] = f'HTTP {response.status}: {text[:200]}'
                        logger.error(f"❌ API Request Failed - HTTP {response.status}")
                        logger.error(f"  Response: {text[:200]}")

        except asyncio.TimeoutError:
            result['error'] = f'Request timeout after {self.timeout}s'
            logger.error(f"❌ API Request Timeout ({self.timeout}s)")
        except aiohttp.ClientConnectorError as e:
            result['error'] = f'Connection error: {str(e)}'
            logger.error(f"❌ API Connection Error: {e}")
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"❌ Unexpected API Error: {e}")

        return result

    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all connectivity checks"""
        logger.info("=" * 80)
        logger.info("GLM API Connectivity Diagnostic")
        logger.info("=" * 80)

        results = {
            'timestamp': asyncio.get_event_loop().time(),
            'env_vars': self.check_env_vars(),
            'dns': self.check_dns_resolution(),
            'proxy': self.check_proxy_settings(),
            'tcp': await self.check_tcp_connection(),
            'api_auth': await self.check_api_authentication()
        }

        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("SUMMARY")
        logger.info("=" * 80)

        issues = []

        if not results['env_vars']['has_api_key']:
            issues.append("❌ API key not configured")

        if not results['dns']['resolved']:
            issues.append(f"❌ DNS resolution failed: {results['dns'].get('error')}")

        if results['proxy'].get('https_proxy'):
            issues.append(f"⚠️  HTTPS proxy configured: {results['proxy']['https_proxy']}")

        if not results['tcp']['connected']:
            issues.append(f"❌ TCP connection failed: {results['tcp'].get('error')}")

        if not results['api_auth']['authenticated']:
            issues.append(f"❌ API authentication failed: {results['api_auth'].get('error')}")

        if issues:
            logger.info("\nIssues Found:")
            for issue in issues:
                logger.info(f"  {issue}")
        else:
            logger.info("\n✅ All checks passed - GLM API is accessible")

        logger.info("=" * 80)

        results['summary'] = {
            'all_passed': len(issues) == 0,
            'issues': issues
        }

        return results


async def main():
    """Main entry point"""
    checker = GLMConnectivityChecker()
    results = await checker.run_all_checks()

    # Save results to file
    output_file = os.path.join(os.path.dirname(__file__), 'glm_connectivity_report.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    logger.info(f"\nDetailed report saved to: {output_file}")

    # Return exit code
    return 0 if results['summary']['all_passed'] else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
