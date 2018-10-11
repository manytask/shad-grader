from . import task


class OsTask(task.Task):
    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)

        self.asm = self.config.get("asm", False)
        self.test_sh = self.config.get("test.sh", False)

    def grade(self, submit_root):
        self.copy_sources(submit_root)

        if self.asm:
            self.check_call(["make"],
                            cwd=str(self.root / self.name),
                            sandboxed=True,
                            timeout=60)
        elif self.test_sh:
            self.check_call(["../private/{}/test.sh".format(self.name)],
                            cwd=str(self.root / self.name),
                            timeout=60)
        else:
            raise ValueError("Unknown task type")
