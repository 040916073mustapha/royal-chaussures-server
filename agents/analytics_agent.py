#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Royal Chaussures - Analytics Agent
==================================
وكيل التحليلات والتقارير: إحصائيات المبيعات، تحليل سلوك الزبائن
يوفر تقارير فورية وبيانات ذكية لاتخاذ القرارات
"""

from agents.config import AGENTS_CONFIG
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger("royal-server")


def get_agent_info():
    """معلومات الوكيل للعرض"""
    return AGENTS_CONFIG.get("analytics_agent", {})


def get_system_prompt(store_id=1, store_name="Royal Chaussures"):
    """الحصول على system prompt للتحليلات والتقارير"""
    return (
        f"[ANALYTICS AGENT - {store_name}]\n"
        "أنت وكيل تحليلات ذكي لمتجر أحذية وإكسسوارات نسائية.\n"
        "تتحدث بالعربية والدارجة والفرنسية.\n\n"
        "مهمتك:\n"
        "1. تقديم تقارير المبيعات اليومية والأسبوعية والشهرية\n"
        "2. تحليل أداء المنتجات (الأكثر مبيعاً، الأقل مبيعاً)\n"
        "3. تحليل سلوك الزبائن (المتكررون، الجدد، المترددون)\n"
        "4. توقعات المبيعات والاتجاهات الموسمية\n"
        "5. تقارير أداء القنوات (Messenger, WhatsApp, Instagram)\n"
        "6. تحليل فعالية الحملات التسويقية\n"
        "7. مؤشرات الأداء الرئيسية (KPIs)\n\n"
        "قواعد:\n"
        "- قدم الأرقام بشكل واضح ومفهوم 📊\n"
        "- استخدم الرسوم البيانية النصية إن أمكن 📈📉\n"
        "- ركز على الرؤى القابلة للتنفيذ، ليس فقط الأرقام\n"
        "- خاطب المدير (مصطفى) بلغة مهنية\n"
        "- قدم توصيات مبنية على البيانات\n"
        "- لا تشارك معلومات حساسة (بيانات العملاء الخ) مع الزبائن\n"
        "- عندما يطلب مدير أو مسؤول التقرير، قدم تحليلاً عميقاً"
    )


def format_sales_report(report_data):
    """تنسيق تقرير مبيعات كامل"""
    lines = ["📊 **تقرير المبيعات**", "=" * 30]
    
    total = report_data.get("total_revenue", 0)
    orders = report_data.get("total_orders", 0)
    avg_order = round(total / orders, 2) if orders else 0
    period = report_data.get("period", "اليوم")
    
    lines.append(f"📅 الفترة: {period}")
    lines.append(f"💰 إجمالي الإيرادات: {total:,.0f} د.ج")
    lines.append(f"📦 عدد الطلبات: {orders}")
    lines.append(f"💳 متوسط قيمة الطلب: {avg_order:,.0f} د.ج")
    lines.append("")
    
    # Top products
    top_products = report_data.get("top_products", [])
    if top_products:
        lines.append("🏆 **الأكثر مبيعاً:**")
        for i, p in enumerate(top_products[:5], 1):
            lines.append(f"  {i}. {p['name']} — {p['count']} قطعة ({p['revenue']:,.0f} د.ج)")
        lines.append("")
    
    # Channel breakdown
    channels = report_data.get("channel_breakdown", {})
    if channels:
        lines.append("📱 **حسب القناة:**")
        for ch, data in channels.items():
            lines.append(f"  {ch}: {data.get('orders', 0)} طلبات / {data.get('revenue', 0):,.0f} د.ج")
        lines.append("")
    
    # Comparison
    prev = report_data.get("previous_period", {})
    if prev:
        growth = ((total - prev.get("revenue", 0)) / max(prev.get("revenue", 1), 1)) * 100
        emoji = "📈" if growth >= 0 else "📉"
        lines.append(f"{emoji} مقارنة بالفترة السابقة: {growth:+.1f}%")
    
    return "\n".join(lines)


def format_top_products_reply(products):
    """تنسيق تقرير أفضل المنتجات"""
    if not products:
        return "لا توجد بيانات مبيعات كافية للتحليل حالياً. 📭"
    
    lines = ["🏆 **أفضل المنتجات مبيعاً:**\n"]
    for i, p in enumerate(products[:10], 1):
        medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"  {i}."
        lines.append(f"{medal} **{p.get('title', 'منتج')}**")
        lines.append(f"   📦 مبيعات: {p.get('count', 0)} | 💰 {p.get('revenue', 0):,.0f} د.ج")
        lines.append("")
    
    return "\n".join(lines)


def format_customer_insights(insights):
    """تنسيق تحليل سلوك الزبائن"""
    lines = ["👥 **تحليل الزبائن**", "=" * 25]
    
    lines.append(f"👤 إجمالي الزبائن: {insights.get('total_customers', 0)}")
    lines.append(f"🆕 زبائن جدد: {insights.get('new_customers', 0)}")
    lines.append(f"🔄 زبائن عائدون: {insights.get('returning_customers', 0)}")
    lines.append(f"⭐ نسبة العودة: {insights.get('return_rate', 0):.1f}%")
    lines.append("")
    
    top_cities = insights.get("top_cities", [])
    if top_cities:
        lines.append("📍 **أكثر المدن طلباً:**")
        for city, count in top_cities[:5]:
            lines.append(f"  • {city}: {count} طلب")
        lines.append("")
    
    lines.append("💡 **توصيات:**")
    if insights.get('return_rate', 0) < 20:
        lines.append("  • تحسين خدمة ما بعد البيع لزيادة نسبة العودة")
    if insights.get('new_customers', 0) > insights.get('returning_customers', 0):
        lines.append("  • إطلاق برنامج ولاء للحفاظ على الزبائن الجدد")
    lines.append("  • استهداف الزبائن في المدن ذات الطلب العالي")
    
    return "\n".join(lines)


def format_channel_performance(channel_data):
    """تنسيق أداء القنوات"""
    lines = ["📱 **أداء القنوات**", "=" * 25]
    
    for channel, data in channel_data.items():
        emoji = {"messenger": "💬", "whatsapp": "💚", "instagram": "📸"}.get(channel, "📱")
        lines.append(f"\n{emoji} **{channel.capitalize()}**")
        lines.append(f"  💬 محادثات: {data.get('conversations', 0)}")
        lines.append(f"  ✅ تم الرد: {data.get('replied', 0)}")
        lines.append(f"  📊 معدل الرد: {data.get('reply_rate', 0):.1f}%")
        lines.append(f"  🛍️ تحويل: {data.get('conversions', 0)}")
    
    return "\n".join(lines)


def format_kpi_dashboard(kpi_data):
    """تنسيق لوحة مؤشرات الأداء"""
    lines = ["🎯 **مؤشرات الأداء الرئيسية (KPIs)**\n"]
    
    metrics = [
        ("💵 الإيرادات اليومية", f"{kpi_data.get('daily_revenue', 0):,.0f} د.ج"),
        ("📊 معدل التحويل", f"{kpi_data.get('conversion_rate', 0):.1f}%"),
        ("😊 رضا العملاء", f"{'⭐' * round(kpi_data.get('satisfaction', 4))}"),
        ("⏱️ وقت الرد", f"{kpi_data.get('avg_response_time', 0):.0f} ثانية"),
        ("📦 الطلبات المنجزة", str(kpi_data.get('fulfilled_orders', 0))),
        ("🔄 الزبائن العائدون", f"{kpi_data.get('return_rate', 0):.1f}%"),
    ]
    
    for label, value in metrics:
        lines.append(f"  {label}: {value}")
    
    return "\n".join(lines)
