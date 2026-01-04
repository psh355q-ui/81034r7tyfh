from typing import List, Dict, Optional
import json
import logging
import csv
from datetime import datetime
from pydantic import BaseModel
from anthropic import AsyncAnthropic
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load Env
load_dotenv()

class Shot(BaseModel):
    shot_id: int
    start_time: float   # Seconds from 0
    end_time: float     # Seconds from 0
    duration: float     # Seconds
    character: str          
    character_name: str     
    dialogue: str           
    action_prompt: str      # For Veo
    camera_angle: str       # Wide, Close-up, etc.
    visual_notes: str       # Extra details

class ProductionManifest(BaseModel):
    title: str
    total_duration: float
    shots: List[Shot]

class ScriptWriter:
    """
    Generates a detailed 'Production Manifest' for Google Opal/Veo.
    Calculates timing based on dialogue length.
    """
    
    # Asset Mapping
    ASSET_MAP = {
        "NVDA": "젠황고양이", 
        "TSLA": "일론마고양이",
        "AAPL": "사과고양이",
        "HOST": "주인공",
        "MSFT": "마소고양이"
    }

    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            logger.warning("⚠️ ANTHROPIC_API_KEY not found.")
        self.client = AsyncAnthropic(api_key=self.api_key)
        
    def _estimate_duration(self, text: str) -> float:
        """Estimates speech duration (approx 4 chars per sec for Korean + buffer)"""
        if not text: return 4.0 # Default action shot duration
        # Korean speaks roughly 3-4 syllables per second.
        # Let's say 0.3 sec per character + 1s buffer
        duration = len(text.replace(" ", "")) * 0.25 + 1.5
        return round(max(duration, 4.0), 1) # Minimum 4s for video gen

    async def generate_manifest(self, market_data: str) -> ProductionManifest:
        logger.info("🎬 Generating Production Manifest...")
        
        system_prompt = """
        You are a Director of Photography and Scriptwriter for a high-end AI financial animation.
        Create a shot-by-shot production manifest.
        
        Characters:
        - HOST (주인공): Energetic, Meme-lover ("가즈아!").
        - NVDA (젠황): Arrogant King.
        - TSLA (일론마): Crazy Astronaut.
        
        Output JSON format with these exact fields for each shot:
        - visual_description: Detailed prompt for video AI (Google Veo). Include lighting, movement (e.g., "dolly in"), background.
        - dialogue: Korean lines.
        - character: Code (HOST, NVDA, etc.)
        - camera_angle: "Wide Shot", "Close-up", "Low Angle", etc.
        
        Structure:
        1. Intro (Host)
        2. Top Gainer 1 (Interaction)
        3. Top Gainer 2 (Interaction)
        4. Outro (All/Host)
        """

        user_message = f"""
        Analyze this market data and create a 4-5 shot sequence:
        {market_data}
        Make it funny and dynamic.
        """

        try:
            response = await self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=2500,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}]
            )
            
            # JSON Parsing Logic
            content = response.content[0].text
            
            # Find JSON/List
            start = content.find('{')
            end = content.rfind('}') + 1
            if start == -1: 
                logger.error(f"No JSON found in response: {content}")
                raise ValueError("No JSON found")
                
            json_str = content[start:end]
            
            # Clean up potential issues (e.g. trailing commas, newlines in strings)
            # Simple approach: standard json load. If fail, maybe just try to use a more robust parser regex?
            # Or ask for "strict_json" mode in prompt.
            # Here we just try/catch with more info.
            try:
                json_data = json.loads(json_str, strict=False)
            except json.JSONDecodeError as e:
                # Fallback: manual cleanup?
                # Sometimes LLMs put unescaped newlines.
                # Let's try replacing unescaped newlines? Dangerous.
                logger.error(f"JSON Parse Error: {e}")
                logger.error(f"Raw Content: {json_str}")
                raise

            shots = []
            current_time = 0.0
            
            # Handle potential variation in JSON structure from LLM
            # Assuming LLM follows instructions to return "shots": [...]
            raw_shots = json_data.get("shots", [])
            if not raw_shots and "scenes" in json_data: raw_shots = json_data["scenes"]
            
            for i, item in enumerate(raw_shots, 1):
                char_code = item.get("character", "HOST")
                dialogue = item.get("dialogue", "")
                duration = self._estimate_duration(dialogue)
                
                shot = Shot(
                    shot_id=i,
                    start_time=current_time,
                    end_time=round(current_time + duration, 2),
                    duration=duration,
                    character=char_code,
                    character_name=self.ASSET_MAP.get(char_code, char_code),
                    dialogue=dialogue,
                    action_prompt=item.get("visual_description", "") + f" Character: {self.ASSET_MAP.get(char_code, char_code)}.",
                    camera_angle=item.get("camera_angle", "Medium Shot"),
                    visual_notes=f"Provide {duration}s video."
                )
                shots.append(shot)
                current_time += duration
                
            manifest = ProductionManifest(
                title=json_data.get("title", "Market Update"),
                total_duration=round(current_time, 2),
                shots=shots
            )
            
            return manifest

        except Exception as e:
            logger.error(f"Error: {e}")
            raise

    def save_to_csv(self, manifest: ProductionManifest, filename="production_cue_sheet.csv"):
        """Export to CSV for Google Sheets/Opal"""
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(["Shot ID", "Start", "End", "Duration", "Character", "Angle", "Dialogue", "Veo Prompt"])
            for shot in manifest.shots:
                writer.writerow([
                    shot.shot_id, 
                    shot.start_time, 
                    shot.end_time, 
                    shot.duration, 
                    shot.character_name,
                    shot.camera_angle,
                    shot.dialogue,
                    shot.action_prompt
                ])
        logger.info(f"✅ CSV saved: {filename}")

if __name__ == "__main__":
    import asyncio
    async def main():
        writer = ScriptWriter()
        market_data = "NVDA +5%, TSLA +3%. AI Sector rally."
        manifest = await writer.generate_manifest(market_data)
        
        # Save JSON
        with open("production_manifest.json", "w", encoding="utf-8") as f:
            f.write(manifest.model_dump_json(indent=2))
        
        # Save CSV
        writer.save_to_csv(manifest)
        print("Done.")

    asyncio.run(main())
