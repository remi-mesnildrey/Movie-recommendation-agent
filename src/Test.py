from pydantic import BaseModel, ValidationError, Field, EmailStr
from typing import List, Optional, Literal
from datetime import date, datetime
from openai import OpenAI
import json

from openai import OpenAI

response_content = {
  "genre": "action",
  "year": 1980,
  "rating": 8.0,
  "audience": "adults",
  "other_preferences": "Bruce Willis"
}



class LibraryLookupArgs(BaseModel):
    title: str = Field(..., description="title of the movie to look up in the library") 
    year: int = Field(..., description="year of the movie to look up in the library")


# Define your FAQ lookup tool
def lookup_faq_answer(args: LibraryLookupArgs) -> str:
    """Look up a movie by matching a title and a release year against the library."""
    with open("src/movie_library.json", "r") as f:
        movie_library = json.load(f)
        for movie in movie_library:
            if movie["title"].lower() == args.title.lower() and movie["year"] == args.year:
                return f"Movie found: {movie['title']} ({movie['year']})"
            else:
                continue
    return "Sorry, I couldn't find an FAQ answer for your question."