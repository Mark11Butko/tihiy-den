"""Atomic storage and kernel-owned locks. No forced deletion of live locks."""
import json
import os
import tempfile
import time


class FileLock:
    def __init__(self, path, timeout=10):
        self.path, self.timeout, self.file = path, timeout, None

    def __enter__(self):
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        self.file = open(self.path, "a+b")
        if os.path.getsize(self.path) == 0:
            self.file.write(b"\0")
            self.file.flush()
        deadline = time.monotonic() + self.timeout
        while True:
            try:
                self.file.seek(0)
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(self.file.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(self.file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return self
            except OSError:
                if time.monotonic() >= deadline:
                    self.file.close()
                    self.file = None
                    raise TimeoutError("Another widget operation is still running") from None
                time.sleep(0.03)

    def __exit__(self, *args):
        if self.file:
            try:
                self.file.seek(0)
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(self.file.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(self.file.fileno(), fcntl.LOCK_UN)
            finally:
                self.file.close()
                self.file = None


def atomic_write(path, value, binary=False):
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=".td-", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "wb" if binary else "w", **({} if binary else {"encoding": "utf-8", "newline": "\n"})) as f:
            f.write(value)
            f.flush()
            os.fsync(f.fileno())
        # Rainmeter / antivirus can briefly open the destination without FILE_SHARE_DELETE.
        # Keep the old file intact and retry only this transient sharing/permission failure.
        deadline = time.monotonic() + 2
        while True:
            try:
                os.replace(temp, path)
                break
            except PermissionError:
                if time.monotonic() >= deadline: raise
                time.sleep(.03)
    finally:
        if os.path.exists(temp):
            os.remove(temp)


def write_json(path, value):
    atomic_write(path, json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False))
