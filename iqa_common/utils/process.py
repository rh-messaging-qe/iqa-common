"""
This module brings an abstraction of a process execution in a way
that all concrete processes will be tracked and forcibly terminated
in case the running program completes and process is still running.
It waits for a pre-defined amount of time * attempts, before killing
the running process.
"""
import time
import subprocess
import atexit
import traceback
import logging


class Process(subprocess.Popen):
    """
    Abstract Popen wrapper that ensures all opened processes will be
    closed when code finishes.
    """

    MAX_ATTEMPTS = 3
    ATTEMPT_DELAY = 1

    def __init__(self, args, name=None, **kwargs):
        self._logger = logging.getLogger(self.__class__.__module__)
        self.name = name
        atexit.register(self.teardown)
        kwargs.setdefault('bufsize', 1)
        kwargs.setdefault('universal_newlines', True)
        try:
            super(Process, self).__init__(args, **kwargs)
        except Exception as ex:
            self._logger.warning("Unable to execute command: %s" % args, exc_info=1)
            # traceback.print_tb(tb=ex)

    def is_running(self):
        """
        Returns true if process is still running.
        :return:
        """
        return self.poll() is None

    def completed_successfully(self):
        """
        Returns true if process has ended and returncode was 0.
        :return:
        """
        return not self.is_running() and self.returncode == 0

    def teardown(self):
        """
        Wait for process to exit or kill it after a MAX_ATTEMPTS.
        :return:
        """
        # Delay till max attempts reached
        attempt = 0
        while self.is_running() and attempt < self.MAX_ATTEMPTS:
            attempt += 1
            time.sleep(Process.ATTEMPT_DELAY)

        # If not terminated after all attempts, kill process
        if self.returncode is None:
            self._logger.debug("Process still running [pid: %s] - %s - Sending a kill signal." % (self.pid, self.args))
            self.kill()
