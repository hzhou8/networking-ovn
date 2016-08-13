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

import networking_ovn.common.constants as const
from neutron_lib.db import model_base
import sqlalchemy as sa


class OvnTaskQueue(model_base.BASEV2, model_base.HasId):
    __tablename__ = 'ovntaskqueue'

    req_uuid = sa.Column(sa.String(36), nullable=False)
    object_type = sa.Column(sa.String(36), nullable=False)
    object_uuid = sa.Column(sa.String(36), nullable=False)
    operation = sa.Column(sa.String(36), nullable=False)
    data = sa.Column(sa.PickleType, nullable=True)
    state = sa.Column(sa.Enum(const.PENDING, const.FAILED,
                              const.PROCESSING, const.COMPLETED),
                      nullable=False, default=const.PENDING)
    created_at = sa.Column(sa.TIMESTAMP, server_default=sa.func.now(),
                           nullable=False)
