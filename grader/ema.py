from . import task


class EmaTask(task.Task):
    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)

    def grade(self, submit_root):
        self.copy_sources(submit_root)

        self.check_call(["../private/{}/test.sh".format(self.name)],
                        cwd=str(self.root / self.name),
                        timeout=1800)
