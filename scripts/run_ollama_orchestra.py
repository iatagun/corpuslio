#!/usr/bin/env python
"""CLI script for Ollama Orchestra document processing.

Usage:
    python scripts/run_ollama_orchestra.py input.pdf
    python scripts/run_ollama_orchestra.py input.pdf -o output.txt
    python scripts/run_ollama_orchestra.py folder/ -o output_folder/
    python scripts/run_ollama_orchestra.py --status
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ocrchestra import OllamaOrchestrator


def main():
    parser = argparse.ArgumentParser(
        description="Ollama Orchestra - Belge işleme sistemi"
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="Giriş dosyası veya klasör yolu",
    )
    parser.add_argument(
        "-o", "--output",
        help="Çıkış dosyası veya klasör yolu",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Sistem durumunu göster",
    )
    parser.add_argument(
        "--conductor-model",
        default="llama3.2:3b",
        help="Conductor model (varsayılan: llama3.2:3b)",
    )
    parser.add_argument(
        "--vision-model",
        default="llava",
        help="Vision model (varsayılan: llava)",
    )
    parser.add_argument(
        "--host",
        default="http://localhost:11434",
        help="Ollama sunucu adresi",
    )

    args = parser.parse_args()

    # Initialize orchestrator
    orch = OllamaOrchestrator(
        conductor_model=args.conductor_model,
        vision_model=args.vision_model,
        ollama_host=args.host,
    )

    # Show status
    if args.status:
        status = orch.get_status()
        print("\n=== Ollama Orchestra Durumu ===\n")
        print(f"Ollama Sunucusu: {'✓ Bağlı' if status['ollama_available'] else '✗ Bağlantı yok'}")
        print(f"Host: {status['ollama_host']}")
        print(f"Conductor Model: {status['conductor_model']}")
        print(f"Vision Model: {status['vision_model']}")
        print(f"Vision Desteği: {'✓ Var' if status['has_vision'] else '✗ llava yüklü değil'}")
        print(f"\nMevcut Modeller: {', '.join(status['available_models']) or 'Yok'}")
        print(f"\nExpert Durumu:")
        print(f"  - PDF Expert: {'✓' if status['experts']['pdf'] else '✗ PyMuPDF yüklü değil'}")
        print(f"  - DOCX Expert: {'✓' if status['experts']['docx'] else '✗ python-docx yüklü değil'}")
        print(f"\nDesteklenen Formatlar: {', '.join(status['supported_formats'])}")
        return 0

    # Check input
    if not args.input:
        parser.print_help()
        return 1

    input_path = Path(args.input)

    if not input_path.exists():
        print(f"Hata: Dosya bulunamadı: {input_path}", file=sys.stderr)
        return 1

    # Process single file or directory
    if input_path.is_file():
        output_path = args.output
        result = orch.process(input_path, output_path)
        
        if result.get("success"):
            print(f"\n✓ İşlendi: {result['file']}")
            print(f"  Format: {result['format']}")
            if "output_file" in result:
                print(f"  Çıkış: {result['output_file']}")
            print(f"\n--- Metin ---\n")
            print(result.get("text", "")[:2000])
            if len(result.get("text", "")) > 2000:
                print("\n... (metin kısaltıldı)")
        else:
            print(f"\n✗ Hata: {result.get('error')}", file=sys.stderr)
            return 1

    elif input_path.is_dir():
        # Process all supported files in directory
        output_dir = Path(args.output) if args.output else None
        
        files = []
        for ext in orch.SUPPORTED_FORMATS.keys():
            files.extend(input_path.glob(f"*{ext}"))

        if not files:
            print(f"Desteklenen dosya bulunamadı: {input_path}")
            return 1

        print(f"\n{len(files)} dosya işlenecek...\n")
        
        results = orch.process_batch(files, output_dir)
        
        success_count = sum(1 for r in results if r.get("success"))
        print(f"\n=== Sonuç ===")
        print(f"Başarılı: {success_count}/{len(results)}")
        
        for r in results:
            status = "✓" if r.get("success") else "✗"
            print(f"  {status} {Path(r['file']).name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
