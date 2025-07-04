import sqlmodel
"""tool call tbl

Revision ID: db9a42a5d8e7
Revises: e755caf2a430
Create Date: 2025-06-24 01:52:41.637517

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'db9a42a5d8e7'
down_revision: Union[str, Sequence[str], None] = 'e755caf2a430'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('tool_calls',
    sa.Column('id', sqlmodel.sql.sqltypes.AutoString(length=50), server_default=sa.text('nanoid()'), nullable=False),
    sa.Column('function_name', sa.String(length=100), nullable=False),
    sa.Column('arguments', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('response', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('execution_time_ms', sa.Integer(), nullable=False),
    sa.Column('success', sa.Boolean(), nullable=False),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('conversation_id', sa.String(length=50), nullable=True),
    sa.Column('request_id', sa.String(length=50), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tool_calls_conversation_id'), 'tool_calls', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_tool_calls_function_name'), 'tool_calls', ['function_name'], unique=False)
    op.create_index(op.f('ix_tool_calls_id'), 'tool_calls', ['id'], unique=False)
    op.create_index(op.f('ix_tool_calls_request_id'), 'tool_calls', ['request_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_tool_calls_request_id'), table_name='tool_calls')
    op.drop_index(op.f('ix_tool_calls_id'), table_name='tool_calls')
    op.drop_index(op.f('ix_tool_calls_function_name'), table_name='tool_calls')
    op.drop_index(op.f('ix_tool_calls_conversation_id'), table_name='tool_calls')
    op.drop_table('tool_calls')
    # ### end Alembic commands ###
