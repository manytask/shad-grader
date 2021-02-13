import os
import pwd
import grp
import sys
import resource
import subprocess
import traceback
import contextlib


ENV_WHITELIST = ["PATH", "GOCACHE"]
TIMEOUT_SECONDS = 60


def drop_privileges():
    uid = pwd.getpwnam("nobody").pw_uid
    try:
        gid = grp.getgrnam("nobody").gr_gid
    except:
        gid = grp.getgrnam("nogroup").gr_gid
    os.setgroups([])
    os.setresgid(gid, gid, gid)
    os.setresuid(uid, uid, uid)


def clean_env():
    env = os.environ.copy()
    os.environ.clear()
    for variable in ENV_WHITELIST:
        os.environ[variable] = env[variable]


def setup_sandbox():
    try:
        drop_privileges()
        clean_env()
    except:
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        raise


def chmod(path):
    os.chmod(path, 0o777)


def check_call(cmd, **kwargs):
    if "timeout" not in kwargs:
        kwargs["timeout"] = TIMEOUT_SECONDS
        
    result = subprocess.run(cmd, close_fds=False, preexec_fn=setup_sandbox, **kwargs)
    result.check_returncode()
