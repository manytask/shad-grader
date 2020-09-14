import abc
import os
import os.path
import sys
import pathlib
import json
import re
import shutil
import subprocess
import codecs

from . import sandbox


def copy_sources(submit_path, task_path, sources, check_fn=None):
    if not submit_path.exists():
        raise RuntimeError("Directory '{}' does not exists".format(submit_path))

    for pattern in sources:
        for file in submit_path.glob(pattern):
            target_path = task_path / file.relative_to(submit_path)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(file, target_path)

            if check_fn is not None:
                check_fn(str(target_path))


class TestFailed(Exception):
    pass


class Task:
    @classmethod
    def create(cls, course_name, name, root=None):
        if course_name.startswith("cpp-fall"):
            from . import cpp
            return cpp.Cpp0Task(name, root=root)
        elif course_name.startswith("cpp-spring"):
            from . import cpp
            if root is not None and (root / "cactus").exists():
                return cpp.CppCactusTask(name, root=root)
            return cpp.CppTask(name, root=root)
        elif course_name.startswith("os-fall"):
            from . import os
            return os.OsTask(name, root=root)
        elif course_name.startswith("db-spring"):
            from . import db
            return db.DbTask(name, root=root)
        elif course_name.startswith("ema-fall"):
            from . import ema
            return ema.EmaTask(name, root=root)
        elif course_name.startswith("hse"):
            from . import hse
            return hse.HsePyTask(name, root=root)
        elif course_name.startswith("ds"):
            from . import ds
            return ds.DsTask(name, root=root)
        else:
            raise ValueError("Unexpected course name '{}'".format(course_name))

    @classmethod
    def list(cls, root=None):
        if root is None:
            root = pathlib.Path.cwd()
        tasks = []
        for path in root.iterdir():
            if not path.is_dir():
                continue

            if not (path / ".tester.json").exists():
                continue

            tasks.append(Task(path.name, root))

        return tasks

    def __init__(self, name, root=None):
        self.name = name

        self.root = root or pathlib.Path('.')
        self.task_path = self.root / name
        self.task_private_path = self.root / 'private' / name

        with (self.task_path / ".tester.json").open() as f:
            self.config = json.load(f)

            self.sources = self.config["allow_change"]
            if not isinstance(self.sources, list):
                self.sources = [self.sources]

            self.regexp_ban = self.config.get("regexp_ban", []) + self.config.get("forbidden_regexp", [])
            self.review = self.config.get("review", False)

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

    def check_regexp_ban(self, file):
        try:
            file_content = codecs.open(file, encoding='utf-8').read()
        except UnicodeError as e:
            raise RuntimeError("File {} contains non-unicode characters".format(file)) from e

        for regexp in self.regexp_ban:
            if re.search(regexp, file_content, re.MULTILINE):
                raise RuntimeError("File {} contains banned regexp '{}'".format(file, regexp))

    def copy_sources(self, submit_root):
        def check_fn(file):
            self.check_regexp_ban(file)

        copy_sources(pathlib.Path(submit_root) / self.name, self.task_path, self.sources, check_fn)

    @abc.abstractmethod
    def grade(self, submit_root: pathlib.Path):
        pass

    def check(self):
        for regex in self.regexp_ban:
            re.compile(regex)

        for src in self.sources:
            if not self.task_path.glob(src):
                raise ValueError("Source file '{}' not found in {}".format(src, self.name))
