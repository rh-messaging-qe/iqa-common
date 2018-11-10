import subprocess
import tempfile
import logging

from .command_base import Command
from ..utils.process import Process
from ..utils.timeout import TimeoutCallback

"""
Defines the representation of a command Execution that is generated
by the Executor implementations when a command is executed.  
"""


class Execution(Process):
    """
    The process that has been started by an Executor instance.
    It wraps the command that was triggered as well as the executor
    who generated the Execution instance.
    """
    def __init__(self, command: Command, executor, modified_args: list=[], env=None):
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

        self.timed_out = False
        self.interrupted = False

        # Adjust time out settings if provided
        if command.timeout > 0:
            self._timeout = TimeoutCallback(command.timeout, self.on_timeout)

        # Avoids executors from modifying the command
        args = self.command.args
        if modified_args:
            args = modified_args

        logging.debug('Executing: %s' % args)
        super(Execution, self).__init__(args, stdout=self.fh_stdout, stderr=self.fh_stderr, env=env)

    def wait(self):
        """
        Wraps the Popen wait method by cancelling the internal timer
        once process completes (or is interrupted).
        :return:
        """
        super(Execution, self).wait()
        self.cancel_timer()

    def on_timeout(self):
        """
        This method is called internally by the TimeoutCallback in case
        the execution times out. It will notify the command instance
        that it has timed out.
        :return:
        """
        if not self.is_running():
            return

        self._logger.debug("Execution timed out after %d - PID: %s - CMD: %s"
                           % (self.command.timeout, self.pid, self.args))
        self.terminate()
        self.timed_out = True
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

        self._logger.debug("Execution interrupted - PID: %s - CMD: %s"
                           % (self.pid, self.args))
        self.terminate()
        self.interrupted = True
        self.cancel_timer()
        self.command.on_interrupt(self)

    def read_stdout(self, lines: bool=False):
        """
        Returns a string with the whole STDOUT content if the original
        command has stdout property defined as True. Otherwise
        None will be returned.
        :param lines: whether to return stdout as a list of lines
        :type lines: bool
        :return: Stdout content as str if lines is False, or as a list
        """
        if not self.command.stdout or self.fh_stdout.closed:
            return None

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
        if not self.command.stderr or self.fh_stderr.closed:
            return None

        self.fh_stderr.seek(0)
        if lines:
            return self.fh_stderr.readlines()
        return self.fh_stderr.read()

    def cancel_timer(self):
        """
        Cancels the TimeoutCallback handler used internally.
        :return:
        """
        if self._timeout is not None:
            self._timeout.interrupt()
