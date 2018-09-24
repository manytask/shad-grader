import subprocess

from . import task
from . import sandbox

import os


class Cpp0Task(task.Task):
    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)

        self.tests = self.config.get("tests", [])
        if isinstance(self.tests, str):
            self.tests = [self.tests]

        self.build_dir = self.root / 'build'
        self.build_type = self.config.get("build_type", "ASAN")

    def grade(self, submit_root):
        self.copy_sources(submit_root)

        submit_build = self.build_dir / "submit"
        submit_build.mkdir(exist_ok=True, parents=True)

        sandbox.chmod(str(submit_build))

        is_coverage = self.build_type == "COVERAGE"

        self.check_call(["cmake", "-G", "Ninja", str(self.root),
                        "-DGRADER=YES", "-DENABLE_PRIVATE_TESTS=YES", "-DCMAKE_BUILD_TYPE=" + self.build_type],
                        env=None if not is_coverage else dict(os.environ, CXX="clang++"),
                        cwd=str(submit_build))
        for test_binary in self.tests:
            self.check_call(["ninja", "-v", test_binary], cwd=str(submit_build))

        self.check_call(["../../run_linter.sh", self.name, "--server"], cwd=str(submit_build))

        for test_binary in self.tests:
            try:
                raw_coverage_data = test_binary + ".profraw"
                raw_coverage_path = submit_build / raw_coverage_data
                coverage_data = test_binary + ".profdata"
                self.check_call([str(submit_build / test_binary)],
                                sandboxed=True,
                                env=None if not is_coverage else dict(os.environ, LLVM_PROFILE_FILE=raw_coverage_path),
                                cwd=str(self.task_path))
                if is_coverage:
                    self.check_call(["llvm-profdata", "merge", "-sparse",
                                    raw_coverage_data, "-o", coverage_data],
                                    cwd=str(submit_build))
                    self.check_call(["llvm-cov", "report", test_binary, "-instr-profile=" + coverage_data],
                                    cwd=str(submit_build))

            except subprocess.CalledProcessError:
                raise task.TestFailed("Test process failed")


class CppTask(task.Task):
    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)

    def grade(self, submit_root):
        pass
