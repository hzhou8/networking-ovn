#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import time

from oslo_log import log
from networking_ovn.db import db

LOG = log.getLogger(__name__)


class OvnTaskQueue(object):

    def __init__(self, retry_interval, timeout):
        self.retry_interval = retry_interval
        self.timeout = timeout

    def add_task(self, db_session, req_uuid, obj_type, obj_uuid,
                 operation, data):
        db.create_pending_row(db_session,
                              req_uuid,
                              obj_type,
                              obj_uuid,
                              operation,
                              data)

    def wait_task_ready(self, db_session, req_uuid, obj_type, obj_uuid):
        waited = 0
        while True:
            row = db.process_req_if_ready(db_session,
                                          req_uuid,
                                          obj_type,
                                          obj_uuid,
                                          self.timeout)
            if row:
                return row

            LOG.debug(_("Conflicting update pending for %s %s, "
                        "retry in %ss"),
                      obj_type,
                      obj_uuid,
                      self.retry_interval)
            waited += self.retry_interval
            if waited > self.timeout + self.retry_interval:
                raise Exception("Task queue internal error: "
                                "waited %s" % waited)
            time.sleep(self.retry_interval)

    def delete_task(self, db_session, row):
        db.delete_row(db_session, row=row)
