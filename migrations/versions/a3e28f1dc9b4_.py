"""empty message

Revision ID: a3e28f1dc9b4
Revises: 81d20b08065e
Create Date: 2024-12-15 12:34:27.467935

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a3e28f1dc9b4'
down_revision = '81d20b08065e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('defects_detected',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('scan_number', sa.Integer(), nullable=False),
    sa.Column('date_scanned', sa.DateTime(), nullable=False),
    sa.Column('defectsDetected', sa.JSON(), nullable=False),
    sa.Column('batch_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['batch_id'], ['batch_session.batch_id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('defects_detected')
    # ### end Alembic commands ###