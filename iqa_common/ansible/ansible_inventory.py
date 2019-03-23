from ansible.inventory.host import Host
from ansible.inventory.manager import InventoryManager
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.template import Templar
import logging


class AnsibleVirtualComponent(object):

    def __init__(self, name: str, type: str, implementation: str, members: list, **kwargs):
        self.name = name
        self.type = type
        self.implementation = implementation
        self.members = members
        self.kwargs = kwargs
        self.component = None  # real component, once created and populated with member


class AnsibleInventory(object):

    virt_component = 'virtual_component'

    def __init__(self, inventory: str=None, extra_vars: dict=None):
        self._logger = logging.getLogger(self.__class__.__module__)
        self.inventory = inventory
        self.loader = DataLoader()
        self._logger.info('Loading inventory: %s' % inventory)
        self._logger.debug('Extra variables: %s' % extra_vars)
        self.inv_mgr = InventoryManager(loader=self.loader, sources=self.inventory)
        self.var_mgr = VariableManager(loader=self.loader, inventory=self.inv_mgr)
        self.var_mgr.extra_vars = extra_vars or dict()

    def get_hosts_containing(self, var: str=None) -> list:
        hosts = []

        for host in self.inv_mgr.get_hosts():
            # If no specific var provided, then add it to the list
            if not var:
                hosts.append(host)
                continue

            # If var is provided and not part of host vars, ignore it
            host_vars = self.var_mgr.get_vars(host=host)
            if var not in host_vars:
                continue

            # Var has been found so adding it
            hosts.append(host)

        return hosts

    def get_host_vars(self, host: Host):
        data = self.var_mgr.get_vars(host=host)
        templar = Templar(variables=data, loader=self.loader)
        return templar.template(data, fail_on_undefined=False)

    def get_virtual_components(self) -> list:
        virtual_components = []
        for group in self.inv_mgr.get_groups_dict():
            group_vars = self.inv_mgr.groups[group].get_vars()

            if self.virt_component in group_vars:
                vcmp_type = group_vars.get(self.virt_component)
                group_vars.pop('virtual_component')
                vcmp_impl = group_vars.get('implementation')
                group_vars.pop('implementation')
                hosts = self.inv_mgr.groups[group].get_hosts()
                vcmp = AnsibleVirtualComponent(name=group,
                                               type=vcmp_type,
                                               implementation=vcmp_impl,
                                               members=hosts,
                                               **group_vars)

                virtual_components.append(vcmp)
        return virtual_components
