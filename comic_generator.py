from __future__ import annotations

import base64
import os
import textwrap
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Optional

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None  # type: ignore
    ImageDraw = None  # type: ignore
    ImageFont = None  # type: ignore


class ComicGenerator:
    """ASCII and visual 4-panel comic generator.

    Supports fallback ASCII export and visual export via MCP xAI Image API.
    """

    def __init__(self, base_dir: Optional[Path] = None, use_visual: bool = False, mcp_url: str = "http://localhost:8080") -> None:
        self.panels: list[dict] = []
        self.episode_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.base_dir = base_dir or (Path(__file__).parent / "episodes")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.use_visual = use_visual
        self._xai = None
        if self.use_visual:
            try:
                # Load .env file if available (support both project root and tvshow/.env)
                try:
                    from dotenv import load_dotenv  # type: ignore
                    # Try tvshow/.env first, then project root .env
                    tvshow_env = Path(__file__).parent / ".env"
                    root_env = Path(__file__).parent.parent.parent / ".env"
                    if tvshow_env.exists():
                        load_dotenv(tvshow_env, override=True)
                        print(f"[DEBUG] Loaded .env from {tvshow_env}")
                    elif root_env.exists():
                        load_dotenv(root_env, override=True)
                        print(f"[DEBUG] Loaded .env from {root_env}")
                    else:
                        # Try to load from current working directory
                        load_dotenv(override=True)
                        print(f"[DEBUG] Loaded .env from current directory")
                except ImportError:
                    print("[DEBUG] python-dotenv not available, using system env only")
                
                from xai_sdk import AsyncClient  # type: ignore
                api_key = os.getenv("XAI_API_KEY")
                if not api_key:
                    raise RuntimeError("XAI_API_KEY not found in environment variables. Checked os.getenv('XAI_API_KEY')")
                print(f"[DEBUG] Found XAI_API_KEY (length: {len(api_key)})")
                
                # Try to initialize xAI async client (for async operations)
                self._xai = AsyncClient(api_key=api_key)
                print(f"[VISUAL ENABLED] xAI SDK AsyncClient initialized successfully")
            except ImportError as e:
                self._xai = None
                print(f"[VISUAL DISABLED] xai-sdk not installed: {e}")
                import traceback
                traceback.print_exc()
            except Exception as e:
                self._xai = None
                print(f"[VISUAL DISABLED] Failed to initialize xAI: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
        self.character_prompts = self._load_character_prompts()

    def add_panel(self, speaker: str, text: str, mood_emoji: str) -> None:
        speaker_label = speaker or "?"
        safe_text = (text or "").strip()
        # Optional emoji mapping for known moods
        MOOD_EMOJI = {
            "sigh": "😔",
            "panic": "😱",
            "confident": "💪",
            "excited": "✨",
            "smirk": "😏",
            "default": "😐",
        }
        emoji_key = (mood_emoji or "").strip()
        emoji = MOOD_EMOJI.get(emoji_key, emoji_key or MOOD_EMOJI["default"])
        self.panels.append({
            "speaker": speaker_label,
            "text": safe_text,
            "mood": emoji_key or "default",
            "emoji": emoji,
        })

    async def export(self, title: str = "AI House Episode") -> Path:
        if self.use_visual and self._xai is not None and len(self.panels) >= 4:
            try:
                return await self._export_visual(title)
            except Exception as exc:
                print(f"[VISUAL FAILED] {exc} → Falling back to ASCII")
                return self._export_ascii(title)
        if self.use_visual and self._xai is None:
            print("[VISUAL SKIPPED] xAI client not available → Falling back to ASCII")
        return self._export_ascii(title)

    def _export_ascii(self, title: str) -> Path:
        header_bar = "═" * 50
        comic = (
            f"╔{header_bar}╗\n"
            f"║  {title}  ║\n"
            f"╚{header_bar}╝\n"
        )

        for index, panel in enumerate(self.panels[:4], start=1):
            ascii_panel = (
                "   ┌──────┐\n"
                f"   │  {panel['emoji']}  │ {panel['speaker']}: \"{panel['text']}\"\n"
                "   └──────┘"
            )
            comic += f"\n[COMIC PANEL {index}]\n{ascii_panel}\n"

        path = self.base_dir / f"episode_{self.episode_id}_comic.txt"
        with path.open("w", encoding="utf-8") as f:
            f.write(comic)

        print(f"[COMIC SAVED] {path}")
        return path

    async def _export_visual(self, title: str) -> Path:
        prompt = self._build_visual_prompt(title)
        # Use xAI SDK to generate an image; SDK returns ImageResponse with URL
        try:
            print(f"[DEBUG] Generating image with prompt length: {len(prompt)}")
            resp = await self._xai.image.sample(  # type: ignore - async method
                prompt=prompt,
                model="grok-2-image-1212",
                image_format="url",
            )
            img_url = resp.url  # type: ignore
            print(f"[DEBUG] Image generated, URL: {img_url[:50]}...")
        except Exception as api_error:
            error_msg = str(api_error)
            print(f"[DEBUG] xAI API error details: {type(api_error).__name__}: {error_msg}")
            # Check if it's a 403 or authentication issue
            if "403" in error_msg or "Forbidden" in error_msg:
                print("[DEBUG] 403 Forbidden - Check if your API key has image generation access")
                print("[DEBUG] Verify your XAI_API_KEY has image generation permissions in xAI console")
            raise
        
        # Download the image bytes
        import urllib.request as _url
        try:
            req = _url.Request(img_url)
            req.add_header('User-Agent', 'Mozilla/5.0')  # Some APIs require user agent
            with _url.urlopen(req, timeout=30) as response:
                data = response.read()
        except Exception as download_error:
            error_str = str(download_error)
            print(f"[DEBUG] Failed to download image from URL: {error_str}")
            # If 403 on download, it might be the image URL itself that's protected
            if "403" in error_str or "Forbidden" in error_str:
                print("[DEBUG] Image URL returned 403 - URL may be expired or require authentication")
            raise

        # Open image with PIL for text overlay
        if PIL_AVAILABLE:
            try:
                img = Image.open(BytesIO(data))
                # Overlay speech bubbles with actual text
                img_with_text = self._add_speech_bubbles(img, self.panels[:4])
                # Convert back to bytes for saving
                output = BytesIO()
                img_with_text.save(output, format="PNG")
                data = output.getvalue()
                print("[DEBUG] Text overlay applied to speech bubbles")
            except Exception as overlay_error:
                print(f"[DEBUG] Text overlay failed: {overlay_error}, saving original image")
        else:
            print("[DEBUG] Pillow not available, saving image without text overlay")

        visual_dir = self.base_dir / "visual"
        visual_dir.mkdir(parents=True, exist_ok=True)
        png_path = visual_dir / f"episode_{self.episode_id}_comic.png"
        html_path = visual_dir / f"episode_{self.episode_id}_comic.html"
        with open(png_path, "wb") as f:
            f.write(data)
        self._generate_html_viewer(png_path, html_path, title)
        print(f"[VISUAL COMIC + TEXT] {png_path}")
        return png_path

    def _build_visual_prompt(self, title: str) -> str:
        """Build prompt requesting blank speech bubbles for text overlay.
        
        Note: xAI has a 1024 character limit, so this prompt is optimized for brevity.
        """
        # Shorten character descriptions to essential details
        short_char_map = {
            "Max": "tall male, brown hair, red hoodie",
            "Leo": "male, long black hair, paint-stained shirt",
            "Emma": "female, glasses, blonde ponytail, blue sweater",
            "Marvin": "tall gray robot, sad green LED eyes, 'Don't Panic' towel",
            "Narrator": "narrator figure or scene focus",
        }
        
        panels_desc: list[str] = []
        for i, p in enumerate(self.panels[:4]):
            char_short = short_char_map.get(p["speaker"], p["speaker"])
            mood_short = p['mood'] if p['mood'] != 'default' else "neutral"
            # Very concise panel description - NO labels that could appear in bubbles
            panels_desc.append(f"{char_short}, {mood_short} face, empty white oval bubble above head")
        
        # Build compact prompt (must be < 1024 chars)
        # CRITICAL: No text in bubbles - emphasize EMPTY bubbles multiple times
        prompt = (
            f"4-panel Pixar comic strip. Title: '{title}'. "
            f"Consistent characters across panels. Setting: student dorm room. "
            f"**CRITICAL: ALL speech bubbles are COMPLETELY EMPTY white ovals with ZERO text or letters inside them**. "
            f"Panel descriptions: {'. '.join(panels_desc)}. "
            f"High detail, vibrant colors, expressive faces. Bubbles must be blank white ovals."
        )
        
        # Enforce 1024 char limit (leave 20 char margin for safety)
        max_length = 1004
        if len(prompt) > max_length:
            # Truncate even more aggressively - keep EMPTY bubble emphasis
            base = "4-panel Pixar comic. Consistent characters. Setting: dorm. **ALL bubbles COMPLETELY EMPTY, ZERO text or letters**. "
            remaining = max_length - len(base) - 20
            max_per_panel = remaining // 4
            panels_desc_short = [p[:max_per_panel] for p in panels_desc]
            prompt = f"{base}{'. '.join(panels_desc_short)}. High detail. Bubbles blank."
        
        # Validate final length
        if len(prompt) > 1024:
            print(f"[WARNING] Prompt still too long ({len(prompt)} chars), truncating...")
            prompt = prompt[:1024]
        
        print(f"[DEBUG] Prompt length: {len(prompt)} chars (max: 1024)")
        return prompt

    def _add_speech_bubbles(self, img, panels: list[dict]):
        """Overlay readable text in speech bubbles using PIL.
        
        Args:
            img: PIL Image object
            panels: List of panel dicts with 'speaker', 'text', 'mood' keys
            
        Returns:
            PIL Image with text overlaid
        """
        if not PIL_AVAILABLE:
            return img
        
        draw = ImageDraw.Draw(img)
        width, height = img.size
        
        # Try to load a nice font, fallback to default
        try:
            # Try system fonts (macOS/Linux/Windows)
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
            except:
                try:
                    font = ImageFont.load_default()
                except:
                    font = None
        
        # Calculate panel dimensions (2x2 grid)
        panel_w = width // 2
        panel_h = height // 2
        
        # Bubble positions for each panel (relative to panel center)
        # Adjust these based on where bubbles appear in generated image
        bubble_positions = [
            (panel_w * 0.15, panel_h * 0.15),   # Top-left panel
            (panel_w * 1.15, panel_h * 0.15),  # Top-right panel
            (panel_w * 0.15, panel_h * 1.15),  # Bottom-left panel
            (panel_w * 1.15, panel_h * 1.15),  # Bottom-right panel
        ]
        
        for i, panel in enumerate(panels):
            if i >= len(bubble_positions):
                break
                
            x, y = bubble_positions[i]
            text = panel.get("text", "").strip()
            speaker = panel.get("speaker", "?")
            
            if not text:
                continue
            
            # Wrap text to fit bubble (max 25 chars per line for readability)
            wrapped_lines = textwrap.wrap(text, width=25)
            num_lines = len(wrapped_lines)
            
            # Calculate bubble size
            line_height = 35
            padding = 20
            bubble_height = (num_lines * line_height) + (padding * 2)
            bubble_width = 320
            
            # Draw rounded rectangle for bubble
            bubble_box = [
                x, y,
                x + bubble_width,
                y + bubble_height
            ]
            
            # White bubble with black outline
            draw.rounded_rectangle(
                bubble_box,
                radius=25,
                fill="white",
                outline="black",
                width=3
            )
            
            # Draw bubble tail (pointing to character)
            tail_points = [
                (x + 60, y + bubble_height),      # Start
                (x + 80, y + bubble_height + 25), # Point
                (x + 100, y + bubble_height)      # End
            ]
            draw.polygon(tail_points, fill="white", outline="black", width=2)
            
            # Draw text lines
            text_y = y + padding
            for line in wrapped_lines:
                # Center text horizontally in bubble
                if font:
                    # Get text bbox for centering
                    bbox = draw.textbbox((0, 0), line, font=font)
                    text_w = bbox[2] - bbox[0]
                    text_x = x + (bubble_width - text_w) // 2
                    draw.text((text_x, text_y), line, fill="black", font=font)
                else:
                    draw.text((x + padding, text_y), line, fill="black")
                text_y += line_height
        
        return img

    def _generate_html_viewer(self, png_path: Path, html_path: Path, title: str) -> None:
        html = (
            "<!DOCTYPE html>\n"
            f"<html><head><title>{title}</title></head>\n"
            "<body style=\"text-align:center;background:#f0f0f0;\">\n"
            f"<h1>{title}</h1>\n"
            f"<img src=\"{png_path.name}\" style=\"max-width:100%;border:2px solid #333;\">\n"
            f"<p>Generated by AI House • {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>\n"
            "</body></html>\n"
        )
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)

    def _load_character_prompts(self) -> dict[str, str]:
        return {
            "Max": "tall male with short brown hair, blue eyes, confident smile, red hoodie, Pixar 3D style",
            "Leo": "creative male with long black hair, paint-stained shirt, artistic pose, Pixar 3D style",
            "Emma": "female with glasses, blonde ponytail, anxious expression, blue sweater, Pixar 3D style",
            "Marvin": "Marvin the Paranoid Android: tall gray robot, oversized head, sad green LED eyes, hunched posture, carrying tiny 'Don't Panic' towel, Pixar 3D style",
        }


