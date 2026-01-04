# Google Opal Final Checklist

현재 대표님의 앱 상태: **✅ 프롬프트 생성기 (Prompt Generator)**
- JSON 입력 -> 샷 정보 추출 -> 고퀄리티 텍스트 변환 (완료)

남은 단계: **🎥 영상 생성기 (Video Generator)**로 레벨업하기

## 🚀 1분 완성 레시피

1.  **Generate 메뉴 열기**: 화면 상단 `✨ Generate` 클릭.
2.  **Veo 노드 추가**: `Video Generator` (또는 Veo)를 캔버스에 끌어놓기.
3.  **선 연결 (Wire)**:
    - 앞 단계의 `Output` (초록색 노드) ➔ Veo 노드의 `Prompt` 구멍.
4.  **이미지 추가 (선택)**:
    - `Use Input` ➔ `Image Input` 추가.
    - `Image Input` ➔ Veo 노드의 `Image` 구멍.
5.  **실행 (Run)**: 이제 "글자"가 아니라 "영상"이 나옵니다!

> **완성 후**: `Download` 버튼을 눌러 영상을 저장하고, 파이프라인(`backend/media/video_editor.py`)에서 합치면 끝!
