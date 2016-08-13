#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#

from networking_ovn.common import config
import networking_ovn.common.constants as ovn_consts
from networking_ovn.ml2.mech_driver import OVNMechanismDriver
from networking_ovn.tests.functional import base
from threading import Thread
from time import sleep

NAME_DELAYED = 'delayed'
NAME_NOT_DELAYED = "not_delayed"
SLEEP_IN_POSTCOMMIT = 2
SLEEP_BEFORE_SECOND_REQ = 0.5
OVERRIDE_TASK_QUEUE_TIMEOUT = 3


class OVNMechanismDriverTest(OVNMechanismDriver):
    def update_port_postcommit(self, context):
        port = context.current
        if port['name'] == NAME_DELAYED:
            sleep(SLEEP_IN_POSTCOMMIT)
        super(OVNMechanismDriverTest, self).update_port_postcommit(context)


class TestMl2Race(base.TestOVNFunctionalBase):
    def setUp(self):
        config.cfg.CONF.set_override('task_queue_timeout',
                                     OVERRIDE_TASK_QUEUE_TIMEOUT, group='ovn')
        super(TestMl2Race, self).setUp(ovn_mech_driver="ovn-func-test")

    def tearDown(self):
        super(TestMl2Race, self).tearDown()

    def test_port_update_race(self):
        with self.network() as n:
            with self.subnet(n):
                res = self._create_port(self.fmt, n['network']['id'])
                port_id = self.deserialize(self.fmt, res)['port']['id']

                def update_port(name=None):
                    pnew = {'port': {}}
                    pnew['port']['name'] = name
                    req = self.new_update_request('ports', pnew, port_id)
                    req.get_response(self.api)

                t1 = Thread(target=update_port, args=(NAME_DELAYED,))
                t1.start()

                # Sleep before the second request to make sure neutron
                # db updated by the first request already
                sleep(SLEEP_BEFORE_SECOND_REQ)

                t2 = Thread(target=update_port, args=(NAME_NOT_DELAYED,))
                t2.start()

                t1.join()
                t2.join()

                res = self._list_ports(self.fmt)
                port_db = self.deserialize(self.fmt, res)['ports'][0]

                ovn_external_ids = self.mech_driver._nb_ovn._tables[
                    'Logical_Switch_Port'].rows.values()[0].external_ids
                self.assertEqual(port_db['name'],
                                 ovn_external_ids[
                                     ovn_consts.OVN_PORT_NAME_EXT_ID_KEY])
