"""лайки, ответы на комментарии, приватные группы и членство

Revision ID: 0002_likes_replies_membership
Revises: 0001_baseline
Create Date: 2026-01-01 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_likes_replies_membership"
down_revision: Union[str, Sequence[str], None] = "0001_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "post_likes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("post_id", "user_id", name="uq_post_likes_post_user"),
    )
    op.create_index(op.f("ix_post_likes_id"), "post_likes", ["id"], unique=False)
    op.create_index(op.f("ix_post_likes_post_id"), "post_likes", ["post_id"], unique=False)
    op.create_index(op.f("ix_post_likes_user_id"), "post_likes", ["user_id"], unique=False)

    op.create_table(
        "group_members",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("group_id", "user_id", name="uq_group_members_group_user"),
    )
    op.create_index(op.f("ix_group_members_id"), "group_members", ["id"], unique=False)
    op.create_index(
        op.f("ix_group_members_group_id"), "group_members", ["group_id"], unique=False
    )
    op.create_index(
        op.f("ix_group_members_user_id"), "group_members", ["user_id"], unique=False
    )

    op.add_column(
        "groups",
        sa.Column("is_private", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    # Самоссылающийся FK на существующей таблице.
    # recreate="auto" — на PG идёт нативный ALTER TABLE (FK не ломается),
    # на SQLite Alembic сам пересоздаёт таблицу (batch), т.к. ADD CONSTRAINT
    # в SQLite не поддерживается.
    with op.batch_alter_table("comments", recreate="auto") as batch_op:
        batch_op.add_column(sa.Column("parent_id", sa.Integer(), nullable=True))
        batch_op.create_index(op.f("ix_comments_parent_id"), ["parent_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_comments_parent_id_comments",
            "comments",
            ["parent_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("comments", recreate="auto") as batch_op:
        batch_op.drop_constraint("fk_comments_parent_id_comments", type_="foreignkey")
        batch_op.drop_index(op.f("ix_comments_parent_id"))
        batch_op.drop_column("parent_id")

    op.drop_column("groups", "is_private")

    op.drop_index(op.f("ix_group_members_user_id"), table_name="group_members")
    op.drop_index(op.f("ix_group_members_group_id"), table_name="group_members")
    op.drop_index(op.f("ix_group_members_id"), table_name="group_members")
    op.drop_table("group_members")

    op.drop_index(op.f("ix_post_likes_user_id"), table_name="post_likes")
    op.drop_index(op.f("ix_post_likes_post_id"), table_name="post_likes")
    op.drop_index(op.f("ix_post_likes_id"), table_name="post_likes")
    op.drop_table("post_likes")