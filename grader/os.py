from . import task


class OsTask(task.Task):
    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)

    def grade(self, submit_root):
        pass
