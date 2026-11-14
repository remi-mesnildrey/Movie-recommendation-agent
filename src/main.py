from pydantic import BaseModel, ValidationError, Field, EmailStr
from typing import List, Optional, Literal
from datetime import date, datetime
from openai import OpenAI
import json

from openai import OpenAI