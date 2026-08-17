#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Royal Chaussures - Cloud Server for Render
============================================
يجمع بين:
1. Flask Web App (Dashboard HTML + API)
2. Webhook Receiver (FB Messenger, WhatsApp, Instagram)
3. Shopify Webhook Handler (New Orders, Fulfillments)
4. ZR Express Tracking
5. Health Check
Designed for 24/7 operation on Render.com
"""
import requests
import json
import os
import sys
import sqlite3
import logging
import hashlib
import hmac
import base64
import time
import threading
from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, render_template_string, Response
def _safe_str(val):
    """Convert exception/value to pure-ASCII string, keeping it safe for logs and JSON"""
    s = repr(val) if isinstance(val, BaseException) else str(val)
    return s.encode('ascii', errors='replace').decode('ascii')
def json_utf8(data, status=200):
    """Return JSON using Flask's native response but with ensured ASCII safety"""
    payload = json.dumps(data, ensure_ascii=True, default=_safe_str)
    return Response(payload, status=status, content_type='application/json; charset=utf-8')
# Logging helper: never pass raw exceptions to logger (they may contain unicode)
def _log_safe(logger_fn, msg_prefix, exc):
    safe = _safe_str(exc) if isinstance(exc, BaseException) else str(exc).encode('ascii', errors='replace').decode('ascii')
    logger_fn(f"{msg_prefix}: {safe}")
load_dotenv()
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("royal-server")
import os
_STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
_TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=_TEMPLATE_DIR, static_folder=_STATIC_DIR, static_url_path='/static')
app.secret_key = os.urandom(24).hex()
# After-request: ensure all text responses declare utf-8
@app.after_request
def set_utf8_headers(response):
    ct = response.content_type or ''
    if 'charset' not in ct.lower() and (ct.startswith('text/') or ct.startswith('application/json')):
        response.content_type = ct.split(';')[0] + '; charset=utf-8'
    return response
