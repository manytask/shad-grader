import subprocess

from . import task
from . import sandbox

import os


class Cpp0Task(task.Task):
    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)

        self.tests = self.config.get("tests", [])
        self.need_lint = self.config.get("linter", True)
        if isinstance(self.tests, str):
            self.tests = [self.tests]

        self.build_dir = self.root / 'build'
        self.build_type = self.config.get("build_type", "ASAN")
        self.test_script = self.config.get("test_script")

    def grade(self, submit_root):
        self.copy_sources(submit_root)

        submit_build = self.build_dir / "submit"
        submit_build.mkdir(exist_ok=True, parents=True)

        sandbox.chmod(str(submit_build))

        is_coverage = self.build_type == "COVERAGE"

        self.check_call(["cmake", "-G", "Ninja", str(self.root),
                        "-DGRADER=YES", "-DENABLE_PRIVATE_TESTS=YES", "-DCMAKE_BUILD_TYPE=" + self.build_type],
                        env=None if not is_coverage else dict(os.environ, CXX="clang++-7"),
                        cwd=str(submit_build))
        for test_binary in self.tests:
            self.check_call(["ninja", "-v", test_binary], cwd=str(submit_build))
        
        if self.need_lint:
            self.check_call(["../../run_linter.sh", self.name, "--server"], cwd=str(submit_build))

        if self.test_script:
            self.check_call([str(self.task_path / self.test_script)],
                            cwd=str(self.task_path),
                            sandboxed=True)
            return

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

        self.tests = self.config.get("tests", [])
        if isinstance(self.tests, str):
            self.tests = [self.tests]

        self.benchmarks = self.config.get("benchmarks", [])
        if isinstance(self.benchmarks, str):
            self.benchmarks = [self.benchmarks]
        
        self.need_lint = self.config.get("linter", True)

        self.build_dir = self.root / 'build'
        self.test_script = self.config.get("test_script")

        self.disable_asan = self.config.get("disable_asan", False)
        self.disable_tsan = self.config.get("disable_tsan", False)

        self.build_types = []
        if not self.disable_asan:
            self.build_types += ["ASAN"]
        if not self.disable_tsan:
            self.build_types += ["TSAN"]

        self.build_types += ["RELWITHDEBINFO"]

    def grade(self, submit_root):
        self.copy_sources(submit_root)

        for build_type in self.build_types:
            release_build = build_type == "RELWITHDEBINFO"

            submit_build = self.build_dir / build_type
            submit_build.mkdir(exist_ok=True, parents=True)
            sandbox.chmod(str(submit_build))

            self.check_call(["cmake", "-G", "Ninja", str(self.root),
                            "-DGRADER=YES", "-DENABLE_PRIVATE_TESTS=YES", "-DCMAKE_BUILD_TYPE=" + build_type],
                            cwd=str(submit_build))

            for test_binary in self.tests + self.benchmarks:
                self.check_call(["ninja", "-v", test_binary], cwd=str(submit_build))
                
            if release_build and self.need_lint:
                self.check_call(["../../run_linter.sh", self.name, "--server"], cwd=str(submit_build))

            try:
                for test_binary in self.tests:
                    self.check_call([str(submit_build / test_binary)],
                        sandboxed=True,
                        cwd=str(self.task_path))

                if release_build:
                    for bench_binary in self.benchmarks:
                        self.check_call([str(submit_build / bench_binary)],
                            sandboxed=True,
                            cwd=str(self.task_path))

            except subprocess.CalledProcessError:
                raise task.TestFailed("Test process failed")

