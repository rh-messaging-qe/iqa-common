#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License
#

"""
Utility classes to retrieve information from local docker environment.
"""
import os
import docker
import logging


class DockerUtil(object):
    """
    Utility class to interact with local docker environment, providing
    basic information on images and containers.
    """

    CONTAINER_STATUS_RUNNING = "running"
    CONTAINER_STATUS_EXITED = "exited"

    def __init__(self, **kwargs):
        self.docker_host = kwargs.get('docker_host', None)
        self._env = os.environ.copy()

        if self.docker_host:
            self._env['DOCKER_HOST'] = self.docker_host

        self._logger = logging.getLogger(__name__)
        self.cli = docker.from_env(environment=self._env)

    def get_container(self, name):
        """
        Returns the container instance for the given name.
        A docker.errors.NotFound exception is raised in case the given
        container does not exist.
        :param name:
        :return:
        """
        return self.cli.containers.get(name)

    def get_container_ip(self, name, network_name='bridge'):
        """
        Returns the IPAddress assigned to the given container name (on the given network).
        :param name:
        :param network_name:
        :return:
        """
        container = self.get_container(name)
        ip_addr = container.attrs['NetworkSettings']['Networks'][network_name]['IPAddress']
        self._logger.debug("Container: %s - IP Address: %s" % (name, ip_addr))
        return container.attrs['NetworkSettings']['Networks'][network_name]['IPAddress']

    def stop_container(self, name):
        """
        Stops a given container based on its name or id.
        :param self:
        :param name:
        :return:
        """
        container = self.get_container(name)
        container.stop()

    def start_container(self, name):
        """
        Starts the given container based on its name or id.
        :param self:
        :param name:
        :return:
        """
        container = self.get_container(name)
        container.start()
