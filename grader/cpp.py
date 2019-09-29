import subprocess

from . import task
from . import sandbox

import os
import sys
import json
import pathlib


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

        is_coverage = self.build_type.startsWith("COVERAGE")
        min_coverage_value = None
        if is_coverage and ':' in self.build_type:
            self.build_type, min_coverage_value = self.build_type.split(':')

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
                    if not min_coverage_value:
                        self.check_call(["llvm-cov", "report", test_binary, "-instr-profile=" + coverage_data],
                                        cwd=str(submit_build))
                    else:
                        coverage_report_path = os.path.join(submit_build, 'coverage.json')
                        with open(coverage_report_path, 'w') as fout:
                            self.check_call(["llvm-cov", "export", test_binary, "-instr-profile=" + coverage_data,
                                            "-summary-only", "-format=text"],
                                            stdout=fout,
                                            cwd=str(submit_build))
                        self.check_call(["python3", "check_coverage.py", min_coverage_value, coverage_report_path],
                                        cwd=str(self.task_path))

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

        self.build_root = self.root / 'build'
        self.test_script = self.config.get("test_script")

        self.disable_asan = self.config.get("disable_asan", False)
        self.disable_tsan = self.config.get("disable_tsan", False)
        self.build_baseline = self.config.get("build_baseline", True)

        self.build_types = []
        if not self.disable_asan:
            self.build_types += ["asan"]
        if not self.disable_tsan:
            self.build_types += ["tsan"]

        self.build_types += ["relwithdebinfo"]

        self.scorer = self.config.get("scorer", None)

    def build_dir(self, build_type, test_solution=False):
        return self.build_root / (build_type + ("_baseline" if test_solution else "")) 
    
    def build(self, build_type, test_solution=False):
        build_dir = self.build_dir(build_type, test_solution)
        build_dir.mkdir(exist_ok=True, parents=True)
        if not test_solution:
            sandbox.chmod(str(build_dir))

        cmake_cmd = [
            "cmake", "-G", "Ninja", str(self.root),
            "-DGRADER=YES", "-DENABLE_PRIVATE_TESTS=YES", "-DCMAKE_BUILD_TYPE=" + build_type
        ]
        if test_solution:
            cmake_cmd.append("-DTEST_SOLUTION=YES")
            
        self.check_call(cmake_cmd, cwd=str(build_dir), sandboxed=not test_solution)

        for test_binary in self.tests + self.benchmarks:
            self.check_call(["ninja", "-v", test_binary], cwd=str(build_dir), sandboxed=not test_solution)

    def report_file(self, benchmark, build_type, test_solution):
        return self.build_dir(build_type, test_solution) / "{}-report.json".format(benchmark)

    def run_test(self, test, build_type):
        self.check_call([str(self.build_dir(build_type) / test)],
            sandboxed = True,
            cwd=str(self.task_path))
    
    def run_benchmark(self, benchmark, build_type, test_solution):
        build_dir = self.build_dir(build_type, test_solution)
        report = self.report_file(benchmark, build_type, test_solution)
        
        self.check_call([str(build_dir / benchmark), "--benchmark_out="+str(report)],
            sandboxed=not test_solution,
            cwd=str(self.task_path))

    def grade(self, submit_root):
        self.copy_sources(submit_root)

        if self.build_baseline:
            self.build("relwithdebinfo", test_solution=True)
        
        for build_type in self.build_types:
            release_build = build_type == "relwithdebinfo"

            build_dir = self.build_dir(build_type)

            self.build(build_type, test_solution=False)

            if release_build and self.need_lint:
                self.check_call(["../../run_linter.sh", self.name, "--server"], cwd=str(build_dir))

            try:
                if self.test_script:
                    self.check_call([str(self.task_path / self.test_script)],
                                    cwd=str(self.task_path),
                                    sandboxed=True)
                    return

                for test_binary in self.tests:
                    self.run_test(test_binary, build_type)

                if not release_build:
                    continue

                for bench_binary in self.benchmarks:
                    self.run_benchmark(bench_binary, build_type, test_solution=False)
                    self.run_benchmark(bench_binary, build_type, test_solution=True)

                    if self.scorer is None:
                        continue

                    self.check_call([
                        str(self.task_path / self.scorer),
                        str(self.report_file(bench_binary, build_type, False)),
                        str(self.report_file(bench_binary, build_type, True))
                    ], cwd=str(self.task_path))
            except subprocess.CalledProcessError:
                raise task.TestFailed("Test process failed")


class CppCactusTask:
    def __init__(self, name, root=None):
        self.name = name
        self.root = root
        self.review = False
        with (self.root / ".tester.json").open() as f:
            self.config = json.load(f)

        if name not in self.config:
            raise ValueError("unknown task name: {}".format(name))

    def check_call(self, cmd, sandboxed=False, **kwargs):
        sys.stderr.write("> {}{} {}\n".format(
            "" if "cwd" not in kwargs else "cd {} && ".format(kwargs["cwd"]),
            "sandbox" if sandboxed else "",
            " ".join(cmd),
        ))
        sys.stderr.flush()

        if sandboxed:
            sandbox.check_call(cmd, **kwargs)
        else:
            subprocess.check_call(cmd, **kwargs)

    def grade(self, submit_root):
        build_dir = pathlib.Path(submit_root) / "build"
        build_dir.mkdir(exist_ok=True, parents=True)

        self.check_call([
            "cmake", "-G", "Ninja",
            str(submit_root),
            "-DCMAKE_BUILD_TYPE=ASAN"],
            cwd=str(build_dir))

        self.check_call(["ninja", self.config[self.name]["target"]],
            cwd=str(build_dir),
            timeout=60)
