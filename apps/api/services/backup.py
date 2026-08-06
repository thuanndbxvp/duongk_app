"""
Backup/restore config — dump metadata của 3 tables sang JSON.
KHÔNG dump encrypted_value (security).
"""
import json
from datetime import datetime, timezone
from typing import Optional
from apps.api.dependencies.supabase import get_supabase_admin


CONFIG_TABLES = [
    {
        'name': 'service_routing_config',
        'select': 'id, feature, primary_provider, fallback_chain, enabled_providers, cost_per_call_usd, config_version',
    },
    {
        'name': 'credit_pricing',
        'select': 'job_type, credits, description, enabled',
    },
    {
        'name': 'api_provider_keys',
        # Exclude encrypted_value — security
        'select': 'id, provider, label, is_active, rate_limit_rpm, monthly_budget_usd, expires_at, archived_at',
    },
]


def dump_config() -> dict:
    """
    Dump tất cả config tables thành dict (KHÔNG bao gồm secrets).
    Returns: {'timestamp': ISO, 'tables': {table_name: [rows]}}
    """
    db = get_supabase_admin()
    output = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'version': '1.0',
        'tables': {},
    }
    
    for table in CONFIG_TABLES:
        result = db.table(table['name']).select(table['select']).execute()
        output['tables'][table['name']] = result.data or []
    
    return output


def restore_config(config_data: dict, dry_run: bool = True) -> dict:
    """
    Restore config từ dict. dry_run=True (default) chỉ report, không apply.
    Returns: {'restored': N, 'errors': [msgs], 'dry_run': bool}
    """
    if dry_run:
        return {
            'dry_run': True,
            'restored': 0,
            'errors': [],
            'would_update': sum(len(v) for v in config_data.get('tables', {}).values()),
        }
    
    db = get_supabase_admin()
    errors = []
    restored = 0
    
    for table_name, rows in config_data.get('tables', {}).items():
        for row in rows:
            try:
                # Upsert by primary key (id) hoặc (job_type) cho credit_pricing
                if 'id' in row:
                    db.table(table_name).upsert(row).execute()
                elif 'job_type' in row:
                    db.table(table_name).upsert(row, on_conflict='job_type').execute()
                restored += 1
            except Exception as e:
                errors.append(f'{table_name}: {e}')
    
    return {
        'dry_run': False,
        'restored': restored,
        'errors': errors,
    }


def export_to_file(filepath: str) -> str:
    """Dump config → JSON file. Return file path."""
    config = dump_config()
    with open(filepath, 'w') as f:
        json.dump(config, f, indent=2)
    return filepath