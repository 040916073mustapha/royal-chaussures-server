#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RC Agents — Notion Sync Module
================================
مزامنة ROADMAP.md مع Notion تلقائياً.
تحويل الأقسام إلى عناصر وبطاقات داخل صفحة Notion.

الاستخدام:
    from services.notion_sync import sync_roadmap_to_notion
    sync_roadmap_to_notion()

متغيرات البيئة المطلوبة (في Render Environment Variables):
    NOTION_TOKEN
    NOTION_PAGE_ID
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
    """إعداد Headers مع Token"""
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }


def _notion_request(method, endpoint, data=None):
    """إرسال طلب إلى Notion API"""
    url = f"https://api.notion.com/v1/{endpoint}"
    resp = requests.request(method, url, headers=_notion_headers(),
                            json=data, timeout=15)
    if resp.status_code >= 400:
        logger.error(f"[NOTION] API error {resp.status_code}: {resp.text[:200]}")
        return None
    return resp.json()


def _get_page_blocks(page_id):
    """جلب جميع الـ blocks في الصفحة"""
    blocks = []
    cursor = None
    while True:
        params = {"page_size": 100}
        if cursor:
            params["start_cursor"] = cursor
        ep = f"blocks/{page_id}/children"
        if cursor:
            ep += f"?start_cursor={cursor}"
        data = _notion_request("GET", ep)
        if not data:
            break
        blocks.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
    return blocks


def _delete_all_blocks(page_id):
    """حذف كل الـ blocks الموجودة في الصفحة (لإعادة البناء الكامل)"""
    blocks = _get_page_blocks(page_id)
    for block in blocks:
        _notion_request("DELETE", f"blocks/{block['id']}")


def _add_block(page_id, block_type, content, emoji=None):
    """إضافة block داخل الصفحة"""
    block = {
        "object": "block",
        "type": block_type,
        block_type: content
    }
    payload = {"children": [block]}
    return _notion_request("PATCH", f"blocks/{page_id}/children", payload)


def _add_heading(page_id, level, text, color="default"):
    """إضافة عنوان"""
    block_type = f"heading_{level}"
    content = {
        "rich_text": [{"type": "text", "text": {"content": text}}],
        "color": color
    }
    return _add_block(page_id, block_type, content)


def _add_paragraph(page_id, text, color="default"):
    """إضافة فقرة"""
    content = {
        "rich_text": [{"type": "text", "text": {"content": text}}],
        "color": color
    }
    return _add_block(page_id, "paragraph", content)


def _add_bullet(page_id, text, color="default"):
    """إضافة نقطة"""
    content = {
        "rich_text": [{"type": "text", "text": {"content": text}}],
        "color": color
    }
    return _add_block(page_id, "bulleted_list_item", content)


def _add_divider(page_id):
    """إضافة فاصل"""
    return _add_block(page_id, "divider", {})


def _add_callout(page_id, text, icon="💡", color="gray_background"):
    """إضافة Callout box"""
    content = {
        "rich_text": [{"type": "text", "text": {"content": text}}],
        "icon": {"emoji": icon},
        "color": color
    }
    return _add_block(page_id, "callout", content)


def _add_table_row(page_id, cells, color="default"):
    """إضافة صف جدول (كـ bullet points مع تنسيق)"""
    content = {
        "rich_text": [{"type": "text", "text": {"content": " │ ".join(str(c) for c in cells)}}],
        "color": color
    }
    return _add_block(page_id, "bulleted_list_item", content)


# ── محلل ROADMAP.md ───────────────────────────────────────

def _parse_roadmap_sections():
    """تحليل ROADMAP.md إلى أقسام مفهومة"""
    if not os.path.exists(ROADMAP_PATH):
        logger.error(f"[NOTION] ROADMAP.md not found at {ROADMAP_PATH}")
        return []

    with open(ROADMAP_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    sections = []
    current_section = {"title": "", "level": 0, "lines": []}

    for line in content.split("\n"):
        # كشف العناوين
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
    """استخراج المهام من قسم Kanban"""
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
        # إذا وصلنا لقسم جديد
        if section["level"] <= 2 and "Kanban" not in section["title"] and "لوحة" not in section["title"]:
            break

        for line in section["lines"]:
            stripped = line.strip()
            # Done items: - [x]
            if "- [x]" in stripped:
                item = stripped.split("- [x]")[-1].strip().lstrip(")").strip()
                if item:
                    done.append(item)
            # In Progress: - [ ]
            elif "- [ ]" in stripped and any(w in stripped.lower() for w in ["in progress", "قيد", "الآن"]):
                item = stripped.split("- [ ]")[-1].strip().lstrip(")").strip()
                if item:
                    in_progress.append(item)
            # Backlog items
            elif "backlog" in section["title"].lower() or "القادمة" in section["title"]:
                if stripped.startswith("- [") and "[x]" not in stripped:
                    item = stripped.split("]")[-1].strip()
                    if item:
                        backlog.append(item)
                elif stripped.startswith("- ") and not stripped.startswith("- ["):
                    item = stripped[2:].strip()
                    if item and not item.startswith("```") and not item.startswith("|"):
                        backlog.append(item)

    return done, in_progress, backlog


def _extract_adr(content_sections):
    """استخراج ADR entries"""
    in_adr = False
    adrs = []

    for section in content_sections:
        if "ADR" in section["title"] or "القرارات" in section["title"]:
            in_adr = True
            continue
        if not in_adr:
            continue
        if section["level"] <= 2 and "ADR" not in section["title"]:
            break

        # كل ADR يبدأ بـ ### ADR-XXX
        for line in section["lines"]:
            m = re.match(r"\|\s*\*\*(.+?)\*\*\s*\|\s*(.+?)\s*\|", line)
            if m and m.group(1) in ["التاريخ", "المشكلة", "القرار", "الملف", "الـ Commits"]:
                adrs.append(f"**{m.group(1)}**: {m.group(2)}")

    return adrs


# ── دوال البناء في Notion ─────────────────────────────────

def _build_status_section(page_id, sections):
    """بناء قسم الوضع الحالي"""
    _add_heading(page_id, 1, "📌 الوضع الحالي (Current Status)", "blue_background")

    # الأسطر المهمة
    for section in sections:
        if "الوضع الحالي" in section["title"] or "Current Status" in section["title"]:
            for line in section["lines"]:
                stripped = line.strip()
                if stripped.startswith("|") and "المعلم" not in stripped and "---" not in stripped:
                    parts = [p.strip() for p in stripped.split("|") if p.strip()]
                    if len(parts) >= 4:
                        _add_table_row(page_id, parts[:4], "default")

    _add_divider(page_id)


def _build_phases_section(page_id, sections):
    """بناء قسم خريطة المراحل"""
    _add_heading(page_id, 1, "🗺️ خريطة المراحل (Phases)", "purple_background")

    for section in sections:
        level = section["level"]
        title = section["title"]

        if "Phase" in title or "المرحلة" in title:
            color = "green_background" if "✅" in title else "yellow_background"
            _add_heading(page_id, level, title, "default" if level > 2 else color)
        elif level == 3:
            _add_heading(page_id, 3, title, "default")

    _add_divider(page_id)


def _build_kanban_section(page_id, sections):
    """بناء قسم لوحة المهام مع أعمدة"""
    _add_heading(page_id, 1, "📋 لوحة المهام (Kanban Board)", "orange_background")

    done, in_progress, backlog = _extract_kanban_items(sections)

    _add_heading(page_id, 2, "✅ Done (تم الإنجاز)", "green_background")
    for item in done[:20]:
        _add_bullet(page_id, f"✅ {item}", "green")

    _add_heading(page_id, 2, "🔄 In Progress (قيد التنفيذ)", "yellow_background")
    for item in in_progress[:10]:
        _add_bullet(page_id, f"🔄 {item}", "yellow")

    _add_heading(page_id, 2, "⏳ Backlog (المهام القادمة)", "gray_background")
    for item in backlog[:15]:
        _add_bullet(page_id, f"⏳ {item}", "default")

    _add_divider(page_id)


def _build_adr_section(page_id, sections):
    """بناء قسم ADR"""
    _add_heading(page_id, 1, "⚠️ سجل القرارات البرمجية (ADR)", "red_background")

    for section in sections:
        if "ADR-" in section["title"]:
            _add_heading(page_id, 3, section["title"], "default")
            for line in section["lines"]:
                stripped = line.strip()
                if stripped.startswith("|") and "---" not in stripped:
                    parts = [p.strip() for p in stripped.split("|") if p.strip()]
                    if len(parts) == 2:
                        _add_bullet(page_id, f"**{parts[0]}**: {parts[1]}", "default")

    _add_divider(page_id)


def _build_footer(page_id):
    """بناء تذييل"""
    _add_callout(page_id,
                 f"🔄 آخر تحديث: {datetime.now().strftime('%d %B %Y %H:%M')} | "
                 f"بواسطة RC Agents → ROADMAP.md Sync",
                 "🤖", "gray_background")


# ── الدالة الرئيسية ───────────────────────────────────────

def sync_roadmap_to_notion():
    """
    الدالة الرئيسية: مسح الصفحة وإعادة بنائها من ROADMAP.md
    """
    if not NOTION_TOKEN or not NOTION_PAGE_ID:
        logger.warning("[NOTION] NOTION_TOKEN أو NOTION_PAGE_ID غير معرفين. تخطي المزامنة.")
        return False

    logger.info("[NOTION] بدء مزامنة ROADMAP.md → Notion...")

    # 1. تحليل ROADMAP.md
    sections = _parse_roadmap_sections()
    if not sections:
        logger.warning("[NOTION] ROADMAP.md فارغ أو غير موجود")
        return False

    # 2. مسح المحتوى القديم
    try:
        _delete_all_blocks(NOTION_PAGE_ID)
    except Exception as e:
        logger.error(f"[NOTION] فشل مسح الـ blocks: {e}")
        return False

    # 3. إضافة header + Callout افتتاحي
    _add_callout(NOTION_PAGE_ID,
                 "🚀 **RC Agents — خارطة الطريق**\n"
                 "يتم تحديثها تلقائياً من ROADMAP.md عند كل Sync.",
                 "🗺️", "blue_background")

    # 4. بناء الأقسام
    _build_status_section(NOTION_PAGE_ID, sections)
    _build_phases_section(NOTION_PAGE_ID, sections)
    _build_kanban_section(NOTION_PAGE_ID, sections)
    _build_adr_section(NOTION_PAGE_ID, sections)
    _build_footer(NOTION_PAGE_ID)

    logger.info("[NOTION] ✅ تمت المزامنة بنجاح!")
    return True


def sync_roadmap_quick():
    """
    إصدار سريع مع طباعة النتيجة
    للاستخدام من سكريبت أو أمر سريع
    """
    success = sync_roadmap_to_notion()
    if success:
        print("✅ ROADMAP.md → Notion: Sync complete!")
    else:
        print("❌ ROADMAP.md → Notion: Sync failed. Check logs.")
    return success


if __name__ == "__main__":
    # تشغيل مباشر
    logging.basicConfig(level=logging.INFO)
    sync_roadmap_quick()
