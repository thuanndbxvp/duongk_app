import pytest
from apps.worker.progress_tracker import ProgressTracker

def test_tracker_initialization():
    tracker = ProgressTracker("job123", "http://localhost", "key")
    assert tracker.job_id == "job123"
    assert len(ProgressTracker.OUTPUTS) == 14
