#!/usr/bin/env python3
"""AI Property Video Generator - Command Line Interface.

Usage examples:
  python cli.py --input sample_data/sample_property.json
  python cli.py --input sample_data/sample_property.json --orientation 9:16 --language hi
  python cli.py --name "Skyline Towers" --location "Sector 62, Noida" --price "₹95 Lakh" --images img1.jpg img2.jpg
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.models import PropertyInput
from src.pipeline import generate_property_video

console = Console()


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AI Property Video Generator - Transform property details & photos into promotional MP4 videos."
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        help="Path to JSON file with property details (e.g., sample_data/sample_property.json)",
    )
    parser.add_argument("--name", type=str, help="Property title / project name")
    parser.add_argument("--location", type=str, help="Property location / city")
    parser.add_argument("--price", type=str, help="Listing price (e.g., ₹1.85 Cr)")
    parser.add_argument("--type", dest="property_type", type=str, help="Property type (e.g., 3 BHK Apartment, Villa)")
    parser.add_argument("--features", nargs="*", help="Key features / amenities list")
    parser.add_argument("--cta", type=str, help="Call to action or contact details")
    parser.add_argument("--images", nargs="*", help="Paths to property images (4-8 recommended)")
    parser.add_argument(
        "--orientation",
        choices=["16:9", "9:16"],
        default="16:9",
        help="Video aspect ratio: 16:9 (Landscape) or 9:16 (Vertical Reel/WhatsApp)",
    )
    parser.add_argument(
        "--language",
        choices=["en", "hi"],
        default="en",
        help="Narration language: 'en' for Indian English, 'hi' for Hindi",
    )
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="Force deterministic template script engine instead of Gemini LLM",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="Google Gemini API key (defaults to GEMINI_API_KEY env variable)",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Custom output filename or directory",
    )
    parser.add_argument(
        "--bgm",
        type=str,
        default="assets/bgm.mp3",
        help="Path to royalty-free background audio track",
    )
    parser.add_argument(
        "--bgm-volume",
        type=float,
        default=0.12,
        help="Background music volume multiplier (0.0 to 1.0)",
    )
    return parser.parse_args()


def load_property_input(args: argparse.Namespace) -> PropertyInput:
    """Builds PropertyInput from JSON file or command line arguments."""
    data = {}
    if args.input:
        input_path = Path(args.input)
        if not input_path.exists():
            console.print(f"[bold red]Error:[/] Input JSON file '{args.input}' not found.")
            sys.exit(1)
        try:
            with open(input_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            console.print(f"[bold red]Error:[/] Failed to parse JSON file '{args.input}': {e}")
            sys.exit(1)

    # CLI arguments override JSON attributes if provided
    if args.name:
        data["name"] = args.name
    if args.location:
        data["location"] = args.location
    if args.price:
        data["price"] = args.price
    if args.property_type:
        data["property_type"] = args.property_type
    if args.features:
        data["features"] = args.features
    if args.cta:
        data["contact_cta"] = args.cta
    if args.images:
        data["images"] = args.images
    if args.orientation:
        data["orientation"] = args.orientation
    if args.language:
        data["language"] = args.language
    if args.no_ai:
        data["enable_ai_script"] = False
    if args.bgm_volume is not None:
        data["bgm_volume"] = args.bgm_volume

    if not data.get("name"):
        console.print("[bold red]Error:[/] Property name is required. Provide via --name or in JSON file.")
        sys.exit(1)

    return PropertyInput(**data)


def main() -> None:
    args = parse_arguments()

    console.print(
        Panel.fit(
            "[bold cyan]AI Property Video Generator[/bold cyan]\n"
            "[dim]Autonomous Multimedia Promo Video Creation for Real Estate[/dim]",
            border_style="cyan",
        )
    )

    prop = load_property_input(args)

    # Display job summary
    table = Table(title="Video Generation Job Summary", show_header=True, header_style="bold magenta")
    table.add_column("Parameter", style="dim", width=20)
    table.add_column("Value")
    table.add_row("Property Name", prop.name)
    table.add_row("Location", prop.location)
    table.add_row("Price", prop.price)
    table.add_row("Property Type", prop.property_type)
    table.add_row("Orientation", prop.orientation)
    table.add_row("Language", "Hindi (हिन्दी)" if prop.language == "hi" else "Indian English")
    table.add_row("Script Engine", "Deterministic Template" if not prop.enable_ai_script else "Gemini LLM (with Template Fallback)")
    table.add_row("Images Provided", str(len(prop.images)))
    console.print(table)

    def status_callback(msg: str, progress: float):
        console.print(f"[bold green]>>[/] [dim][{progress*100:3.0f}%][/dim] {msg}")

    try:
        result = generate_property_video(
            prop=prop,
            output_filename=args.output,
            bgm_path=Path(args.bgm) if args.bgm else None,
            api_key=args.api_key,
            status_callback=status_callback,
        )

        console.print(
            Panel(
                f"[bold green]Video Successfully Generated![/bold green]\n\n"
                f"• Output Path: [bold yellow]{result['output_path']}[/bold yellow]\n"
                f"• Duration: [bold]{result['duration']} seconds[/bold]\n"
                f"• Resolution: [bold]{result['resolution']}[/bold] ({result['orientation']})\n"
                f"• File Size: [bold]{result['filesize_mb']} MB[/bold]\n"
                f"• Script Engine: [bold cyan]{result['script_source']}[/bold cyan]",
                title="Job Completed",
                border_style="green",
            )
        )

    except Exception as e:
        console.print(f"[bold red]Pipeline Error:[/] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
