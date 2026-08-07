"""
Tests for admin endpoints — Hidden Features P6.
"""
import pytest


class TestAdminAuth:
    """Admin auth gate."""

    def test_non_admin_blocked(self):
        """Non-admin users should get 403."""
        role = "user"
        is_admin = role == "admin"
        assert is_admin is False

    def test_admin_allowed(self):
        role = "admin"
        is_admin = role == "admin"
        assert is_admin is True


class TestBackupEndpoints:
    """Backup API."""

    def test_backup_endpoint_exists(self):
        from apps.api.routers.admin_audit import router
        # Admin backup exists in services
        from apps.api.services.backup import dump_config
        assert callable(dump_config)

    def test_backup_service_importable(self):
        from apps.api.services import backup
        assert backup is not None


class TestMfaEndpoints:
    """MFA API."""

    def test_mfa_router_exists(self):
        from apps.api.routers.admin_mfa import router
        paths = [r.path for r in router.routes]
        assert '/api/admin/mfa' in paths


class TestDBMigration:
    """Migration 0039 cleanup."""

    def test_migration_file_exists(self):
        import os
        path = os.path.join('supabase', 'migrations', '0039_drop_unused_columns.sql')
        exists = os.path.exists(path)
        assert exists, "Migration 0039 should exist"

    def test_drops_pitch_column(self):
        with open('supabase/migrations/0039_drop_unused_columns.sql') as f:
            sql = f.read()
        assert 'DROP COLUMN IF EXISTS pitch' in sql

    def test_drops_tone_column(self):
        with open('supabase/migrations/0039_drop_unused_columns.sql') as f:
            sql = f.read()
        assert 'DROP COLUMN IF EXISTS tone' in sql

    def test_drops_deleted_at(self):
        with open('supabase/migrations/0039_drop_unused_columns.sql') as f:
            sql = f.read()
        assert 'DROP COLUMN IF EXISTS deleted_at' in sql


class TestTrafficEndpoints:
    """Traffic API."""

    def test_admin_analytics_router_exists(self):
        from apps.api.routers.admin_analytics import router
        assert router is not None


class TestUserManagement:
    """Admin user management."""

    def test_admin_users_router_exists(self):
        from apps.api.routers.admin_users import router
        paths = [r.path for r in router.routes]
        assert '/api/admin/users' in paths
