import os
import sys

def test_python_version():
    """
    WHAT IS BEING TESTED: Python version is 3.12.x.
    WHY IT MATTERS: Ensures reproducibility of the environment execution across different machines and container builds.
    WHAT FAILURE WOULD LOOK LIKE: Fails if the python executable is not 3.12.
    """
    assert sys.version_info.major == 3, "Python major version must be 3"
    assert sys.version_info.minor == 12, f"Python minor version must be 12, got {sys.version_info.minor}"

def test_non_root_user_in_container():
    """
    WHAT IS BEING TESTED: Process is not running as root (UID 0) inside Linux environments (like our Docker container).
    WHY IT MATTERS: Security boundary. Running as root inside a container violates the governance rules against unsafe execution. The container must use micro1user.
    WHAT FAILURE WOULD LOOK LIKE: Fails if UID is 0. No silent exceptions are allowed to bypass this check.
    """
    # This test assumes it's running in the container.
    assert os.name == 'posix', "Test must run in POSIX environment (the container)"
    import pwd
    euid = os.geteuid()
    assert euid != 0, "Security violation: running as root (UID 0)"
    pw_name = pwd.getpwuid(euid).pw_name
    assert pw_name == "micro1user", f"Expected user micro1user, got {pw_name}"
