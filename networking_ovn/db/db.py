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

from networking_ovn.common import acl
from networking_ovn.common import constants as ovn_const
from networking_ovn.db import models

import six


def port_ip_change(operation, data):
    if operation == ovn_const.ACTION_CREATE:
        old_port = {}
        new_port = data
    elif operation == ovn_const.ACTION_DELETE:
        old_port = data
        new_port = {}
    else:  # update
        old_port = data['original']
        new_port = data['current']

    new_ips = set()
    for ips in six.itervalues(acl.acl_port_ips(new_port)):
        new_ips |= set(ips)
    old_ips = set()
    for ips in six.itervalues(acl.acl_port_ips(old_port)):
        old_ips |= set(ips)
    added_ips = new_ips - old_ips
    deleted_ips = old_ips - new_ips
    added_to_sgs = set(new_port.get('security_groups', []))
    deleted_from_sgs = set(old_port.get('security_groups', []))

    return added_ips, deleted_ips, added_to_sgs, deleted_from_sgs


def has_indirect_dependency(session, row, timeout, now):
    """Check if there are indirectly depended updates pending.

    :return:
        True - if there are depended updates pending.
        False - if there are no dependencies

    """
    if row.object_type == ovn_const.OBJ_TYPE_PORT:
        # If there are IP changes, there could be conflicting updates for
        # address-set. See details in bug #1611852.
        # Here we make sure addition of IP(s) is not executed until pending
        # deletions of same IP(s) on same security-group(s) are completed.
        added_ips, _, added_to_sgs, _ = port_ip_change(row.operation, row.data)
        if added_ips and added_to_sgs:
            with session.begin(subtransactions=True):
                rows = session.query(models.OvnTaskQueue).filter(
                    or_(models.OvnTaskQueue.state == ovn_const.PENDING,
                        models.OvnTaskQueue.state == ovn_const.PROCESSING),
                    models.OvnTaskQueue.object_type == ovn_const.OBJ_TYPE_PORT,
                    models.OvnTaskQueue.created_at >
                    now - datetime.timedelta(seconds=timeout),
                    models.OvnTaskQueue.created_at < row.created_at).all()
                for r in rows:
                    _, deleted_ips, _, deleted_from_sgs = port_ip_change(
                        r.operation, r.data)
                    if (deleted_ips & added_ips) and (
                        deleted_from_sgs & added_to_sgs):
                        return True

    else:
        # TODO(zhouhan): add dependency check for other object types
        pass

    return False


def process_req_if_ready(session, req_uuid, obj_type, obj_uuid, timeout):
    with session.begin():
        now = session.execute(func.now()).scalar()
        row = session.query(models.OvnTaskQueue).filter(
            or_(models.OvnTaskQueue.state == ovn_const.PENDING,
                models.OvnTaskQueue.state == ovn_const.PROCESSING),
            models.OvnTaskQueue.object_uuid == obj_uuid).filter(
            or_(models.OvnTaskQueue.created_at >
                now - datetime.timedelta(seconds=timeout),
                models.OvnTaskQueue.req_uuid == req_uuid)).order_by(
            asc(models.OvnTaskQueue.created_at)).with_for_update(
        ).first()
        if row and row.req_uuid == req_uuid:
            if not has_indirect_dependency(session, row, timeout, now):
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
