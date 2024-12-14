"""empty message

Revision ID: 6efa47ee5bca
Revises: 62ae33eb61d2
Create Date: 2024-12-14 13:25:48.582182

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6efa47ee5bca'
down_revision = '62ae33eb61d2'
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
    with op.batch_alter_table('batch_session', schema=None) as batch_op:
        batch_op.add_column(sa.Column('bean_type', sa.String(length=255), nullable=False))
        batch_op.add_column(sa.Column('farm', sa.String(length=255), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('batch_session', schema=None) as batch_op:
        batch_op.drop_column('farm')
        batch_op.drop_column('bean_type')

    op.drop_table('defects_detected')
    # ### end Alembic commands ###