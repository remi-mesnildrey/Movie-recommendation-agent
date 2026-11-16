from pydantic import BaseModel, ValidationError, Field, EmailStr
from typing import List, Optional, Literal
from datetime import date, datetime
from openai import OpenAI
from pathlib import Path
import json

from openai import OpenAI
openai_client = OpenAI()




## Example user input for movie recommendation requests
user_input = "Please recommend an action movie from the 80s with a good rating. Something with Bruce Willis would be great!"


## Pydantic Models
class Movie(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=100)
    year: Optional[int] = Field(default=None, ge=1900, le=2026)
    genre: Optional[Literal["action", "comedy", "drama", "sci-fi", "thriller", "horror", "romance"]] = None
    rating: Optional[float] = Field(default=None, ge=0.0, le=10.0)
    audience: Optional[Literal["family", "adults", "teens"]] = None
    director: Optional[str] = None
    lead_actors: Optional[List[str]] = None
    synopsis: Optional[str] = Field(default=None, min_length=10, max_length=500)

class MoviesInLibrary(BaseModel):
    movies: List[Movie]

class RecommendationResponse(Movie):
    source: Literal["In Movie Library", "External link"] = "Movie Library"
    link_to_streaming: Optional[str] = None
    availability: Optional[Literal["available", "unavailable"]] = None



# Get the demo movie library from the JSON file.

folder = Path(__file__).parent
file_path = folder / "movie_library.json"
raw_data = json.loads(file_path.read_text())

if isinstance(raw_data, list):
    movie_library = [Movie.model_validate(m) for m in raw_data]
elif "movies" in raw_data:
    movie_library = [Movie.model_validate(m) for m in raw_data["movies"]]
else:
    first_key = next(iter(raw_data))
    movie_library = [Movie.model_validate(m) for m in raw_data[first_key]]




# Tool argument classes
class LibraryLookupArgs(BaseModel):
    title: Optional[str] = Field(None, description="title of the movie to look up in the library") 
    genre: Optional[Literal["action", "comedy", "drama", "sci-fi", "thriller", "horror", "romance"]] = Field(default=None, description="Genre of the movie")
    lead_actors: Optional[List[str]] = Field(None, description="lead actors of the movie to look up in the library")

class StreamingSearchArgs(BaseModel):
    title: str = Field(None, description="title of the movie to search for streaming availability") 
    year: Optional[int] = Field(default=None, description="Release year of the movie to ensure an accurate search")


# Tool functions
def lookup_movie_in_library(lookup_args: LibraryLookupArgs) -> str:
    """
    Look up movies in the local JSON library based on the provided lookup arguments.
    """
    print(f"[Tool Executed] lookup_movie_in_library({lookup_args.model_dump(exclude_none=True)})")

    matching_movies = []
    for movie in movie_library:
        if lookup_args.title and lookup_args.title.lower() not in (movie.title or "").lower():
            continue
        if lookup_args.genre and lookup_args.genre != movie.genre:
            continue
        if lookup_args.lead_actors:
            movie_actors_lower = [a.lower() for a in (movie.lead_actors or [])]
            if not any(
                any(req_actor.lower() in m_actor for m_actor in movie_actors_lower)
                for req_actor in lookup_args.lead_actors
            ):
                continue

        matching_movies.append(movie.model_dump())

    if not matching_movies:
        return json.dumps({"status": "no_matches", "movies": []})
    return json.dumps({"status": "found", "movies": matching_movies})

def find_streaming_link_for_movie(args: StreamingSearchArgs) -> str:
    """
    Finds an online streaming or rental link for a specific movie when it is not
    available in the local library.
    """
    print(f"[Tool Executed] find_streaming_link_for_movie({args.model_dump(exclude_none=True)})")

    year_str = f" ({args.year})" if args.year else ""
    prompt = (
        f"Find where to legally stream, rent, or buy the movie '{args.title}'{year_str} online. "
        f"Provide a direct URL (e.g., JustWatch, Amazon Prime Video, Apple TV, Disney+, etc.)."
    )

    # Uses OpenAI's web-search enabled model to get a real streaming URL
    search_response = openai_client.chat.completions.create(
        model="gpt-4o-search-preview",
        messages=[{"role": "user", "content": prompt}],
    )

    return search_response.choices[0].message.content or "No streaming link found."


# Convert Pydantic argument classes into OpenAI tool schemas
tools = [
    {
        "type": "function",
        "function": {
            "name": "lookup_movie_in_library",
            "description": "Looks up movies in the local JSON library based on title, genre, lead actors, and other optional filters.",
            "parameters": LibraryLookupArgs.model_json_schema(),
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_streaming_link_for_movie",
            "description": "Finds an online streaming or rental link for a specific movie when it is not available in the local library.",
            "parameters": StreamingSearchArgs.model_json_schema(),
        }
    }
]



def recommend_movie(user_input: str) -> RecommendationResponse:
    """
    Recommends a movie based on the user's input.
    Checks the local library first; if not found, recommends a film and finds a streaming link.
    """
    system_prompt = (
        "You are a movie recommendation assistant. Follow these steps strictly:\n"
        "1. Always call `lookup_movie_in_library` first to check if a matching film exists.\n"
        "2. If a matching movie is found in the library, recommend it with source='Movie Library' "
        "and availability='available'.\n"
        "3. If `lookup_movie_in_library` returns 'no_matches', choose a real-world movie that "
        "fits the user's request, then call `find_streaming_link_for_movie` to find where to stream it. "
        "Set source='External API', availability='available' (if a link is found), and include the URL in `link_to_streaming`."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
    ]

    # Loop until the model stops calling tools and is ready to give a final answer
    while True:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools,
        )

        assistant_message = response.choices[0].message
        messages.append(assistant_message)

        # If the LLM didn't call any tools, exit the loop and format the final output
        if not assistant_message.tool_calls:
            break

        # Execute every tool call requested by the LLM
        for tool_call in assistant_message.tool_calls:
            fn_name = tool_call.function.name
            raw_args = tool_call.function.arguments

            if fn_name == "lookup_movie_in_library":
                parsed_args = LibraryLookupArgs.model_validate_json(raw_args)
                tool_output = lookup_movie_in_library(parsed_args)

            elif fn_name == "find_streaming_link_for_movie":
                parsed_args = StreamingSearchArgs.model_validate_json(raw_args)
                tool_output = find_streaming_link_for_movie(parsed_args)

            else:
                tool_output = json.dumps({"error": f"Unknown tool: {fn_name}"})

            # Feed the tool result back to the LLM
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_output,
                }
            )

    # Parse the final conversation state into your Pydantic RecommendationResponse model
    final_parsed = openai_client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=messages,
        response_format=RecommendationResponse,
    )

    return final_parsed.choices[0].message.parsed




if __name__ == "__main__":
    user_input = (
        "Please recommend an action movie from the 80s with a good rating. "
        "Something with Bruce Willis would be great!"
    )

    recommendation = recommend_movie(user_input)
    print("\nFinal Recommendation:")
    print(recommendation.model_dump_json(indent=2))

    