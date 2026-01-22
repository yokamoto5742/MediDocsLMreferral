"""Add indexes for performance optimization

Revision ID: 370f18528085
Revises: 
Create Date: 2026-01-22 13:17:20.535344

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '370f18528085'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add performance indexes."""
    # Add indexes for Prompt table
    op.create_index('ix_prompts_lookup', 'prompts', ['department', 'document_type', 'doctor'], unique=False)

    # Add indexes for SummaryUsage table
    op.create_index('ix_summary_usage_aggregation', 'summary_usage', ['document_types', 'department', 'doctor'], unique=False)
    op.create_index(op.f('ix_summary_usage_date'), 'summary_usage', ['date'], unique=False)


def downgrade() -> None:
    """Downgrade schema - Remove performance indexes."""
    # Drop indexes for SummaryUsage table
    op.drop_index(op.f('ix_summary_usage_date'), table_name='summary_usage')
    op.drop_index('ix_summary_usage_aggregation', table_name='summary_usage')

    # Drop indexes for Prompt table
    op.drop_index('ix_prompts_lookup', table_name='prompts')
