from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Literal
from openai import OpenAI
from pathlib import Path
import json

openai_client = OpenAI()


## Pydantic Models
class Movie(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=100)
    year: Optional[int] = Field(default=None, ge=1900, le=2026)
    genre: Optional[
        Literal[
            "action", "comedy", "drama", "sci-fi", "thriller", "horror", "romance"
        ]
    ] = None
    rating: Optional[float] = Field(default=None, ge=0.0, le=10.0)
    audience: Optional[Literal["family", "adults", "teens"]] = None
    director: Optional[str] = None
    lead_actors: Optional[List[str]] = None
    synopsis: Optional[str] = Field(default=None, min_length=10, max_length=500)

    @field_validator("lead_actors", mode="before")
    @classmethod
    def split_actors_string(cls, v):
        if isinstance(v, str):
            return [actor.strip() for actor in v.split(",") if actor.strip()]
        return v


class RecommendationResponse(Movie):
    # Fixed Literal values to match your system prompt and default
    source: Literal["In Movie Library", "External link"] = "In Movie Library"
    link_to_streaming: Optional[str] = None
    availability: Optional[Literal["available", "unavailable"]] = None


# Load demo movie library
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
    title: Optional[str] = Field(
        None, description="title of the movie to look up in the library"
    )
    genre: Optional[
        Literal[
            "action", "comedy", "drama", "sci-fi", "thriller", "horror", "romance"
        ]
    ] = Field(default=None, description="Genre of the movie")
    lead_actors: Optional[List[str]] = Field(
        None, description="lead actors of the movie to look up in the library"
    )


class StreamingSearchArgs(BaseModel):
    # Removed default=None on a required str field
    title: str = Field(
        ..., description="title of the movie to search for streaming availability"
    )
    year: Optional[int] = Field(
        default=None,
        description="Release year of the movie to ensure an accurate search",
    )


# Tool functions
def lookup_movie_in_library(lookup_args: LibraryLookupArgs) -> str:
    matching_movies = []
    for movie in movie_library:
        if (
            lookup_args.title
            and lookup_args.title.lower() not in (movie.title or "").lower()
        ):
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
    year_str = f" ({args.year})" if args.year else ""
    prompt = (
        f"Find where to legally stream, rent, or buy the movie '{args.title}'{year_str} online. "
        f"Provide a direct URL (e.g., JustWatch, Amazon Prime Video, Apple TV, Disney+, etc.)."
    )

    search_response = openai_client.responses.create(
        model="gpt-4o",
        tools=[{"type": "web_search"}],
        input=prompt,
    )

    text = getattr(search_response, "output_text", None)
    return text.strip() if text and text.strip() else "No streaming link found."


tools = [
    {
        "type": "function",
        "function": {
            "name": "lookup_movie_in_library",
            "description": "Looks up movies in the local JSON library based on title, genre, lead actors, and other optional filters.",
            "parameters": LibraryLookupArgs.model_json_schema(),
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_streaming_link_for_movie",
            "description": "Finds an online streaming or rental link for a specific movie when it is not available in the local library.",
            "parameters": StreamingSearchArgs.model_json_schema(),
        },
    },
]


def recommend_movie(user_input: str) -> RecommendationResponse:
    # Aligned source strings with RecommendationResponse Literal values
    system_prompt = (
        "You are a movie recommendation assistant. Follow these steps strictly:\n"
        "1. Always call `lookup_movie_in_library` first to check if a matching film exists.\n"
        "2. If a matching movie is found in the library, recommend it with source='In Movie Library' "
        "and availability='available'.\n"
        "3. If `lookup_movie_in_library` returns 'no_matches', choose a real-world movie that "
        "fits the user's request, then call `find_streaming_link_for_movie` to find where to stream it. "
        "Set source='External link', availability='available' (if a link is found), and include the URL in `link_to_streaming`."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
    ]

    while True:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools,
        )

        assistant_message = response.choices[0].message
        messages.append(assistant_message)

        if not assistant_message.tool_calls:
            break

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

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_output,
                }
            )

    final_parsed = openai_client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=messages,
        response_format=RecommendationResponse,
    )

    return final_parsed.choices[0].message.parsed