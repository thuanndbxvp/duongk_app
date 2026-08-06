"""
FFmpegRunner — run FFmpeg subprocess with progress parsing + cancel support.
Phase 04.
"""
from __future__ import annotations
import subprocess
import re
import os
import signal
import threading
from typing import Callable


# Track running PIDs for cancel
_RUNNING_PIDS: dict[str, int] = {}


def register_pid(job_id: str, pid: int):
    _RUNNING_PIDS[job_id] = pid


def unregister_pid(job_id: str):
    _RUNNING_PIDS.pop(job_id, None)


def kill_pid(job_id: str) -> bool:
    """Kill the FFmpeg process for a job. Returns True if killed."""
    pid = _RUNNING_PIDS.get(job_id)
    if not pid:
        return False
    try:
        if os.name == 'nt':
            subprocess.run(['taskkill', '/F', '/T', '/PID', str(pid)], capture_output=True)
        else:
            os.killpg(pid, signal.SIGTERM)
    except Exception:
        pass
    unregister_pid(job_id)
    return True


_TIME_RE = re.compile(r'time=(\d{2}):(\d{2}):(\d{2})\.(\d{2})')


def parse_ffmpeg_time(line: str) -> float | None:
    """Extract time_seconds from FFmpeg stderr line like 'time=00:01:23.45'."""
    m = _TIME_RE.search(line)
    if not m:
        return None
    h, mi, s, cs = int(m[1]), int(m[2]), int(m[3]), int(m[4])
    return h * 3600 + mi * 60 + s + cs / 100.0


def run_ffmpeg(
    argv: list[str],
    job_id: str,
    cancel_check: Callable[[], bool],
    progress_cb: Callable[[float], None],
    total_duration: float = 0,
) -> int:
    """
    Run FFmpeg as subprocess.

    Args:
        argv: Full command args (without 'ffmpeg').
        job_id: Render job UUID for PID tracking.
        cancel_check: Returns True when cancel requested.
        progress_cb: Called with progress 0.0-1.0.
        total_duration: Expected total duration for progress calc.

    Returns:
        FFmpeg exit code.
    """
    cmd = ['ffmpeg'] + argv

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        encoding='utf-8',
        errors='replace',
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0,
    )

    register_pid(job_id, proc.pid)
    last_progress = 0.0

    def read_stderr():
        nonlocal last_progress
        try:
            for line in proc.stderr:
                if cancel_check():
                    kill_pid(job_id)
                    break
                t = parse_ffmpeg_time(line)
                if t is not None and total_duration > 0:
                    p = min(t / total_duration, 1.0)
                    if p > last_progress + 0.01:
                        last_progress = p
                        progress_cb(p)
        except Exception:
            pass

    reader = threading.Thread(target=read_stderr, daemon=True)
    reader.start()

    try:
        rc = proc.wait(timeout=3600)  # 1 hour max
    except subprocess.TimeoutExpired:
        kill_pid(job_id)
        rc = -1
    finally:
        reader.join(timeout=2)
        unregister_pid(job_id)

    return rc
