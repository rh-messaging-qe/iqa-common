import subprocess
import tempfile
import logging
import threading
import abc
from typing import IO

from .command_base import Command
from ..utils.process import Process
from ..utils.timeout import TimeoutCallback

"""
Defines the representation of a command Execution that is generated
by the Executor implementations when a command is executed.  
"""
# Logger
logger = logging.getLogger(__name__)


class ExecutionException(Exception):
    """
    Exception thrown if a given Execution instance could be created
    """
    pass


class Execution(abc.ABC):
    """
    Represents the execution of a process that has been started by an Executor instance.
    It wraps the command that was triggered as well as the executor
    who generated the Execution instance.
    """
    def __init__(self, command: Command, executor, modified_args: list=None, env=None):
        """
        Instance is initialized with the command that was effectively
        executed and the Executor instance that produced this new object.
        :param command:
        :param executor:
        :param modified_args:
        :param env:
        """
        self.command = command
        self.executor = executor
        self.env = env

        # Flags to control whether execution timed out or was interrupted by user
        self.timed_out = False
        self.interrupted = False
        self.failure = False

        # Adjust time out settings if provided
        self._timeout = None
        if command.timeout and command.timeout > 0:
            self._timeout = TimeoutCallback(command.timeout, self._on_timeout)

        # Avoids executors from modifying the command
        self.args = self.command.args
        if modified_args:
            self.args = modified_args

        logger.debug('Executing: %s' % self.args)
        self._run()

    @abc.abstractmethod
    def _run(self):
        """
        Executes the command with different execution strategies (subprocess or others).
        :return:
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def wait(self):
        """
        Waits for command execution to complete.
        :return:
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def is_running(self) -> bool:
        """
        Returns True if execution is still running and False otherwise.
        :return:
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def completed_successfully(self) -> bool:
        """
        Returns True if execution is done and no errors observed or False otherwise.
        :return:
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def on_timeout(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def terminate(self):
        """
        Terminates the execution.
        :return:
        """
        raise NotImplementedError

    @abc.abstractmethod
    def read_stdout(self, lines: bool=False):
        """
        Returns a string with the whole STDOUT content if the original
        command has stdout property defined as True. Otherwise
        None will be returned.
        :param lines: whether to return stdout as a list of lines
        :type lines: bool
        :return: Stdout content as str if lines is False, or as a list
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def read_stderr(self, lines: bool=False):
        """
        Returns a string with the whole STDERR content if the original
        command has stderr property defined as True. Otherwise
        None will be returned.
        :param lines: whether to return stdout as a list of lines
        :type lines: bool
        :return: Stdout content as str if lines is False, or as a list
       """
        raise NotImplementedError()

    def _on_timeout(self):
        """
        This method is called internally by the TimeoutCallback in case
        the execution times out. It will notify concrete Execution and the
        Command instance that it has timed out.
        :return:
        """
        if self.is_running():
            self.timed_out = True
            self.on_timeout()
            self.command.on_timeout(self)

    def interrupt(self):
        """
        Interrupts a running process (if it is still running).
        Once interrupted, if a timer is active, it will be cancelled and
        the command instance will be notified of the interruption.
        :return:
        """
        if not self.is_running():
            return

        logger.debug("Interrupting execution")
        self.terminate()
        self.interrupted = True
        self.cancel_timer()
        self.command.on_interrupt(self)

    def cancel_timer(self):
        """
        Cancels the TimeoutCallback handler used internally.
        :return:
        """
        if self._timeout is not None:
            self._timeout.interrupt()


class ExecutionProcess(Execution):
    """
    Represents a command Execution that is performed by a Process (subprocess.Popen child).
    Executors that want to run a given command as a Process must use this Execution strategy.
    """

    def __init__(self, command: Command, executor, modified_args: list=None, env=None):
        """
        Instance is initialized with the command that was effectively
        executed and the Executor instance that produced this new object.
        :param command:
        :param executor:
        :param modified_args:
        :param env:
        """

        # Prepare stdout handler
        if command.stdout:
            self.fh_stdout = tempfile.TemporaryFile(mode="w+t", encoding=command.encoding)
        else:
            self.fh_stdout = subprocess.DEVNULL

        # Prepare stderr handler
        if command.stderr:
            self.fh_stderr = tempfile.TemporaryFile(mode="w+t", encoding=command.encoding)
        else:
            self.fh_stderr = subprocess.DEVNULL

        # Subprocess instance
        self._process: Process = None

        # Initializes the super class which will invoke the run method
        super(ExecutionProcess, self).__init__(command=command, executor=executor, modified_args=modified_args, env=env)

    def _run(self):
        """
        Executes the given command in a separate Thread using a Process (child of subprocess.Popen)
        and monitoring it, till it's done running. When done (or failed), if a timeout was defined,
        the TimeoutCallback will be canceled.
        :return:
        """
        def start_process():
            """
            Trigger method for separate thread that will effectively run the command.
            :return:
            """
            try:
                self._process = Process(self.args, stdout=self.fh_stdout, stderr=self.fh_stderr, env=self.env)
            except Exception as ex:
                logger.error("Error executing process", ex)
                self.cancel_timer()
                self.failure = True
                raise ExecutionException(ex)

            # do nothing while process still running
            while self._process.poll() is None:
                pass

            logger.debug("Process has terminated")
            self.cancel_timer()

        # Execute process in a thread, so we can interrupt the timeout callback
        # when process completes without blocking calling thread.
        threading.Thread(target=start_process).start()
        while not self._process and not self.failure:
            pass

    def is_running(self):
        """
        Returns true if process is still running.
        :return:
        """
        return self._process.is_running()

    def completed_successfully(self):
        """
        Returns true if process has ended and return code was 0.
        :return:
        """
        return self._process.completed_successfully()

    def terminate(self):
        """
        Forces a given Process to terminate.
        :return:
        """
        logger.debug("Terminating execution - PID: %s - CMD: %s" %
                     (self._process.pid, self.args))
        self._process.terminate()

    def wait(self):
        """
        Wraps the Popen wait method till process exits or times out.
        :return:
        """
        # Wait till process completes or timeout (notified by TimeoutCallback
        self._process.wait()

    def on_timeout(self):
        """
        This method is called internally by the TimeoutCallback in case
        the execution times out. It will notify the command instance
        that it has timed out.
        :return:
        """
        logger.debug("Execution timed out after %d - PID: %s - CMD: %s"
                     % (self.command.timeout, self._process.pid, self.args))
        self.terminate()

    def read_stdout(self, lines: bool=False):
        """
        Returns a string with the whole STDOUT content if the original
        command has stdout property defined as True. Otherwise
        None will be returned.
        :param lines: whether to return stdout as a list of lines
        :type lines: bool
        :return: Stdout content as str if lines is False, or as a list
        """
        if self.fh_stdout == subprocess.DEVNULL:
            return None

        # Type hinting
        self.fh_stdout: IO
        self.fh_stdout.seek(0)

        if lines:
            return self.fh_stdout.readlines()

        return self.fh_stdout.read()

    def read_stderr(self, lines: bool=False):
        """
        Returns a string with the whole STDERR content if the original
        command has stderr property defined as True. Otherwise
        None will be returned.
        :param lines: whether to return stdout as a list of lines
        :type lines: bool
        :return: Stdout content as str if lines is False, or as a list
       """
        if self.fh_stderr == subprocess.DEVNULL:
            return None

        # Type hinting
        self.fh_stderr: IO
        self.fh_stderr.seek(0)

        if lines:
            return self.fh_stderr.readlines()

        return self.fh_stderr.read()
