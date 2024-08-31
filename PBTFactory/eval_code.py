# Error codes
NO_TESTS = "NO_TESTS"
NO_MUTANTS = "NO_MUTANTS"
NO_REPORT = "NO_REPORT"
TEST_ERROR = "TEST_ERROR"
ERROR_READING_REPORT = "ERROR_READING_REPORT"
TIMEOUT = "TIMEOUT"
NO_MUTANTS = "NO_MUTANTS"


import logging
import os
import re
import time
import typing

import docker


def remove_dup_lines(s):
    s = s.split("\n")
    s2 = []
    for i in s:
        if i not in s2[-1:]:
            s2.append(i)
    return "\n".join(s2)


def write_to_file(file_path, content, mode="a"):
    if not file_path:
        return

    with open(file_path, mode) as f:
        f.write(content)


class ContainerTimeoutError(Exception):
    pass


def wait_for_container(
    container: docker.models.containers.Container,
    timeout: int,
    timeout_msg="",
    log_file_path: typing.Optional[str] = None,
) -> typing.Tuple[int, str]:
    if log_file_path:
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

    start_time = time.time()
    timeouted = False
    try:
        while True:
            container.reload()
            if container.status != "running":
                break
            if time.time() - start_time > timeout:
                raise ContainerTimeoutError(
                    f"Container {container.id[:10]} timed out after {timeout} seconds"
                )
            write_to_file(
                log_file_path,
                container.logs().decode("utf-8"),
                "w",
            )
            time.sleep(5)
    except ContainerTimeoutError:
        container.stop()
        timeouted = True
        logging.warning(
            f"Container {container.id[:10]}, stopped due to timeout. {timeout_msg}"
        )
    except KeyboardInterrupt:
        container.stop()
        logging.warning(
            f"Container {container.id[:10]}, stopped due to KeyboardInterrupt"
        )
        raise
    except Exception as e:
        container.stop()
        logging.warning(f"Container {container.id[:10]}, stopped due to {e}")
        raise e

    exit_code = container.wait()["StatusCode"]
    logs = container.logs(stdout=True, stderr=False).decode("utf-8")
    logs_err = container.logs(stdout=False, stderr=True).decode("utf-8")
    if timeouted and not logs_err:
        logs_err = f"Timeout after {timeout} seconds"
    write_to_file(
        log_file_path,
        logs + "\nERROR:\n" + logs_err,
        "w",
    )
    container.remove()
    return exit_code, logs, logs_err, time.time() - start_time, timeouted


class DockerContainerConfig:
    imageid: str
    volumes: typing.Dict[str, typing.Dict[str, str]]
    environment: typing.List[str]
    command: str
    detach: bool
    working_dir: str

    def __init__(self, imageid, volumes, environment, command, detach, working_dir):
        self.imageid = imageid
        self.volumes = volumes
        self.environment = environment
        self.command = command
        self.detach = detach
        self.working_dir = working_dir


def create_docker_container(
    docer_config: DockerContainerConfig,
) -> docker.models.containers.Container:
    for k in docer_config.volumes:
        assert k.startswith("/"), f"Volume {k} must be absolute path. Got {k}"

    common_params = {
        "volumes": docer_config.volumes,
        "environment": docer_config.environment,
        "command": docer_config.command,
        "detach": docer_config.detach,
        "working_dir": docer_config.working_dir,
    }
    container = docker.from_env().containers.run(docer_config.imageid, **common_params)
    return container


def run_code(file_path, project_path=None, log_path=None, timeout_msg=""):
    if not file_path.startswith("/"):
        file_path = os.path.abspath(file_path)
    volumes = {file_path: {"bind": "/workdir/test_code.py", "mode": "ro"}}
    if project_path:
        if not project_path.startswith("/"):
            project_path = os.path.abspath(project_path)
        volumes[project_path] = {"bind": "/workdir/project", "mode": "ro"}

    docker_config = DockerContainerConfig(
        imageid="hypothesis_docker",
        volumes=volumes,
        environment=[f"PYTHONPATH=/workdir/project"],
        working_dir="/workdir",
        command="bash /usr/src/scripts/run_python_code.sh",
        detach=True,
    )
    container = create_docker_container(docker_config)
    exit_code, logs, logs_err, time_taken, timeouted = wait_for_container(
        container, 600, timeout_msg
    )

    write_to_file(
        os.path.join(log_path, "run_code.log"),
        file_path + "\n" + logs + "\n" + logs_err,
        "a",
    )

    return exit_code, remove_dup_lines(logs), remove_dup_lines(logs_err), time_taken


def run_pytest(file_path, project_path=None, log_path=None, timeout_msg=""):
    if not file_path.startswith("/"):
        file_path = os.path.abspath(file_path)
    volumes = {file_path: {"bind": "/workdir/test_code.py", "mode": "ro"}}
    if project_path:
        if not project_path.startswith("/"):
            project_path = os.path.abspath(project_path)
        volumes[project_path] = {"bind": "/workdir/project", "mode": "ro"}

    docker_config = DockerContainerConfig(
        imageid="hypothesis_docker",
        volumes=volumes,
        environment=[f"PYTHONPATH=/workdir/project"],
        working_dir="/workdir",
        command="bash /usr/src/scripts/run_test_code.sh",
        detach=True,
    )
    container = create_docker_container(docker_config)
    exit_code, logs, logs_err, time_taken, timeouted = wait_for_container(
        container, 60 * 20, timeout_msg
    )

    write_to_file(
        os.path.join(log_path, "run_pytest.log"),
        file_path + "\n" + logs + "\n" + logs_err,
        "a",
    )

    if exit_code != 0:
        error_part = re.search(
            r"=+ (ERRORS|FAILURES) .*?=+\n(.*?)\n=+", logs, re.DOTALL
        )
        if error_part:
            logs_err = error_part.group(2).strip()
        else:
            logs_err = logs

    return (
        exit_code,
        remove_dup_lines(logs),
        remove_dup_lines(logs_err),
        time_taken,
        timeouted,
    )


def eval_with_mutmut(
    path_to_tests,
    project_path,
    module_name,
    result_path,
    log_path=None,
    mut_line_start=0,
    mut_line_end=1000000,
    timeout_msg="",
):
    logging.info(
        f"eval_with_mutmut: {path_to_tests}, {project_path}, {module_name}, {result_path}, {log_path}, {mut_line_start}, {mut_line_end}, {timeout_msg}"
    )
    if not path_to_tests.startswith("/"):
        path_to_tests = os.path.abspath(path_to_tests)
    if not project_path.startswith("/"):
        project_path = os.path.abspath(project_path)
    if not result_path.startswith("/"):
        result_path = os.path.abspath(result_path)
    volumes = {
        path_to_tests: {"bind": "/workdir/tests", "mode": "ro"},
        result_path: {"bind": "/workdir/mutmut_report", "mode": "rw"},
    }
    if project_path:
        if not project_path.startswith("/"):
            project_path = os.path.abspath(project_path)
        volumes[project_path] = {"bind": "/workdir/project", "mode": "ro"}

    docker_config = DockerContainerConfig(
        imageid="hypothesis_docker",
        volumes=volumes,
        environment=[
            "PROJECT_ROOT=/workdir/project",
            f"module_name={module_name}",
            f"line_start={mut_line_start}",
            f"line_end={mut_line_end}",
            "PYTHONPATH=/usr/src/project",
        ],
        working_dir="/workdir",
        command="bash /workdir/run_mutmut.sh",
        detach=True,
    )
    container = create_docker_container(docker_config)
    exit_code, logs, logs_err, time_taken, timeouted = wait_for_container(
        container,
        60 * 60,  # 1 hour
        timeout_msg,
        os.path.join(log_path, "eval_with_mutmut.log"),
    )

    write_to_file(
        os.path.join(log_path, "eval_with_mutmut.log"), logs + "\n" + logs_err, "a"
    )

    return exit_code, logs, logs_err, time_taken, timeouted
