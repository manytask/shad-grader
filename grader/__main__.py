"""C++ Task Grader

Usage:
  grader

Options:
  -h --help    Show this message.
"""
import docopt
import requests
import time
import os
import subprocess
import pathlib

from .task import Task, TestFailed


def push_report(user_id, task, course_name, failed=False):
    if course_name.startswith("cpp"):
        url = "https://cpp.manytask.org/api/report"
    elif course_name.startswith("ds"):
        url = "https://ds.manytask.org/api/report"
    elif course_name.startswith("db"):
        url = "https://db.manytask.org/api/report"
    elif course_name.startswith("ema"):
        url = "https://ema.manytask.org/api/report"
    elif course_name.startswith("hse"):
        url = "https://hse-programming-intro.manytask.org/api/report"
    else:
        url = "https://os.manytask.org/api/report"

    # Do not expose token in logs.
    for _ in range(3):
        data = {
            "token": os.environ["TESTER_TOKEN"],
            "task": task,
            "user_id": user_id,
        }

        if failed:
            data["failed"] = 1

        rsp = requests.post(url, data=data)

        if rsp.status_code != 500 or failed:
            break
        else:
            time.sleep(1.0)

    rsp.raise_for_status()


def grade():
    task_name = os.environ["CI_COMMIT_REF_NAME"].split("/")[1]
    course_name = os.environ["CI_PROJECT_NAMESPACE"]
    submit_root = os.environ["CI_PROJECT_DIR"]
    user_id = os.environ["GITLAB_USER_ID"]

    task = Task.create(course_name, task_name, pathlib.Path("/opt/shad"))
    try:
        task.grade(submit_root)

        if task.review:
            return

        push_report(user_id, task_name, course_name)
    except TestFailed:
        push_report(user_id, task_name, course_name, failed=True)
        raise


def main():
    args = docopt.docopt(__doc__, version='C++ Task Grader 1.0')
    grade()


if __name__ == "__main__":
    main()
