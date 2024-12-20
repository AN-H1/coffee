"""empty message

Revision ID: 62ae33eb61d2
Revises: 9ae94c701148
Create Date: 2024-12-14 13:08:38.072169

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '62ae33eb61d2'
down_revision = '9ae94c701148'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('batch_session',
    sa.Column('batch_id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('date_created', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('batch_id'),
    sa.UniqueConstraint('title')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('batch_session')
    # ### end Alembic commands ###
