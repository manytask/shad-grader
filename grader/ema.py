from . import task


class EmaTask(task.Task):
    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)

    def grade(self, submit_root):
        self.copy_sources(submit_root)

        self.check_call(["../private/{}/test.sh".format(self.name)],
                        cwd=str(self.root / self.name),
                        timeout=10800)

        shutil.copytree("/tmp/artifacts_1", str(pathlib.Path(submit_root) / "artifacts_1"))
        shutil.copytree("/tmp/artifacts_2", str(pathlib.Path(submit_root) / "artifacts_2"))
        shutil.copytree("/tmp/artifacts_3", str(pathlib.Path(submit_root) / "artifacts_3"))
        shutil.copytree("/tmp/artifacts_4", str(pathlib.Path(submit_root) / "artifacts_4"))
        shutil.copytree("/tmp/artifacts_5", str(pathlib.Path(submit_root) / "artifacts_5"))
        shutil.copytree("/tmp/artifacts_6", str(pathlib.Path(submit_root) / "artifacts_6"))
        shutil.copytree("/tmp/artifacts_7", str(pathlib.Path(submit_root) / "artifacts_7"))
