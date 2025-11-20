# scaled_content_agent/subagents/brief_ingestion_agent.py

from pathlib import Path
import json

# create config object schemas
class ProductConfig:
    def __init__(self, id, slug, name, description, asset_folder, benefits):
        self.id = id
        self.slug = slug
        self.name = name
        self.description = description
        self.asset_folder = asset_folder
        self.benefits = benefits


class CampaignConfig:
    def __init__(
        self,
        name,
        objective,
        kpi_primary,
        kpi_secondary,
        target_region,
        target_audience_label,
        target_audience_desc,
        campaign_message,
        brand_name,
        brand_logo_path,
        primary_color,
        secondary_color,
        products,
        legal_disclaimer="",
    ):
        self.name = name
        self.objective = objective
        self.kpi_primary = kpi_primary
        self.kpi_secondary = kpi_secondary
        self.target_region = target_region
        self.target_audience_label = target_audience_label
        self.target_audience_desc = target_audience_desc
        self.campaign_message = campaign_message
        self.brand_name = brand_name
        self.brand_logo_path = brand_logo_path
        self.primary_color = primary_color
        self.secondary_color = secondary_color
        self.products = products
        self.legal_disclaimer = legal_disclaimer


# create agent to ingest brief and create configs using schema

class BriefIngestionAgent:
    """
    Read the brief JSON and turn it into simple Python objects
    (CampaignConfig + ProductConfig list).
    access with cfg. syntax in the main.py
    """

    def __init__(self, project_root):
        # project_root will be scaled_content_agent/
        self.project_root = Path(project_root)

    def _load_json(self, path):
        with Path(path).open("r", encoding="utf-8") as f:
            return json.load(f)

    def _slug_from_product_id(self, product_id):
        # "purepath-floor-wash" -> "purepath"
        return product_id.split("-")[0]

    def ingest(self, brief_path):
        data = self._load_json(brief_path)

        campaign = data["campaign"]
        brand = data["brand"]
        products_raw = data["products"]

        products = []
        for p in products_raw:
            product_id = p["id"]
            slug = self._slug_from_product_id(product_id)
            asset_folder = self.project_root / p["assetFolder"]

            product = ProductConfig(
                id=product_id,
                slug=slug,
                name=p["name"],
                description=p.get("description", ""),
                asset_folder=asset_folder,
                benefits=p.get("benefits", []),
            )
            products.append(product)

        target_audience = campaign["targetAudience"]
        brand_logo_path = self.project_root / brand["logoPath"]
        #legal_disclaimer = campaign["legalDisclaimer"]
        legal_disclaimer = campaign.get("legalDisclaimer", "")

        # set object using keys
        # todo implement pyndantic for schema layer for missing key errors
        config = CampaignConfig(
            name=campaign["name"],
            objective=campaign.get("objective", ""),
            kpi_primary=campaign["kpi"]["primary"],
            kpi_secondary=campaign["kpi"]["secondary_conversion"],
            target_region=campaign["targetRegion"],
            target_audience_label=target_audience["label"],
            target_audience_desc=target_audience["description"],
            campaign_message=campaign["campaignMessage"],
            brand_name=brand["name"],
            brand_logo_path=brand_logo_path,
            primary_color=brand["primaryColor"],
            secondary_color=brand["secondaryColor"],
            products=products,
            legal_disclaimer=legal_disclaimer,
        )
        # return a data object to be accessed via [.] dot syntax ie cfg.legal_disclaimer easier to read and use
        return config
