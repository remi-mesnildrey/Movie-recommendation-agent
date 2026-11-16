from pydantic import BaseModel, ValidationError, Field, EmailStr
from typing import List, Optional, Literal
from datetime import date, datetime
from openai import OpenAI
import json
from pathlib import Path

folder = Path(__file__).parent
file_path = folder / "movie_library.json"
movie_library = {"Movie library": json.loads(file_path.read_text())}

print(movie_library)

function isJsonString(str) {
  try {
    JSON.parse(str);
    return true;
  } catch (e) {
    return false;
  }
}

