from sentry_sdk import configure_scope, set_context

from app.db.models.users import User


def attach_user_context(user: User):

    with configure_scope() as scope:
        scope.set_tag("user_id", user.id)

    set_context("user", {
        "user_id": user.id,
        "auth_provider": user.auth_provider,
        "auth_provider_id":  user.provider_user_id,
        "email_verified": user.email_verified,
        "created_at": user.created_at,
        "updated_at": user.updated_at
    })