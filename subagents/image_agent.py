# scaled_content_agent/subagents/image_agent.py

import os
from pathlib import Path
import json

from tempfile import NamedTemporaryFile  # add this import at the top with others

from google import genai
from google.genai.types import GenerateImagesConfig

# use pillow to help us load existing assets and compose them
from PIL import Image, ImageOps

# Create image gen agent
class ImageGenerationAgent:
    """
    v1 Image Agent:
      - Generates a hero background using Imagen
      - Loads local product.png, mascot.png, and brand logo
      - Composites layers onto the background using Pillow
      - Saves 3 aspect ratios per product
    """

    def __init__(self):
        location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "adk-llm-agent")
        # create genai client
        self.client = genai.Client(
            vertexai=True,
            project=project_id,
            location=location,
        )

        self.aspect_ratios = {
            "1x1": (1024, 1024),
            "9x16": (900, 1600),
            "16x9": (1600, 900),
        }

    # generate images when there are none, load if they exist
    # also take the output folder and seed as params
    # generate the hero
    def generate_images_for_products(self, campaign_cfg, output_root, seed=None):
        output_root = Path(output_root)
        # loop thru products in config (2)
        for product in campaign_cfg.products:
            # create the folders if they dont exist on the parent directory
            product_dir = output_root / product.slug
            product_dir.mkdir(parents=True, exist_ok=True)

            copy_path = product_dir / "copy.json"
            if not copy_path.exists():
                print(f"⚠️ No copy.json found for {product.name}, skipping.")
                continue
            # iterate through the json f = item
            with copy_path.open("r", encoding="utf-8") as f:
                copy_data = json.load(f)

            # product + mascot image locations
            product_image_path = product.asset_folder / "product.png"
            mascot_image_path = product.asset_folder / "mascot.png"

            # brand logo
            logo_path = campaign_cfg.brand_logo_path

            # Load assets (skip missing, warn lightly)
            product_img = self._load_png(product_image_path, "product")
            mascot_img = self._load_png(mascot_image_path, "mascot")  # optional
            logo_img = self._load_png(logo_path, "logo")

            # Generate all ratios
            for ratio_label, (w, h) in self.aspect_ratios.items():
                print(f"\n▶ Generating background for {product.name} / {ratio_label}")
                # create the localized hero with copy image (shortcut)
                background = self._generate_background_image(
                    product=product,
                    campaign_cfg=campaign_cfg,
                    copy_data=copy_data,
                    width=w,
                    height=h,
                    seed=seed,
                )

                # Now composite layers
                final_img = self._composite_layers(
                    background=background,
                    product_img=product_img,
                    mascot_img=mascot_img,
                    logo_img=logo_img,
                )

                output_path = product_dir / f"{ratio_label}_awareness.png"
                final_img.save(output_path)
                print(f"✅ Saved {output_path}")

    def _load_png(self, path, label):
        """
        Loads a PNG if it exists; otherwise returns None.
        Keeps POC clean with graceful fallback.
        """
        try:
            path = Path(path)
            if path.exists():
                return Image.open(path).convert("RGBA")
            else:
                print(f"⚠️ {label} image not found at {path}, skipping.")
                return None
        except Exception as e:
            print(f"⚠️ Failed to load {label} image ({path}): {e}")
            return None

    def _generate_background_image(self, product, campaign_cfg, copy_data, width, height, seed):
        """
        Calls Imagen to generate a hero background that ALSO includes text:
          - headline
          - body
          - disclaimer (near mascot position)
        No product bottle or logo; those are composited later.
        """
        headline = copy_data.get("headline", "")
        body = copy_data.get("body", "")
        disclaimer = copy_data.get("disclaimer", "") or getattr(campaign_cfg, "legal_disclaimer", "")

        prompt = (
            f"Bright, minimal, daylight {campaign_cfg.target_region} home interior. "
            f"Eco-friendly aesthetic, clean, calm, modern. "
            f"Soft shadows, open space for copy and product placement. "
            f"Aspect ratio {width}:{height}. "
            f"Do NOT include any product bottles or brand logos. "
            f"This is a background hero image for an eco cleaning product ad. "
            f"Add this headline text EXACTLY as written near the top center of the ad: '{headline}'. "
            f"Add this supporting body text EXACTLY as written below the headline: '{body}'. "
        )

        if disclaimer:
            prompt += (
                f"Add this small legal disclaimer text EXACTLY as written near the bottom-left area, "
                f"where a mascot or character might sit: '{disclaimer}'. "
            )

        # Build config; only pass seed if not None
        if seed is not None:
            config = GenerateImagesConfig(
                aspect_ratio="1:1",
                image_size="1K",
                number_of_images=1,
                output_mime_type="image/png",
                seed=seed,
            )
        else:
            config = GenerateImagesConfig(
                aspect_ratio="1:1",
                image_size="1K",
                number_of_images=1,
                output_mime_type="image/png",
            )

        try:
            result = self.client.models.generate_images(
                model="imagen-4.0-generate-001",
                prompt=prompt,
                config=config,
            )

            if not result.generated_images:
                raise RuntimeError("Imagen returned no images")

            from tempfile import NamedTemporaryFile
            import os

            gimg = result.generated_images[0].image

            with NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp_path = tmp.name

            try:
                gimg.save(tmp_path)
                img = Image.open(tmp_path).convert("RGBA")
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

        except Exception as e:
            print(f"⚠️ Imagen failed, using plain white background: {e}")
            return Image.new("RGBA", (width, height), (255, 255, 255, 255))

        return img.resize((width, height), Image.LANCZOS)

    # todo create layouts for different campaigns / regions
    # for now this is a simple layout tool using Pillow keeping brand guidelines consistent
    def _composite_layers(self, background, product_img, mascot_img, logo_img):
        """
        Composite: logo → product (bottom-right) → mascot (bottom-left, optional)
        """
        canvas = background.copy()

        def scale(img, max_w, max_h):
            if img is None:
                return None
            img = ImageOps.contain(img, (max_w, max_h))
            return img

        W, H = canvas.size

        # Make product more prominent
        product_img = scale(product_img, W // 2, H // 2)
        mascot_img = scale(mascot_img, W // 5, H // 5)
        logo_img = scale(logo_img, W // 6, H // 6)

        # Logo: top-left with margin
        if logo_img:
            canvas.paste(logo_img, (40, 40), logo_img)

        # Product: bottom-right, more prominent
        if product_img:
            pw, ph = product_img.size
            px = (W - pw) // 2
            py = H - ph - 40
            canvas.paste(product_img, (px, py), product_img)

        # Mascot: bottom-left (optional). Disclaimer is already in background prompt near here.
        if mascot_img:
            mw, mh = mascot_img.size
            mx = 40
            my = H - mh - 40
            canvas.paste(mascot_img, (mx, my), mascot_img)

        return canvas


