from pydantic import BaseModel, ValidationError, Field, EmailStr
from typing import List, Optional, Literal
from datetime import date, datetime
from openai import OpenAI
import json

from openai import OpenAI


## Example user input for movie recommendation requests
user_input = "Please recommend an action movie from the 80s with a good rating. Something with Bruce Willis would be great!"


## Pydantic Models
class Movies(BaseModel):
    title: Optional[str] = Field(min_length=1, max_length=100)
    genre: Optional[Literal["action", "comedy", "drama", "sci-fi", "thriller", "horror", "romance"]] = None
    year: Optional[int] = Field(ge=1900, le=2025)
    rating: Optional[float] = Field(ge=0.0, le=10.0) 
    audience: Optional[Literal["family", "adults", "teens"]] = None
    director: Optional[str] = None
    lead_actor: Optional[str] = None
    synopsis: Optional[str] = Field(min_length=10, max_length=500)
    other_preferences: Optional[str] = None







# System prompt to guide the model's response
prompt = (
    f"Analyze the following customer query {user_input} "
    f"and provide a structured response."
)

# Call to OpenAI to format the user input into a structured response using the Movies model
openai_client = OpenAI()
response = openai_client.beta.chat.completions.parse(
    model="gpt-4o",
    messages=[{"role": "user", "content": prompt}],
    response_format=Movies
)
response_content = response.choices[0].message.content
print(type(response_content))
print(response_content)

# Validate the repsonse you got from the LLM
valid_data = Movies.model_validate_json(
    response_content
)
print(type(valid_data))
print(valid_data.model_dump_json(indent=2))




class LibraryLookupArgs(BaseModel):
    title: str = Field(..., description="title of the movie to look up in the library") 
    year: int = Field(..., description="year of the movie to look up in the library")


