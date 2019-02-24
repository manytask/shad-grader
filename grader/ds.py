from . import task


class DsTask(task.Task):
    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)

    def grade(self, submit_root):
        self.copy_sources(submit_root)

        self.check_call(["go", "test",
                         "-c", "test.run",
                         "-tags", "private"
                         "gitlab.com/slon/shad-ds/" + self.name])

        self.check_call(["./test.run", "-v"], sandboxed=True, timeout=60)
