from .command_base import Command
from .execution import Execution
import logging

"""
Defines the generic Executor class, which is responsible for
running a given Command instance similarly across different
implementations. 
"""


class Executor(object):
    """
    Abstract and generic definition of a Command executor.
    """
    def __init__(self, **kwargs):
        self._logger = logging.getLogger(self.__class__.__module__)
        self.name = None

    @property
    def implementation(self):
        """
        This property must be defined in each concrete class that can be
        instantiated according to the implementation name.
        :return:
        """
        raise NotImplementedError

    def execute(self, command: Command) -> Execution:
        """
        Executes the given command differently based on
        concrete implementation of this generic Executor.
        An Execution instance will be returned and both
        pre and post execution handlers will be invoked
        on the given command.
        :param command:
        :return:
        """

        # Call pre-execution hooks
        command.on_pre_execution(self)

        # Delegate execution to concrete Executor
        self._logger.debug("Executing command with [%s] - %s" % (self.__class__.__name__, command.args))
        execution = self._execute(command)

        # If command is a not a daemon, wait for it
        if not command.daemon and command.timeout > 0:
            execution.wait()

        # Processing post-execution hooks
        command.on_post_execution(execution)

        # returning execution
        return execution

    def _execute(self, command: Command) -> Execution:
        """
        Abstract method that must be implemented by child classes.
        :param command:
        :return:
        """
        raise NotImplementedError()


class ExecutorLocal(Executor):
    """
    Executes a given command locally.
    """

    implementation = "local"

    def __init__(self, name: str="ExecutorLocal", **kwargs):
        super(ExecutorLocal, self).__init__(**kwargs)
        self.name = name

    def _execute(self, command):
        return Execution(command, self)
