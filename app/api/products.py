from typing import List, Optional
from fastapi import APIRouter, Depends, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.product import Product, ProductImage, Tag
from app.schemas.product import (
    ProductCreate, ProductUpdate, ProductResponse,
    TagCreate, TagUpdate, TagResponse,
    ProductImageResponse,
    ProductBulkCreate, ProductBulkResponse
)
from app.services.product_service import ProductService
from app.services.s3_service import S3Service, get_s3_service
from app.utils.auth_dependencies import get_current_user
from app.services.store_service import StoreService

router = APIRouter(prefix="/products", tags=["Products"])


def get_product_service(db: Session = Depends(get_db)) -> ProductService:
    """Dependency to get ProductService instance."""
    return ProductService(db)


def get_store_service(db: Session = Depends(get_db)) -> StoreService:
    """Dependency to get StoreService instance."""
    return StoreService(db)


# ========== Product CRUD Endpoints ==========

@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product",
    description="Create a new product. Requires authentication and user must own the store."
)
def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service),
    store_service: StoreService = Depends(get_store_service)
):
    """
    Create a new product.
    
    Requirements:
    - User must be authenticated
    - User must own the store (store.owner_id == user.id)
    - Store and category must exist
    - Tag IDs must be valid (if provided)
    """
    # Verify user owns the store
    store_service.verify_store_ownership(product_data.store_id, current_user.id)
    
    return product_service.create_product(product_data)


@router.post(
    "/bulk",
    response_model=ProductBulkResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create multiple products at once",
    description="Bulk create products. Requires authentication and user must own all stores."
)
def create_products_bulk(
    bulk_data: ProductBulkCreate,
    current_user: User = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service),
    store_service: StoreService = Depends(get_store_service)
):
    """
    Create multiple products at once.
    
    Requirements:
    - User must be authenticated
    - User must own ALL stores referenced in the products
    - Products with invalid stores, categories, or tags will be skipped
    - Returns detailed response with created and failed products
    
    Example request body:
    ```json
    {
        "products": [
            {
                "name": "Laptop",
                "short_description": "High-performance laptop",
                "price": 999.99,
                "stock": 10,
                "store_id": 1,
                "category_id": 1,
                "tag_ids": [1, 2]
            },
            {
                "name": "Mouse",
                "short_description": "Wireless mouse",
                "price": 29.99,
                "stock": 50,
                "store_id": 1,
                "category_id": 1
            }
        ]
    }
    ```
    
    Limits:
    - Minimum: 1 product
    - Maximum: 100 products per request
    """
    # Verify user owns all stores referenced in the products
    store_ids = {product.store_id for product in bulk_data.products}
    for store_id in store_ids:
        store_service.verify_store_ownership(store_id, current_user.id)
    
    # Create products in bulk
    created, failed = product_service.create_products_bulk(bulk_data.products)
    
    # Convert Product models to ProductResponse schemas
    created_responses = [ProductResponse.model_validate(product) for product in created]
    
    return ProductBulkResponse(
        created=created_responses,
        failed=failed,
        total_requested=len(bulk_data.products),
        total_created=len(created),
        total_failed=len(failed)
    )


@router.get(
    "/",
    response_model=List[ProductResponse],
    summary="List all products with filters",
    description="Get all products with optional filtering. Public endpoint."
)
def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    is_active: Optional[bool] = None,
    category_id: Optional[int] = None,
    store_id: Optional[int] = None,
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    in_stock: Optional[bool] = None,
    search: Optional[str] = None,
    product_service: ProductService = Depends(get_product_service)
):
    """
    Get all products with filtering.
    
    **Public endpoint - no authentication required.**
    
    Query Parameters:
    - `skip`: Pagination offset (default: 0)
    - `limit`: Maximum results (default: 100, max: 100)
    - `is_active`: Filter by active status
    - `category_id`: Filter by category
    - `store_id`: Filter by store
    - `min_price`: Minimum price (inclusive)
    - `max_price`: Maximum price (inclusive)
    - `in_stock`: Only show products with stock > 0
    - `search`: Search in name and descriptions
    """
    return product_service.get_all_products(
        skip=skip,
        limit=limit,
        is_active=is_active,
        category_id=category_id,
        store_id=store_id,
        min_price=min_price,
        max_price=max_price,
        in_stock=in_stock,
        search=search
    )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get product by ID",
    description="Get detailed product information. Public endpoint."
)
def get_product(
    product_id: int,
    product_service: ProductService = Depends(get_product_service)
):
    """
    Get a product by its ID.
    
    **Public endpoint - no authentication required.**
    
    Returns complete product information including tags and images.
    """
    return product_service.get_product_by_id(product_id)


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Update a product",
    description="Update product details. Requires authentication and store ownership."
)
def update_product(
    product_id: int,
    product_data: ProductUpdate,
    current_user: User = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service),
    store_service: StoreService = Depends(get_store_service),
    db: Session = Depends(get_db)
):
    """
    Update a product.
    
    Requirements:
    - User must be authenticated
    - User must own the store that the product belongs to
    - All fields are optional (only update what's provided)
    """
    # Get product to check store ownership
    product = product_service.get_product_by_id(product_id)
    store_service.verify_store_ownership(product.store_id, current_user.id)
    
    return product_service.update_product(product_id, product_data)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a product",
    description="Delete a product. Requires authentication and store ownership."
)
def delete_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service),
    store_service: StoreService = Depends(get_store_service),
    s3_service: S3Service = Depends(get_s3_service),
    db: Session = Depends(get_db)
):
    """
    Delete a product.
    
    Requirements:
    - User must be authenticated
    - User must own the store
    - Also deletes associated images from S3 and database
    """
    # Get product to check store ownership and images
    product = product_service.get_product_by_id(product_id)
    store_service.verify_store_ownership(product.store_id, current_user.id)
    
    # Delete images from S3 (if configured)
    if s3_service.is_configured() and product.images:
        image_urls = [img.image_url for img in product.images]
        s3_service.delete_multiple_images(image_urls)
    
    product_service.delete_product(product_id)
    return None


# ========== Product Image Management ==========

@router.post(
    "/{product_id}/images",
    response_model=List[ProductImageResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload product images",
    description="Upload one or more images for a product. Requires authentication and store ownership."
)
async def upload_product_images(
    product_id: int,
    files: List[UploadFile] = File(..., description="Image files (max 10)"),
    current_user: User = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service),
    store_service: StoreService = Depends(get_store_service),
    s3_service: S3Service = Depends(get_s3_service),
    db: Session = Depends(get_db)
):
    """
    Upload product images to S3 and associate with product.
    
    Requirements:
    - User must be authenticated
    - User must own the store
    - S3 must be configured
    - Maximum 10 images per upload
    - Supported formats: JPEG, PNG, GIF, WebP
    - Maximum file size: 10MB per image
    
    Returns list of created ProductImage records with S3 URLs.
    """
    # Verify product exists and user owns the store
    product = product_service.get_product_by_id(product_id)
    store_service.verify_store_ownership(product.store_id, current_user.id)
    
    # Upload images to S3
    image_urls = s3_service.upload_multiple_product_images(files, product_id)
    
    # Save image URLs to database
    product_images = []
    for url in image_urls:
        product_image = product_service.add_product_image(product_id, url)
        product_images.append(product_image)
    
    return product_images


@router.get(
    "/{product_id}/images",
    response_model=List[ProductImageResponse],
    summary="Get product images",
    description="Get all images for a product. Public endpoint."
)
def get_product_images(
    product_id: int,
    product_service: ProductService = Depends(get_product_service),
    db: Session = Depends(get_db)
):
    """
    Get all images for a product.
    
    **Public endpoint - no authentication required.**
    """
    product = product_service.get_product_by_id(product_id)
    return product.images


@router.delete(
    "/{product_id}/images/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a product image",
    description="Delete a product image. Requires authentication and store ownership."
)
def delete_product_image(
    product_id: int,
    image_id: int,
    current_user: User = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service),
    store_service: StoreService = Depends(get_store_service),
    s3_service: S3Service = Depends(get_s3_service),
    db: Session = Depends(get_db)
):
    """
    Delete a product image from S3 and database.
    
    Requirements:
    - User must be authenticated
    - User must own the store
    - Image must belong to the specified product
    """
    # Verify product exists and user owns the store
    product = product_service.get_product_by_id(product_id)
    store_service.verify_store_ownership(product.store_id, current_user.id)
    
    # Get image
    image = db.query(ProductImage).filter(
        ProductImage.id == image_id,
        ProductImage.product_id == product_id
    ).first()
    
    if not image:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with id {image_id} not found for product {product_id}"
        )
    
    # Delete from S3 (if configured)
    if s3_service.is_configured():
        s3_service.delete_image(image.image_url)
    
    # Delete from database
    product_service.delete_product_image(image_id)
    return None


# ========== Tag Management ==========

@router.post(
    "/tags",
    response_model=TagResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a tag",
    description="Create a new product tag. Requires authentication."
)
def create_tag(
    tag_data: TagCreate,
    current_user: User = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service)
):
    """
    Create a new tag.
    
    Requirements:
    - User must be authenticated
    - Tag name must be unique
    """
    return product_service.create_tag(tag_data)


@router.get(
    "/tags",
    response_model=List[TagResponse],
    summary="List all tags",
    description="Get all available product tags. Public endpoint."
)
def list_tags(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = None,
    product_service: ProductService = Depends(get_product_service)
):
    """
    Get all tags with optional search.
    
    **Public endpoint - no authentication required.**
    """
    return product_service.get_all_tags(skip, limit, search)


@router.get(
    "/tags/{tag_id}",
    response_model=TagResponse,
    summary="Get tag by ID",
    description="Get a specific tag. Public endpoint."
)
def get_tag(
    tag_id: int,
    product_service: ProductService = Depends(get_product_service)
):
    """Get a tag by its ID."""
    return product_service.get_tag_by_id(tag_id)


@router.put(
    "/tags/{tag_id}",
    response_model=TagResponse,
    summary="Update a tag",
    description="Update a tag. Requires authentication."
)
def update_tag(
    tag_id: int,
    tag_data: TagUpdate,
    current_user: User = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service)
):
    """
    Update a tag.
    
    Requirements:
    - User must be authenticated
    - New name must be unique
    """
    return product_service.update_tag(tag_id, tag_data)


@router.delete(
    "/tags/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a tag",
    description="Delete a tag. Requires authentication."
)
def delete_tag(
    tag_id: int,
    current_user: User = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service)
):
    """
    Delete a tag.
    
    Requirements:
    - User must be authenticated
    - This will remove the tag from all products
    """
    product_service.delete_tag(tag_id)
    return None


# ========== Product Search & Discovery ==========

@router.get(
    "/search",
    response_model=List[ProductResponse],
    summary="Search products",
    description="Search products by name and description. Public endpoint."
)
def search_products(
    q: str = Query(..., min_length=1, description="Search query"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    category_id: Optional[int] = None,
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    in_stock: bool = False,
    product_service: ProductService = Depends(get_product_service)
):
    """
    Search products by name and description.
    
    **Public endpoint - no authentication required.**
    
    Can be combined with filters (category, price range, stock status).
    """
    return product_service.search_products(
        search_term=q,
        skip=skip,
        limit=limit,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        in_stock=in_stock
    )


@router.get(
    "/by-tag/{tag_id}",
    response_model=List[ProductResponse],
    summary="Get products by tag",
    description="Get all products with a specific tag. Public endpoint."
)
def get_products_by_tag(
    tag_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    is_active: bool = True,
    product_service: ProductService = Depends(get_product_service)
):
    """
    Get all products that have a specific tag.
    
    **Public endpoint - no authentication required.**
    """
    return product_service.get_products_by_tag(tag_id, skip, limit, is_active)


# ========== Stock Management ==========

@router.patch(
    "/{product_id}/stock",
    response_model=ProductResponse,
    summary="Update product stock",
    description="Update product stock level. Requires authentication and store ownership."
)
def update_product_stock(
    product_id: int,
    stock: int = Query(..., ge=0, description="New stock level"),
    current_user: User = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service),
    store_service: StoreService = Depends(get_store_service)
):
    """
    Update product stock level.
    
    Requirements:
    - User must be authenticated
    - User must own the store
    - Stock must be >= 0
    """
    # Verify ownership
    product = product_service.get_product_by_id(product_id)
    store_service.verify_store_ownership(product.store_id, current_user.id)
    
    return product_service.update_stock(product_id, stock)


@router.patch(
    "/{product_id}/stock/increment",
    response_model=ProductResponse,
    summary="Increment product stock",
    description="Add to product stock. Requires authentication and store ownership."
)
def increment_product_stock(
    product_id: int,
    amount: int = Query(..., gt=0, description="Amount to add to stock"),
    current_user: User = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service),
    store_service: StoreService = Depends(get_store_service)
):
    """
    Increment product stock by specified amount.
    
    Requirements:
    - User must be authenticated
    - User must own the store
    - Amount must be > 0
    """
    # Verify ownership
    product = product_service.get_product_by_id(product_id)
    store_service.verify_store_ownership(product.store_id, current_user.id)
    
    return product_service.increment_stock(product_id, amount)


@router.patch(
    "/{product_id}/stock/decrement",
    response_model=ProductResponse,
    summary="Decrement product stock",
    description="Subtract from product stock. Requires authentication and store ownership."
)
def decrement_product_stock(
    product_id: int,
    amount: int = Query(..., gt=0, description="Amount to subtract from stock"),
    current_user: User = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service),
    store_service: StoreService = Depends(get_store_service)
):
    """
    Decrement product stock by specified amount.
    
    Requirements:
    - User must be authenticated
    - User must own the store
    - Amount must be > 0
    - Resulting stock must be >= 0
    """
    # Verify ownership
    product = product_service.get_product_by_id(product_id)
    store_service.verify_store_ownership(product.store_id, current_user.id)
    
    return product_service.decrement_stock(product_id, amount)


# ========== Product Status Management ==========

@router.patch(
    "/{product_id}/activate",
    response_model=ProductResponse,
    summary="Activate a product",
    description="Set product as active. Requires authentication and store ownership."
)
def activate_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service),
    store_service: StoreService = Depends(get_store_service)
):
    """
    Activate a product (set is_active = True).
    
    Requirements:
    - User must be authenticated
    - User must own the store
    """
    # Verify ownership
    product = product_service.get_product_by_id(product_id)
    store_service.verify_store_ownership(product.store_id, current_user.id)
    
    return product_service.activate_product(product_id)


@router.patch(
    "/{product_id}/deactivate",
    response_model=ProductResponse,
    summary="Deactivate a product",
    description="Set product as inactive. Requires authentication and store ownership."
)
def deactivate_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service),
    store_service: StoreService = Depends(get_store_service)
):
    """
    Deactivate a product (set is_active = False).
    
    Requirements:
    - User must be authenticated
    - User must own the store
    """
    # Verify ownership
    product = product_service.get_product_by_id(product_id)
    store_service.verify_store_ownership(product.store_id, current_user.id)
    
    return product_service.deactivate_product(product_id)


# ========== Offer/Discount Endpoints ==========

@router.get(
    "/offers/all",
    response_model=List[ProductResponse],
    summary="Get all products with active offers",
    description="Get all products currently on offer. Public endpoint."
)
def get_all_offers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    product_service: ProductService = Depends(get_product_service)
):
    """
    Get all products with active discount offers.
    
    **Public endpoint - no authentication required.**
    
    An offer is active if:
    - Product has a discount_price set
    - discount_end_date is null (no expiry) OR in the future
    
    Perfect for displaying "Hot Deals" or "Special Offers" sections.
    """
    return product_service.get_products_with_active_offers(skip=skip, limit=limit)


@router.get(
    "/offers/store/{store_id}",
    response_model=List[ProductResponse],
    summary="Get store offers",
    description="Get all products with active offers from a specific store. Public endpoint."
)
def get_store_offers(
    store_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    product_service: ProductService = Depends(get_product_service)
):
    """
    Get all products with active offers from a specific store.
    
    **Public endpoint - no authentication required.**
    
    Great for "Store Deals" or "Store Promotions" pages.
    
    Example:
    ```
    GET /products/offers/store/1?skip=0&limit=20
    ```
    """
    return product_service.get_store_offers(store_id, skip=skip, limit=limit)


@router.get(
    "/offers/category/{category_id}",
    response_model=List[ProductResponse],
    summary="Get category offers",
    description="Get all products with active offers from a specific category. Public endpoint."
)
def get_category_offers(
    category_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    product_service: ProductService = Depends(get_product_service)
):
    """
    Get all products with active offers from a specific category.
    
    **Public endpoint - no authentication required.**
    
    Perfect for "Electronics on Sale" or "Fashion Deals" sections.
    
    Example:
    ```
    GET /products/offers/category/5?skip=0&limit=20
    ```
    """
    return product_service.get_category_offers(category_id, skip=skip, limit=limit)
