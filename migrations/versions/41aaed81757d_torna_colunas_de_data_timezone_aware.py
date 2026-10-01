"""torna colunas de data timezone-aware

Revision ID: 41aaed81757d
Revises: eeaf9ac52681
Create Date: 2026-09-28 20:19:33.848230

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '41aaed81757d'
down_revision = 'eeaf9ac52681'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('link', schema=None) as batch_op:
                batch_op.alter_column(
                    'created_at',
                    existing_type=sa.DateTime(),
                    type_=sa.DateTime(timezone=True),
                    existing_nullable=True,
                    postgresql_using="created_at AT TIME ZONE 'UTC'",
                )
    
    with op.batch_alter_table('click', schema=None) as batch_op:
                batch_op.alter_column(
                    'clicked_at',
                    existing_type=sa.DateTime(),
                    type_=sa.DateTime(timezone=True),
                    existing_nullable=True,
                    postgresql_using="clicked_at AT TIME ZONE 'UTC'",
                )
    
    with op.batch_alter_table('user', schema=None) as batch_op:
                batch_op.alter_column(
                    'created_at',
                    existing_type=sa.DateTime(),
                    type_=sa.DateTime(timezone=True),
                    existing_nullable=True,
                    postgresql_using="created_at AT TIME ZONE 'UTC'",
                )


def downgrade():
    with op.batch_alter_table('link', schema=None) as batch_op:
            batch_op.alter_column(
                'created_at',
               existing_type=sa.DateTime(timezone=True),
               type_=sa.DateTime(),
               existing_nullable=True,
            )
    
    with op.batch_alter_table('click', schema=None) as batch_op:
            batch_op.alter_column(
                'clicked_at',
               existing_type=sa.DateTime(timezone=True),
               type_=sa.DateTime(),
               existing_nullable=True,
            )
    
    with op.batch_alter_table('user', schema=None) as batch_op:
            batch_op.alter_column(
                'created_at',
               existing_type=sa.DateTime(timezone=True),
               type_=sa.DateTime(),
               existing_nullable=True,
            )