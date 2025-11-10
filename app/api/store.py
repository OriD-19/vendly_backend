from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.store import StoreCreate, StoreUpdate, StoreResponse
from app.schemas.product import ProductResponse
from app.schemas.user import CustomerResponse
from app.services.store_service import StoreService
from app.utils.auth_dependencies import get_current_user

router = APIRouter(prefix="/stores", tags=["Stores"])
SHOWCASE_IMAGE_LIMIT = 5


def get_store_service(db: Session = Depends(get_db)) -> StoreService:
    """Dependency to get StoreService instance."""
    return StoreService(db)


# ========== Protected Endpoints (Store Owners Only) ==========

@router.post(
    "/",
    response_model=StoreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new store",
    description="Create a new store. Requires user to be a store owner (user_type=STORE)."
)
def create_store(
    store_data: StoreCreate,
    current_user: User = Depends(get_current_user),
    store_service: StoreService = Depends(get_store_service)
):
    """
    Create a new store.
    
    Requirements:
    - User must be authenticated
    - User must have user_type = STORE (store owner)
    - Store name must be unique
    """
    return store_service.create_store(store_data, current_user)


@router.get(
    "/my-store",
    response_model=List[StoreResponse],
    summary="Get current user's stores",
    description="Get all stores owned by the current user."
)
def get_my_stores(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    store_service: StoreService = Depends(get_store_service)
):
    """
    Get all stores owned by the authenticated user.
    
    Supports pagination.
    """
    stores = store_service.get_user_stores(current_user.id, skip, limit)
    
    # Convert to response models and add showcase images
    from app.schemas.store import StoreResponse
    store_responses = []
    for store in stores:
        showcase_images = store_service.get_store_showcase_images(store.id, limit=SHOWCASE_IMAGE_LIMIT)
        store_dict = StoreResponse.model_validate(store).model_dump()
        store_dict['showcase_images'] = showcase_images
        store_responses.append(StoreResponse(**store_dict))
    
    return store_responses


@router.put(
    "/{store_id}",
    response_model=StoreResponse,
    summary="Update a store",
    description="Update store details. Only the store owner can update their store."
)
def update_store(
    store_id: int,
    store_data: StoreUpdate,
    current_user: User = Depends(get_current_user),
    store_service: StoreService = Depends(get_store_service)
):
    """
    Update a store.
    
    Requirements:
    - User must be authenticated
    - User must own the store (owner_id matches user.id)
    - If updating name, new name must be unique
    """
    return store_service.update_store(store_id, store_data, current_user)


@router.delete(
    "/{store_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a store",
    description="Delete a store. Only the store owner can delete their store."
)
def delete_store(
    store_id: int,
    current_user: User = Depends(get_current_user),
    store_service: StoreService = Depends(get_store_service)
):
    """
    Delete a store.
    
    Requirements:
    - User must be authenticated
    - User must own the store
    - Store must not have any associated products
    """
    store_service.delete_store(store_id, current_user)
    return None


@router.get(
    "/{store_id}/statistics",
    summary="Get store statistics",
    description="Get detailed statistics for a store. Only accessible by the store owner."
)
def get_store_statistics(
    store_id: int,
    current_user: User = Depends(get_current_user),
    store_service: StoreService = Depends(get_store_service)
):
    """
    Get detailed statistics for a store.
    
    Returns:
    - Total products
    - Active/inactive products
    - Products in/out of stock
    - Total inventory value
    - Average product price
    - Total stock quantity
    
    Requirements:
    - User must be authenticated
    - User must own the store
    """
    return store_service.get_store_statistics(store_id, current_user)


# ========== Public Endpoints (No Authentication Required) ==========

@router.get(
    "/",
    response_model=List[StoreResponse],
    summary="List all stores",
    description="Get all stores with optional search and filtering. Public endpoint."
)
def list_stores(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    store_type: Optional[str] = None,
    location: Optional[str] = None,
    sort_by: str = "name",
    sort_order: str = "asc",
    store_service: StoreService = Depends(get_store_service)
):
    """
    Get all stores with optional filtering and search.
    
    **Public endpoint - no authentication required.**
    
    Query Parameters:
    - `skip`: Pagination offset (default: 0)
    - `limit`: Maximum results (default: 100, max: 100)
    - `search`: Search term (searches name, location, type)
    - `store_type`: Filter by store type
    - `location`: Filter by location
    - `sort_by`: Field to sort by (name, created_at, type)
    - `sort_order`: Sort order (asc or desc)
    
    Example:
    ```
    GET /stores/?search=electronics&location=New%20York&sort_by=name&sort_order=asc
    ```
    """
    stores = store_service.get_all_stores(
        skip=skip,
        limit=min(limit, 100),  # Cap at 100
        search=search,
        store_type=store_type,
        location=location,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    # Convert to response models and add showcase images
    from app.schemas.store import StoreResponse
    store_responses = []
    for store in stores:
        showcase_images = store_service.get_store_showcase_images(store.id, limit=SHOWCASE_IMAGE_LIMIT)
        store_dict = StoreResponse.model_validate(store).model_dump()
        store_dict['showcase_images'] = showcase_images
        store_responses.append(StoreResponse(**store_dict))
    
    return store_responses


@router.get(
    "/search",
    response_model=List[StoreResponse],
    summary="Search stores",
    description="Quick search for stores by name or location. Public endpoint."
)
def search_stores(
    q: str,
    limit: int = 10,
    store_service: StoreService = Depends(get_store_service)
):
    """
    Quick search for stores by name or location.
    
    **Public endpoint - no authentication required.**
    
    Query Parameters:
    - `q`: Search query (required)
    - `limit`: Maximum results (default: 10, max: 50)
    
    Example:
    ```
    GET /stores/search?q=electronics&limit=10
    ```
    """
    stores = store_service.search_stores(q, min(limit, 50))
    
    # Convert to response models and add showcase images
    from app.schemas.store import StoreResponse
    store_responses = []
    for store in stores:
        showcase_images = store_service.get_store_showcase_images(store.id, limit=SHOWCASE_IMAGE_LIMIT)
        store_dict = StoreResponse.model_validate(store).model_dump()
        store_dict['showcase_images'] = showcase_images
        store_responses.append(StoreResponse(**store_dict))
    
    return store_responses


@router.get(
    "/{store_id}",
    response_model=StoreResponse,
    summary="Get store by ID",
    description="Get detailed information about a specific store. Public endpoint."
)
def get_store(
    store_id: int,
    store_service: StoreService = Depends(get_store_service)
):
    """
    Get a store by its ID.
    
    **Public endpoint - no authentication required.**
    
    Returns complete store information including contact details and metadata.
    """
    store = store_service.get_store_by_id(store_id)
    
    # Add showcase images to the response
    from app.schemas.store import StoreResponse
    showcase_images = store_service.get_store_showcase_images(store_id, limit=SHOWCASE_IMAGE_LIMIT)
    store_dict = StoreResponse.model_validate(store).model_dump()
    store_dict['showcase_images'] = showcase_images
    
    return StoreResponse(**store_dict)


@router.get(
    "/{store_id}/products",
    response_model=List[ProductResponse],
    summary="Get store products with filters",
    description="Get all products from a store with advanced filtering. Public endpoint for customer browsing."
)
def get_store_products(
    store_id: int,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    in_stock_only: bool = False,
    active_only: bool = True,
    sort_by: str = "name",
    sort_order: str = "asc",
    store_service: StoreService = Depends(get_store_service)
):
    """
    Get all products from a specific store with filtering.
    
    **Public endpoint - no authentication required.**
    This endpoint is designed for customer browsing.
    
    Query Parameters:
    - `skip`: Pagination offset (default: 0)
    - `limit`: Maximum results (default: 100, max: 100)
    - `search`: Search product name/description
    - `category_id`: Filter by category ID
    - `min_price`: Minimum price (inclusive)
    - `max_price`: Maximum price (inclusive)
    - `in_stock_only`: Only show products with stock > 0 (default: false)
    - `active_only`: Only show active products (default: true)
    - `sort_by`: Field to sort by (name, price, created_at, stock)
    - `sort_order`: Sort order (asc or desc)
    
    Example:
    ```
    GET /stores/1/products?category_id=5&min_price=10&max_price=100&in_stock_only=true&sort_by=price&sort_order=asc
    ```
    """
    return store_service.get_store_products(
        store_id=store_id,
        skip=skip,
        limit=min(limit, 100),  # Cap at 100
        search=search,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        in_stock_only=in_stock_only,
        active_only=active_only,
        sort_by=sort_by,
        sort_order=sort_order
    )


@router.get(
    "/{store_id}/products/count",
    summary="Get product count",
    description="Get the number of products in a store. Public endpoint."
)
def get_store_product_count(
    store_id: int,
    active_only: bool = True,
    store_service: StoreService = Depends(get_store_service)
):
    """
    Get the count of products in a store.
    
    **Public endpoint - no authentication required.**
    
    Query Parameters:
    - `active_only`: Only count active products (default: true)
    
    Returns:
    ```json
    {
        "store_id": 1,
        "product_count": 42,
        "active_only": true
    }
    ```
    """
    count = store_service.get_store_product_count(store_id, active_only)
    return {
        "store_id": store_id,
        "product_count": count,
        "active_only": active_only
    }


@router.get(
    "/{store_id}/customers",
    response_model=List[CustomerResponse],
    summary="Get store customers",
    description="Get all customers who have purchased from a store. Requires authentication."
)
def get_store_customers(
    store_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    include_order_stats: bool = Query(False, description="Include order statistics for each customer"),
    current_user: User = Depends(get_current_user),
    store_service: StoreService = Depends(get_store_service)
):
    """
    Get all customers who have made purchases from a specific store.
    
    **Requires authentication.**
    
    Query Parameters:
    - `skip`: Pagination offset (default: 0)
    - `limit`: Maximum results (default: 100, max: 200)
    - `include_order_stats`: Include order count and total spent per customer (default: false)
    
    Returns a list of customers with their basic information.
    If `include_order_stats` is true, also includes:
    - `total_orders`: Number of orders placed
    - `total_spent`: Total amount spent at the store
    - `last_order_date`: Date of most recent order
    
    Example:
    ```
    GET /stores/1/customers?skip=0&limit=50&include_order_stats=true
    ```
    """
    return store_service.get_store_customers(
        store_id=store_id,
        skip=skip,
        limit=limit,
        include_order_stats=include_order_stats
    )
