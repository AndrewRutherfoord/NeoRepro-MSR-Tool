"""Added 'started' status

Revision ID: 7ac124de6ffe
Revises: 9f9a6f0e5ac2
Create Date: 2024-06-19 19:14:54.171176

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
import sqlalchemy_utils



# revision identifiers, used by Alembic.
revision: str = '7ac124de6ffe'
down_revision: Union[str, None] = '9f9a6f0e5ac2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
