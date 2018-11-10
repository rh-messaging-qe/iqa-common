from iqa_common.executor import CommandContainer
from .command_base import Command
from .executor_base import Executor
from .execution import Execution

"""
Executor instance that runs a given Command instance using
Docker CLI against a pre-defined container (by name or id).
"""


class ExecutorContainer(Executor):
    """
    Executor that runs Command instances in a Docker container.
    """

    implementation = 'docker'

    def __init__(self, container_name: str=None, container_user: str=None, name: str="ExecutorContainer", **kwargs):
        super(ExecutorContainer, self).__init__()
        self.container_name = kwargs.get('inventory_hostname', container_name)
        self.name = kwargs.get('executor_name', name)
        self.user = kwargs.get('executor_docker_user', container_user)
        self.docker_host = kwargs.get('executor_docker_host')

    def _execute(self, command: Command):

        docker_args = ['docker']

        if isinstance(command, CommandContainer):
            # Logging docker command to use
            self._logger.debug("Using docker command: %s" % command.docker_command)
            docker_args.append(command.docker_command)
        else:
            docker_args.append('exec')

        if self.user:
            docker_args += ['-u', self.user]

        docker_args.append(self.container_name)
        docker_args += command.args

        # define environment when docker_host provided
        env = dict()
        if self.docker_host:
            env['DOCKER_HOST'] = self.docker_host

        # Set new args
        return Execution(command, self, modified_args=docker_args, env=env)
