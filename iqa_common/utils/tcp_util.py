#!/usr/bin/env python
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
Provides utility classes and methods to deal with TCP communication.
"""
import socket
import logging


class TcpUtil(object):
    """
    TCP Utility class.
    """

    @staticmethod
    def is_tcp_port_available(port, host="0.0.0.0"):
        """
        Returns True if a given port is accessibly on the specified host.
        :param port:
        :param host:
        :return:
        """
        test_port = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            test_port.connect((host, port))
            test_port.close()
            return True
        except Exception:
            logging.getLogger(__name__).debug('%s:%s is_tcp_port_available failed' % (host, port), exc_info=1)
            return False
