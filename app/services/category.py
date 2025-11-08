from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from fastapi import HTTPException, status
from app.models.category import Category
from app.models.product import Product
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryService:
    """
    Service for managing categories and their associated products.
    
    Provides CRUD operations for categories and methods to query products
    within specific categories with filtering and search capabilities.
    """

    def __init__(self, db: Session):
        self.db = db

    # ========== CRUD Operations ==========

    def create_category(self, category_data: CategoryCreate) -> Category:
        """
        Create a new category.
        
        Args:
            category_data: Category creation data
            
        Returns:
            Created category object
            
        Raises:
            HTTPException 400: If category name already exists
        """
        # Check if category already exists
        existing_category = self.db.query(Category).filter(
            func.lower(Category.name) == func.lower(category_data.name)
        ).first()
        
        if existing_category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category '{category_data.name}' already exists"
            )
        
        # Create new category
        category = Category(**category_data.model_dump())
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        
        return category

    def create_categories_bulk(self, categories_data: List[CategoryCreate]) -> Tuple[List[Category], List[dict]]:
        """
        Create multiple categories at once.
        
        This method will:
        - Skip categories that already exist (case-insensitive name check)
        - Create all new categories in a single transaction
        - Return both created categories and skipped ones
        
        Args:
            categories_data: List of category creation data
            
        Returns:
            Tuple of (created_categories, skipped_categories)
            - created_categories: List of successfully created Category objects
            - skipped_categories: List of dicts with info about skipped categories
        """
        created_categories = []
        skipped_categories = []
        
        # Get all existing category names (lowercase for comparison)
        existing_names = {
            name[0].lower() for name in 
            self.db.query(Category.name).all()
        }
        
        # Process each category
        for category_data in categories_data:
            category_name_lower = category_data.name.lower()
            
            # Check if category already exists
            if category_name_lower in existing_names:
                skipped_categories.append({
                    "name": category_data.name,
                    "reason": "Category already exists"
                })
                continue
            
            # Create new category
            category = Category(**category_data.model_dump())
            self.db.add(category)
            created_categories.append(category)
            
            # Add to existing names to prevent duplicates within the same batch
            existing_names.add(category_name_lower)
        
        # Commit all at once
        if created_categories:
            self.db.commit()
            # Refresh all created categories
            for category in created_categories:
                self.db.refresh(category)
        
        return created_categories, skipped_categories

    def get_category_by_id(self, category_id: int) -> Category:
        """
        Get a category by its ID.
        
        Args:
            category_id: The ID of the category to retrieve
            
        Returns:
            Category object
            
        Raises:
            HTTPException 404: If category not found
        """
        category = self.db.query(Category).filter(Category.id == category_id).first()
        
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with id {category_id} not found"
            )
        
        return category

    def get_category_by_name(self, name: str) -> Category:
        """
        Get a category by its name (case-insensitive).
        
        Args:
            name: The name of the category
            
        Returns:
            Category object
            
        Raises:
            HTTPException 404: If category not found
        """
        category = self.db.query(Category).filter(
            func.lower(Category.name) == func.lower(name)
        ).first()
        
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category '{name}' not found"
            )
        
        return category

    def get_all_categories(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        sort_by: str = "name",
        sort_order: str = "asc"
    ) -> List[Category]:
        """
        Get all categories with optional search and sorting.
        
        Args:
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return
            search: Search term to filter categories by name
            sort_by: Field to sort by (name, created_at, updated_at)
            sort_order: Sort order (asc or desc)
            
        Returns:
            List of categories
        """
        query = self.db.query(Category)
        
        # Apply search filter
        if search:
            query = query.filter(
                Category.name.ilike(f"%{search}%")
            )
        
        # Apply sorting
        sort_column = getattr(Category, sort_by, Category.name)
        if sort_order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Apply pagination
        categories = query.offset(skip).limit(limit).all()
        
        return categories

    def update_category(self, category_id: int, category_data: CategoryUpdate) -> Category:
        """
        Update a category.
        
        Args:
            category_id: The ID of the category to update
            category_data: Updated category data
            
        Returns:
            Updated category object
            
        Raises:
            HTTPException 404: If category not found
            HTTPException 400: If new name already exists
        """
        category = self.get_category_by_id(category_id)
        
        # Check if new name already exists (if name is being updated)
        if category_data.name and category_data.name != category.name:
            existing_category = self.db.query(Category).filter(
                func.lower(Category.name) == func.lower(category_data.name)
            ).first()
            
            if existing_category:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Category '{category_data.name}' already exists"
                )
        
        # Update category
        update_data = category_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(category, field, value)
        
        self.db.commit()
        self.db.refresh(category)
        
        return category

    def delete_category(self, category_id: int) -> None:
        """
        Delete a category.
        
        Note: This will fail if there are products associated with this category
        due to foreign key constraints. Consider moving products to another
        category first or implementing cascade delete.
        
        Args:
            category_id: The ID of the category to delete
            
        Raises:
            HTTPException 404: If category not found
            HTTPException 400: If category has associated products
        """
        category = self.get_category_by_id(category_id)
        
        # Check if category has products
        product_count = self.db.query(func.count(Product.id)).filter(
            Product.category_id == category_id
        ).scalar()
        
        if product_count and product_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete category '{category.name}' because it has {product_count} associated product(s). Please reassign or delete the products first."
            )
        
        self.db.delete(category)
        self.db.commit()

    # ========== Product Filtering Methods ==========

    def get_category_products(
        self,
        category_id: int,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        in_stock_only: bool = False,
        active_only: bool = True,
        store_id: Optional[int] = None,
        sort_by: str = "name",
        sort_order: str = "asc"
    ) -> List[Product]:
        """
        Get all products in a specific category with advanced filtering.
        
        Args:
            category_id: The ID of the category
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return
            search: Search term to filter products by name or description
            min_price: Minimum price filter
            max_price: Maximum price filter
            in_stock_only: If True, only return products with stock > 0
            active_only: If True, only return active products
            store_id: Filter by specific store
            sort_by: Field to sort by (name, price, created_at, stock)
            sort_order: Sort order (asc or desc)
            
        Returns:
            List of products in the category
            
        Raises:
            HTTPException 404: If category not found
        """
        # Verify category exists
        self.get_category_by_id(category_id)
        
        query = self.db.query(Product).filter(Product.category_id == category_id)
        
        # Apply filters
        if search:
            query = query.filter(
                or_(
                    Product.name.ilike(f"%{search}%"),
                    Product.short_description.ilike(f"%{search}%"),
                    Product.long_description.ilike(f"%{search}%")
                )
            )
        
        if min_price is not None:
            query = query.filter(Product.price >= min_price)
        
        if max_price is not None:
            query = query.filter(Product.price <= max_price)
        
        if in_stock_only:
            query = query.filter(Product.stock > 0)
        
        if active_only:
            query = query.filter(Product.is_active == True)
        
        if store_id is not None:
            query = query.filter(Product.store_id == store_id)
        
        # Apply sorting
        sort_column = getattr(Product, sort_by, Product.name)
        if sort_order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Apply pagination
        products = query.offset(skip).limit(limit).all()
        
        return products

    def get_category_products_by_name(
        self,
        category_name: str,
        skip: int = 0,
        limit: int = 100,
        **filters
    ) -> List[Product]:
        """
        Get all products in a category by category name.
        
        Args:
            category_name: The name of the category
            skip: Number of records to skip
            limit: Maximum number of records to return
            **filters: Additional filters (same as get_category_products)
            
        Returns:
            List of products in the category
            
        Raises:
            HTTPException 404: If category not found
        """
        category = self.get_category_by_name(category_name)
        return self.get_category_products(category.id, skip, limit, **filters)

    def get_category_product_count(self, category_id: int, active_only: bool = True) -> int:
        """
        Get the count of products in a category.
        
        Args:
            category_id: The ID of the category
            active_only: If True, only count active products
            
        Returns:
            Number of products in the category
            
        Raises:
            HTTPException 404: If category not found
        """
        # Verify category exists
        self.get_category_by_id(category_id)
        
        query = self.db.query(func.count(Product.id)).filter(
            Product.category_id == category_id
        )
        
        if active_only:
            query = query.filter(Product.is_active == True)
        
        count = query.scalar() or 0
        return count

    def get_category_statistics(self, category_id: int) -> dict:
        """
        Get statistics for a category.
        
        Returns:
            - Total products
            - Active products
            - Inactive products
            - Products in stock
            - Products out of stock
            - Average price
            - Price range (min/max)
            - Total inventory value
            
        Args:
            category_id: The ID of the category
            
        Returns:
            Dictionary containing category statistics
            
        Raises:
            HTTPException 404: If category not found
        """
        category = self.get_category_by_id(category_id)
        
        # Get all products in category
        products = self.db.query(Product).filter(
            Product.category_id == category_id
        ).all()
        
        if not products:
            return {
                "category_id": category_id,
                "category_name": category.name,
                "total_products": 0,
                "active_products": 0,
                "inactive_products": 0,
                "in_stock_products": 0,
                "out_of_stock_products": 0,
                "average_price": 0,
                "min_price": 0,
                "max_price": 0,
                "total_inventory_value": 0,
                "total_stock_quantity": 0
            }
        
        # Calculate statistics
        active_products = [p for p in products if p.is_active]
        inactive_products = [p for p in products if not p.is_active]
        in_stock = [p for p in products if p.stock > 0]
        out_of_stock = [p for p in products if p.stock == 0]
        
        prices = [p.price for p in products]
        average_price = sum(prices) / len(prices) if prices else 0
        min_price = min(prices) if prices else 0
        max_price = max(prices) if prices else 0
        
        # Total inventory value (price * stock)
        inventory_value = sum(p.price * p.stock for p in products)
        total_stock = sum(p.stock for p in products)
        
        return {
            "category_id": category_id,
            "category_name": category.name,
            "total_products": len(products),
            "active_products": len(active_products),
            "inactive_products": len(inactive_products),
            "in_stock_products": len(in_stock),
            "out_of_stock_products": len(out_of_stock),
            "average_price": round(average_price, 2),
            "min_price": min_price,
            "max_price": max_price,
            "total_inventory_value": round(inventory_value, 2),
            "total_stock_quantity": total_stock
        }

    # ========== Utility Methods ==========

    def move_products_to_category(
        self,
        source_category_id: int,
        target_category_id: int
    ) -> int:
        """
        Move all products from one category to another.
        
        Useful before deleting a category.
        
        Args:
            source_category_id: The ID of the source category
            target_category_id: The ID of the target category
            
        Returns:
            Number of products moved
            
        Raises:
            HTTPException 404: If source or target category not found
            HTTPException 400: If source and target are the same
        """
        if source_category_id == target_category_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Source and target categories cannot be the same"
            )
        
        # Verify both categories exist
        source_category = self.get_category_by_id(source_category_id)
        self.get_category_by_id(target_category_id)
        
        # Move products
        products_moved = self.db.query(Product).filter(
            Product.category_id == source_category_id
        ).update({Product.category_id: target_category_id})
        
        self.db.commit()
        
        return products_moved

    def search_categories(self, search_term: str, limit: int = 10) -> List[Category]:
        """
        Search categories by name.
        
        Args:
            search_term: The search term
            limit: Maximum number of results
            
        Returns:
            List of matching categories
        """
        categories = self.db.query(Category).filter(
            Category.name.ilike(f"%{search_term}%")
        ).limit(limit).all()
        
        return categories

    def get_categories_with_product_count(self) -> List[dict]:
        """
        Get all categories with their product counts.
        
        Returns:
            List of dictionaries with category info and product count
        """
        categories = self.db.query(Category).all()
        
        result = []
        for category in categories:
            product_count = self.db.query(func.count(Product.id)).filter(
                Product.category_id == category.id,
                Product.is_active == True
            ).scalar() or 0
            
            result.append({
                "id": category.id,
                "name": category.name,
                "product_count": product_count,
                "created_at": category.created_at,
                "updated_at": category.updated_at
            })
        
        return result
