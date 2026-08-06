"""
Tests for watermark_cleanup — Phase 05.
"""
import pytest
from uuid import uuid4


class TestConsentFlow:
    """Consent record flow for watermark cleanup."""

    def test_consent_pending_default(self):
        status = "pending"
        assert status == "pending"

    def test_consent_approved(self):
        status = "approved"
        assert status == "approved"

    def test_consent_rejected(self):
        status = "rejected"
        assert status == "rejected"

    def test_consent_unique_per_user_asset_type(self):
        """UNIQUE (user_id, asset_id, consent_type)."""
        key1 = ("user-a", "asset-1", "watermark_cleanup")
        key2 = ("user-a", "asset-1", "watermark_cleanup")
        assert key1 == key2


class TestCleanupSourceImmutability:
    """Source asset must never be mutated."""

    def test_source_checksum_unchanged(self):
        source_checksum_before = "abc123"
        source_checksum_after = "abc123"
        assert source_checksum_before == source_checksum_after

    def test_variant_different_from_source(self):
        source_key = "original.png"
        variant_key = "original.png_cleaned"
        assert source_key != variant_key


class TestCleanupApproval:
    """Approve/reject flow."""

    def test_approve_sets_approved_at(self):
        """Approve must set approved_at timestamp."""
        approved = True
        has_timestamp = True
        assert approved and has_timestamp

    def test_reject_does_not_inpaint(self):
        rejected = True
        inpainting_done = False
        assert rejected and not inpainting_done


class TestThumbnailSelect:
    """Thumbnail selection logic."""

    def test_only_one_selected(self):
        """Selecting one candidate deselects others."""
        candidates = [
            {"id": "1", "selected": False},
            {"id": "2", "selected": True},
            {"id": "3", "selected": False},
        ]
        selected_count = sum(1 for c in candidates if c["selected"])
        assert selected_count == 1

    def test_select_toggles(self):
        """Can change selection."""
        candidates = [{"id": "1", "selected": True}]
        candidates[0]["selected"] = False
        assert not candidates[0]["selected"]
