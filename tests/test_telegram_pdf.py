"""
Telegram PDF 전송 테스트 (requests 사용)
"""
import os
from pathlib import Path
from dotenv import load_dotenv
import requests

def send_pdf_telegram(pdf_path: str):
    """Telegram으로 PDF 전송 (requests 사용)"""
    
    load_dotenv()
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        print("❌ Telegram 설정 누락")
        return False
    
    print(f"Token: {len(token)} chars")
    print(f"Chat ID: {chat_id}")
    print(f"PDF: {pdf_path}")
    
    # Check if PDF exists
    if not Path(pdf_path).exists():
        print(f"❌ PDF 파일 없음: {pdf_path}")
        return False
    
    print(f"✅ PDF 파일 확인: {Path(pdf_path).stat().st_size} bytes")
    
    # Telegram API URL
    url = f"https://api.telegram.org/bot{token}/sendDocument"
    
    # Caption
    caption = """📄 ChatGPT 고급 기능 통합 완료 보고서

✅ 9/9 Backend 기능
✅ 3/3 Frontend UI  
✅ 28개 파일 (~4,200 lines)
✅ 100% 완성

상세 내용은 첨부 PDF를 확인하세요!"""
    
    # Send PDF
    try:
        with open(pdf_path, 'rb') as pdf_file:
            files = {'document': pdf_file}
            data = {
                'chat_id': chat_id,
                'caption': caption
            }
            
            print("\n전송 중...")
            response = requests.post(url, data=data, files=files)
            
            if response.status_code == 200:
                print("✅ PDF 전송 성공!")
                result = response.json()
                print(f"Message ID: {result.get('result', {}).get('message_id')}")
                return True
            else:
                print(f"❌ 전송 실패: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Telegram PDF 전송 테스트")
    print("=" * 60)
    
    # PDF 경로
    pdf_path = "reports/chatgpt_completion_report.pdf"
    
    # 전송
    success = send_pdf_telegram(pdf_path)
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 테스트 성공!")
    else:
        print("❌ 테스트 실패")
    print("=" * 60)
