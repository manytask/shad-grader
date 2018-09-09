import pytest
import pathlib
import subprocess


from .task import Task


@pytest.fixture
def course_root(tmpdir):
    subprocess.check_call(["cp", "-r", "grader/test_cpp_course", tmpdir])
    return pathlib.Path(tmpdir) / "test_cpp_course"


@pytest.fixture
def submit_root(tmpdir):
    subprocess.check_call(["cp", "-r", "grader/test_submits", tmpdir])
    return pathlib.Path(tmpdir) / "test_submits"


def test_grade(course_root, submit_root):
    task = Task.create("cpp-fall", "hello-world", course_root)

    task.grade(submit_root / "hello-world-good")

def test_grade_failed_test(course_root, submit_root):
    task = Task.create("cpp-fall", "hello-world", course_root)

    with pytest.raises(subprocess.CalledProcessError):
        task.grade(submit_root / "hello-world-failed-test")

def test_grade_banned_regex(course_root, submit_root):
    task = Task.create("cpp-fall", "hello-world", course_root)

    with pytest.raises(RuntimeError):
        task.grade(submit_root / "hello-world-banned-regex")

#    with pytest.raises(RuntimeError):
#        task.grade(submit_root / "hello-world-badly-formatted")
