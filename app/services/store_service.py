from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from fastapi import HTTPException, status
from app.models.store import Store
from app.models.product import Product
from app.models.user import User, UserType
from app.schemas.store import StoreCreate, StoreUpdate


class StoreService:
    """
    Service for managing stores and their products.
    
    Store owners can create and manage their stores.
    Customers can browse stores and their products.
    """

    def __init__(self, db: Session):
        self.db = db

    # ========== Authorization Helpers ==========

    @staticmethod
    def verify_store_owner(user: User) -> None:
        """
        Verify that the user is a store owner.
        
        Args:
            user: The user to verify
            
        Raises:
            HTTPException 403: If user is not a store owner
        """
        if user.user_type != UserType.STORE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only store owners can perform this action"
            )

    def verify_store_ownership(self, store_id: int, user_id: int) -> Store:
        """
        Verify that the user owns the specified store.
        
        Args:
            store_id: The ID of the store
            user_id: The ID of the user
            
        Returns:
            Store object if user is the owner
            
        Raises:
            HTTPException 404: If store not found
            HTTPException 403: If user doesn't own the store
        """
        store = self.get_store_by_id(store_id)
        
        if store.owner_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this store"
            )
        
        return store

    # ========== CRUD Operations ==========

    def create_store(self, store_data: StoreCreate, owner: User) -> Store:
        """
        Create a new store.
        
        Args:
            store_data: Store creation data
            owner: The user creating the store (must be store owner type)
            
        Returns:
            Created store object
            
        Raises:
            HTTPException 403: If user is not a store owner
            HTTPException 400: If store name already exists
        """
        # Verify user is a store owner
        self.verify_store_owner(owner)
        
        # Check if store name already exists
        existing_store = self.db.query(Store).filter(
            func.lower(Store.name) == func.lower(store_data.name)
        ).first()
        
        if existing_store:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Store name '{store_data.name}' already exists"
            )
        
        # Create store
        store = Store(**store_data.model_dump())
        store.owner_id = owner.id  # Ensure owner_id matches authenticated user
        
        self.db.add(store)
        self.db.commit()
        self.db.refresh(store)
        
        return store

    def get_store_by_id(self, store_id: int) -> Store:
        """
        Get a store by its ID.
        
        Args:
            store_id: The ID of the store
            
        Returns:
            Store object
            
        Raises:
            HTTPException 404: If store not found
        """
        store = self.db.query(Store).filter(Store.id == store_id).first()
        
        if not store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Store with id {store_id} not found"
            )
        
        return store

    def get_store_by_name(self, name: str) -> Store:
        """
        Get a store by its name (case-insensitive).
        
        Args:
            name: The name of the store
            
        Returns:
            Store object
            
        Raises:
            HTTPException 404: If store not found
        """
        store = self.db.query(Store).filter(
            func.lower(Store.name) == func.lower(name)
        ).first()
        
        if not store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Store '{name}' not found"
            )
        
        return store

    def get_all_stores(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        store_type: Optional[str] = None,
        location: Optional[str] = None,
        sort_by: str = "name",
        sort_order: str = "asc"
    ) -> List[Store]:
        """
        Get all stores with optional filtering and search.
        
        Args:
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return
            search: Search term to filter stores by name
            store_type: Filter by store type
            location: Filter by store location
            sort_by: Field to sort by (name, created_at, type)
            sort_order: Sort order (asc or desc)
            
        Returns:
            List of stores
        """
        query = self.db.query(Store)
        
        # Apply search filter
        if search:
            query = query.filter(
                or_(
                    Store.name.ilike(f"%{search}%"),
                    Store.store_location.ilike(f"%{search}%"),
                    Store.type.ilike(f"%{search}%")
                )
            )
        
        # Filter by store type
        if store_type:
            query = query.filter(Store.type.ilike(f"%{store_type}%"))
        
        # Filter by location
        if location:
            query = query.filter(Store.store_location.ilike(f"%{location}%"))
        
        # Apply sorting
        sort_column = getattr(Store, sort_by, Store.name)
        if sort_order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Apply pagination
        stores = query.offset(skip).limit(limit).all()
        
        return stores

    def get_user_stores(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Store]:
        """
        Get all stores owned by a specific user.
        
        Args:
            user_id: The ID of the user
            skip: Pagination offset
            limit: Maximum number of results
            
        Returns:
            List of stores owned by the user
        """
        stores = self.db.query(Store).filter(
            Store.owner_id == user_id
        ).offset(skip).limit(limit).all()
        
        return stores

    def update_store(self, store_id: int, store_data: StoreUpdate, user: User) -> Store:
        """
        Update a store.
        
        Args:
            store_id: The ID of the store to update
            store_data: Updated store data
            user: The user performing the update
            
        Returns:
            Updated store object
            
        Raises:
            HTTPException 403: If user is not the store owner
            HTTPException 404: If store not found
            HTTPException 400: If new name already exists
        """
        # Verify ownership
        store = self.verify_store_ownership(store_id, user.id)
        
        # Check if new name already exists (if name is being updated)
        if store_data.name and store_data.name != store.name:
            existing_store = self.db.query(Store).filter(
                func.lower(Store.name) == func.lower(store_data.name)
            ).first()
            
            if existing_store:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Store name '{store_data.name}' already exists"
                )
        
        # Update store
        update_data = store_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(store, field, value)
        
        self.db.commit()
        self.db.refresh(store)
        
        return store

    def delete_store(self, store_id: int, user: User) -> None:
        """
        Delete a store.
        
        Note: This will fail if there are products associated with this store
        due to foreign key constraints. Consider soft delete or cascade delete.
        
        Args:
            store_id: The ID of the store to delete
            user: The user performing the deletion
            
        Raises:
            HTTPException 403: If user is not the store owner
            HTTPException 404: If store not found
            HTTPException 400: If store has associated products
        """
        # Verify ownership
        store = self.verify_store_ownership(store_id, user.id)
        
        # Check if store has products
        product_count = self.db.query(func.count(Product.id)).filter(
            Product.store_id == store_id
        ).scalar()
        
        if product_count and product_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete store '{store.name}' because it has {product_count} associated product(s). Please delete the products first."
            )
        
        self.db.delete(store)
        self.db.commit()

    # ========== Product Management ==========

    def get_store_products(
        self,
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
        sort_order: str = "asc"
    ) -> List[Product]:
        """
        Get all products for a specific store with filtering.
        
        Public endpoint - anyone can browse store products.
        
        Args:
            store_id: The ID of the store
            skip: Pagination offset
            limit: Maximum number of results
            search: Search term for product name/description
            category_id: Filter by category
            min_price: Minimum price filter
            max_price: Maximum price filter
            in_stock_only: Only show products with stock > 0
            active_only: Only show active products
            sort_by: Field to sort by (name, price, created_at, stock)
            sort_order: Sort order (asc or desc)
            
        Returns:
            List of products
            
        Raises:
            HTTPException 404: If store not found
        """
        # Verify store exists
        self.get_store_by_id(store_id)
        
        query = self.db.query(Product).filter(Product.store_id == store_id)
        
        # Apply filters
        if search:
            query = query.filter(
                or_(
                    Product.name.ilike(f"%{search}%"),
                    Product.short_description.ilike(f"%{search}%"),
                    Product.long_description.ilike(f"%{search}%")
                )
            )
        
        if category_id is not None:
            query = query.filter(Product.category_id == category_id)
        
        if min_price is not None:
            query = query.filter(Product.price >= min_price)
        
        if max_price is not None:
            query = query.filter(Product.price <= max_price)
        
        if in_stock_only:
            query = query.filter(Product.stock > 0)
        
        if active_only:
            query = query.filter(Product.is_active == True)
        
        # Apply sorting
        sort_column = getattr(Product, sort_by, Product.name)
        if sort_order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Apply pagination
        products = query.offset(skip).limit(limit).all()
        
        return products

    # ========== Store Statistics ==========

    def get_store_statistics(self, store_id: int, user: User) -> dict:
        """
        Get statistics for a store.
        
        Only accessible by the store owner.
        
        Returns:
            - Total products
            - Active/inactive products
            - Products in stock/out of stock
            - Total inventory value
            - Average product price
            
        Args:
            store_id: The ID of the store
            user: The user requesting statistics (must be store owner)
            
        Returns:
            Dictionary containing store statistics
            
        Raises:
            HTTPException 403: If user is not the store owner
            HTTPException 404: If store not found
        """
        # Verify ownership
        store = self.verify_store_ownership(store_id, user.id)
        
        # Get all products for the store
        products = self.db.query(Product).filter(Product.store_id == store_id).all()
        
        if not products:
            return {
                "store_id": store_id,
                "store_name": store.name,
                "total_products": 0,
                "active_products": 0,
                "inactive_products": 0,
                "in_stock_products": 0,
                "out_of_stock_products": 0,
                "total_inventory_value": 0,
                "average_price": 0,
                "total_stock_quantity": 0
            }
        
        # Calculate statistics
        active_products = [p for p in products if p.is_active]
        inactive_products = [p for p in products if not p.is_active]
        in_stock = [p for p in products if p.stock > 0]
        out_of_stock = [p for p in products if p.stock == 0]
        
        prices = [p.price for p in products]
        average_price = sum(prices) / len(prices) if prices else 0
        
        # Total inventory value (price * stock)
        inventory_value = sum(p.price * p.stock for p in products)
        total_stock = sum(p.stock for p in products)
        
        return {
            "store_id": store_id,
            "store_name": store.name,
            "total_products": len(products),
            "active_products": len(active_products),
            "inactive_products": len(inactive_products),
            "in_stock_products": len(in_stock),
            "out_of_stock_products": len(out_of_stock),
            "total_inventory_value": round(inventory_value, 2),
            "average_price": round(average_price, 2),
            "total_stock_quantity": total_stock
        }

    # ========== Utility Methods ==========

    def search_stores(self, search_term: str, limit: int = 10) -> List[Store]:
        """
        Search stores by name or location.
        
        Args:
            search_term: The search term
            limit: Maximum number of results
            
        Returns:
            List of matching stores
        """
        stores = self.db.query(Store).filter(
            or_(
                Store.name.ilike(f"%{search_term}%"),
                Store.store_location.ilike(f"%{search_term}%")
            )
        ).limit(limit).all()
        
        return stores

    def get_store_product_count(self, store_id: int, active_only: bool = True) -> int:
        """
        Get the count of products in a store.
        
        Args:
            store_id: The ID of the store
            active_only: If True, only count active products
            
        Returns:
            Number of products in the store
            
        Raises:
            HTTPException 404: If store not found
        """
        # Verify store exists
        self.get_store_by_id(store_id)
        
        query = self.db.query(func.count(Product.id)).filter(
            Product.store_id == store_id
        )
        
        if active_only:
            query = query.filter(Product.is_active == True)
        
        count = query.scalar() or 0
        return count
