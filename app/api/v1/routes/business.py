import json
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, Request, status
from app.api.v1.dependencies import get_db
from app.helpers.idempotency import idempotency_checker
from app.schemas.business_schema import BusinessCreate, BusinessResponse, BusinessUpdate
from sqlalchemy.orm import Session
from app.core.security import get_current_user_dependency
from app.services.business_service import BusinessService
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from app.main import limiter
from fastapi.encoders import jsonable_encoder
from app.core.redis import redis_client


router = APIRouter(prefix="/v1/businesses", tags=["Business"])
business_service = BusinessService()


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=BusinessResponse)
@limiter.limit("10/minute")
async def create_business(
    request: Request,
    business_data: BusinessCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
):
    idemp_resp = await idempotency_checker(request, redis_client, current_user.id)

    if idemp_resp.get("status") == "cached":
        return idemp_resp.get("response")

    resp = business_service.create_business(
        db=db,
        business_data=business_data.model_dump(mode="json"),
        owner_id=current_user.id,
    )

    data = jsonable_encoder(resp)

    await redis_client.set(
        idemp_resp.get("redis_key"),
        json.dumps(
            {
                "status": "completed",
                "payload_hash": idemp_resp.get("hashed_body"),
                "response": data,
            }
        ),
        ex=86400,
    )

    return resp


@router.get("/{id}", status_code=status.HTTP_200_OK, response_model=BusinessResponse)
@limiter.limit("100/minute")
async def get_business(
    request: Request,
    id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
):

    return await business_service.get_business(id=id, db=db, owner_id=current_user.id)


@router.get("/", status_code=status.HTTP_200_OK, response_model=Page[BusinessResponse])
@limiter.limit("50/minute")
def get_businesses(
    request: Request,
    params: Params = Depends(),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
):
    query = business_service.get_businesses(owner_id=current_user.id, db=db)
    return paginate(query, params)


@router.put("/{id}", status_code=status.HTTP_200_OK, response_model=BusinessResponse)
@limiter.limit("20/minute")
async def update_business(
    request: Request,
    business_data: BusinessUpdate,
    id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
):
    return await business_service.update_business(
        id=id,
        owner_id=current_user.id,
        db=db,
        business_data=business_data.model_dump(exclude_unset=True, mode="json"),
    )


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
async def delete_business(
    request: Request,
    id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_dependency),
):
    return await business_service.delete_business(id=id, owner_id=current_user.id, db=db)
