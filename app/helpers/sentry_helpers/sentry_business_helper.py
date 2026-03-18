from app.db.models.business import Business
from sentry_sdk import configure_scope, set_context


def attach_business_partial_context(business: Business):
    with configure_scope() as scope:
        scope.set_tag("owner_id", business.owner_id)

    set_context(
        "business",
        {
            "owner_id": business.owner_id,
            "is_active": business.is_active,
        },
    )


def attach_business_full_context(business: Business):
    with configure_scope() as scope:
        scope.set_tag("business_id", business.id)

    set_context(
        "business",
        {
            "business_id": business.id,
            "owner_id": business.owner_id,
            "is_active": business.is_active,
            "created_at": business.created_at,
            "updated_at": business.updated_at,
        },
    )
