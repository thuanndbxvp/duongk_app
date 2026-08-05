import pytest
from unittest.mock import MagicMock
from apps.api.services.credit_manager import CreditManager


class TestCreditManager:
    @pytest.fixture
    def mock_admin(self):
        return MagicMock()
    
    @pytest.fixture
    def manager(self, mock_admin, monkeypatch):
        monkeypatch.setattr('apps.api.services.credit_manager.get_supabase_admin', lambda: mock_admin)
        return CreditManager()
    
    def test_get_pricing(self, manager):
        assert manager.get_pricing('script_generation') == 30
        assert manager.get_pricing('rag_retrieve') == 1
        assert manager.get_pricing('unknown') == 0
    
    def test_get_balance(self, manager, mock_admin):
        mock_admin.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
            data={'credits': 100}
        )
        assert manager.get_balance('user-1') == 100
    
    def test_hold_succeeds(self, manager, mock_admin):
        mock_admin.rpc.return_value.execute.return_value = MagicMock(
            data=[{'transaction_id': 'tx-1', 'balance_after': 70}]
        )
        result = manager.hold('user-1', 'job-1', 30)
        assert result['balance_after'] == 70
    
    def test_hold_insufficient_raises(self, manager, mock_admin):
        # Simulate RPC failure
        mock_admin.rpc.return_value.execute.return_value = MagicMock(data=[])
        with pytest.raises(ValueError):
            manager.hold('user-1', 'job-1', 30)
