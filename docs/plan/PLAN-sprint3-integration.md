# Sprint 3 Task Group 5: Integration - Plan

## Integration Test Strategy

### 1. Unit Tests (Fast, No I/O)

```python
# tests/unit/test_api_scripts.py
class TestScriptsAPI:
    """Unit tests for scripts API endpoints."""
    
    async def test_generate_script_validation(self, mock_user):
        """Test input validation."""
        # ...
    
    async def test_get_script_not_found(self):
        """Test 404 for missing script."""
        # ...
```

### 2. Integration Tests (Slower, Uses Test DB)

```python
# tests/integration/test_script_flow.py
class TestScriptFlow:
    """End-to-end integration tests."""
    
    async def test_full_pipeline(self, test_db, auth_token):
        """Test complete script generation flow."""
        # 1. Create assistant
        # 2. Generate script
        # 3. Wait for completion
        # 4. Breakdown scenes
        # 5. Verify results
```

## Test Database Setup

```python
# conftest.py
@pytest.fixture
async def test_db():
    """Create test database with schema."""
    # Use Supabase local or test container
    # Run migrations
    # Yield
    # Cleanup
```

## Files to Create

### 1. Integration Tests
**File:** `tests/integration/test_script_flow.py`

### 2. Unit Tests
**File:** `tests/unit/test_api_scripts.py`

### 3. API Updates
**File:** `apps/api/routers/scripts.py` - Add GET endpoint

### 4. Test Config
**File:** `tests/conftest.py`
