from .command_base import *
from .command_ansible import *
from .command_container import *
from .execution import *
from .execution_kubernetes import *
from .executor_base import *
from .executor_ansible import *
from .executor_ssh import *
from .executor_container import *


class ExecutorFactory(object):
    """
    Loops through all implementations of the Executor class
    and returns an instance of the executor initialized from kwargs.
    """

    @staticmethod
    def create_executor(exec_impl: str= 'ansible', **kwargs):

        for exec_class in Executor.__subclasses__():
            if exec_class.implementation != exec_impl:
                continue

            return exec_class(**kwargs)

        raise ValueError('Invalid Executor implementation given: %s' % exec_impl)
