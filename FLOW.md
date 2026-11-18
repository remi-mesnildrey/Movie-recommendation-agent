```mermaid
sequenceDiagram
    autonumber
    actor User
    participant UI as Streamlit UI (app.py)
    participant Agent as Agent & Tool Loop (agent.py)
    participant Local as Local movie_library.json
    participant Model as OpenAI GPT-4o / Tools
    participant Web as Web Search (gpt-5-search-api)

    User->>UI: Enter prompt / click preset & submit
    UI->>Agent: recommend_movie(user_input)
    Agent->>Model: Chat completion with system prompt & tools
    
    rect rgb(240, 248, 255)
        note right of Model: Step 1: Check Local Library
        Model->>Agent: Tool Call: lookup_movie_in_library(...)
        Agent->>Local: Filter movies by title/genre/actors
        Local-->>Agent: JSON status ("found" or "no_matches")
        Agent->>Model: Return tool output
    end

    alt Movie found in local library
        Model-->>Agent: Final conversational response matching library movie
    else No matches found locally
        rect rgb(255, 245, 238)
            note right of Model: Step 2: Fallback to Web Search
            Model->>Agent: Tool Call: find_streaming_link_for_movie(...)
            Agent->>Web: Search online streaming links / JustWatch
            Web-->>Agent: Direct streaming URL & details
            Agent->>Model: Return streaming tool output
        end
        Model-->>Agent: Final recommendation incorporating external link
    end

    Agent->>Model: beta.chat.completions.parse(RecommendationResponse)
    Model-->>Agent: Validated Pydantic Object (RecommendationResponse)
    Agent-->>UI: Return RecommendationResponse object
    UI->>User: Display success badges, metadata, & streaming button
