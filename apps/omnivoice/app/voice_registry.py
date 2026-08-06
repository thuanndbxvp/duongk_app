"""VoiceID Registry — service layer cho Phase 6.

Luu voiceID metadata vao file JSON local (`voice_registry.json` ngay cung cap
voi main.py). Dung threading.Lock cho atomic write (R10 trong plan).

3 loai voice (D9):
  - clone: ref_audio (path to file trong voices/)
  - design: instruct (text mo ta giong)
  - auto: random (model tu chon)

API:
  - list() -> list[dict]: metadata (khong bao gom instruct)
  - get(voice_id) -> dict | None
  - upsert(voice_id, meta) -> dict (tra ve entry moi)
  - delete(voice_id) -> bool
  - resolve_path(voice_id) -> Path | None: path den ref_audio neu type=clone
"""

import json
import logging
import threading
from pathlib import Path
from typing import Any, ClassVar

logger = logging.getLogger("omnivoice-api-server.voice_registry")


class VoiceRegistry:
    """JSON-backed VoiceID registry with atomic writes."""

    SCHEMA_VERSION: ClassVar[str] = "1.0"

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._lock = threading.Lock()
        self._data: dict[str, Any] = self._load()

    # ─── Internal I/O ─────────────────────────────────────────────
    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            logger.info("VoiceRegistry: file %s not found, initializing empty", self.path)
            return {"version": self.SCHEMA_VERSION, "voices": {}}
        try:
            with self.path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            # Sanity check schema
            if "voices" not in data:
                logger.warning("VoiceRegistry: missing 'voices' key, resetting")
                data["voices"] = {}
            return data
        except (OSError, json.JSONDecodeError) as e:
            logger.error("VoiceRegistry: failed to load %s: %s", self.path, e)
            return {"version": self.SCHEMA_VERSION, "voices": {}}

    def _save(self) -> None:
        # Atomic write: ghi vao .tmp roi rename (R10 giam thieu race condition)
        tmp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        try:
            with tmp_path.open("w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
            tmp_path.replace(self.path)
        except OSError as e:
            logger.error("VoiceRegistry: failed to save %s: %s", self.path, e)
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
            raise

    # ─── Public API ────────────────────────────────────────────────
    def list(self, include_instruct: bool = False) -> list[dict[str, Any]]:
        """Tra ve danh sach voice (mac dinh KHONG bao gom instruct de giam leak)."""
        system_voices = {'ban_mai', 'lan_trinh', 'minhquan_vb', 'ngan_ha', 'ngoc_huyen', 'ngochuyen_vb', 'thao_trinh', 'tuong_vy'}
        out = []
        for vid, meta in self._data["voices"].items():
            entry = {"id": vid, **{k: v for k, v in meta.items() if k != "instruct"}}
            if include_instruct:
                entry["instruct"] = meta.get("instruct")
            if vid in system_voices:
                entry["is_system"] = True
            else:
                entry["is_system"] = False
            out.append(entry)
        # Sort by id de stable order
        return sorted(out, key=lambda x: x["id"])

    def get(self, voice_id: str) -> dict[str, Any] | None:
        return self._data["voices"].get(voice_id)

    def upsert(self, voice_id: str, meta: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            self._data["voices"][voice_id] = meta
            self._save()
        logger.info("VoiceRegistry: upsert '%s' (type=%s)", voice_id, meta.get("type"))
        return meta

    def delete(self, voice_id: str) -> bool:
        with self._lock:
            if voice_id not in self._data["voices"]:
                return False
            del self._data["voices"][voice_id]
            self._save()
        logger.info("VoiceRegistry: deleted '%s'", voice_id)
        return True

    def rename(self, old_id: str, new_id: str) -> dict[str, Any] | None:
        """Doi voice_id (atomic). Tra ve entry moi, hoac None neu old_id khong co
        hoac new_id da ton tai."""
        with self._lock:
            if old_id not in self._data["voices"]:
                return None
            if new_id in self._data["voices"]:
                return None
            entry = self._data["voices"].pop(old_id)
            entry["previous_id"] = old_id
            self._data["voices"][new_id] = entry
            self._save()
        logger.info("VoiceRegistry: renamed '%s' -> '%s'", old_id, new_id)
        return entry

    def update(self, voice_id: str, patch: dict[str, Any]) -> dict[str, Any] | None:
        """Patch mot/ nhieu field cua voice (khong doi id). Tra ve entry moi."""
        with self._lock:
            existing = self._data["voices"].get(voice_id)
            if existing is None:
                return None
            # Chi cho phep update cac field an toan
            for k, v in patch.items():
                if k in {"type", "id", "previous_id"}:
                    continue
                existing[k] = v
            self._save()
        logger.info("VoiceRegistry: updated '%s' fields=%s", voice_id, list(patch.keys()))
        return existing

    def resolve_path(self, voice_id: str) -> Path | None:
        """Resolve ref_audio_file (relative to voices_dir) cho type=clone.

        Tra ve None neu khong phai clone hoac file khong ton tai (R11).
        """
        meta = self.get(voice_id)
        if not meta or meta.get("type") != "clone":
            return None
        ref = meta.get("ref_audio_file")
        if not ref:
            return None
        # Thuong thi ref_audio_file chi chua basename (vd "my_voice.wav")
        # Server se resolve tu voices_dir cua main.py
        return Path(ref) if Path(ref).is_absolute() else None


# ─── Validation helpers ────────────────────────────────────────────
VALID_TYPES = {"clone", "design", "auto"}
VALID_LANGUAGES = {"vi", "km", "my", "en", "zh", "es", "hi", "ar", "auto"}


def validate_voice_meta(meta: dict[str, Any]) -> tuple[bool, str]:
    """Kiem tra meta hop le. Tra ve (is_valid, error_message)."""
    if not isinstance(meta, dict):
        return False, "meta must be a dict"

    vtype = meta.get("type")
    if vtype not in VALID_TYPES:
        return False, f"type must be one of {VALID_TYPES}, got {vtype!r}"

    if vtype == "design":
        if not meta.get("instruct") or not isinstance(meta["instruct"], str):
            return False, "type='design' requires non-empty 'instruct' string"
    elif vtype == "clone":
        if not meta.get("ref_audio_file"):
            return False, "type='clone' requires 'ref_audio_file'"

    lang = meta.get("language", "vi")
    if lang not in VALID_LANGUAGES:
        return False, f"language must be one of {VALID_LANGUAGES}, got {lang!r}"

    return True, ""
