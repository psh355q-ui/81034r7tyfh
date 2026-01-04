from typing import Dict, List
import json
import logging
import os
from dotenv import load_dotenv

# Env Setup
load_dotenv()
logger = logging.getLogger(__name__)

class OpalNodePrompts:
    """
    Generates copy-paste prompts for Google Opal nodes.
    Designed to allow the user to manually construct the flow with precision.
    """
    
    def generate_all_nodes(self) -> str:
        """Returns a markdown string containing all node prompts"""
        
        return """
# Google Opal Node Recipes

Copy these prompts into your Opal Canvas nodes.

## Node 1: The Director (Gemini 1.5 Pro)
**Role**: Extract Shot Details from JSON.
**Prompt**:
```text
SYSTEM: You are a video production assistant.
INPUT: 
1. Full Manifest JSON (see variable {{manifest}})
2. Current Shot Index (see variable {{shot_index}})

INSTRUCTION:
Find the shot with "shot_id" equal to {{shot_index}}.
Extract the "action_prompt" and "character_name".
Output format:
"prompt: [Action Prompt] | character: [Character Name]"
```

## Node 2: The Cinematographer (Veo Prompt Enhancer)
**Role**: Polish the prompt for Veo 3.
**Prompt**:
```text
SYSTEM: You are an expert prompt engineer for Google Veo.
INPUT: Raw description "{{Node1_Output}}"

INSTRUCTION:
1. Identify the character (e.g. 젠황고양이 -> NVDA Cat).
2. Add high-quality visual keywords: "Pixar style, 8k, cinematic lighting, volumetric fog, octane render".
3. Ensure the action makes sense physically.
4. OUTPUT: The final, optimized English prompt for video generation.
```

## Node 3: The Animator (Veo 3)
**Role**: Generation.
**Input**: {{Node2_Output}}
**Configuration**:
- Model: Veo 3
- Aspect Ratio: 9:16
- Duration: 6 seconds
"""

if __name__ == "__main__":
    generator = OpalNodePrompts()
    print(generator.generate_all_nodes())
