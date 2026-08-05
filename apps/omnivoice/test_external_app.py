"""App mau (boilerplate) cho dev ben thu 3 tich hop voi OmniVoice server.

Mo phong 1 ung dung bat ky (CLI, web, mobile) chi can biet IP:port + voiceID
la goi duoc TTS. KHONG can upload file, KHONG can biet instruct.

Workflow:
  1. Validate IP:port bang /v1/identify (tranh nhap nham server khac)
  2. Lay danh sach voiceID tu /v1/catalog
  3. Goi TTS voi /v1/voices/{voiceID}/tts
  4. Luu audio thanh file .wav

Chay:
    python test_external_app.py
    # hoac:
    python test_external_app.py --server http://192.168.1.50:8088 --voice narrator_vi_female
"""

import argparse
import sys
from pathlib import Path

import requests


def identify(base_url: str) -> dict:
    """Validate server + lay thong tin IP/port/version.

    Tra ve dict neu server OK, raise neu khong.
    """
    r = requests.get(f"{base_url}/v1/identify", timeout=10)
    r.raise_for_status()
    return r.json()


def list_voices(base_url: str) -> list[dict]:
    r = requests.get(f"{base_url}/v1/catalog", timeout=10)
    r.raise_for_status()
    return r.json()["voices"]


def tts(
    base_url: str,
    voice_id: str,
    text: str,
    language: str | None = None,
    speed: float | None = None,
    output: str = "external_output.wav",
) -> int:
    """Generate TTS bang voiceID don gian. Tra ve so byte audio."""
    payload = {"text": text}
    if language:
        payload["language"] = language
    params = {}
    if speed:
        params["speed"] = speed

    r = requests.post(
        f"{base_url}/v1/voices/{voice_id}/tts",
        json=payload,
        params=params,
        timeout=300,
    )
    if r.status_code != 200:
        try:
            err = r.json()
        except Exception:
            err = {"detail": r.text}
        print(f"[ERR] {r.status_code}: {err}", file=sys.stderr)
        return 0
    Path(output).write_bytes(r.content)
    return len(r.content)


def main():
    parser = argparse.ArgumentParser(
        description="External app mau tich hop voi OmniVoice voice server (Phase 6).",
    )
    parser.add_argument(
        "--server",
        default="http://127.0.0.1:8088",
        help="Base URL cua server (mac dinh: http://127.0.0.1:8088)",
    )
    parser.add_argument(
        "--voice",
        default="narrator_vi_female",
        help="voiceID (mac dinh: narrator_vi_female)",
    )
    parser.add_argument(
        "--text",
        default="Xin chào! Đây là giọng nói được tạo bởi app bên thứ 3 qua API đơn giản.",
        help="Van ban can doc",
    )
    parser.add_argument(
        "--language",
        default=None,
        help="Override ngon ngu (vi/en/zh/...). Mac dinh: dung theo voice registry.",
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=None,
        help="Override toc do (0.5-2.0). Mac dinh: dung theo voice registry.",
    )
    parser.add_argument(
        "--output",
        default="external_output.wav",
        help="File output (.wav)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Chi list voiceID (khong generate audio)",
    )
    args = parser.parse_args()

    base_url = args.server.rstrip("/")
    print(f"=== OmniVoice External App Sample ===")
    print(f"Server: {base_url}")
    print()

    # Buoc 1: Identify (validate IP:port)
    print("[1/3] Validate server...")
    try:
        info = identify(base_url)
    except requests.RequestException as e:
        print(f"[FAIL] Khong the ket noi server: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"  server_id={info['server_id'][:16]}...")
    print(f"  server_version={info['server_version']} omnivoice={info['omnivoice_version']}")
    print(f"  ip_local={info['ip_local']} port={info['port']}")
    print(f"  supported_languages={info['supported_languages']}")
    print(f"  model_status={info['model_status']}")
    if info["model_status"] != "ready":
        print(f"[WARN] Model chua ready, output co the that bai.", file=sys.stderr)

    # Buoc 2: List voices
    print()
    print("[2/3] Lay danh sach voiceID...")
    voices = list_voices(base_url)
    print(f"  Found {len(voices)} voice(s):")
    for v in voices:
        marker = " *" if v["id"] == args.voice else ""
        print(f"    - {v['id']:25s} type={v['type']:6s} lang={v['language']}{marker}")

    # Kiem tra voiceID ton tai
    voice_ids = {v["id"] for v in voices}
    if not args.list and args.voice not in voice_ids:
        print(f"[FAIL] voiceID '{args.voice}' khong co trong catalog.", file=sys.stderr)
        print(f"  Available: {sorted(voice_ids)}", file=sys.stderr)
        sys.exit(1)

    if args.list:
        return

    # Buoc 3: Generate TTS
    print()
    print(f"[3/3] Generate TTS voi voiceID='{args.voice}'...")
    print(f"  text={args.text[:60]!r}{'...' if len(args.text) > 60 else ''}")
    if args.language:
        print(f"  language override={args.language}")
    if args.speed:
        print(f"  speed override={args.speed}")
    print()
    n_bytes = tts(base_url, args.voice, args.text, args.language, args.speed, args.output)
    if n_bytes == 0:
        sys.exit(1)
    print(f"[OK] Saved {n_bytes} bytes to {Path(args.output).resolve()}")
    print()
    print("=== Done! ===")


if __name__ == "__main__":
    main()