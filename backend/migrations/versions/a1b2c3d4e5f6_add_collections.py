"""Add collections and collection_members tables

Revision ID: a1b2c3d4e5f6
Revises: 842535b7916f
Create Date: 2026-03-22 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '842535b7916f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create collections table
    op.create_table(
        'collections',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=False),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_collections_created_by', 'collections', ['created_by'], unique=False)
    op.create_index('idx_collections_created_at', 'collections', ['created_at'], unique=False)

    # 2. Create collection_members table
    op.create_table(
        'collection_members',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('collection_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('role', sa.Enum('owner', 'editor', 'viewer', name='collectionmemberrole'), nullable=False),
        sa.Column('added_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['collection_id'], ['collections.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_collection_members_collection_id', 'collection_members', ['collection_id'], unique=False)
    op.create_index('idx_collection_members_user_id', 'collection_members', ['user_id'], unique=False)

    # 3. Add collection_id to documents (nullable — existing docs unaffected)
    op.add_column('documents', sa.Column('collection_id', sa.String(length=36), nullable=True))
    op.create_foreign_key(
        'fk_documents_collection_id',
        'documents', 'collections',
        ['collection_id'], ['id']
    )
    op.create_index('idx_documents_collection_id', 'documents', ['collection_id'], unique=False)

    # 4. Add collection_id to qa_history (nullable — existing history unaffected)
    op.add_column('qa_history', sa.Column('collection_id', sa.String(length=36), nullable=True))
    op.create_foreign_key(
        'fk_qa_history_collection_id',
        'qa_history', 'collections',
        ['collection_id'], ['id']
    )
    op.create_index('idx_qa_collection_id', 'qa_history', ['collection_id'], unique=False)


def downgrade() -> None:
    # Reverse in opposite order
    op.drop_index('idx_qa_collection_id', table_name='qa_history')
    op.drop_constraint('fk_qa_history_collection_id', 'qa_history', type_='foreignkey')
    op.drop_column('qa_history', 'collection_id')

    op.drop_index('idx_documents_collection_id', table_name='documents')
    op.drop_constraint('fk_documents_collection_id', 'documents', type_='foreignkey')
    op.drop_column('documents', 'collection_id')

    op.drop_index('idx_collection_members_user_id', table_name='collection_members')
    op.drop_index('idx_collection_members_collection_id', table_name='collection_members')
    op.drop_table('collection_members')

    op.drop_index('idx_collections_created_at', table_name='collections')
    op.drop_index('idx_collections_created_by', table_name='collections')
    op.drop_table('collections')

    op.execute("DROP TYPE IF EXISTS collectionmemberrole")