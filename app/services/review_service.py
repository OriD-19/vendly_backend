from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_
from fastapi import HTTPException, status
from app.models.review import Review
from app.models.product import Product
from app.models.user import User
from app.models.store import Store
from app.schemas.review import ReviewCreate, ReviewUpdate, ProductReviewStats, StoreReviewStats, StoreScoreResponse


class ReviewService:
    """
    Service for managing product reviews.
    
    Features:
    - CRUD operations for reviews
    - One review per customer per product
    - Review statistics and aggregations
    - Store-level review aggregations
    """

    def __init__(self, db: Session):
        self.db = db

    # ========== CRUD Operations ==========

    def create_review(self, review_data: ReviewCreate, customer_id: int) -> Review:
        """
        Create a new review for a product.
        
        Args:
            review_data: Review creation data
            customer_id: ID of the customer creating the review
            
        Returns:
            Created review object
            
        Raises:
            HTTPException 404: If product not found
            HTTPException 400: If customer already reviewed this product
        """
        # Check if product exists
        product = self.db.query(Product).filter(Product.id == review_data.product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id {review_data.product_id} not found"
            )
        
        # Check if customer already reviewed this product
        existing_review = self.db.query(Review).filter(
            and_(
                Review.customer_id == customer_id,
                Review.product_id == review_data.product_id
            )
        ).first()
        
        if existing_review:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already reviewed this product. Use PUT to update your review."
            )
        
        # Create review
        review = Review(
            rating=review_data.rating,
            comment=review_data.comment,
            customer_id=customer_id,
            product_id=review_data.product_id
        )
        
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        
        return review

    def get_review_by_id(self, review_id: int) -> Review:
        """
        Get a review by its ID.
        
        Args:
            review_id: The ID of the review
            
        Returns:
            Review object with customer relationship loaded
            
        Raises:
            HTTPException 404: If review not found
        """
        review = self.db.query(Review).options(
            joinedload(Review.customer)
        ).filter(Review.id == review_id).first()
        
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Review with id {review_id} not found"
            )
        
        return review

    def get_customer_review_for_product(self, customer_id: int, product_id: int) -> Optional[Review]:
        """
        Get a customer's review for a specific product.
        
        Args:
            customer_id: The ID of the customer
            product_id: The ID of the product
            
        Returns:
            Review object with customer relationship loaded, or None if not found
        """
        review = self.db.query(Review).options(
            joinedload(Review.customer)
        ).filter(
            and_(
                Review.customer_id == customer_id,
                Review.product_id == product_id
            )
        ).first()
        
        return review

    def update_review(self, review_id: int, review_data: ReviewUpdate, customer_id: int) -> Review:
        """
        Update a review.
        
        Only the customer who created the review can update it.
        
        Args:
            review_id: The ID of the review to update
            review_data: Updated review data
            customer_id: ID of the customer attempting to update
            
        Returns:
            Updated review object
            
        Raises:
            HTTPException 404: If review not found
            HTTPException 403: If customer doesn't own this review
        """
        review = self.get_review_by_id(review_id)
        
        # Check if customer owns this review
        if review.customer_id != customer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own reviews"
            )
        
        # Update review
        update_data = review_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(review, field, value)
        
        self.db.commit()
        self.db.refresh(review)
        
        return review

    def delete_review(self, review_id: int, customer_id: int) -> None:
        """
        Delete a review.
        
        Only the customer who created the review can delete it.
        
        Args:
            review_id: The ID of the review to delete
            customer_id: ID of the customer attempting to delete
            
        Raises:
            HTTPException 404: If review not found
            HTTPException 403: If customer doesn't own this review
        """
        review = self.get_review_by_id(review_id)
        
        # Check if customer owns this review
        if review.customer_id != customer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own reviews"
            )
        
        self.db.delete(review)
        self.db.commit()

    # ========== Query Operations ==========

    def get_product_reviews(
        self,
        product_id: int,
        skip: int = 0,
        limit: int = 100,
        rating_filter: Optional[int] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> List[Review]:
        """
        Get all reviews for a product with filtering and sorting.
        
        Args:
            product_id: The ID of the product
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return
            rating_filter: Filter by specific rating (1-5)
            sort_by: Field to sort by (created_at, rating)
            sort_order: Sort order (asc or desc)
            
        Returns:
            List of reviews
            
        Raises:
            HTTPException 404: If product not found
        """
        # Verify product exists
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id {product_id} not found"
            )
        
        query = self.db.query(Review).options(
            joinedload(Review.customer)
        ).filter(Review.product_id == product_id)
        
        # Apply rating filter
        if rating_filter is not None:
            if rating_filter < 1 or rating_filter > 5:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Rating filter must be between 1 and 5"
                )
            query = query.filter(Review.rating == rating_filter)
        
        # Apply sorting
        if sort_by == "rating":
            sort_column = Review.rating
        else:
            sort_column = Review.created_at
        
        if sort_order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Apply pagination
        reviews = query.offset(skip).limit(limit).all()
        
        return reviews

    def get_customer_reviews(
        self,
        customer_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Review]:
        """
        Get all reviews created by a customer.
        
        Args:
            customer_id: The ID of the customer
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of reviews with customer relationship loaded
        """
        reviews = (
            self.db.query(Review)
            .options(joinedload(Review.customer))
            .filter(Review.customer_id == customer_id)
            .order_by(Review.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        return reviews

    # ========== Statistics Operations ==========

    def get_product_review_stats(self, product_id: int) -> ProductReviewStats:
        """
        Get review statistics for a product.
        
        Args:
            product_id: The ID of the product
            
        Returns:
            ProductReviewStats object with aggregated data
            
        Raises:
            HTTPException 404: If product not found
        """
        # Verify product exists
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id {product_id} not found"
            )
        
        # Get all reviews for this product
        reviews = self.db.query(Review).filter(Review.product_id == product_id).all()
        
        if not reviews:
            return ProductReviewStats(
                product_id=product_id,
                total_reviews=0,
                average_rating=0.0,
                rating_distribution={1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            )
        
        # Calculate statistics
        total_reviews = len(reviews)
        ratings = [review.rating for review in reviews]
        average_rating = sum(ratings) / total_reviews if total_reviews > 0 else 0.0
        
        # Rating distribution
        rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for rating in ratings:
            rating_distribution[rating] += 1
        
        return ProductReviewStats(
            product_id=product_id,
            total_reviews=total_reviews,
            average_rating=round(average_rating, 2),
            rating_distribution=rating_distribution
        )

    def get_store_review_stats(self, store_id: int) -> StoreReviewStats:
        """
        Get aggregated review statistics for all products in a store.
        
        Args:
            store_id: The ID of the store
            
        Returns:
            StoreReviewStats object with aggregated data
            
        Raises:
            HTTPException 404: If store not found
        """
        # Verify store exists
        store = self.db.query(Store).filter(Store.id == store_id).first()
        if not store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Store with id {store_id} not found"
            )
        
        # Get all reviews for products in this store
        reviews = (
            self.db.query(Review)
            .join(Product, Review.product_id == Product.id)
            .filter(Product.store_id == store_id)
            .all()
        )
        
        if not reviews:
            return StoreReviewStats(
                store_id=store_id,
                total_reviews=0,
                average_rating=0.0,
                total_products_reviewed=0,
                rating_distribution={1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            )
        
        # Calculate statistics
        total_reviews = len(reviews)
        ratings = [review.rating for review in reviews]
        average_rating = sum(ratings) / total_reviews if total_reviews > 0 else 0.0
        
        # Rating distribution
        rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for rating in ratings:
            rating_distribution[rating] += 1
        
        # Count unique products with reviews
        unique_products = len(set(review.product_id for review in reviews))
        
        return StoreReviewStats(
            store_id=store_id,
            total_reviews=total_reviews,
            average_rating=round(average_rating, 2),
            total_products_reviewed=unique_products,
            rating_distribution=rating_distribution
        )

    def get_overall_product_score(self, product_id: int) -> float:
        """
        Get the overall average score for a product.
        
        Args:
            product_id: The ID of the product
            
        Returns:
            Average rating (0-5)
        """
        stats = self.get_product_review_stats(product_id)
        return stats.average_rating

    def get_overall_store_score(self, store_id: int) -> float:
        """
        Get the overall average score for a store.
        
        Args:
            store_id: The ID of the store
            
        Returns:
            Average rating (0-5)
        """
        stats = self.get_store_review_stats(store_id)
        return stats.average_rating

    def get_all_stores_scores(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[StoreScoreResponse]:
        """
        Get average scores for multiple stores with pagination.
        
        Args:
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of StoreScoreResponse objects with store scores
        """
        # Get all stores with pagination
        stores = (
            self.db.query(Store)
            .order_by(Store.id)
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        results = []
        
        for store in stores:
            # Get all reviews for products in this store
            reviews = (
                self.db.query(Review)
                .join(Product, Review.product_id == Product.id)
                .filter(Product.store_id == store.id)
                .all()
            )
            
            # Calculate average rating
            if reviews:
                total_reviews = len(reviews)
                ratings = [review.rating for review in reviews]
                average_rating = sum(ratings) / total_reviews
            else:
                total_reviews = 0
                average_rating = 0.0
            
            results.append(
                StoreScoreResponse(
                    store_id=store.id,
                    store_name=store.name,
                    average_rating=round(average_rating, 2),
                    total_reviews=total_reviews
                )
            )
        
        return results
