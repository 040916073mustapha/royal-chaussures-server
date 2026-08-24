"""
Fix: Force seed AI settings for store_id=1 directly via raw SQL
"""
import os
import sys
import json

# Set dummy DATABASE_URL to force the engine to pick up the real one
if not os.getenv("DATABASE_URL"):
    os.environ["DATABASE_URL"] = os.getenv("SAAS_DATABASE_URL", "")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rcagents_saas_core.database.models import get_engine, get_session, AISettings
from rcagents_saas_core.database.crud import get_or_create_ai_settings, DEFAULT_SYSTEM_PROMPT

engine = get_engine()
print(f"[FIX] Engine URL: {engine.url}")

session = get_session(engine)
try:
    settings = session.query(AISettings).filter(AISettings.store_id == "1").first()
    if settings:
        print(f"[FIX] Found existing AI settings for store 1:")
        print(f"  ai_model: '{settings.ai_model}'")
        print(f"  system_prompt length: {len(settings.system_prompt) if settings.system_prompt else 0}")
        print(f"  language: '{settings.language}'")
        
        if not settings.ai_model:
            print(f"[FIX] Setting ai_model to DeepSeek-V4-Flash...")
            settings.ai_model = "openai/deepseek-ai/DeepSeek-V4-Flash"
        if not settings.system_prompt:
            print(f"[FIX] Setting system prompt...")
            settings.system_prompt = DEFAULT_SYSTEM_PROMPT
        if not settings.language:
            print(f"[FIX] Setting language to ar...")
            settings.language = "ar"
        
        settings.temperature = 0.7
        settings.max_tokens = 2048
        settings.greeting_enabled = True
        session.commit()
        print(f"[FIX] ✅ Updated AI settings for store 1")
    else:
        print(f"[FIX] Creating new AI settings for store 1...")
        settings = AISettings(
            store_id="1",
            ai_model="openai/deepseek-ai/DeepSeek-V4-Flash",
            system_prompt=DEFAULT_SYSTEM_PROMPT,
            temperature=0.7,
            max_tokens=2048,
            language="ar",
            greeting_enabled=True
        )
        session.add(settings)
        session.commit()
        print(f"[FIX] ✅ Created AI settings for store 1")
    
    session.refresh(settings)
    print(f"\n[FIX] Final state:")
    print(f"  ai_model: '{settings.ai_model}'")
    print(f"  system_prompt length: {len(settings.system_prompt) if settings.system_prompt else 0}")
    print(f"  language: '{settings.language}'")

except Exception as e:
    session.rollback()
    print(f"[FIX] ❌ Error: {e}")
finally:
    session.close()
