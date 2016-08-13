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

"""Add ovn task queue

Revision ID: c01a920585a6
Revises: e10c1b12f18e
Create Date: 2016-08-25 23:10:34.513335

"""

# revision identifiers, used by Alembic.
revision = 'c01a920585a6'
down_revision = 'e10c1b12f18e'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'ovntaskqueue',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('req_uuid', sa.String(length=36), nullable=False),
        sa.Column('object_type', sa.String(length=36), nullable=False),
        sa.Column('object_uuid', sa.String(length=36), nullable=False),
        sa.Column('operation', sa.String(length=36), nullable=False),
        sa.Column('data', sa.PickleType(), nullable=True),
        sa.Column('state',
                  sa.Enum('pending', 'failed', 'processing', 'completed'),
                  nullable=False, default='pending'),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.func.now(),
                  nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
