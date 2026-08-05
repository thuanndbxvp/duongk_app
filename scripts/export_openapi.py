#!/usr/bin/env python
"""
Export OpenAPI Schema for Frontend Team.

This script fetches the OpenAPI schema from the running API
and exports it to JSON files for TypeScript generation.
"""
import json
import asyncio
from pathlib import Path
import httpx


API_BASE_URL = "http://localhost:8000"
OUTPUT_DIR = Path("docs")


async def export_schemas():
    """Export OpenAPI schema to JSON files."""
    
    print(f"Fetching OpenAPI schema from {API_BASE_URL}/openapi.json...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Fetch full OpenAPI schema
        response = await client.get(f"{API_BASE_URL}/openapi.json")
        response.raise_for_status()
        full_schema = response.json()
        
        # Ensure output directory exists
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        # Save full schema
        full_schema_path = OUTPUT_DIR / "openapi_schema.json"
        with open(full_schema_path, "w", encoding="utf-8") as f:
            json.dump(full_schema, f, indent=2, ensure_ascii=False)
        print(f"[OK] Saved full schema to {full_schema_path}")
        
        # Extract only schemas (for TypeScript generation)
        schemas = {
            "components": {
                "schemas": full_schema.get("components", {}).get("schemas", {})
            },
            "info": full_schema.get("info", {}),
            "openapi": full_schema.get("openapi", "")
        }
        
        schemas_path = OUTPUT_DIR / "schemas.json"
        with open(schemas_path, "w", encoding="utf-8") as f:
            json.dump(schemas, f, indent=2, ensure_ascii=False)
        print(f"[OK] Saved schemas to {schemas_path}")
        
        # Generate TypeScript types (basic)
        ts_types = _generate_typescript_types(schemas["components"]["schemas"])
        ts_types_path = OUTPUT_DIR / "api-types.ts"
        with open(ts_types_path, "w", encoding="utf-8") as f:
            f.write(ts_types)
        print(f"[OK] Saved TypeScript types to {ts_types_path}")
        
        # Summary
        schema_count = len(schemas["components"]["schemas"])
        print(f"\n[SUCCESS] Export complete!")
        print(f"   - {schema_count} schemas exported")
        print(f"   - Output directory: {OUTPUT_DIR.absolute()}")


def _generate_typescript_types(schemas: dict) -> str:
    """Generate TypeScript types from OpenAPI schemas."""
    lines = [
        "// Auto-generated from OpenAPI schema",
        "// Do not edit manually",
        "",
        "export interface OpenAPISchema {",
    ]
    
    for name, schema in schemas.items():
        lines.append(f"  // Schema: {name}")
        
        # Handle basic types
        if "type" in schema:
            if schema["type"] == "object" and "properties" in schema:
                lines.append(f"  export interface {name} {{")
                for prop_name, prop in schema["properties"].items():
                    prop_type = _map_openapi_to_ts(prop)
                    required = prop_name in schema.get("required", [])
                    lines.append(f"    {prop_name}{'' if required else '?'}: {prop_type};")
                lines.append("  }")
            elif schema["type"] == "array" and "items" in schema:
                item_type = _map_openapi_to_ts(schema["items"])
                lines.append(f"  export type {name} = {item_type}[];")
            else:
                lines.append(f"  export type {name} = {_map_openapi_to_ts(schema)};")
        
        lines.append("")
    
    lines.append("}")
    return "\n".join(lines)


def _map_openapi_to_ts(schema: dict) -> str:
    """Map OpenAPI type to TypeScript type."""
    if "$ref" in schema:
        return schema["$ref"].split("/")[-1]
    
    openapi_type = schema.get("type", "string")
    
    type_mapping = {
        "string": "string",
        "integer": "number",
        "number": "number",
        "boolean": "boolean",
        "array": "unknown[]",
        "object": "Record<string, unknown>",
        "null": "null"
    }
    
    return type_mapping.get(openapi_type, "unknown")


if __name__ == "__main__":
    asyncio.run(export_schemas())
