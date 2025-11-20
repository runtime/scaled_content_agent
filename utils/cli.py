# scaled_content_agent/utils/cli.py
# python lib to create custom cli args
import argparse
from pathlib import Path
# root agent import
from ..main import Orchestrator


def parse_args():
    # usse an instance of the argument parser
    parser = argparse.ArgumentParser(
        description="RapidClean POC – scaled content generator"
    )
    # add arguments (flags)
    # one for the brief ingestion
    parser.add_argument(
        "--brief",
        type=str,
        default="inputs/briefs/awareness_rapidclean_westcoast.json",
        help="Path to the brief JSON (relative to scaled_content_agent/).",
    )
    # one for the output root
    parser.add_argument(
        "--output-root",
        type=str,
        default="outputs/awareness_campaign/v1",
        help="Root output directory for generated render files.",
    )
    # one for seeds so we can edit creative later without the agents re-doing every part of it.
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
    # create an instance of the root_agent
    orchestrator = Orchestrator(project_root=project_root)
    # run the initial method from the model, pass in the path of the brief and the output folder, seed is optional
    orchestrator.run_ingestion_and_prepare_outputs(
        brief_path=args.brief,
        output_root=args.output_root,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
