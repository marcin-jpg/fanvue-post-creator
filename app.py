"""
Fanvue Post Creator - Gradio Application
Upload media and create posts on Fanvue with AI-generated captions.
"""

import gradio as gr
import httpx
import base64
import os
import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Configuration
FANVUE_API_BASE = "https://api.fanvue.com"
FANVUE_AUTH_URL = "https://auth.fanvue.com/oauth2/auth"
FANVUE_TOKEN_URL = "https://auth.fanvue.com/oauth2/token"
API_VERSION = "2025-06-26"

# Content ideas configuration
SEASONAL_THEMES = {
    1: ["New Year energy", "Winter cozy vibes", "Fresh start goals"],
    2: ["Valentine's Day", "Self-love", "Galentine's"],
    3: ["Spring awakening", "New beginnings", "Women's day"],
    4: ["Easter vibes", "Spring fashion", "Outdoor shoots"],
    5: ["Summer teaser", "Fitness motivation", "Beach prep"],
    6: ["Summer vibes", "Pool day", "Travel content"],
    7: ["Hot summer", "Vacation mode", "Beach content"],
    8: ["Late summer", "Golden hour shoots", "Back to routine"],
    9: ["Fall fashion", "Cozy season starts", "New chapter"],
    10: ["Halloween", "Costume/cosplay", "Spooky & sexy"],
    11: ["Thanksgiving", "Gratitude posts", "Black Friday promo"],
    12: ["Christmas", "Gift guides/wishlists", "New Year countdown"]
}

POST_TYPES = ["Photo", "Video", "Selfie", "Behind the scenes", "PPV exclusive", "Text/Story", "Poll/Q&A", "Carousel"]

# State
class AppState:
    def __init__(self):
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.creator_uuid: Optional[str] = None
        self.openai_client: Optional[OpenAI] = None

    def is_authenticated(self) -> bool:
        return self.access_token is not None

    def init_openai(self, api_key: str):
        self.openai_client = OpenAI(api_key=api_key)

state = AppState()

# Load saved tokens if exist
TOKEN_FILE = Path(__file__).parent / ".tokens.json"

def save_tokens():
    data = {
        "access_token": state.access_token,
        "refresh_token": state.refresh_token,
        "creator_uuid": state.creator_uuid
    }
    TOKEN_FILE.write_text(json.dumps(data))

def load_tokens():
    if TOKEN_FILE.exists():
        data = json.loads(TOKEN_FILE.read_text())
        state.access_token = data.get("access_token")
        state.refresh_token = data.get("refresh_token")
        state.creator_uuid = data.get("creator_uuid")
        return True
    return False

# Initialize OpenAI from env
if os.getenv("OPENAI_API_KEY"):
    state.init_openai(os.getenv("OPENAI_API_KEY"))


def get_headers():
    """Get headers for Fanvue API requests."""
    return {
        "Authorization": f"Bearer {state.access_token}",
        "X-Fanvue-API-Version": API_VERSION,
        "Content-Type": "application/json"
    }


def authenticate_with_token(access_token: str, refresh_token: str = "") -> str:
    """Authenticate using existing tokens."""
    state.access_token = access_token.strip()
    state.refresh_token = refresh_token.strip() if refresh_token else None

    # Test the token by getting user info
    try:
        with httpx.Client() as client:
            response = client.get(
                f"{FANVUE_API_BASE}/users/me",
                headers=get_headers()
            )
            if response.status_code == 200:
                # Get creator UUID
                creators_resp = client.get(
                    f"{FANVUE_API_BASE}/agency/creators",
                    headers=get_headers()
                )
                if creators_resp.status_code == 200:
                    creators = creators_resp.json().get("data", [])
                    if creators:
                        state.creator_uuid = creators[0]["uuid"]
                        save_tokens()
                        return f"Zalogowano! Creator: {creators[0].get('displayName', state.creator_uuid)}"
                    return "Zalogowano, ale nie znaleziono creatora."
                return f"Zalogowano, ale blad pobierania creatorow: {creators_resp.status_code}"
            else:
                state.access_token = None
                return f"Blad autoryzacji: {response.status_code} - {response.text}"
    except Exception as e:
        state.access_token = None
        return f"Blad polaczenia: {str(e)}"


def set_openai_key(api_key: str) -> str:
    """Set OpenAI API key."""
    if not api_key.strip():
        return "Podaj klucz API"
    state.init_openai(api_key.strip())
    return "Klucz OpenAI ustawiony!"


def generate_caption(image_path: str, style: str, custom_prompt: str = "") -> str:
    """Generate caption using AI."""
    if not state.openai_client:
        return "Najpierw ustaw klucz OpenAI API!"

    if not image_path:
        return "Najpierw wybierz obraz!"

    # Read and encode image
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode()

    # Determine mime type
    ext = Path(image_path).suffix.lower()
    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".gif": "image/gif", ".webp": "image/webp"}
    mime_type = mime_map.get(ext, "image/jpeg")

    # Build prompt based on style
    style_prompts = {
        "Sexy & Flirty": "Write a flirty, teasing caption for this photo. Be playful and seductive but tasteful. Use 1-2 emojis. Keep under 200 characters. Write in English.",
        "Casual & Fun": "Write a casual, fun caption for this photo. Be friendly and approachable. Use emojis. Keep under 200 characters. Write in English.",
        "Mysterious": "Write a mysterious, intriguing caption for this photo. Create curiosity. Use 1 emoji max. Keep under 200 characters. Write in English.",
        "Promotional": "Write a promotional caption encouraging followers to subscribe for more exclusive content. Mention 'link in bio' or similar. Use emojis. Keep under 250 characters. Write in English.",
        "Custom": custom_prompt if custom_prompt else "Write an engaging social media caption for this photo. Keep under 200 characters."
    }

    prompt = style_prompts.get(style, style_prompts["Casual & Fun"])

    try:
        response = state.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_data}",
                                "detail": "low"
                            }
                        }
                    ]
                }
            ],
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Blad generowania: {str(e)}"


def generate_video_caption(style: str, custom_prompt: str = "") -> str:
    """Generate caption for video (without vision)."""
    if not state.openai_client:
        return "Najpierw ustaw klucz OpenAI API!"

    style_prompts = {
        "Sexy & Flirty": "Write a flirty, teasing caption for a video post by a content creator. Be playful and seductive but tasteful. Use 1-2 emojis. Keep under 200 characters. Write in English.",
        "Casual & Fun": "Write a casual, fun caption for a video post. Be friendly and approachable. Use emojis. Keep under 200 characters. Write in English.",
        "Mysterious": "Write a mysterious, intriguing caption for a video. Create curiosity about what's in the video. Use 1 emoji max. Keep under 200 characters. Write in English.",
        "Promotional": "Write a promotional caption for a video encouraging followers to subscribe for more exclusive video content. Use emojis. Keep under 250 characters. Write in English.",
        "Custom": custom_prompt if custom_prompt else "Write an engaging social media caption for a video post. Keep under 200 characters."
    }

    prompt = style_prompts.get(style, style_prompts["Casual & Fun"])

    try:
        response = state.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Blad generowania: {str(e)}"


def upload_media(file_path: str) -> tuple[Optional[str], str]:
    """Upload media to Fanvue using multipart upload."""
    if not state.is_authenticated():
        return None, "Najpierw zaloguj sie!"

    if not file_path:
        return None, "Wybierz plik!"

    file_path = Path(file_path)
    filename = file_path.name
    file_size = file_path.stat().st_size

    # Determine media type
    ext = file_path.suffix.lower()
    if ext in [".mp4", ".mov", ".avi", ".webm"]:
        media_type = "video"
    else:
        media_type = "image"

    try:
        with httpx.Client(timeout=120.0) as client:
            # 1. Create upload session
            create_resp = client.post(
                f"{FANVUE_API_BASE}/media/upload/multipart/create",
                headers=get_headers(),
                json={
                    "name": filename,
                    "filename": filename,
                    "mediaType": media_type
                }
            )

            if create_resp.status_code != 200:
                return None, f"Blad tworzenia sesji: {create_resp.status_code} - {create_resp.text}"

            upload_data = create_resp.json()
            upload_id = upload_data["uploadId"]

            # 2. Get signed URL for upload
            sign_resp = client.post(
                f"{FANVUE_API_BASE}/media/upload/multipart/sign",
                headers=get_headers(),
                json={
                    "uploadId": upload_id,
                    "partNumber": 1
                }
            )

            if sign_resp.status_code != 200:
                return None, f"Blad pobierania URL: {sign_resp.status_code} - {sign_resp.text}"

            signed_url = sign_resp.json()["url"]

            # 3. Upload file to S3
            with open(file_path, "rb") as f:
                file_content = f.read()

            upload_resp = client.put(
                signed_url,
                content=file_content,
                headers={"Content-Type": "application/octet-stream"}
            )

            if upload_resp.status_code not in [200, 201]:
                return None, f"Blad uploadu S3: {upload_resp.status_code}"

            etag = upload_resp.headers.get("etag", "").strip('"')

            # 4. Complete upload
            complete_resp = client.post(
                f"{FANVUE_API_BASE}/media/upload/multipart/complete",
                headers=get_headers(),
                json={
                    "uploadId": upload_id,
                    "parts": [{"partNumber": 1, "eTag": etag}]
                }
            )

            if complete_resp.status_code != 200:
                return None, f"Blad finalizacji: {complete_resp.status_code} - {complete_resp.text}"

            media_uuid = complete_resp.json()["uuid"]
            return media_uuid, f"Upload ukonczony! Media UUID: {media_uuid}"

    except Exception as e:
        return None, f"Blad uploadu: {str(e)}"


def create_post(caption: str, media_uuid: str, audience: str, scheduled_at: str = "") -> str:
    """Create a post on Fanvue."""
    if not state.is_authenticated():
        return "Najpierw zaloguj sie!"

    if not state.creator_uuid:
        return "Brak creator UUID!"

    if not caption.strip():
        return "Podaj tekst posta!"

    audience_map = {
        "Wszyscy (publiczny)": "everyone",
        "Obserwujacy i subskrybenci": "followers-and-subscribers",
        "Tylko subskrybenci": "subscribers-only"
    }

    post_data = {
        "text": caption.strip(),
        "audience": audience_map.get(audience, "followers-and-subscribers")
    }

    if media_uuid:
        post_data["mediaUuids"] = [media_uuid]

    if scheduled_at:
        post_data["scheduledAt"] = scheduled_at

    try:
        with httpx.Client() as client:
            response = client.post(
                f"{FANVUE_API_BASE}/creators/{state.creator_uuid}/posts",
                headers=get_headers(),
                json=post_data
            )

            if response.status_code in [200, 201]:
                result = response.json()
                return f"Post utworzony!\nID: {result.get('uuid', 'N/A')}"
            else:
                return f"Blad tworzenia posta: {response.status_code} - {response.text}"

    except Exception as e:
        return f"Blad: {str(e)}"


def generate_content_ideas(niche: str, days: int, include_seasonal: bool, include_ppv: bool, progress=gr.Progress()) -> tuple:
    """Generate content ideas plan using GPT-4o."""
    if not state.openai_client:
        return [], "[]", "Najpierw ustaw klucz OpenAI API!"

    if not niche.strip():
        return [], "[]", "Opisz swoja nisze/styl!"

    progress(0.1, desc="Generowanie pomyslow...")

    current_month = datetime.now().month
    month_name = datetime.now().strftime("%B")

    seasonal_part = ""
    if include_seasonal:
        themes = SEASONAL_THEMES.get(current_month, [])
        seasonal_part = f"\nCurrent month: {month_name} - incorporate these seasonal themes: {', '.join(themes)}"

    ppv_part = ""
    if include_ppv:
        ppv_part = "\nInclude 2-3 PPV exclusive content ideas spread across the plan. PPV posts should be premium, exclusive content that subscribers pay extra for."
    else:
        ppv_part = "\nDo NOT include any PPV exclusive posts."

    post_types_str = ", ".join(POST_TYPES)

    prompt = f"""You are a content strategist for an adult content creator on Fanvue.

Niche/style: {niche}

Generate a {days}-day content plan.{seasonal_part}{ppv_part}

Mix these content types throughout the plan: {post_types_str}
Ensure variety - don't repeat the same type on consecutive days.
Include at least one series idea (e.g. "7 days of...", "Behind the scenes week").

For each day provide:
- day: day number (1 to {days})
- type: one of [{post_types_str}]
- idea: short description of the content idea (max 80 chars)
- caption_draft: a ready-to-use caption with emojis (max 200 chars)
- audience: one of [public, followers, subscribers]
- best_time: suggested posting time in HH:MM format (consider peak engagement hours)
- hashtags: 3-5 relevant hashtags as a string

Return ONLY a valid JSON array, no markdown formatting, no code blocks. Example format:
[{{"day":1,"type":"Photo","idea":"...","caption_draft":"...","audience":"public","best_time":"19:00","hashtags":"#tag1 #tag2 #tag3"}}]"""

    try:
        response = state.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            temperature=0.8
        )

        content = response.choices[0].message.content.strip()
        # Clean potential markdown code blocks
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            if content.endswith("```"):
                content = content[:-3].strip()

        ideas = json.loads(content)

        progress(0.9, desc="Przygotowywanie tabeli...")

        # Build table data
        table_data = []
        for idea in ideas:
            table_data.append([
                idea.get("day", ""),
                idea.get("type", ""),
                idea.get("idea", ""),
                idea.get("caption_draft", ""),
                idea.get("audience", ""),
                idea.get("best_time", ""),
                idea.get("hashtags", "")
            ])

        progress(1.0, desc="Gotowe!")
        return table_data, json.dumps(ideas, ensure_ascii=False), f"Wygenerowano plan na {len(ideas)} dni!"

    except json.JSONDecodeError as e:
        return [], "[]", f"Blad parsowania odpowiedzi AI: {str(e)}\n\nOdpowiedz:\n{content[:500]}"
    except Exception as e:
        return [], "[]", f"Blad generowania: {str(e)}"


def export_ideas_csv(ideas_json: str) -> Optional[str]:
    """Export ideas to CSV file."""
    if not ideas_json or ideas_json == "[]":
        return None

    try:
        ideas = json.loads(ideas_json)
        if not ideas:
            return None

        # Ensure pomysly directory exists
        export_dir = Path(__file__).parent / "pomysly"
        export_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = export_dir / f"content_plan_{timestamp}.csv"

        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["Dzien", "Typ", "Pomysl", "Caption", "Odbiorcy", "Godzina", "Hashtagi"])
            for idea in ideas:
                writer.writerow([
                    idea.get("day", ""),
                    idea.get("type", ""),
                    idea.get("idea", ""),
                    idea.get("caption_draft", ""),
                    idea.get("audience", ""),
                    idea.get("best_time", ""),
                    idea.get("hashtags", "")
                ])

        return str(filepath)

    except Exception:
        return None


def full_upload_and_post(file, caption: str, audience: str, progress=gr.Progress()) -> str:
    """Complete flow: upload media and create post."""
    if not file:
        return "Wybierz plik!"

    progress(0.1, desc="Uploadowanie media...")
    media_uuid, upload_msg = upload_media(file)

    if not media_uuid:
        return upload_msg

    progress(0.7, desc="Tworzenie posta...")
    result = create_post(caption, media_uuid, audience)

    progress(1.0, desc="Gotowe!")
    return f"{upload_msg}\n\n{result}"


# Load tokens on startup
load_tokens()


# Build Gradio Interface
with gr.Blocks(title="Fanvue Post Creator", theme=gr.themes.Soft()) as app:
    gr.Markdown("# Fanvue Post Creator")
    gr.Markdown("Upload media i tworzenie postow na Fanvue z AI-generowanymi opisami.")

    with gr.Tab("Ustawienia"):
        gr.Markdown("## Autoryzacja Fanvue")
        gr.Markdown("""
        Aby uzyskac token:
        1. Zaloguj sie na [fanvue.com](https://fanvue.com)
        2. Otworz DevTools (F12) -> Application -> Cookies
        3. Skopiuj wartosc `access_token`

        Lub uzyj OAuth2 flow przez developer portal Fanvue.
        """)

        with gr.Row():
            access_token_input = gr.Textbox(
                label="Access Token",
                type="password",
                placeholder="Wklej access token z Fanvue..."
            )
            refresh_token_input = gr.Textbox(
                label="Refresh Token (opcjonalnie)",
                type="password",
                placeholder="Opcjonalnie..."
            )

        auth_btn = gr.Button("Zaloguj", variant="primary")
        auth_status = gr.Textbox(label="Status", interactive=False,
                                  value="Zalogowany!" if state.is_authenticated() else "Niezalogowany")

        auth_btn.click(
            authenticate_with_token,
            inputs=[access_token_input, refresh_token_input],
            outputs=auth_status
        )

        gr.Markdown("---")
        gr.Markdown("## OpenAI API")

        openai_key_input = gr.Textbox(
            label="OpenAI API Key",
            type="password",
            placeholder="sk-...",
            value="" if not os.getenv("OPENAI_API_KEY") else "***ustawiony z .env***"
        )
        openai_btn = gr.Button("Ustaw klucz OpenAI")
        openai_status = gr.Textbox(label="Status OpenAI", interactive=False,
                                    value="Skonfigurowany" if state.openai_client else "Nie skonfigurowany")

        openai_btn.click(
            set_openai_key,
            inputs=openai_key_input,
            outputs=openai_status
        )

    with gr.Tab("Nowy Post"):
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### Media")
                file_input = gr.File(
                    label="Wybierz plik (obraz lub wideo)",
                    file_types=["image", "video"]
                )
                image_preview = gr.Image(label="Podglad", visible=True)

                gr.Markdown("### Generowanie opisu AI")
                style_dropdown = gr.Dropdown(
                    choices=["Sexy & Flirty", "Casual & Fun", "Mysterious", "Promotional", "Custom"],
                    value="Casual & Fun",
                    label="Styl opisu"
                )
                custom_prompt = gr.Textbox(
                    label="Custom prompt (dla stylu Custom)",
                    placeholder="Napisz wlasny prompt...",
                    visible=False
                )
                generate_btn = gr.Button("Generuj opis AI", variant="secondary")

            with gr.Column(scale=1):
                gr.Markdown("### Tresc posta")
                caption_input = gr.Textbox(
                    label="Opis / Caption",
                    lines=5,
                    placeholder="Wpisz lub wygeneruj opis..."
                )

                audience_dropdown = gr.Dropdown(
                    choices=["Wszyscy (publiczny)", "Obserwujacy i subskrybenci", "Tylko subskrybenci"],
                    value="Obserwujacy i subskrybenci",
                    label="Odbiorcy"
                )

                # scheduled_input = gr.Textbox(
                #     label="Zaplanuj (ISO date, opcjonalnie)",
                #     placeholder="2024-12-31T12:00:00Z"
                # )

                post_btn = gr.Button("Opublikuj Post", variant="primary", size="lg")
                result_output = gr.Textbox(label="Wynik", lines=5, interactive=False)

        # Show/hide custom prompt
        def toggle_custom(style):
            return gr.update(visible=(style == "Custom"))

        style_dropdown.change(toggle_custom, inputs=style_dropdown, outputs=custom_prompt)

        # Update preview when file selected
        def update_preview(file):
            if file and file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                return gr.update(value=file, visible=True)
            return gr.update(value=None, visible=False)

        file_input.change(update_preview, inputs=file_input, outputs=image_preview)

        # Generate caption
        def generate_caption_handler(file, style, custom):
            if not file:
                return "Najpierw wybierz plik!"

            ext = Path(file).suffix.lower()
            if ext in [".mp4", ".mov", ".avi", ".webm"]:
                return generate_video_caption(style, custom)
            else:
                return generate_caption(file, style, custom)

        generate_btn.click(
            generate_caption_handler,
            inputs=[file_input, style_dropdown, custom_prompt],
            outputs=caption_input
        )

        # Post button
        post_btn.click(
            full_upload_and_post,
            inputs=[file_input, caption_input, audience_dropdown],
            outputs=result_output
        )

    with gr.Tab("Historia"):
        gr.Markdown("### Ostatnie posty")
        gr.Markdown("_Funkcja w przygotowaniu..._")

        refresh_history_btn = gr.Button("Odswież")
        history_output = gr.JSON(label="Historia")

        def get_history():
            if not state.is_authenticated():
                return {"error": "Niezalogowany"}
            try:
                with httpx.Client() as client:
                    response = client.get(
                        f"{FANVUE_API_BASE}/creators/{state.creator_uuid}/posts",
                        headers=get_headers(),
                        params={"limit": 10}
                    )
                    if response.status_code == 200:
                        return response.json()
                    return {"error": f"Status {response.status_code}"}
            except Exception as e:
                return {"error": str(e)}

        refresh_history_btn.click(get_history, outputs=history_output)

    with gr.Tab("Pomysly na posty"):
        gr.Markdown("### Generator pomyslow na posty")
        gr.Markdown("AI wygeneruje plan tresci na wybrana liczbe dni, z uwzglednieniem sezonowosci i roznorodnosci.")

        with gr.Row():
            with gr.Column(scale=2):
                niche_input = gr.Textbox(
                    label="Opisz swoja nisze / styl",
                    placeholder="np. glamour, lingerie, fitness, cosplay...",
                    lines=2
                )
            with gr.Column(scale=1):
                days_slider = gr.Slider(
                    minimum=7, maximum=30, step=1, value=14,
                    label="Liczba dni"
                )

        with gr.Row():
            include_seasonal = gr.Checkbox(label="Tematy sezonowe", value=True)
            include_ppv = gr.Checkbox(label="Dolacz pomysly PPV", value=True)
            generate_ideas_btn = gr.Button("Generuj plan tresci", variant="primary")

        ideas_status = gr.Textbox(label="Status", interactive=False)
        ideas_json_state = gr.State("[]")

        ideas_table = gr.Dataframe(
            headers=["Dzien", "Typ", "Pomysl", "Caption", "Odbiorcy", "Godzina", "Hashtagi"],
            datatype=["number", "str", "str", "str", "str", "str", "str"],
            label="Plan tresci",
            interactive=False,
            wrap=True
        )

        with gr.Row():
            export_csv_btn = gr.Button("Eksportuj do CSV", variant="secondary")
            export_file = gr.File(label="Pobierz CSV", visible=False)

        gr.Markdown("---")
        gr.Markdown("### Uzyj pomyslu w nowym poscie")

        with gr.Row():
            idea_row_number = gr.Number(
                label="Numer wiersza (1, 2, 3...)",
                value=1, minimum=1, precision=0
            )
            use_idea_btn = gr.Button("Uzyj tego pomyslu w Nowym Poscie", variant="secondary")
            use_idea_status = gr.Textbox(label="", interactive=False)

        # Generate ideas handler
        generate_ideas_btn.click(
            generate_content_ideas,
            inputs=[niche_input, days_slider, include_seasonal, include_ppv],
            outputs=[ideas_table, ideas_json_state, ideas_status]
        )

        # Export CSV handler
        def handle_export_csv(ideas_json):
            filepath = export_ideas_csv(ideas_json)
            if filepath:
                return gr.update(value=filepath, visible=True)
            return gr.update(value=None, visible=False)

        export_csv_btn.click(
            handle_export_csv,
            inputs=[ideas_json_state],
            outputs=[export_file]
        )

        # Use idea handler - copies caption to new post tab
        def handle_use_idea(ideas_json, row_num):
            try:
                ideas = json.loads(ideas_json)
                idx = int(row_num) - 1
                if 0 <= idx < len(ideas):
                    caption = ideas[idx].get("caption_draft", "")
                    return caption, f"Caption z dnia {int(row_num)} skopiowany do zakladki Nowy Post!"
                return "", f"Nie ma wiersza nr {int(row_num)}. Dostepne: 1-{len(ideas)}"
            except Exception as e:
                return "", f"Blad: {str(e)}"

        use_idea_btn.click(
            handle_use_idea,
            inputs=[ideas_json_state, idea_row_number],
            outputs=[caption_input, use_idea_status]
        )


if __name__ == "__main__":
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
