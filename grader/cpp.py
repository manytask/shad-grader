import subprocess

from . import task
from . import sandbox


class Cpp0Task(task.Task):
    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)

        self.tests = self.config.get("tests", [])
        if isinstance(self.tests, str):
            self.tests = [self.tests]

        self.build_dir = self.root / 'build'

    def grade(self, submit_root):
        self.copy_sources(submit_root)

        submit_build = self.build_dir / "submit"
        submit_build.mkdir(exist_ok=True, parents=True)

        sandbox.chmod(str(submit_build))

        self.check_call(["cmake", "-G", "Ninja", str(self.root), "-DGRADER=YES", "-DENABLE_PRIVATE_TESTS=YES"],
                        cwd=str(submit_build))
        for test_binary in self.tests:
            self.check_call(["ninja", "-v", test_binary], cwd=str(submit_build))

        self.check_call(["../../run_linter.sh", self.name, "--server"], cwd=str(submit_build))

        for test_binary in self.tests:
            try:
                self.check_call([str(submit_build / test_binary)],
                                sandboxed=True,
                                cwd=str(self.task_path))
            except subprocess.CalledProcessError:
                raise task.TestFailed("Test process failed")


class CppTask(task.Task):
    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)

    def grade(self, submit_root):
        pass
