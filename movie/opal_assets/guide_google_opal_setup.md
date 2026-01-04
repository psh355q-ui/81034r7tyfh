# Google Opal Video Automation Guide

Google Opal은 노드 기반(Canvas)으로 AI 워크플로우를 만드는 도구입니다. 우리가 생성한 **`production_manifest.json`**을 활용하여 영상을 만드는 방법을 안내합니다.

> **⚠️ 주의**: Opal은 현재 '초대된 사용자' 또는 'Google Labs' 환경에 따라 기능 차이가 있을 수 있습니다.

## 🏗️ 1. Basic Flow Setup (기본 구조)

Opal Canvas에서 다음 순서대로 노드를 연결합니다.

### Step 1: Input Node (데이터 입력)
1. 화면 왼쪽 도구에서 **[Input]** 또는 **[Text]** 노드를 꺼냅니다.
2. 이름을 **"Manifest Input"**으로 변경합니다.
3. 이 노드에 `production_manifest.json` 파일의 내용을 **전체 복사 + 붙여넣기** 합니다.

### Step 2: Selection Node (샷 추출)
(Opal에 'Iterator' 기능이 없다면, LLM 노드를 사용하여 특정 샷을 추출합니다.)
1. **[Gemini / Text Generator]** 노드를 추가합니다.
2. **Prompt**란에 다음과 같이 적습니다:
   ```text
   Look a the following JSON data:
   {{Manifest Input}}
   
   Extract the 'action_prompt' for Shot ID 1. Just output the prompt text only.
   ```
3. 이것을 "Get Shot 1 Prompt"라고 이름 붙입니다.

### Step 3: Video Generation Node (영상 생성)
1. **[Veo / Video Generator]** 노드를 추가합니다.
2. **Prompt** 입력란을 Step 2의 출력(`{{Get Shot 1 Prompt}}`)과 연결합니다.
3. **Settings**:
   - Aspect Ratio: 9:16 (Shorts용) 또는 16:9 (옵션 확인)
   - Duration: 6s (매니페스트의 Duration 참고)

### Step 4: Output / Preview
1. Veo 노드의 결과가 화면에 미리보기로 뜹니다.
2. 마음에 들면 다운로드합니다.

---

## ⚡ 2. Advanced: Multi-Shot Batch Processing

만약 Opal이 **Repeater**나 **Map** 기능을 지원한다면:

1. **Input**: JSON 데이터.
2. **Map List**: `shots` 배열을 기준으로 반복.
3. **Process Item**: 각 샷의 `action_prompt`를 Veo 노드에 전달.
4. **Output**: 여러 개의 영상 파일 생성.

## 🧩 3. Detailed Prompt for Each Node (노드별 상세 프롬프트)

Opal Canvas의 각 노드에 **그대로 복사해서 넣을 수 있는** 상세 프롬프트입니다.

### [Node A] JSON Parser (Gemini 1.5 Pro)
이 노드는 전체 JSON에서 우리가 원하는 샷 정보를 "구조화된 텍스트"로 변환합니다.
- **Input**: `{{Manifest Input}}` (위의 JSON 전체)
- **Prompt**:
```text
You are a data extractor. 
I have a JSON dataset describing a video sequence.
Your job is to parse it and output the details for **Shot ID {{shot_id}}** only.

Input JSON:
{{Manifest Input}}

Target Shot ID: {{shot_id}}

Output Requirement:
Return ONLY the raw string for the 'action_prompt' and nothing else. 
Do not include "Here is the prompt" or quotes. Just the prompt text.
```

### [Node B] Character Injector (Text Generator)
이 노드는 "젠황고양이" 같은 캐릭터 이름을 실제 Veo가 이해할 수 있는 "시각적 묘사"로 강화합니다.
- **Input**: `{{Parsed Prompt}}` (Node A의 결과)
- **Prompt**:
```text
Enhance the following video prompt for Google Veo (AI Video Generator).
The user prompt mentions a character code (e.g. NVDA, HOST).
Replace the character name with this visual description:

- HOST: "Cute tuxedo cat wearing a headset, enthusiastic expression"
- NVDA: "Black cat with green glowing eyes, wearing a leather jacket, cool vibe"
- TSLA: "White cat in a space suit, floating in zero gravity, crazy eyes"

Original Prompt:
{{Parsed Prompt}}

Enhanced Prompt:
```

### [Node C] Video Generator (Veo)
- **Settings**:
  - Resolution: 1080p
  - Aspect Ratio: 9:16
- **Inputs**:
  1. **Prompt**: Connect `{{Enhanced Prompt}}` here.
  2. **Image Input (중요!)**: 
     - 여기에 **[Image Input]** 노드를 새로 추가해서 연결하세요.
     - 샷에 맞는 캐릭터 이미지(예: `젠황고양이.png`)를 업로드하면, AI가 그 얼굴을 참고해서 영상을 만듭니다.
```

## 🖼️ 4. 캐릭터 이미지 적용 방법 (Reference Image)

대표님이 디자인한 **'고양이 에셋'**을 영상에 그대로 나오게 하려면:

1.  Opal Canvas에서 **[Image Input]** 노드를 꺼냅니다.
2.  **Veo Video Generator** 노드의 **'Image'** 또는 **'Reference'** 입력 핀에 연결합니다.
3.  **사용법**:
    - **Shot 1 (주인공)** 생성 시: `주인공.png` 업로드 -> 실행
    - **Shot 2 (NVDA)** 생성 시: `젠황고양이.png` 업로드 -> 실행
    - **Shot 3 (TSLA)** 생성 시: `일론마고양이.png` 업로드 -> 실행

> **팁**: 이렇게 하면 AI가 캐릭터 디자인을 유지한 채 춤추거나 움직이는 영상을 만들어줍니다.

## 🧭 5. 노드가 안 보일 때 (메뉴 찾기)

Opal 화면 상단 메뉴바를 확인하세요:

1.  **🎥 Veo (Video Generator) 찾기**:
    - 상단 **`✨ Generate`** 메뉴 클릭 -> **[Video Generator]** 또는 **[Veo]** 선택.
    - 또는 **`+ Add Assets`** -> 검색창에 "Veo" 입력.

2.  **🖼️ Image Input (이미지 업로드)**:
    - **`User Input` 노드는 텍스트용입니다.** 이미지는 안 들어갑니다.
    - 화면 맨 위 중앙의 **`+ Add Assets`** 버튼을 누르세요.
    - `Upload`를 눌러 `젠황고양이.png` 등을 업로드하세요.
    - 업로드된 이미지를 **Veo 노드**로 드래그 앤 드롭(Drag & Drop) 하세요.



