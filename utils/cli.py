# scaled_content_agent/utils/cli.py

import argparse
from pathlib import Path

from ..main import Orchestrator


def parse_args():
    parser = argparse.ArgumentParser(
        description="RapidClean POC – scaled content generator"
    )

    parser.add_argument(
        "--brief",
        type=str,
        default="inputs/briefs/awareness_rapidclean_westcoast.json",
        help="Path to the brief JSON (relative to scaled_content_agent/).",
    )

    parser.add_argument(
        "--output-root",
        type=str,
        default="outputs/awareness_campaign/v1",
        help="Root output directory for generated render files.",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional Imagen seed for deterministic results.",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    # project root = scaled_content_agent/
    project_root = Path(__file__).resolve().parents[1]

    orchestrator = Orchestrator(project_root=project_root)

    orchestrator.run_ingestion_and_prepare_outputs(
        brief_path=args.brief,
        output_root=args.output_root,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
