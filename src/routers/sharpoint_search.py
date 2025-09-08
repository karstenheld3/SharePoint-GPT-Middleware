import os
import json
import logging
from typing import Any, Dict, Optional, List
from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import JSONResponse
from utils import *

router = APIRouter()

# Configuration will be injected from app.py
config = None

logger = logging.getLogger(__name__)

def set_config(app_config):
  """Set the configuration for SharePoint Search."""
  global config
  config = app_config

