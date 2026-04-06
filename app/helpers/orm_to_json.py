import json
from datetime import datetime
from app.db.models.business import Business


def business_to_json(business: Business):
    business_data = {
        "id": str(business.id),
        "owner_id": str(business.owner_id),
        "name": business.name,
        "legal_name": business.legal_name,
        "tax_id": business.tax_id,
        "currency": business.currency,
        "email": business.email,
        "phone": business.phone,
        "website": str(business.website) if business.website else None,
        "address_line1": business.address_line1,
        "address_line2": business.address_line2,
        "city": business.city,
        "state": business.state,
        "country": business.country,
        "postal_code": business.postal_code,
        "logo_url": str(business.logo_url) if business.logo_url else None,
        "timezone": business.timezone,
        "is_active": business.is_active,
        "created_at": business.created_at.isoformat() if business.created_at else None,
        "updated_at": business.updated_at.isoformat() if business.updated_at else None,
    }

    return business_data
