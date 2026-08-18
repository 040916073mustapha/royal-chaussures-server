#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RC Agents — Notion Sync Module (Pro Level v2)
================================================
مزامنة ROADMAP.md مع Notion تلقائياً.
- To-Do blocks (✓ قابل للشطب)
- Toggle blocks لكل ADR
- Bold annotations (بدون نصوص Markdown)
- Kanban كأقسام تفاعلية + To-Do Lists

الاستخدام:
    from services.notion_sync import sync_roadmap_to_notion
    sync_roadmap_to_notion()
"""

import os
import re
import json
import logging
import requests
from datetime import datetime

logger = logging.getLogger("royal-server")

# ── الإعدادات ─────────────────────────────────────────────
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")
NOTION_PAGE_ID = os.getenv("NOTION_PAGE_ID", "")
NOTION_VERSION = "2026-03-11"

ROADMAP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ROADMAP.md")


# ── دوال Notion API الأساسية ─────────────────────────────

def _notion_headers():
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }


def _notion_request(method, endpoint, data=None):
    url = f"https://api.notion.com/v1/{endpoint}"
    resp = requests.request(method, url, headers=_notion_headers(), json=data, timeout=20)
    if resp.status_code >= 400:
        logger.error(f"[NOTION] API {resp.status_code}: {resp.text[:150]}")
        return None
    return resp.json()


def _get_page_blocks(page_id):
    blocks = []
    cursor = None
    while True:
        params = {"page_size": 100}
        if cursor:
            params["start_cursor"] = cursor
        data = _notion_request("GET", f"blocks/{page_id}/children?page_size=100" + (f"&start_cursor={cursor}" if cursor else ""))
        if not data:
            break
        blocks.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
    return blocks


def _delete_all_blocks(page_id):
    blocks = _get_page_blocks(page_id)
    for block in blocks:
        _notion_request("DELETE", f"blocks/{block['id']}")


# ── Builder Helpers ───────────────────────────────────────

def _rt(text, bold=False, color=None):
    """rich text helper"""
    t = {"type": "text", "text": {"content": text}}
    if bold:
        t["annotations"] = {"bold": True}
    return t


def _add_blocks(page_id, blocks):
    """إضافة blocks في دفعات (chunks of 30)"""
    chunk_size = 30
    for i in range(0, len(blocks), chunk_size):
        chunk = blocks[i:i+chunk_size]
        _notion_request("PATCH", f"blocks/{page_id}/children", {"children": chunk})


def heading(level, text, color="default"):
    bt = f"heading_{level}"
    return {"object": "block", "type": bt, bt: {"rich_text": [_rt(text)], "color": color}}

def paragraph(text, color="default"):
    return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [_rt(text)], "color": color}}

def bullet(text, color="default"):
    return {"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": [_rt(text)], "color": color}}

def todo(text, checked=False, color="default"):
    return {"object": "block", "type": "to_do", "to_do": {"rich_text": [_rt(text)], "checked": checked, "color": color}}

def toggle(title, children_blocks):
    """Toggle block مع محتواه"""
    b = {"object": "block", "type": "toggle", "toggle": {"rich_text": [_rt(title)], "color": "default"}}
    return b

def divider():
    return {"object": "block", "type": "divider", "divider": {}}

def callout(text, icon="💡", color="gray_background"):
    return {"object": "block", "type": "callout", "callout": {"rich_text": [_rt(text)], "icon": {"emoji": icon}, "color": color}}

def rich_text_block(block_type, rich_text_list, color="default"):
    """كتلة مع rich_text مخصص (لـ bold inline)"""
    btype = block_type if block_type != "to_do" else "to_do"
    key = block_type if block_type != "to_do" else "to_do"
    obj = {"object": "block", "type": btype}
    obj[key] = {"rich_text": rich_text_list, "color": color}
    if block_type == "to_do":
        obj[key]["checked"] = False
    return obj


# ── محلل ROADMAP.md ───────────────────────────────────────

def _parse_roadmap_sections():
    if not os.path.exists(ROADMAP_PATH):
        logger.error(f"[NOTION] ROADMAP.md not found at {ROADMAP_PATH}")
        return []
    with open(ROADMAP_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    sections = []
    current_section = {"title": "", "level": 0, "lines": []}
    for line in content.split("\n"):
        h_match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if h_match:
            if current_section["lines"]:
                sections.append(current_section)
            level = len(h_match.group(1))
            title = h_match.group(2).strip()
            current_section = {"title": title, "level": level, "lines": []}
        else:
            current_section["lines"].append(line)
    if current_section["lines"]:
        sections.append(current_section)
    return sections


def _extract_kanban_items(content_sections):
    """استخراج المهام مع حالة الإنجاز"""
    in_kanban = False
    done = []
    in_progress = []
    backlog = []

    for section in content_sections:
        if "لوحة المهام" in section["title"] or "Kanban" in section["title"]:
            in_kanban = True
            continue
        if not in_kanban:
            continue
        if section["level"] <= 2 and "Kanban" not in section["title"] and "لوحة" not in section["title"]:
            break

        for line in section["lines"]:
            stripped = line.strip()
            if "- [x]" in stripped:
                item = stripped.split("- [x]")[-1].strip().lstrip(")").strip()
                if item: done.append(item)
            elif "- [ ]" in stripped and any(w in stripped.lower() for w in ["in progress", "قيد", "الآن"]):
                item = stripped.split("- [ ]")[-1].strip().lstrip(")").strip()
                if item: in_progress.append(item)
            elif "backlog" in section["title"].lower() or "القادمة" in section["title"]:
                if stripped.startswith("- [") and "[x]" not in stripped:
                    item = stripped.split("]")[-1].strip()
                    if item: backlog.append(item)
                elif stripped.startswith("- ") and not stripped.startswith("- ["):
                    item = stripped[2:].strip()
                    if item and not item.startswith("```") and not item.startswith("|"):
                        backlog.append(item)

    return done, in_progress, backlog


def _extract_adr_entries(content_sections):
    """استخراج ADR entries مع الحقول المهمة بدون Markdown"""
    in_adr = False
    current_adr_title = None
    adrs = []

    for section in content_sections:
        if "ADR" in section["title"] or "سجل القرارات" in section["title"]:
            in_adr = True
            continue
        if not in_adr:
            continue
        if section["level"] <= 2 and "ADR" not in section["title"]:
            break

        # ADR title
        m_adr = re.match(r"ADR-\d+", section["title"])
        if m_adr:
            if current_adr_title:
                adrs.append((current_adr_title, current_fields))
            current_adr_title = section["title"]
            current_fields = {}
            for line in section["lines"]:
                stripped = line.strip()
                # | field | value | format
                m = re.match(r"\|\s*\*\*(.*?)\*\*\s*\|\s*(.*?)\s*\|", stripped)
                if m:
                    key = m.group(1).strip()
                    val = m.group(2).strip()
                    # إزالة علامات الـ markdown
                    val = re.sub(r"\*\*", "", val)
                    val = re.sub(r"`", "", val)
                    current_fields[key] = val

    if current_adr_title:
        adrs.append((current_adr_title, current_fields))

    return adrs


# ── بناء المحتوى الكامل ──────────────────────────────────

def build_all_blocks(sections):
    """بناء قائمة blocks كاملة"""
    blocks = []

    # ── Header ──
    blocks.append(heading(1, "🚀 RC Agents — خارطة الطريق الشاملة", "blue_background"))
    blocks.append(paragraph("🟢 Multi-Tenant SaaS • Render + Neon PostgreSQL • 18 أغسطس 2026"))
    blocks.append(divider())
    blocks.append(callout("🤖 يتم تحديث هذه الصفحة تلقائياً من ROADMAP.md عبر RC Agents Bot", "🗺️", "blue_background"))
    blocks.append(divider())

    # ── 📌 الوضع الحالي ──
    blocks.append(heading(1, "📌 الوضع الحالي (Current Status)", "blue_background"))

    # جدول الحالة من الـ MD
    for section in sections:
        if "الوضع الحالي" in section["title"] or "Current Status" in section["title"]:
            for line in section["lines"]:
                stripped = line.strip()
                if stripped.startswith("|") and "المعلم" not in stripped and "---" not in stripped:
                    parts = [p.strip() for p in stripped.split("|") if p.strip()]
                    if len(parts) >= 4:
                        table_line = f"{parts[0]} | {parts[1]} | {parts[2]} | {parts[3]}"
                        blocks.append(bullet(f"🏪 **{parts[0]}** → {parts[1]} | {parts[2]} | {parts[3][:30]}"))

    blocks.append(heading(2, "المتاجر المنشأة", "green_background"))
    blocks.append(todo("store_id=1: Royal Chaussures (إنتاجي 🏪)", checked=True))
    blocks.append(todo("store_id=2: متجر اختبار (Onboarding Test)", checked=True))
    blocks.append(todo("store_id=3: Urban Moda (أول تاجر حقيقي ثانٍ)", checked=True))
    blocks.append(divider())

    # ── 🗺️ خريطة المراحل ──
    blocks.append(heading(1, "🗺️ خريطة المراحل (Phases)", "purple_background"))

    phase_order = ["Phase 1", "Phase 2", "Phase 3", "Phase 4"]
    for phase_key in phase_order:
        phase_done = "✅" in phase_key
        for section in sections:
            if phase_key in section["title"] or ("المرحلة" in section["title"] and phase_key.split()[-1] in section["title"]):
                # Extract header
                is_done = "✅" in section["title"] or "مكتملة" in section["title"]
                is_active = "🔄" in section["title"] or "قيد" in section["title"]
                clr = "green_background" if is_done else ("yellow_background" if is_active else "gray_background")
                blocks.append(heading(2, section["title"], clr))

                # Bullet items
                for line in section["lines"]:
                    stripped = line.strip()
                    if stripped.startswith("- [x]") or stripped.startswith("- ✅"):
                        item = stripped.split("]")[-1].strip() if "]" in stripped else stripped[2:].strip()
                        blocks.append(todo(item, checked=True, color="green"))
                    elif stripped.startswith("- ") and not stripped.startswith("- ["):
                        item = stripped[2:].strip()
                        if item and not item.startswith("|") and not item.startswith("```"):
                            if is_done:
                                blocks.append(todo(item, checked=True, color="green"))
                            else:
                                blocks.append(todo(item, checked=False, color="default"))
                break

    blocks.append(divider())

    # ── 📋 Kanban Board ──
    blocks.append(heading(1, "📋 لوحة المهام (Kanban Board)", "orange_background"))

    done, in_progress, backlog = _extract_kanban_items(sections)

    blocks.append(heading(2, "✅ Done (تم الإنجاز)", "green_background"))
    for item in done[:25]:
        blocks.append(todo(item, checked=True, color="green"))

    blocks.append(heading(2, "🔄 In Progress (قيد التنفيذ)", "yellow_background"))
    for item in in_progress[:10]:
        blocks.append(todo(item, checked=False, color="yellow"))

    blocks.append(heading(2, "⏳ Backlog (المهام القادمة)", "gray_background"))
    for item in backlog[:20]:
        blocks.append(todo(item, checked=False, color="default"))

    blocks.append(divider())

    # ── ⚠️ ADR ──
    blocks.append(heading(1, "⚠️ سجل القرارات البرمجية (ADR)", "red_background"))

    adr_entries = _extract_adr_entries(sections)
    for adr_title, fields in adr_entries:
        # Toggle block لكل ADR
        toggle_block = {"object": "block", "type": "toggle",
                        "toggle": {"rich_text": [_rt(adr_title)], "color": "default"},
                        "children": []}  # Notion API لا يدعم الأطفال في PATCH, نضيفهم كـ inline instead

        # محتوى ADR كـ bullets داخلية
        adr_blocks = []
        for key, val in fields.items():
            # Bold للعنوان + عادي للقيمة (بدون markdown)
            rt = [
                {"type": "text", "text": {"content": f"{key}: "}, "annotations": {"bold": True}},
                {"type": "text", "text": {"content": val}}
            ]
            adr_blocks.append(rich_text_block("bulleted_list_item", rt))

        # نضيف الـ toggle + محتواه
        blocks.append(toggle_block)
        blocks.extend(adr_blocks)

    blocks.append(divider())

    # ── Footer ──
    blocks.append(callout(f"آخر تحديث: {datetime.now().strftime('%d %B %Y %H:%M')} • ROADMAP.md Sync", "🤖", "gray_background"))

    return blocks


# ── الدالة الرئيسية ───────────────────────────────────────

def sync_roadmap_to_notion():
    if not NOTION_TOKEN or not NOTION_PAGE_ID:
        logger.warning("[NOTION] NOTION_TOKEN/PAGE_ID غير معرفين")
        return False

    logger.info("[NOTION] بدء مزامنة ROADMAP.md → Notion (Pro v2)...")

    sections = _parse_roadmap_sections()
    if not sections:
        return False

    # حذف القديم
    _delete_all_blocks(NOTION_PAGE_ID)

    # بناء المحتوى
    blocks = build_all_blocks(sections)
    logger.info(f"[NOTION] بني {len(blocks)} blocks")

    # إضافة في دفعات
    _add_blocks(NOTION_PAGE_ID, blocks)

    logger.info("[NOTION] ✅ تمت المزامنة بنجاح!")
    return True


def sync_roadmap_quick():
    success = sync_roadmap_to_notion()
    if success:
        print("✅ ROADMAP.md → Notion: Sync complete (Pro v2)!")
    else:
        print("❌ ROADMAP.md → Notion: Failed.")
    return success


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sync_roadmap_quick()
