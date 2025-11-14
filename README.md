# 📘 Scaled Content Orchestration Agent

#### An agentic platform that accelerates campaign velocity enabling agencies to release more campaigns per month, drive localized engagement and maintain brand guidelines.

#### author:
- runtime@github.com
## Features:
### 🧠 Google's ADK agentic Development Kit
A valid and quick way to create a scalable POC for a custom orchestration that emulates an agency production pipeline.
The ADK orchestration pattern mirrors how an enterprise platform would coordinate brief → copy → hero → resizing.

### 📄 Brief in JSON Format
In a real workflow the brief might be uploaded as PDF/Docx.
In large P&D pipelines i have used Vertex AI or OCR libs which normalizes to JSON for predictable ingestion.
For this POC, the brief is already provided as structured JSON so the tool can consume it instantly.

### ✍️ Gemini to generate structured copy in JSON format
This allows the rest of the pipeline to treat copy as data: headline, body, and disclaimer are contained within. fallback for failures makes it llm safe :)
- headline
- body text
- legal disclaimer
- All generated in one structured pass. 

### 🖼️ Imagen 4 for image generation
Ability to create regional or targeted hero images by passing dynamic prompts (see region in config).
 - creates regionally specific hero 
 - incorporates the generated copy into the ad (shortcut and blessing :P)
 - region specific affects look at aesthetic
 - prompts are dynamic & constructed from brief data

### 🧩 Seeds for consistency
 - this version seeding gives us reproducible creatives per product and size via the optional flag `-- seed 42`
 - future roadmap, I’d generate a single master 1:1 creative with a fixed seed and then derive the other sizes from that master.


### 🖌️ Pillow to composite product, mascot, and logo
Bottle and logo come from stubbed DAM → no hallucinated product packaging
imagine that they are assets approved by client for product and mascot
ProTip: 🥷🏼 I used transparent png files for product, logo and mascot for compositing
Layout is consistent across sizes, to match brand requirements
`Pillow` handles:
- placement
- scaling
- alpha
- compositing

## ✨ POC Requirements Overview

### Lets assume we are handling a brief for an awareness campaign for two of clients' products.
#### Client
- RapidClean
  - an eco friendly cleaning product manufacturer
#### Products
- PurePath Floor Wash
- NaturaGlow Wood Polish
#### Campaign (workfront-program)
- Eco Awareness - drive traffic to local compliance etc...
#### Required outputs:
- reuse existing assets
- generate missing elements when there are none
- produce 3 sizes
- place consistent copy and legal
- local run cli script with organized outputs

This project implements the **required elements** of the project in local environment agentic pipeline.
Lets assume we are handling an awareness campaign for two products

### ✅ Brief ingestion + asset reuse
- Accepts a JSON brief with:
  - campaign name, KPIs, audience, region  
  - two RapidClean products  
  - campaign messaging & brand guidelines  
  - legal disclaimer  
- Uses reusable assets from `/inputs/assets/...`:
  - product bottle PNGs  
  - mascot PNG  
  - brand logo  
- If assets aren’t there → pipeline still works (Imagen fills the gap)

### ✅ Three aspect ratios
Generates 3 standard social sizes for each product:
- **1:1** (Instagram feed)  
- **9:16** (Stories/Reels/TikTok)  
- **16:9** (YouTube/FB widescreen)

### ✅ Consistent messaging across all sizes
- Headline, body, and legal are generated once via Vertex Gemini (LLM)
- Written to `copy.json`
- Same exact copy is passed to every image generation call → consistent across all formats

### ✅ Text overlay placed through Imagen
- The Imagen hero prompt includes:
  - headline  
  - body  
  - disclaimer  
- Pillow compositing ensures brand elements (bottle, mascot, logo) stay exactly where they belong

### ✅ Local run + organized outputs
```python
    outputs/
      awareness_campaign/
        v1/
          purepath/
          naturaglow/

```

### 👩🏽‍🎨 Wanna try it? ... Pregame Setup:
#### Important:
you will need to fork over a credit card to run this application.
- create a google cloud account
- create a project and enable the vertexai api and genai apis
- create some keys
- create an .env file in the orchestration-agent-poc/scaled_content_agent
- put the keys in there and you are in the right direction
- finally gcloud auth in terminal to log you in 
  - all not covered here for speed

```python
cd orchestration-agent-poc

source .venv/bin/activate
```
```python
pip install -r /scaled_content_agent/requirements.txt
```
Simple CLI:
  ```bash
    python -m scaled_content_agent.utils.cli
```

Simple optional flag for seeds:
  ```bash
    python -m scaled_content_agent.utils.cli --seed 42
```




## 📤 Pipeline (Step-by-step)
#### what happens under the hood...
- cli loads the `orchestrator agent` which is our task master 💅🏽
- orchestrator agent calls these agents/tools inline
  -  🔧 `brief ingestion agent` (tool):
    - loads the brief `campaign.json` acts as a big setter returns a python obj
      - builds a `CampaignConfig` (top-level campaign + brand info)
      - builds a `ProductConfig` for each product.
      - maps a python object -> `campaign_cfg.products[0].name` with properties i can easily deal with
  -  🤖 `copy_agent` (Vertex Gemini)
    - reads the config and generates the copy for the ad
      - writes output to `outputs/.../copy.json`
      - structured JSON becomes a data object for the image agent to add for consistency
  -  🤖 `image_agent` (Imagen 4 + Pillow)
    - leverages imagen `GenerateImagesConfig`
      - uses dynamic prompt from orchestration agent - takes location and regional copy
        - ```prompt = (
                  f"Bright, minimal, daylight {campaign_cfg.target_region} home interior. "
                  f"Eco-friendly aesthetic, clean, calm, modern. "
                  f"Soft shadows, open space near bottom for product placement. "
                  f"Aspect ratio {width}:{height}. "
                  f"Do NOT include any product bottles. "
                  f"Do include copy from copy.text file in input folder. "
                  f"This is a background hero image for an eco cleaning product ad."
              )
          ```
      - saves hero result and opens image in `Pillow`
      - composites the image
      - creates the sizes
      - uses legal and copy json generated by copy_agent to have consistent legal and copy

GLHF~!



