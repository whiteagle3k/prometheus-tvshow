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
                img = Image.open(BytesIO(data)).convert("RGB")  # Ensure RGB mode
                print(f"[DEBUG] Image opened: {img.size[0]}x{img.size[1]}, mode: {img.mode}")
                # Overlay speech bubbles with actual text
                img_with_text = self._overlay_dialogue(img, self.panels[:4])
                # Convert back to bytes for saving
                output = BytesIO()
                img_with_text.save(output, format="PNG")
                data = output.getvalue()
                print("[DEBUG] Text overlay applied successfully")
            except Exception as overlay_error:
                print(f"[DEBUG] Text overlay failed: {overlay_error}")
                import traceback
                traceback.print_exc()
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
        """Build action-based prompt with full-body characters and small corner bubbles.
        
        Note: xAI has a 1024 character limit, so this prompt is optimized for brevity while being explicit.
        """
        # Enhanced character descriptions with full-body and actions
        char_descs = {
            "Emma": "Emma: anxious young woman with glasses, blonde ponytail, blue sweater, full-body",
            "Max": "Max: confident tall young man, short brown hair, red hoodie, full-body",
            "Marvin": "Marvin the Paranoid Android: tall gray robot, oversized head, sad green LED eyes, hunched, holding tiny 'Don't Panic' towel, full-body",
            "Leo": "Leo: excited young man, long black hair, paint-stained shirt, full-body",
            "Narrator": "narrator figure",
        }
        
        # Get first 4 panels and extract speakers
        panels_data = self.panels[:4]
        speakers = [p.get("speaker", "?") for p in panels_data]
        
        # Build panel descriptions with actions and small corner bubbles
        panel_descs = []
        for i, (speaker, panel) in enumerate(zip(speakers, panels_data), 1):
            char_desc = char_descs.get(speaker, speaker)
            # Get action based on speaker and text
            action = self._get_action(speaker, panel.get("text", ""))
            
            panel_descs.append(
                f"Panel {i}: {char_desc}, {action}, **small empty white speech bubble in TOP-RIGHT CORNER**, dorm room background"
            )
        
        # Hyper-explicit prompt with full-body and dynamic poses
        prompt = (
            f"**STRICT 2x2 GRID**, 4 panels, Pixar 3D style. "
            f"**FULL-BODY CHARACTERS, DYNAMIC POSES, NO ZOOM-IN**. "
            f"**SMALL EMPTY WHITE SPEECH BUBBLE IN TOP-RIGHT CORNER OF EACH PANEL**. "
            f"**ONE CHARACTER PER PANEL**. "
            f"Panel 1 (top-left): {panel_descs[0]}. "
            f"Panel 2 (top-right): {panel_descs[1]}. "
            f"Panel 3 (bottom-left): {panel_descs[2]}. "
            f"Panel 4 (bottom-right): {panel_descs[3]}. "
            f"Consistent dorm: bunk beds, desk, warm light. High detail."
        )
        
        # Enforce 1024 char limit with ultra-compact fallback
        if len(prompt) > 1024:
            # Ultra-compact: just character names and actions
            char_names = [char_descs.get(s, s).split(":")[0] if ":" in char_descs.get(s, s) else s for s in speakers]
            actions = [self._get_action(s, panels_data[i].get("text", "")) for i, s in enumerate(speakers)]
            prompt = (
                f"STRICT 2x2 grid, 4 panels, Pixar style. Full-body, small corner bubbles. "
                f"P1 (top-left): {char_names[0]}, {actions[0]}. "
                f"P2 (top-right): {char_names[1]}, {actions[1]}. "
                f"P3 (bottom-left): {char_names[2]}, {actions[2]}. "
                f"P4 (bottom-right): {char_names[3]}, {actions[3]}. "
                f"Dorm room."
            )
            if len(prompt) > 1024:
                prompt = prompt[:1024]
        
        print(f"[DEBUG] Prompt length: {len(prompt)} chars (max: 1024)")
        return prompt
    
    def _get_action(self, speaker: str, text: str) -> str:
        """Get action verb based on speaker and text content."""
        text_lower = text.lower()
        
        if speaker == "Emma" and ("crash" in text_lower or "fail" in text_lower):
            return "hands on head in panic"
        if speaker == "Max" and ("fix" in text_lower or "together" in text_lower):
            return "pointing forward confidently"
        if speaker == "Marvin":
            return "sitting slouched, looking down"
        if speaker == "Leo" and ("inspired" in text_lower or "draw" in text_lower):
            return "holding up sketchbook excitedly"
        
        return "standing naturally"

    def _overlay_dialogue(self, img, panels: list[dict]):
        """Overlay readable text in speech bubbles using hardcoded bubble zones.
        
        Args:
            img: PIL Image object (RGB mode)
            panels: List of panel dicts with 'speaker', 'text', 'mood' keys
            
        Returns:
            PIL Image with text overlaid
        """
        if not PIL_AVAILABLE:
            return img
        
        draw = ImageDraw.Draw(img)
        width, height = img.size
        
        print(f"[DEBUG] Overlaying dialogue on {len(panels)} panels in {width}x{height} image")
        
        # Try to load font (smaller for corner bubbles)
        try:
            # macOS
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
        except:
            try:
                # Linux
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
            except:
                try:
                    font = ImageFont.load_default()
                except:
                    font = None
        
        # Calculate panel dimensions (2x2 grid)
        panel_w = width // 2
        panel_h = height // 2
        
        # Small corner bubble zones: (x, y, width, height) for each panel
        # Positioned in TOP-RIGHT corner to avoid covering faces
        bubble_zones = [
            (int(panel_w * 0.55), int(panel_h * 0.05), int(panel_w * 0.4), int(panel_h * 0.25)),   # P1: top-left panel, top-right bubble
            (int(panel_w * 1.55), int(panel_h * 0.05), int(panel_w * 0.4), int(panel_h * 0.25)),   # P2: top-right panel, top-right bubble
            (int(panel_w * 0.55), int(panel_h * 1.05), int(panel_w * 0.4), int(panel_h * 0.25)),   # P3: bottom-left panel, top-right bubble
            (int(panel_w * 1.55), int(panel_h * 1.05), int(panel_w * 0.4), int(panel_h * 0.25)),   # P4: bottom-right panel, top-right bubble
        ]
        
        for i, panel in enumerate(panels):
            if i >= len(bubble_zones):
                break
            
            x, y, bw, bh = bubble_zones[i]
            text = panel.get("text", "").strip()
            speaker = panel.get("speaker", "?")
            
            if not text:
                continue
            
            print(f"[DEBUG] Panel {i+1} ({speaker}): '{text}'")
            
            # Wrap text (max 16 chars per line for smaller corner bubbles)
            lines = textwrap.wrap(text, width=16)
            lines = lines[:3]  # Max 3 lines per small bubble
            
            # Draw small rounded rectangle bubble in corner
            bubble_box = [x, y, x + bw, y + bh]
            draw.rounded_rectangle(
                bubble_box,
                radius=20,
                fill="white",
                outline="black",
                width=3
            )
            
            # Draw bubble tail (pointing from top-right corner down-left toward character)
            tail_x = x + bw - 30
            tail_points = [
                (tail_x, y + bh),
                (tail_x - 20, y + bh + 25),
                (tail_x + 10, y + bh)
            ]
            draw.polygon(tail_points, fill="white", outline="black", width=2)
            
            # Draw text lines (top-aligned in small bubble)
            line_h = 35
            start_y = y + 15
            
            # Add padding for text
            text_padding = 15
            
            for j, line in enumerate(lines):
                text_y = start_y + (j * line_h)
                
                if font:
                    # Left-aligned text in small corner bubble
                    draw.text((x + text_padding, text_y), line, fill="black", font=font)
                else:
                    # Left-aligned fallback with padding
                    draw.text((x + text_padding, text_y), line, fill="black")
            
            print(f"[DEBUG] Panel {i+1} complete: {len(lines)} lines at ({x}, {y})")
        
        print(f"[DEBUG] All dialogue overlays completed")
        return img
    
    # Keep old method name for backwards compatibility
    def _add_speech_bubbles(self, img, panels: list[dict]):
        """Alias for _overlay_dialogue for backwards compatibility."""
        return self._overlay_dialogue(img, panels)
    
    def _detect_bubble_positions(self, img, panel_w: int, panel_h: int):
        """Detect existing bubble positions by finding white regions in image.
        
        Returns list of (x, y) positions, or None if detection fails.
        """
        if not PIL_AVAILABLE:
            return None
        
        try:
            import numpy as np
            np_available = True
        except ImportError:
            np_available = False
        
        if not np_available:
            return None
        
        width, height = img.size
        
        # Convert to numpy array for processing
        img_array = np.array(img)
        
        # Define search regions for each panel (upper portion where bubbles typically are)
        search_regions = [
            (0, 0, panel_w, int(panel_h * 0.4)),           # Top-left
            (panel_w, 0, width, int(panel_h * 0.4)),      # Top-right
            (0, panel_h, panel_w, height),                # Bottom-left
            (panel_w, panel_h, width, height),           # Bottom-right
        ]
        
        positions = []
        for x0, y0, x1, y1 in search_regions:
            # Ensure valid coordinates
            x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
            if x1 > width:
                x1 = width
            if y1 > height:
                y1 = height
            if x0 >= x1 or y0 >= y1:
                continue
            
            # Extract region
            region = img_array[y0:y1, x0:x1]
            if region.size == 0:
                continue
            
            # Find white pixels (RGB > 240)
            if len(region.shape) == 3 and region.shape[2] >= 3:
                white_mask = (region[:, :, 0] > 240) & (region[:, :, 1] > 240) & (region[:, :, 2] > 240)
                
                if white_mask.sum() > 1000:  # Significant white area found
                    # Find center of white region
                    y_coords, x_coords = np.where(white_mask)
                    if len(x_coords) > 0:
                        center_x = int(x0 + x_coords.mean())
                        center_y = int(y0 + y_coords.mean())
                        positions.append((center_x, center_y))
        
        return positions if len(positions) >= 4 else None

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
            "Emma": "Emma: anxious young woman with glasses, blonde ponytail, blue sweater, full-body, Pixar 3D style",
            "Max": "Max: confident tall young man, short brown hair, red hoodie, full-body, Pixar 3D style",
            "Marvin": "Marvin the Paranoid Android: tall gray robot, oversized head, sad green LED eyes, hunched, holding tiny 'Don't Panic' towel, full-body, Pixar 3D style",
            "Leo": "Leo: excited young man, long black hair, paint-stained shirt, full-body, Pixar 3D style",
        }


