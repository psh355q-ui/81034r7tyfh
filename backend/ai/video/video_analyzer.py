"""
Video Analysis Engine - 영상 분석 엔진

YouTube 영상을 텍스트로 변환하고 멀티모달(음성+텍스트) 감성 분석 및 인텔리전스 추출 수행

핵심 기능:
1. YouTube 영상 다운로드 (yt-dlp)
2. 음성 → 텍스트 (Whisper STT)
3. 오디오 특징 분석 (Librosa: Pitch, Energy) - 어조/자신감 감지
4. 텍스트 감성 분석 (TextBlob) - 긍정/부정 흐름
5. 인텔리전스 추출 (Claude Wall Street Editor) - 경제/지정학/정책 팩트 추출
6. AI 종합 요약 (Claude)

작성일: 2026-01-21
Phase: D Week 1 (Upgraded V2)
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import os
import tempfile
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class VideoAnalysisResult:
    """영상 분석 결과"""
    url: str
    title: str
    duration_seconds: int
    transcript: str
    topics: List[Dict]  # {timestamp, topic, content}
    summary: str
    key_points: List[str]
    analyzed_at: datetime
    
    # Multimodal Metrics
    tone_metrics: Dict[str, Any] = field(default_factory=dict)  # {energy_mean, pitch_mean, confidence_score}
    sentiment_timeline: List[Dict] = field(default_factory=list)  # [{time, sentiment, text}, ...]
    
    # Intelligence Data (New)
    intelligence_data: List[Dict] = field(default_factory=list) # [{category, entity, fact, impact_score}, ...]


class VideoAnalyzer:
    """
    영상 분석기 (Multimodal + Intelligence)
    """
    
    def __init__(self, claude_client=None):
        if claude_client is None:
            from backend.ai.claude_client import get_claude_client
            self.claude = get_claude_client()
        else:
            self.claude = claude_client
        
        logger.info("VideoAnalyzer initialized (Multimodal Ready)")
    
    async def analyze_youtube(
        self,
        url: str,
        extract_keywords: Optional[List[str]] = None,
        download_sections: Optional[List[tuple]] = None
    ) -> VideoAnalysisResult:
        """
        YouTube 영상 종합 분석
        """
        logger.info(f"Analyzing YouTube video: {url}")
        
        # 1. 영상 다운로드
        video_info = self._download_youtube(url, download_sections=download_sections)
        
        # 2. Whisper STT
        transcript = await self._transcribe_audio(video_info['audio_path'])
        
        # 3. 오디오 특징 분석 (어조, 자신감)
        tone_metrics = self._analyze_audio_features(video_info['audio_path'])
        
        # 4. 텍스트 감성 분석 (긍정/부정)
        sentiment_timeline = self._analyze_text_sentiment(transcript)
        
        # 5. 토픽 추출
        topics = self._extract_topics(transcript)
        
        # 6. 인텔리전스 추출 (Thinking Layer)
        logger.info("Extracting market intelligence...")
        intelligence_data = await self._extract_intelligence(transcript, video_info['title'])
        
        # 6.5 Signal Mapping (Entity -> Ticker)
        try:
            from backend.ai.thinking.signal_mapper import get_signal_mapper
            mapper = get_signal_mapper()
            intelligence_data = mapper.map_signals(intelligence_data)
        except Exception as e:
            logger.error(f"Signal Mapping failed: {e}")
            # Continue with raw intelligence data if mapping fails
        
        # 7. AI 종합 분석 (Multimodal Data 포함)
        summary, key_points = await self._analyze_content_with_multimodal(
            transcript, 
            video_info['title'],
            tone_metrics,
            sentiment_timeline,
            keywords=extract_keywords,
            intelligence_data=intelligence_data
        )
        
        # 8. 임시 파일 삭제
        self._cleanup(video_info['audio_path'])
        
        result = VideoAnalysisResult(
            url=url,
            title=video_info['title'],
            duration_seconds=video_info['duration'],
            transcript=transcript,
            topics=topics,
            summary=summary,
            key_points=key_points,
            analyzed_at=datetime.now(),
            tone_metrics=tone_metrics,
            sentiment_timeline=sentiment_timeline,
            intelligence_data=intelligence_data
        )
        
        logger.info(f"Video analysis completed: {video_info['title']}")
        return result
    
    def _download_youtube(self, url: str, download_sections: Optional[List[tuple]] = None) -> Dict:
        """YouTube 영상 오디오 다운로드"""
        try:
            import yt_dlp
            import imageio_ffmpeg
            
            temp_dir = tempfile.gettempdir()
            output_template = os.path.join(temp_dir, '%(id)s.%(ext)s')
            
            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'ffmpeg_location': ffmpeg_path,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': output_template,
                'quiet': False, # Verbose logs
                'verbose': True,
                'no_warnings': False,
            }
            
            if download_sections:
                logger.info(f"Downloading sections: {download_sections}")
                ydl_opts['download_ranges'] = yt_dlp.utils.download_range_func(None, download_sections)
                ydl_opts['force_keyframes_at_cuts'] = True

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'Unknown Title')
                duration = info.get('duration', 0)
                video_id = info.get('id')
                
                audio_path = os.path.join(temp_dir, f"{video_id}.mp3")
                
                return {
                    "title": title,
                    "duration": duration,
                    "audio_path": audio_path
                }
            
        except Exception as e:
            logger.error(f"Failed to download YouTube video: {e}")
            raise

    async def _transcribe_audio(self, audio_path: str) -> str:
        """음성 → 텍스트 (Whisper API)"""
        try:
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
                
            from openai import AsyncOpenAI
            client = AsyncOpenAI()
            
            logger.info("Starting Whisper transcription...")
            with open(audio_path, "rb") as audio_file:
                transcript = await client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
            return transcript
        except Exception as e:
            logger.error(f"Failed to transcribe audio: {e}")
            return f"[Transcription Failed: {str(e)}]"

    def _analyze_audio_features(self, audio_path: str) -> Dict[str, Any]:
        """Librosa 오디오 분석"""
        try:
            import librosa
            logger.info("Analyzing audio features (Librosa)...")
            y, sr = librosa.load(audio_path, sr=16000)
            
            rms = librosa.feature.rms(y=y)[0]
            energy_mean = float(np.mean(rms))
            energy_std = float(np.std(rms))
            
            cent = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            tone_mean = float(np.mean(cent))
            
            high_energy_threshold = energy_mean + 1.5 * energy_std
            high_energy_ratio = float(np.sum(rms > high_energy_threshold) / len(rms))
            
            return {
                "energy_mean": energy_mean,
                "energy_variability": energy_std,
                "tone_brightness": tone_mean,
                "high_energy_ratio": high_energy_ratio,
                "interpretation": self._interpret_audio_metrics(energy_mean, tone_mean)
            }
        except Exception as e:
            logger.error(f"Audio analysis failed: {e}")
            return {"error": str(e)}

    def _interpret_audio_metrics(self, energy: float, tone: float) -> str:
        if energy > 0.1:
            if tone > 2000: return "PASSIONATE / AGGRESSIVE"
            else: return "CONFIDENT / BOOMING"
        else:
            if tone > 2000: return "TENSE / NERVOUS"
            else: return "CALM / SUBDUED"

    def _analyze_text_sentiment(self, transcript: str) -> List[Dict]:
        """TextBlob 감성 분석"""
        try:
            from textblob import TextBlob
            logger.info("Analyzing text sentiment...")
            blob = TextBlob(transcript)
            timeline = []
            for sentence in blob.sentences:
                sentiment = sentence.sentiment.polarity
                if abs(sentiment) > 0.1 and len(sentence.string) > 10:
                    status = "POSITIVE" if sentiment > 0 else "NEGATIVE"
                    timeline.append({
                        "text": sentence.string[:50] + "...",
                        "sentiment_score": float(sentiment),
                        "status": status
                    })
            return timeline
        except Exception:
            return []

    def _extract_topics(self, transcript: str) -> List[Dict]:
        topics = []
        chunks = transcript.split('\n\n')
        for i, chunk in enumerate(chunks):
            if not chunk.strip(): continue
            topics.append({
                "timestamp": f"Section {i+1}", 
                "topic": self._infer_topic(chunk),
                "content": chunk[:200] + "..."
            })
        return topics
    
    def _infer_topic(self, content: str) -> str:
        c = content.lower()
        if "inflation" in c or "price" in c: return "Economy/Inflation"
        if "trade" in c or "tariff" in c: return "Trade/Tariffs"
        if "job" in c or "employment" in c: return "Labor Market"
        if "war" in c or "military" in c: return "Geopolitics"
        return "General"

    async def _extract_intelligence(self, transcript: str, title: str) -> List[Dict]:
        """
        인텔리전스 추출 (Thinking Layer)
        월가 속보 에디터 페르소나
        """
        system_prompt = """You are a Wall Street Breaking News AI Editor.
Your task is to extract "Market-Moving Intelligence" from the speech transcript.

[INSTRUCTIONS]
Extract ONLY sentences that contain specific facts regarding:
1. **Economic Indicators**: Inflation numbers, GDP, Stock market targets.
2. **Geopolitics**: Specific countries, Borders, Wars, Territory (e.g. Greenland).
3. **Industrial Policy**: Energy (Nuclear/Oil), Trade tariffs, Regulations.

Ignore emotional rhetoric. Focus on Hard Facts, Numbers, and Entities.

[OUTPUT FORMAT]
Return a valid JSON list of objects:
[
    {
        "category": "Economy" | "Geopolitics" | "Policy",
        "entity": ["Entity1", "Entity2"],
        "fact": "One concise sentence summarizing the fact",
        "impact_score": "High" | "Medium" | "Low",
        "related_sectors": ["Sector1", "Sector2"]
    }
]"""

        user_prompt = f"""
TRANSCRIPT TITLE: {title}

TRANSCRIPT (Excerpt):
{transcript[:3000]}
"""
        
        try:
            logger.info("Calling Claude for Intelligence Extraction (Cached)...")
            # Nemotron-style: use caching for system prompt
            response = await self.claude.generate(
                prompt=user_prompt, 
                system_prompt=system_prompt, 
                use_caching=True
            )
            
            import json
            import re
            
            import json
            import re
            
            match = re.search(r'\[.*\]', response, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            else:
                logger.warning("No JSON found in intelligence response")
                return []
        except Exception as e:
            logger.error(f"Intelligence extraction failed: {e}")
            return []

    async def _analyze_content_with_multimodal(
        self,
        transcript: str,
        title: str,
        tone_metrics: Dict,
        sentiment_timeline: List[Dict],
        keywords: Optional[List[str]] = None,
        intelligence_data: Optional[List[Dict]] = None
    ) -> tuple:
        """AI 종합 분석 (Multimodal + Intelligence)"""
        
        top_pos = sorted(sentiment_timeline, key=lambda x: x['sentiment_score'], reverse=True)[:3]
        top_neg = sorted(sentiment_timeline, key=lambda x: x['sentiment_score'])[:3]
        
        multimodal_context = f"""
        [Audio Analysis]
        - Tone/Energy: {tone_metrics.get('interpretation', 'N/A')}
        - High Energy Ratio: {tone_metrics.get('high_energy_ratio', 0):.2%}
        
        [Sentiment Analysis]
        - Positive Highlights: {str([p['text'] for p in top_pos])}
        - Negative Highlights: {str([n['text'] for n in top_neg])}
        
        [Intelligence Data - Key Facts]
        {str(intelligence_data)[:1000] if intelligence_data else "None"}
        """
        
        prompt = f"""
        Analyze this video transcript.
        
        Title: {title}
        
        Context:
        {multimodal_context}
        
        Transcript (Start):
        {transcript[:2000]}
        
        Task:
        1. Summarize main message (3-4 sentences).
        2. Identify emotional state/intent.
        3. Key investment implications (5 bullet points).
        """
        
        try:
            analysis = await self.claude.generate(prompt)
            summary = analysis[:500] + "..."
            key_points = ["Analysis completed."]
            return analysis, key_points
        except Exception:
            return "Analysis Failed", []

    def _cleanup(self, file_path: str):
        try:
            if os.path.exists(file_path): os.remove(file_path)
        except Exception: pass


def get_video_analyzer() -> VideoAnalyzer:
    global _video_analyzer
    if _video_analyzer is None:
        _video_analyzer = VideoAnalyzer()
    return _video_analyzer
