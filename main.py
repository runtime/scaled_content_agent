# scaled_content_agent/main.py

from pathlib import Path

from .subagents.brief_ingestion_agent import BriefIngestionAgent
from .subagents.copy_agent import CopywritingAgent
from .subagents.image_agent import ImageGenerationAgent


class Orchestrator:
    """
    v1 Orchestrator
    ----------------
    Responsibilities:
      1. Load the brief
      2. Build campaign + product config
      3. Create product output folders
      4. Generate copy.json per product
      5. Generate hero images + composite local assets
      6. Print a summary

    No fancy logic, no complex state — just a clean pipeline.
    """

    def __init__(self, project_root=None):
        # project_root should resolve to scaled_content_agent/
        if project_root is None:
            self.project_root = Path(__file__).resolve().parent
        else:
            self.project_root = Path(project_root)

        # Instantiate core agents
        self.brief_agent = BriefIngestionAgent(project_root=self.project_root)
        self.copy_agent = CopywritingAgent()
        self.image_agent = ImageGenerationAgent()

    def run_ingestion_and_prepare_outputs(self, brief_path, output_root, seed=None):
        """
        Main entrypoint called by the CLI.
        """

        brief_path = Path(brief_path)
        output_root = Path(output_root)

        # Resolve relative paths to scaled_content_agent/
        if not brief_path.is_absolute():
            brief_path = self.project_root / brief_path

        if not output_root.is_absolute():
            output_root = self.project_root / output_root

        # 1. Ingest brief → CampaignConfig + ProductConfigs
        campaign_cfg = self.brief_agent.ingest(brief_path)

        # 2. Create per-product output folders
        for product in campaign_cfg.products:
            product_dir = output_root / product.slug
            product_dir.mkdir(parents=True, exist_ok=True)

        # 3. Generate copy.json per product
        self.copy_agent.generate_copy_for_products(
            campaign_cfg=campaign_cfg,
            output_root=output_root,
        )

        # 4. Generate hero images + composite assets
        self.image_agent.generate_images_for_products(
            campaign_cfg=campaign_cfg,
            output_root=output_root,
            seed=seed,
        )

        # 5. Summary
        self._print_summary(campaign_cfg, output_root)

        return campaign_cfg

    def _print_summary(self, cfg, output_root):
        print("\n=== RapidClean POC – Brief + Copy + Images Complete ===\n")
        print(f"Project root: {self.project_root}")
        print(f"Output root:  {output_root}")
        print()

        print(f"Campaign:     {cfg.name}")
        print(f"Objective:    {cfg.objective}")
        print(f"KPI (primary):   {cfg.kpi_primary}")
        print(f"KPI (secondary): {cfg.kpi_secondary}")
        print()

        print(f"Region:       {cfg.target_region}")
        print(f"Audience:     {cfg.target_audience_label}")
        print(f"  → {cfg.target_audience_desc}")
        print()

        print("Brand:")
        print(f"  Name:       {cfg.brand_name}")
        print(f"  Logo path:  {cfg.brand_logo_path}")
        print(f"  Colors:     {cfg.primary_color}, {cfg.secondary_color}")
        print()

        print("Products:")
        for p in cfg.products:
            print(f"  - {p.name} ({p.id})")
            print(f"    slug:         {p.slug}")
            print(f"    assets:       {p.asset_folder}")

            product_dir = output_root / p.slug
            print(f"    copy:         {product_dir / 'copy.json'}")
            print("    renders:")
            print(f"      - {product_dir / '1x1_awareness.png'}")
            print(f"      - {product_dir / '9x16_awareness.png'}")
            print(f"      - {product_dir / '16x9_awareness.png'}")
        print(f"  Legal disclaimer: {cfg.legal_disclaimer}")

        print("\nStatus: ✅ All outputs generated successfully.\n")
