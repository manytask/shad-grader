import pytest
import os
import tempfile
import subprocess

from . import sandbox


def test_sandbox_env(tmpdir):
    env_output = os.path.join(tmpdir, "env")

    os.environ["SECRET"] = "1"
    with open(os.path.join(tmpdir, "env"), "w") as env:
        sandbox.check_call(["env"], stdout=env)

    assert "SECRET" not in open(env_output).read()


def test_timeout():
    with pytest.raises(subprocess.TimeoutExpired):
        sandbox.check_call(["sleep", "2"], timeout=1)


def test_return_code():
    with pytest.raises(subprocess.CalledProcessError):
        sandbox.check_call(["false"])


def test_output_file(tmpdir):
    with tempfile.TemporaryDirectory() as tmpdir:
        sandbox.chmod(tmpdir)

        sandbox.check_call(["touch", os.path.join(tmpdir, "out.json")])

