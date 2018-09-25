from .command_ansible import CommandAnsible
from .command_base import Command
from .executor_base import Executor
from .execution import Execution

"""
Executor implementation that uses the "ansible" CLI to
run the given Command instance on the target host.
"""


class ExecutorAnsible(Executor):
    """
    Executes the given command using Ansible.
    """

    implementation = 'ansible'

    def __init__(self, ansible_host: str=None, inventory: str=None, ansible_user: str="root", module: str="raw",
                 name: str="ExecutorAnsible", **kwargs):
        """
        Initializes the ExecutorAnsible instance based on provided arguments.
        When an inventory is provided, the 'ansible_host' can be an ip address or any
        ansible name (machine or group) within the inventory. If an inventory is not
        provided, then 'ansible_host' must be a valid IP Address or Hostname.
        :param ansible_host:
        :param inventory:
        :param ansible_user:
        :param module:
        :param name:
        :param kwargs:
        """
        self.inventory = kwargs.get('inventory_file', inventory)
        self.ansible_host = kwargs.get('ansible_host', ansible_host) if not self.inventory else kwargs.get('inventory_hostname', ansible_host)
        self.ansible_user = kwargs.get('ansible_user', ansible_user)
        self.module = kwargs.get('executor_module', module)
        self.name = kwargs.get('executor_name', name)

    def _execute(self, command: Command):

        ansible_args = ['ansible', '-u', self.ansible_user]

        if self.inventory is not None:
            ansible_args += ['-i', self.inventory]
        else:
            ansible_args += ['-i', '%s,' % self.ansible_host]

        # Executing using the "raw" module
        module = self.module

        # If given command is an instance of CommandAnsible
        # the module is read from it
        if isinstance(command, CommandAnsible):
            module = command.ansible_module
        ansible_args += ['-m', module, '-a']

        # Appending command as a literal string
        ansible_args.append('%s' % ' '.join(command.args))

        # Host where command will be executed
        ansible_args.append(self.ansible_host)

        # Set new args
        return Execution(command, self, modified_args=ansible_args)
