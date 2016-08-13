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
#

import datetime

from sqlalchemy import asc
from sqlalchemy import func
from sqlalchemy import or_

from networking_ovn.common import constants as ovn_const
from networking_ovn.db import models


def process_req_if_ready(session, req_uuid, obj_type, obj_uuid, timeout):
    with session.begin():
        now = session.execute(func.now()).scalar()
        row = session.query(models.OvnTaskQueue).filter(
            or_(models.OvnTaskQueue.state == ovn_const.PENDING,
                models.OvnTaskQueue.state == ovn_const.PROCESSING),
            models.OvnTaskQueue.object_uuid == obj_uuid,
            or_(models.OvnTaskQueue.created_at >
                now - datetime.timedelta(seconds=timeout),
                models.OvnTaskQueue.req_uuid == req_uuid)).order_by(
            asc(models.OvnTaskQueue.created_at)).with_for_update(
        ).first()
        if row and row.req_uuid == req_uuid:
            update_db_row_state(session, row, ovn_const.PROCESSING)
            return row
    return None


def update_db_row_state(session, row, state):
    row.state = state
    session.merge(row)
    session.flush()


def delete_row(session, row=None, row_id=None):
    if row_id:
        row = session.query(models.OvnTaskQueue).filter_by(
            id=row_id).one()
    if row:
        session.delete(row)
        session.flush()


def create_pending_row(session, req_uuid, object_type, object_uuid,
                       operation, data):
    row = models.OvnTaskQueue(req_uuid=req_uuid,
                              object_type=object_type,
                              object_uuid=object_uuid,
                              operation=operation,
                              data=data,
                              created_at=func.now(),
                              state=ovn_const.PENDING)
    session.add(row)
    session.flush()
