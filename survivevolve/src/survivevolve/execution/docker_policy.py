"""Restricted Docker IPC for untrusted policy code, never executed on host.

Defense in depth, not a formal security proof. Use a VM/gVisor for malicious
workloads. Referee, keys, Docker socket and host network stay outside.
"""
import json
import os
import select
import subprocess
import time
import uuid
from pathlib import Path


class PolicyFailure(Exception):
    """Candidate is invalid, crashed or exceeded its inference time budget."""


class DockerPolicy:
    def __init__(self, source: Path, seed: int,
                 image: str = "survivevolve-policy:m1", timeout: float = 10.0):
        self.source = Path(source).resolve(strict=True)
        if not self.source.is_file() or self.source.suffix != ".py" or self.source.stat().st_size > 64000:
            raise PolicyFailure("policy must be a Python file of at most 64KB")
        if any(char in str(self.source) for char in (",", "\n", "\r")):
            raise PolicyFailure("unsupported path characters")
        self.timeout = timeout
        self.name = f"sv-policy-{uuid.uuid4().hex[:16]}"
        self._buffer = b""
        command = [
            "docker", "run", "--rm", "-i", "--name", self.name,
            "--network", "none", "--ipc", "none", "--read-only", "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges", "--pids-limit", "32",
            "--memory", "256m", "--memory-swap", "256m", "--cpus", "1",
            "--user", "65534:65534", "--tmpfs", "/tmp:rw,nosuid,nodev,size=16m",
            "--ulimit", "nofile=64:64",
            "--mount", f"type=bind,src={self.source},dst=/code/policy.py,readonly",
            image, "python", "-I", "/app/worker.py", str(seed),
        ]
        try:
            self.process = subprocess.Popen(
                command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, bufsize=0,
            )
        except OSError as exc:
            raise PolicyFailure(f"Docker startup failed: {type(exc).__name__}") from exc

    def _write(self, payload: bytes):
        fd = self.process.stdin.fileno()
        end = time.monotonic() + self.timeout
        remaining = memoryview(payload)
        while remaining:
            if self.process.poll() is not None:
                raise PolicyFailure("policy container exited")
            wait = end - time.monotonic()
            if wait <= 0 or not select.select([], [fd], [], wait)[1]:
                raise PolicyFailure("policy input timeout")
            try:
                n = os.write(fd, remaining[:4096])
            except (BrokenPipeError, OSError) as exc:
                raise PolicyFailure("policy input closed") from exc
            if n <= 0:
                raise PolicyFailure("no input progress")
            remaining = remaining[n:]

    def _read_line(self):
        fd = self.process.stdout.fileno()
        end = time.monotonic() + self.timeout
        while b"\n" not in self._buffer:
            if len(self._buffer) > 32768:
                raise PolicyFailure("policy output too large")
            wait = end - time.monotonic()
            if wait <= 0 or not select.select([fd], [], [], wait)[0]:
                raise PolicyFailure("policy response timeout")
            data = os.read(fd, 8192)
            if not data:
                raise PolicyFailure("policy container exited without response")
            self._buffer += data
        line, self._buffer = self._buffer.split(b"\n", 1)
        if len(line) > 32768:
            raise PolicyFailure("policy output too large")
        return line

    def actions(self, observation_batch):
        data = (json.dumps({"batch": observation_batch}, separators=(",", ":"), allow_nan=False) + "\n").encode()
        self._write(data)
        try:
            answer = json.loads(self._read_line())
        except (ValueError, UnicodeDecodeError) as exc:
            raise PolicyFailure("malformed response") from exc
        actions = answer.get("actions") if isinstance(answer, dict) else None
        if not isinstance(actions, list) or len(actions) != len(observation_batch):
            raise PolicyFailure("policy returned an invalid batch")
        for item, action in zip(observation_batch, actions):
            if type(action) is not int or not (0 <= action < item["num_actions"]):
                raise PolicyFailure("policy returned invalid action")
        return actions

    def close(self):
        # Never wait indefinitely on untrusted code or Docker CLI IO.
        if self.process.poll() is None:
            try:
                os.write(self.process.stdin.fileno(), b'{"stop":true}\n')
            except OSError:
                pass
            try:
                self.process.wait(timeout=0.5)
            except subprocess.TimeoutExpired:
                self.process.kill()
        try:
            self.process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
        try:
            subprocess.run(["docker", "rm", "-f", self.name], capture_output=True, timeout=3, check=False)
        except (OSError, subprocess.TimeoutExpired):
            pass

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
