"""The entry point for the LinkedIn Post Generator API."""

import json
import logging
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator


logger = logging.getLogger(__name__)
AI_PROVIDER = os.getenv("AI_PROVIDER", "ollama").strip().lower()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
FRONTEND_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "FRONTEND_ORIGINS",
        "http://127.0.0.1:5500,http://localhost:5500,https://linkedin-post-generator-369j.onrender.com",
    ).split(",")
    if origin.strip()
]


app = FastAPI(
    title="LinkedIn Post Generator API",
    description="Backend API for generating LinkedIn post drafts.",
    version="0.1.0",
)

# Configure local and deployed frontend origins with FRONTEND_ORIGINS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


class GeneratePostRequest(BaseModel):
    """The fields the frontend must send to request a post."""

    topic: str
    purpose: str
    tone: str
    audience: str
    length: str
    additional_info: str = ""

    @field_validator("topic")
    @classmethod
    def topic_must_not_be_empty(cls, value: str) -> str:
        """Reject a topic that is empty or contains only whitespace."""
        cleaned_topic = value.strip()
        if not cleaned_topic:
            raise ValueError("Topic must not be empty.")
        return cleaned_topic


@app.get("/health")
def health_check():
    """Confirm that the API server is running."""
    return {"status": "ok"}


def generate_linkedin_post(
    topic: str, purpose: str, audience: str, tone: str, length: str, additional_info: str = ""
) -> str:
    """Generate one LinkedIn post using the configured AI provider."""

    length_guidance = {
        "Short": "about 80 to 120 words",
        "Medium": "about 150 to 220 words",
        "Long": "about 220 to 300 words",
    }.get(length, length)

    purpose_guidance = {
        "Project Progress": "Open with a first-person update about the work, but only name work, progress, tools, or next steps that the user stated.",
        "Learning Progress": "Open with a personal learning reflection. Cover only stated learning and challenges; finish with a takeaway grounded in those details.",
        "Achievement": "Announce the stated achievement near the beginning with pride and humility. Do not inflate its impact.",
        "Milestone": "Open with a varied first-person milestone announcement and celebrate the stated milestone. Say it was completed only when the user explicitly says so; reflect on effort only if described.",
        "Gratitude": "Open naturally with appreciation and thank only the person or group named by the user, for the support they described.",
        "Tech News": "Write an engaging, informative post about the stated news. Do not frame it as the user's personal achievement or add unsupported claims.",
        "Collaboration": "Highlight only the stated teamwork, contributions, and shared accomplishment. Do not invent team members or outcomes.",
        "Other": "Write a personal, natural LinkedIn post based on the user's stated experience and details.",
    }.get(purpose, "Write a natural professional LinkedIn post guided by the user's input.")

    tone_guidance = {
        "Professional": "polished and credible",
        "Friendly": "warm and approachable",
        "Inspirational": "encouraging and uplifting",
        "Storytelling": "narrative, personal, and engaging",
        "Casual": "conversational and relaxed",
        "Thoughtful": "reflective and considered",
    }.get(tone, "natural and appropriate")

    prompt = f"""Write a LinkedIn post for the person described by these inputs. For personal purposes, write from their first-person perspective instead of explaining the topic like an essay. Start with an engaging, purpose-appropriate personal hook; vary its wording rather than reusing a template. Use short paragraphs, simple language, and a natural, grounded conclusion. The final line MUST contain 3 to 6 relevant hashtags. Use an emoji only if it feels natural. Do not add headings unless needed.

Topic: {topic}
Post purpose: {purpose}
Purpose-specific approach: {purpose_guidance}
Target audience: {audience}
Tone: {tone} — make the wording and rhythm {tone_guidance} throughout.
Target length: {length_guidance}.
User-provided personal facts, experience, challenges, people, and context: {additional_info or "None provided"}

Important factual boundary: only the additional information contains personal events and claims. The topic is a subject, not proof that the person completed a course, made progress, built something, achieved a result, or has future plans. Do not invent experiences, technologies, people, effort, outcomes, or next steps. Do not embellish a named person's role, qualities, or contribution. Do not add emotions or judgments as if the user stated them. You may use a modest reflection directly supported by the stated details, but no other personal claims. If details are limited, write a shorter, honest post rather than filling gaps. Mention challenges and gratitude only when supplied.
"""

    system_instruction = (
        "You are an editor helping a real person write an engaging LinkedIn post, not an essay generator. "
        "Follow the requested purpose, tone, first-person voice, hook, and length. Use only facts explicitly "
        "present in the user's details. Do not embellish or infer motives, effort, emotions, progress, outcomes, "
        "or anything about a named person's role. Do not claim a course was completed unless explicitly stated. "
        "For personal posts, open with an engaging first-person hook and finish with 3 to 6 relevant hashtags. "
        "Return only the post text."
    )

    if AI_PROVIDER == "ollama":
        request = Request(
            f"{OLLAMA_BASE_URL}/api/generate",
            data=json.dumps({
                "model": "llama3.2:3b",
                "system": system_instruction,
                "prompt": prompt,
                "stream": False,
            }).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=120) as response:
                result = json.loads(response.read().decode("utf-8"))
        except URLError as error:
            if isinstance(error, HTTPError):
                raise HTTPException(
                    status_code=502,
                    detail=f"Ollama returned HTTP {error.code}. Check that model llama3.2:3b is available.",
                ) from error
            raise HTTPException(
                status_code=502,
                detail=f"Cannot connect to Ollama at {OLLAMA_BASE_URL}. Start Ollama and ensure llama3.2:3b is available.",
            ) from error
        generated_post = result.get("response", "").strip()
    elif AI_PROVIDER == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=503,
                detail="Production AI configuration is missing: set GEMINI_API_KEY in the service environment.",
            )

        try:
            from google import genai
            from google.genai import errors as genai_errors, types
        except ImportError as error:
            raise HTTPException(
                status_code=503,
                detail="Gemini support is not installed. Install the dependencies in backend/requirements.txt.",
            ) from error

        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(system_instruction=system_instruction),
            )
            generated_post = (response.text or "").strip()
        except genai_errors.APIError as error:
            status_code = getattr(error, "code", None)
            message = str(getattr(error, "message", None) or "Gemini API request failed.")
            message = message.replace(api_key, "[REDACTED]")
            logger.error(
                "Gemini API error type=%s status_code=%s message=%s",
                type(error).__name__,
                status_code,
                message,
            )
            raise HTTPException(
                status_code=502,
                detail=f"Gemini API error (HTTP {status_code}): {message}",
            ) from error
        except Exception as error:
            logger.error("Gemini request failed type=%s", type(error).__name__)
            raise HTTPException(
                status_code=502,
                detail="Gemini request failed. Check network access and the Gemini service configuration.",
            ) from error
    else:
        raise HTTPException(
            status_code=503,
            detail=f"Unsupported AI_PROVIDER '{AI_PROVIDER}'. Set it to 'ollama' or 'gemini'.",
        )

    if not generated_post:
        raise HTTPException(
            status_code=502,
            detail="The LLM service returned an empty post. Please try again.",
        )

    return generated_post


@app.post("/generate")
def generate_post(request: GeneratePostRequest):
    """Generate and return a LinkedIn post for the submitted choices."""
    post = generate_linkedin_post(
        topic=request.topic,
        purpose=request.purpose,
        audience=request.audience,
        tone=request.tone,
        length=request.length,
        additional_info=request.additional_info,
    )
    return {"post": post}
