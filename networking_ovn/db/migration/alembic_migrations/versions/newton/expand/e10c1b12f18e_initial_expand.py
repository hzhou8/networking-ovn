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

"""initial expand

Revision ID: e10c1b12f18e
Revises: 19a647f25c34
Create Date: 2016-08-25 22:41:23.621937

"""

from neutron.db.migration import cli


# revision identifiers, used by Alembic.
revision = 'e10c1b12f18e'
down_revision = '19a647f25c34'
branch_labels = (cli.EXPAND_BRANCH,)


def upgrade():
    pass
