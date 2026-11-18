import streamlit as st
from agent import recommend_movie, movie_library

st.set_page_config(
    page_title="Movie Recommendation Agent",
    page_icon="🎬",
    layout="centered",
)

st.title("🎬 Movie Recommendation Agent")
st.caption("Searches your local library first, then searches the web for streaming links if not found.")

# Sidebar showing what's currently in the local JSON library
with st.sidebar:
    st.header("📚 Local Movie Library")
    st.write(f"You have **{len(movie_library)}** movies in your library")
    for m in movie_library:
        with st.expander(f"{m.title} ({m.year or 'N/A'})"):
            st.write(f"**Genre:** {m.genre or 'N/A'}")
            st.write(f"**Rating:** {m.rating or 'N/A'}/10")
            st.write(f"**Director:** {m.director or 'N/A'}")
            if m.lead_actors:
                st.write(f"**Cast:** {', '.join(m.lead_actors)}")

# Example prompt presets
st.markdown("**Try an example or enter your own request:**")
col1, col2 = st.columns(2)
default_prompt = ""

if col1.button("💥 80s Bruce Willis Action"):
    default_prompt = "Please recommend an action movie from the 80s with a good rating. Something with Bruce Willis would be great!"
if col2.button("🚀 Mind-bending Sci-Fi"):
    default_prompt = "Recommend a high-rated sci-fi movie with great visuals."
if col2.button("A Christopher Nolan movie"):
    default_prompt = "Recommend a high-rated movie directed by Christopher Nolan."

# Input form
with st.form("recommendation_form"):
    user_query = st.text_area(
        "What are you in the mood to watch?",
        value=default_prompt,
        placeholder="e.g., A feel-good 90s comedy with Tom Hanks...",
        height=100,
    )
    submitted = st.form_submit_button("Find Movie", type="primary", use_container_width=True)

# Handle submission
if submitted:
    if not user_query.strip():
        st.warning("Please enter a movie request first.")
    else:
        with st.spinner("Searching library and checking streaming availability..."):
            try:
                rec = recommend_movie(user_query)

                st.divider()

                # Header & Source Badge
                title_text = f"{rec.title or 'Unknown Title'}"
                if rec.year:
                    title_text += f" ({rec.year})"
                st.subheader(title_text)

                if rec.source == "In Movie Library":
                    st.success("✅ Available in your Local Movie Library")
                else:
                    st.info("🌐 Found via External Streaming Search")

                # Key Metadata Columns
                m1, m2, m3 = st.columns(3)
                m1.metric("Rating", f"{rec.rating}/10" if rec.rating is not None else "N/A")
                m2.metric("Genre", rec.genre.capitalize() if rec.genre else "N/A")
                m3.metric("Audience", rec.audience.capitalize() if rec.audience else "N/A")

                # Credits & Synopsis
                if rec.director:
                    st.markdown(f"**Director:** {rec.director}")
                if rec.lead_actors:
                    st.markdown(f"**Lead Actors:** {', '.join(rec.lead_actors)}")
                if rec.synopsis:
                    st.markdown(f"**Synopsis:** {rec.synopsis}")

                # Streaming Link Button
                if rec.link_to_streaming:
                    st.link_button("▶️ Watch / Stream Online", rec.link_to_streaming)

                # Raw JSON Output Expander
                with st.expander("View Raw Pydantic Output"):
                    st.json(rec.model_dump())

            except Exception as e:
                st.error(f"An error occurred while generating a recommendation: {e}")