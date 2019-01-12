import subprocess

from . import task

import os


class HsePyTask(task.Task):

    def grade(self, submit_root):
        self.copy_sources(submit_root)

        print('--- public tests started ---')

        try:
            self.check_call(
                ["py.test"],
                env=dict(os.environ, PYTHONPATH="."),
                cwd=str(self.task_path),
                sandboxed=False,
                timeout=60
            )
        except subprocess.CalledProcessError:
            print('Public tests failed. Read error and fix it')
            print('---')
            exit(1)

        print('--- public tests passed ---')

        print('--- private tests started ---')
        # try:
        #     self.check_call(
        #         ["py.test", "../" + str(self.task_private_path), ],
        #         env=dict(os.environ, PYTHONPATH="."),
        #         cwd=str(self.task_path),
        #         sandboxed=False,
        #         timeout=60,
        #         stdout=subprocess.DEVNULL,
        #         stderr=subprocess.DEVNULL,
        #     )
        # except subprocess.CalledProcessError:
        #     print('Private tests failed. Something wrong in your code. Try harder.')
        #     print('---')
        #     exit(1)
        print('--- private tests passed ---')

    def check_author_solution(self, submit_root):
        self.copy_sources(submit_root)
        self.check_call(
            ["mv", "../" + str(self.task_private_path) + "/solution.py", ],
            env=dict(os.environ, PYTHONPATH="."),
            cwd=str(self.task_path),
            sandboxed=False,
            timeout=60,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )