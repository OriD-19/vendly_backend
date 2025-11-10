from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.review import (
    ReviewCreate, 
    ReviewUpdate, 
    ReviewResponse, 
    ProductReviewStats,
    StoreReviewStats
)
from app.services.review_service import ReviewService
from app.utils.auth_dependencies import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/reviews", tags=["reviews"])


# ========== CRUD Endpoints ==========

@router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_review(
    review_data: ReviewCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new review for a product.
    
    **Requires authentication** (customer only).
    
    **Rules:**
    - Each customer can only review a product once
    - Use PUT /reviews/{review_id} to update an existing review
    - Rating must be between 1 and 5
    
    **Note:** For now, any customer can review any product. 
    Purchase verification will be added later.
    """
    review_service = ReviewService(db)
    review = review_service.create_review(review_data, current_user.id)
    
    # Build response with customer username
    response = ReviewResponse.model_validate(review)
    response.customer_username = current_user.username
    
    return response


@router.get("/{review_id}", response_model=ReviewResponse)
def get_review(
    review_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a single review by ID.
    
    **Public endpoint** - no authentication required.
    """
    review_service = ReviewService(db)
    review = review_service.get_review_by_id(review_id)
    
    # Build response with customer username from relationship
    response = ReviewResponse.model_validate(review)
    if review.customer:
        response.customer_username = review.customer.username
    
    return response


@router.put("/{review_id}", response_model=ReviewResponse)
def update_review(
    review_id: int,
    review_data: ReviewUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing review.
    
    **Requires authentication** (must be the review owner).
    
    **Rules:**
    - Only the customer who created the review can update it
    - Can update rating, comment, or both
    """
    review_service = ReviewService(db)
    review = review_service.update_review(review_id, review_data, current_user.id)
    
    # Build response with customer username
    response = ReviewResponse.model_validate(review)
    response.customer_username = current_user.username
    
    return response


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    review_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a review.
    
    **Requires authentication** (must be the review owner).
    
    **Rules:**
    - Only the customer who created the review can delete it
    """
    review_service = ReviewService(db)
    review_service.delete_review(review_id, current_user.id)
    return None


# ========== Query Endpoints ==========

@router.get("/product/{product_id}", response_model=List[ReviewResponse])
def get_product_reviews(
    product_id: int,
    skip: int = Query(0, ge=0, description="Number of reviews to skip (pagination)"),
    limit: int = Query(100, ge=1, le=200, description="Maximum number of reviews to return"),
    rating: Optional[int] = Query(None, ge=1, le=5, description="Filter by specific rating (1-5)"),
    sort_by: str = Query("created_at", regex="^(created_at|rating)$", description="Field to sort by"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    db: Session = Depends(get_db)
):
    """
    Get all reviews for a specific product.
    
    **Public endpoint** - no authentication required.
    
    **Query Parameters:**
    - `skip`: Pagination offset (default: 0)
    - `limit`: Max results (default: 100, max: 200)
    - `rating`: Filter by rating (1-5)
    - `sort_by`: Sort by created_at or rating
    - `sort_order`: asc or desc (default: desc)
    
    **Examples:**
    - Get latest reviews: `?sort_by=created_at&sort_order=desc`
    - Get 5-star reviews: `?rating=5`
    - Get lowest rated first: `?sort_by=rating&sort_order=asc`
    """
    review_service = ReviewService(db)
    reviews = review_service.get_product_reviews(
        product_id=product_id,
        skip=skip,
        limit=limit,
        rating_filter=rating,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    # Build responses with customer usernames
    result = []
    for review in reviews:
        response = ReviewResponse.model_validate(review)
        if review.customer:
            response.customer_username = review.customer.username
        result.append(response)
    
    return result


@router.get("/customer/me", response_model=List[ReviewResponse])
def get_my_reviews(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all reviews created by the authenticated customer.
    
    **Requires authentication**.
    """
    review_service = ReviewService(db)
    reviews = review_service.get_customer_reviews(
        customer_id=current_user.id,
        skip=skip,
        limit=limit
    )
    
    # Build responses with customer username
    result = []
    for review in reviews:
        response = ReviewResponse.model_validate(review)
        response.customer_username = current_user.username
        result.append(response)
    
    return result


@router.get("/customer/{customer_id}", response_model=List[ReviewResponse])
def get_customer_reviews(
    customer_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    Get all reviews created by a specific customer.
    
    **Public endpoint** - no authentication required.
    """
    review_service = ReviewService(db)
    reviews = review_service.get_customer_reviews(
        customer_id=customer_id,
        skip=skip,
        limit=limit
    )
    
    # Build responses with customer usernames
    result = []
    for review in reviews:
        response = ReviewResponse.model_validate(review)
        if review.customer:
            response.customer_username = review.customer.username
        result.append(response)
    
    return result


# ========== Statistics Endpoints ==========

@router.get("/product/{product_id}/stats", response_model=ProductReviewStats)
def get_product_review_stats(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    Get review statistics for a product.
    
    **Public endpoint** - no authentication required.
    
    **Returns:**
    - Total number of reviews
    - Average rating (0-5)
    - Distribution of ratings (how many 1-star, 2-star, etc.)
    
    **Example Response:**
    ```json
    {
        "product_id": 1,
        "total_reviews": 52,
        "average_rating": 4.23,
        "rating_distribution": {
            "1": 2,
            "2": 3,
            "3": 8,
            "4": 15,
            "5": 24
        }
    }
    ```
    """
    review_service = ReviewService(db)
    stats = review_service.get_product_review_stats(product_id)
    return stats


@router.get("/product/{product_id}/score")
def get_product_overall_score(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    Get the overall average score for a product.
    
    **Public endpoint** - no authentication required.
    
    **Returns:**
    Simple average rating value (0-5).
    """
    review_service = ReviewService(db)
    score = review_service.get_overall_product_score(product_id)
    return {
        "product_id": product_id,
        "average_rating": score
    }


@router.get("/store/{store_id}/stats", response_model=StoreReviewStats)
def get_store_review_stats(
    store_id: int,
    db: Session = Depends(get_db)
):
    """
    Get aggregated review statistics for all products in a store.
    
    **Public endpoint** - no authentication required.
    
    **Returns:**
    - Total reviews across all products
    - Average rating across all products (0-5)
    - Number of products with at least one review
    - Distribution of ratings across all products
    
    **Example Response:**
    ```json
    {
        "store_id": 1,
        "total_reviews": 150,
        "average_rating": 4.35,
        "total_products_reviewed": 25,
        "rating_distribution": {
            "1": 5,
            "2": 8,
            "3": 20,
            "4": 45,
            "5": 72
        }
    }
    ```
    """
    review_service = ReviewService(db)
    stats = review_service.get_store_review_stats(store_id)
    return stats


@router.get("/store/{store_id}/score")
def get_store_overall_score(
    store_id: int,
    db: Session = Depends(get_db)
):
    """
    Get the overall average score for a store.
    
    **Public endpoint** - no authentication required.
    
    **Returns:**
    Simple average rating value (0-5) across all products.
    """
    review_service = ReviewService(db)
    score = review_service.get_overall_store_score(store_id)
    return {
        "store_id": store_id,
        "average_rating": score
    }


@router.get("/product/{product_id}/customer/me")
def get_my_review_for_product(
    product_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Check if the authenticated customer has reviewed a specific product.
    
    **Requires authentication**.
    
    **Returns:**
    - Review object if exists
    - null if no review exists
    
    **Use case:** Check if user can review or needs to update existing review.
    """
    review_service = ReviewService(db)
    review = review_service.get_customer_review_for_product(
        customer_id=current_user.id,
        product_id=product_id
    )
    
    if not review:
        return None
    
    # Build response with customer username
    response = ReviewResponse.model_validate(review)
    response.customer_username = current_user.username
    
    return response
