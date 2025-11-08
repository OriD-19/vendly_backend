from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse, CategoryBulkCreate, CategoryBulkResponse
from app.schemas.product import ProductResponse
from app.services.category import CategoryService
from app.utils.auth_dependencies import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/categories", tags=["categories"])


# ========== CRUD Endpoints ==========

@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new category.
    
    Requires authentication. Category names must be unique (case-insensitive).
    """
    category_service = CategoryService(db)
    category = category_service.create_category(category_data)
    return category


@router.post("/bulk", response_model=CategoryBulkResponse, status_code=status.HTTP_201_CREATED)
def create_categories_bulk(
    bulk_data: CategoryBulkCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create multiple categories at once.
    
    Requires authentication.
    
    This endpoint will:
    - Create all new categories that don't already exist
    - Skip categories with duplicate names (case-insensitive)
    - Return a detailed response with created and skipped categories
    
    Example request body:
    ```json
    {
        "categories": [
            {"name": "Electronics"},
            {"name": "Clothing"},
            {"name": "Food"}
        ]
    }
    ```
    
    Limits:
    - Minimum: 1 category
    - Maximum: 100 categories per request
    """
    category_service = CategoryService(db)
    created, skipped = category_service.create_categories_bulk(bulk_data.categories)
    
    return CategoryBulkResponse(
        created=created,
        skipped=skipped,
        total_requested=len(bulk_data.categories),
        total_created=len(created),
        total_skipped=len(skipped)
    )


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a single category by ID.
    
    Public endpoint - no authentication required.
    """
    category_service = CategoryService(db)
    category = category_service.get_category_by_id(category_id)
    return category


@router.get("/name/{category_name}", response_model=CategoryResponse)
def get_category_by_name(
    category_name: str,
    db: Session = Depends(get_db)
):
    """
    Get a single category by name (case-insensitive).
    
    Public endpoint - no authentication required.
    """
    category_service = CategoryService(db)
    category = category_service.get_category_by_name(category_name)
    return category


@router.get("/", response_model=List[CategoryResponse])
def get_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    search: Optional[str] = None,
    sort_by: str = Query("name", regex="^(name|created_at|updated_at)$"),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    """
    Get all categories with optional search and sorting.
    
    Public endpoint - no authentication required.
    
    Query Parameters:
    - skip: Pagination offset (default: 0)
    - limit: Max results (default: 100, max: 200)
    - search: Search term to filter by name
    - sort_by: Field to sort by (name, created_at, updated_at)
    - sort_order: Sort order (asc or desc)
    """
    category_service = CategoryService(db)
    categories = category_service.get_all_categories(
        skip=skip,
        limit=limit,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return categories


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update a category.
    
    Requires authentication.
    """
    category_service = CategoryService(db)
    category = category_service.update_category(category_id, category_data)
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a category.
    
    Requires authentication.
    
    Note: Cannot delete categories with associated products.
    Use move_products endpoint first to reassign products.
    """
    category_service = CategoryService(db)
    category_service.delete_category(category_id)
    return None


# ========== Product Filtering Endpoints ==========

@router.get("/{category_id}/products", response_model=List[ProductResponse])
def get_category_products(
    category_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    search: Optional[str] = None,
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    in_stock_only: bool = False,
    active_only: bool = True,
    store_id: Optional[int] = None,
    sort_by: str = Query("name", regex="^(name|price|created_at|stock)$"),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    """
    Get all products in a specific category with advanced filtering.
    
    Public endpoint - no authentication required.
    
    Query Parameters:
    - skip: Pagination offset (default: 0)
    - limit: Max results (default: 100, max: 200)
    - search: Search products by name or description
    - min_price: Minimum price filter
    - max_price: Maximum price filter
    - in_stock_only: Only show products with stock > 0
    - active_only: Only show active products (default: true)
    - store_id: Filter by specific store
    - sort_by: Field to sort by (name, price, created_at, stock)
    - sort_order: Sort order (asc or desc)
    """
    category_service = CategoryService(db)
    products = category_service.get_category_products(
        category_id=category_id,
        skip=skip,
        limit=limit,
        search=search,
        min_price=min_price,
        max_price=max_price,
        in_stock_only=in_stock_only,
        active_only=active_only,
        store_id=store_id,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return products


@router.get("/name/{category_name}/products", response_model=List[ProductResponse])
def get_category_products_by_name(
    category_name: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    search: Optional[str] = None,
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    in_stock_only: bool = False,
    active_only: bool = True,
    store_id: Optional[int] = None,
    sort_by: str = Query("name", regex="^(name|price|created_at|stock)$"),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    """
    Get all products in a category by category name.
    
    Public endpoint - no authentication required.
    
    Same filtering options as get_category_products.
    """
    category_service = CategoryService(db)
    products = category_service.get_category_products_by_name(
        category_name=category_name,
        skip=skip,
        limit=limit,
        search=search,
        min_price=min_price,
        max_price=max_price,
        in_stock_only=in_stock_only,
        active_only=active_only,
        store_id=store_id,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return products


# ========== Statistics & Analytics Endpoints ==========

@router.get("/{category_id}/count")
def get_category_product_count(
    category_id: int,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """
    Get the count of products in a category.
    
    Public endpoint - no authentication required.
    """
    category_service = CategoryService(db)
    count = category_service.get_category_product_count(category_id, active_only)
    return {
        "category_id": category_id,
        "product_count": count,
        "active_only": active_only
    }


@router.get("/{category_id}/statistics")
def get_category_statistics(
    category_id: int,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive statistics for a category.
    
    Returns:
    - Total products
    - Active/inactive products
    - In stock/out of stock counts
    - Price statistics (min, max, average)
    - Total inventory value
    - Total stock quantity
    
    Public endpoint - no authentication required.
    """
    category_service = CategoryService(db)
    statistics = category_service.get_category_statistics(category_id)
    return statistics


@router.get("/all/with-counts")
def get_categories_with_counts(
    db: Session = Depends(get_db)
):
    """
    Get all categories with their product counts.
    
    Useful for displaying category menus with product counts.
    
    Public endpoint - no authentication required.
    """
    category_service = CategoryService(db)
    categories = category_service.get_categories_with_product_count()
    return categories


# ========== Utility Endpoints ==========

@router.post("/{source_category_id}/move-products/{target_category_id}")
def move_products_to_category(
    source_category_id: int,
    target_category_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Move all products from one category to another.
    
    Requires authentication.
    
    Useful before deleting a category with products.
    """
    category_service = CategoryService(db)
    products_moved = category_service.move_products_to_category(
        source_category_id, target_category_id
    )
    return {
        "source_category_id": source_category_id,
        "target_category_id": target_category_id,
        "products_moved": products_moved,
        "message": f"Successfully moved {products_moved} product(s)"
    }


@router.get("/search/{search_term}")
def search_categories(
    search_term: str,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Search categories by name.
    
    Public endpoint - no authentication required.
    
    Useful for autocomplete/typeahead functionality.
    """
    category_service = CategoryService(db)
    categories = category_service.search_categories(search_term, limit)
    return categories
