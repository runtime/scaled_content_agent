# scaled_content_agent/subagents/copy_agent.py

import os
import json
from pathlib import Path
# this is an agent and it uses genai. env needs to be set accordingly
from google import genai


class CopywritingAgent:
    # docstring is for AI to clarify purpose, output format and what the downstream agents depend on
    """
    v1 GenAI Copy Agent
    -------------------
    - Uses Gemini to generate:
        • headline
        • body
        • disclaimer
    - Writes copy.json per product:
        {
          "campaignName": ...,
          "objective": ...,
          "targetRegion": ...,
          "targetAudience": ...,
          "productId": ...,
          "productName": ...,
          "headline": ...,
          "body": ...,
          "disclaimer": ...
        }
    """

    def __init__(self):
        # agent needs to own execution context so env vars need to be passed during CONSTRUCTION
        # agent can be configured once and reused against many calls.
        location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "adk-llm-agent")

        # create agent via genai.Client, pass in project id and location
        # agent needs your project id (with billing account) and location (default is global so use regional)
        self.client = genai.Client(
            vertexai=True,
            project=project_id,
            location=location,
        )

    # public function called by ingestion agent
    # use the config to pass to genai as dynamic prompt
    # call the LLM for the copy
    # parse it
    # write it to the json file
    def generate_copy_for_products(self, campaign_cfg, output_root):
        output_root = Path(output_root)

        for product in campaign_cfg.products:
            product_dir = output_root / product.slug
            product_dir.mkdir(parents=True, exist_ok=True)

            # receive a tuple of headline body and legal
            headline, body, disclaimer = self._gen_copy_for_product(
                campaign_cfg, product
            )

            copy_payload = {
                "campaignName": campaign_cfg.name,
                "objective": campaign_cfg.objective,
                "targetRegion": campaign_cfg.target_region,
                "targetAudience": campaign_cfg.target_audience_label,
                "productId": product.id,
                "productName": product.name,
                "headline": headline,
                "body": body,
                "disclaimer": disclaimer,
            }
            # save the copy to the local store
            # indent 2 = human readable
            # ascii = false ensures accents and emojis (localization things)
            copy_path = product_dir / "copy.json"
            try:
                with copy_path.open("w", encoding="utf-8") as f:
                    json.dump(copy_payload, f, indent=2, ensure_ascii=False)
                print(f"✅ Wrote copy.json for {product.name} → {copy_path}")
            except OSError as e:
                print(f"⚠️  Failed to write copy file for {product.name}: {e}")

    # private method called by self returns a tuple
    def _gen_copy_for_product(self, campaign_cfg, product):
        """
        Ask Gemini for structured ad copy.
        If anything fails, fall back to simple templates.
        """
        # Default fallback strings (never leave blank)
        fallback_headline = f"Clear your space with {product.name}"
        fallback_body = (
            f"{product.description or 'Eco-friendly cleaning made simple.'} "
            f"RapidClean™ helps you keep a calm, clutter-free home in {campaign_cfg.target_region}."
        )
        fallback_disclaimer = (
            campaign_cfg.legal_disclaimer if getattr(campaign_cfg, "legal_disclaimer", "") else
            "Read label for use instructions. Keep out of reach of children and pets."
        )
         # some error handling on the benefits aka legal we want to inform people about
        try:
            benefits_text = ", ".join(product.benefits) if product.benefits else ""

            base_disclaimer = getattr(campaign_cfg, "legal_disclaimer", "")

            # prompt for the copy agent.  campaign loaded dynamically for agent to work with
            prompt = f"""
            You are an ad copywriter for an eco-friendly cleaning brand called RapidClean.
            
            Write short, social-friendly ad copy for a single static image ad.
            Return ONLY valid JSON with the following keys: "headline", "body", "disclaimer".
            
            Constraints:
            - Headline: max 70 characters, punchy and positive.
            - Body: 2–3 short sentences, Instagram-caption style, friendly and practical.
            - Disclaimer: 1–2 short sentences of legal or safety language. If a base disclaimer is provided,
              incorporate or adapt it, but keep it concise.
            
            Campaign:
            - Name: {campaign_cfg.name}
            - Objective: {campaign_cfg.objective}
            - KPI primary: {campaign_cfg.kpi_primary}
            - KPI secondary: {campaign_cfg.kpi_secondary}
            - Target region: {campaign_cfg.target_region}
            - Target audience: {campaign_cfg.target_audience_label} — {campaign_cfg.target_audience_desc}
            - Brand mission: {campaign_cfg.campaign_message}
            
            Product:
            - Name: {product.name}
            - Description: {product.description}
            - Benefits: {benefits_text}
            
            Base legal disclaimer (optional):
            "{base_disclaimer}"
            """

            # return the response
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )

            # strip the response of docstrings and stuff
            text = response.text.strip()

            # Strip ```json code fences if present from the LLM
            if text.startswith("```"):
                text = text.strip("`")
                # remove possible leading 'json' or 'JSON'
                if text.lower().startswith("json"):
                    text = text[4:].strip()

            # then feed the data json.loads
            data = json.loads(text)
            # use get for the headline, fallback (never blank) if none exists repeat for all three.
            headline = data.get("headline", fallback_headline)
            body = data.get("body", fallback_body)
            disclaimer = data.get("disclaimer", fallback_disclaimer)

            # helper tuple of headline, body and legal, if the genai failed, fall back to json obj data
            return headline.strip(), body.strip(), disclaimer.strip()

        except Exception as e:
            print(f"⚠️ Gemini copy generation failed for {product.name}, using fallback: {e}")
            return fallback_headline, fallback_body, fallback_disclaimer
