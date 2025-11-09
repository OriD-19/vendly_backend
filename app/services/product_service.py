from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi import HTTPException, status
from app.models.product import Product, Tag, ProductImage, ProductTag
from app.models.category import Category
from app.models.store import Store
from app.schemas.product import ProductCreate, ProductUpdate, TagCreate, TagUpdate


class ProductService:
    def __init__(self, db_session: Session):
        self.db = db_session
    
    # ========== Product CRUD Operations ==========
    
    def create_product(self, product_data: ProductCreate) -> Product:
        """
        Create a new product with optional tags.
        Validates that store and category exist before creating.
        """
        # Validate store exists
        store = self.db.query(Store).filter(Store.id == product_data.store_id).first()
        if not store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Store with id {product_data.store_id} not found"
            )
        
        # Validate category exists
        category = self.db.query(Category).filter(Category.id == product_data.category_id).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with id {product_data.category_id} not found"
            )
        
        # Create product (exclude tag_ids from the model)
        product_dict = product_data.model_dump(exclude={'tag_ids'})
        new_product = Product(**product_dict)
        
        # Add tags if provided
        if product_data.tag_ids:
            tags = self.db.query(Tag).filter(Tag.id.in_(product_data.tag_ids)).all()
            if len(tags) != len(product_data.tag_ids):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="One or more tag IDs not found"
                )
            new_product.tags = tags
        
        self.db.add(new_product)
        self.db.commit()
        self.db.refresh(new_product)
        
        return new_product

    def create_products_bulk(self, products_data: List[ProductCreate]) -> Tuple[List[Product], List[dict]]:
        """
        Create multiple products at once.
        
        This method will:
        - Validate each product's store and category
        - Skip products that fail validation (collect errors)
        - Create all valid products in a single transaction
        - Return both created products and failed ones with error messages
        
        Args:
            products_data: List of product creation data
            
        Returns:
            Tuple of (created_products, failed_products)
            - created_products: List of successfully created Product objects
            - failed_products: List of dicts with info about failed products
        """
        created_products = []
        failed_products = []
        
        # Pre-fetch all stores and categories to minimize DB queries
        store_ids = {p.store_id for p in products_data}
        category_ids = {p.category_id for p in products_data}
        
        existing_stores = {
            store.id: store for store in 
            self.db.query(Store).filter(Store.id.in_(store_ids)).all()
        }
        
        existing_categories = {
            category.id: category for category in 
            self.db.query(Category).filter(Category.id.in_(category_ids)).all()
        }
        
        # Get all unique tag IDs from all products
        all_tag_ids = set()
        for product_data in products_data:
            if product_data.tag_ids:
                all_tag_ids.update(product_data.tag_ids)
        
        existing_tags = {}
        if all_tag_ids:
            existing_tags = {
                tag.id: tag for tag in 
                self.db.query(Tag).filter(Tag.id.in_(all_tag_ids)).all()
            }
        
        # Process each product
        for idx, product_data in enumerate(products_data):
            try:
                # Validate store exists
                if product_data.store_id not in existing_stores:
                    failed_products.append({
                        "index": idx,
                        "product_name": product_data.name,
                        "reason": f"Store with id {product_data.store_id} not found"
                    })
                    continue
                
                # Validate category exists
                if product_data.category_id not in existing_categories:
                    failed_products.append({
                        "index": idx,
                        "product_name": product_data.name,
                        "reason": f"Category with id {product_data.category_id} not found"
                    })
                    continue
                
                # Validate tags if provided
                if product_data.tag_ids:
                    missing_tags = [tid for tid in product_data.tag_ids if tid not in existing_tags]
                    if missing_tags:
                        failed_products.append({
                            "index": idx,
                            "product_name": product_data.name,
                            "reason": f"Tag IDs not found: {missing_tags}"
                        })
                        continue
                
                # Create product
                product_dict = product_data.model_dump(exclude={'tag_ids'})
                new_product = Product(**product_dict)
                
                # Add tags if provided
                if product_data.tag_ids:
                    new_product.tags = [existing_tags[tid] for tid in product_data.tag_ids]
                
                self.db.add(new_product)
                created_products.append(new_product)
                
            except Exception as e:
                failed_products.append({
                    "index": idx,
                    "product_name": product_data.name,
                    "reason": str(e)
                })
        
        # Commit all valid products at once
        if created_products:
            try:
                self.db.commit()
                # Refresh all created products
                for product in created_products:
                    self.db.refresh(product)
            except Exception as e:
                self.db.rollback()
                # If commit fails, mark all as failed
                for product in created_products:
                    failed_products.append({
                        "index": len(failed_products),
                        "product_name": product.name,
                        "reason": f"Database commit failed: {str(e)}"
                    })
                created_products = []
        
        return created_products, failed_products
    
    def get_product_by_id(self, product_id: int) -> Product:
        """
        Get a single product by ID with all relationships loaded.
        Raises HTTPException if not found.
        """
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id {product_id} not found"
            )
        return product
    
    def get_all_products(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        category_id: Optional[int] = None,
        store_id: Optional[int] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        in_stock: Optional[bool] = None,
        search: Optional[str] = None
    ) -> List[Product]:
        """
        Get all products with optional filtering and pagination.
        Supports filtering by: active status, category, store, price range, stock, and search term.
        """
        query = self.db.query(Product)
        
        # Apply filters
        if is_active is not None:
            query = query.filter(Product.is_active == is_active)
        
        if category_id is not None:
            query = query.filter(Product.category_id == category_id)
        
        if store_id is not None:
            query = query.filter(Product.store_id == store_id)
        
        if min_price is not None:
            query = query.filter(Product.price >= min_price)
        
        if max_price is not None:
            query = query.filter(Product.price <= max_price)
        
        if in_stock is not None:
            if in_stock:
                query = query.filter(Product.stock > 0)
            else:
                query = query.filter(Product.stock == 0)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Product.name.ilike(search_term),
                    Product.short_description.ilike(search_term),
                    Product.long_description.ilike(search_term)
                )
            )
        
        # Apply pagination
        products = query.offset(skip).limit(limit).all()
        return products
    
    def update_product(self, product_id: int, product_data: ProductUpdate) -> Product:
        """
        Update a product's information.
        Only updates fields that are provided (not None).
        """
        product = self.get_product_by_id(product_id)
        
        # Update only provided fields
        update_data = product_data.model_dump(exclude_unset=True, exclude={'tag_ids'})
        
        # Validate category if being updated
        if 'category_id' in update_data:
            category = self.db.query(Category).filter(
                Category.id == update_data['category_id']
            ).first()
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Category with id {update_data['category_id']} not found"
                )
        
        # Update product fields
        for field, value in update_data.items():
            setattr(product, field, value)
        
        # Update tags if provided
        if product_data.tag_ids is not None:
            tags = self.db.query(Tag).filter(Tag.id.in_(product_data.tag_ids)).all()
            if len(tags) != len(product_data.tag_ids):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="One or more tag IDs not found"
                )
            product.tags = tags
        
        self.db.commit()
        self.db.refresh(product)
        
        return product
    
    def delete_product(self, product_id: int) -> bool:
        """
        Delete a product by ID.
        Also deletes associated product images and tag relationships.
        """
        product = self.get_product_by_id(product_id)
        
        self.db.delete(product)
        self.db.commit()
        
        return True
    
    def deactivate_product(self, product_id: int) -> Product:
        """
        Soft delete: Mark a product as inactive instead of deleting it.
        """
        product = self.get_product_by_id(product_id)
        product.is_active = False
        
        self.db.commit()
        self.db.refresh(product)
        
        return product
    
    def activate_product(self, product_id: int) -> Product:
        """
        Reactivate a previously deactivated product.
        """
        product = self.get_product_by_id(product_id)
        product.is_active = True
        
        self.db.commit()
        self.db.refresh(product)
        
        return product
    
    def update_stock(self, product_id: int, quantity: int, operation: str = "set") -> Product:
        """
        Update product stock.
        Operations: 'set' (set to exact value), 'add' (increase), 'subtract' (decrease)
        """
        product = self.get_product_by_id(product_id)
        
        if operation == "set":
            product.stock = quantity
        elif operation == "add":
            product.stock += quantity
        elif operation == "subtract":
            new_stock = product.stock - quantity
            if new_stock < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot subtract more than available stock"
                )
            product.stock = new_stock
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid operation. Use 'set', 'add', or 'subtract'"
            )
        
        self.db.commit()
        self.db.refresh(product)
        
        return product
    
    def increment_stock(self, product_id: int, amount: int) -> Product:
        """
        Increment product stock by a specific amount.
        Convenience method for adding stock.
        """
        return self.update_stock(product_id, amount, "add")
    
    def decrement_stock(self, product_id: int, amount: int) -> Product:
        """
        Decrement product stock by a specific amount.
        Raises error if result would be negative.
        """
        return self.update_stock(product_id, amount, "subtract")
    
    # ========== Product Image Operations ==========
    
    def add_product_image(self, product_id: int, image_url: str) -> ProductImage:
        """
        Add an image to a product.
        """
        product = self.get_product_by_id(product_id)
        
        new_image = ProductImage(
            product_id=product_id,
            image_url=image_url
        )
        
        self.db.add(new_image)
        self.db.commit()
        self.db.refresh(new_image)
        
        return new_image
    
    def get_product_images(self, product_id: int) -> List[ProductImage]:
        """
        Get all images for a specific product.
        """
        self.get_product_by_id(product_id)  # Validate product exists
        
        images = self.db.query(ProductImage).filter(
            ProductImage.product_id == product_id
        ).all()
        
        return images
    
    def delete_product_image(self, image_id: int) -> bool:
        """
        Delete a product image by ID.
        """
        image = self.db.query(ProductImage).filter(ProductImage.id == image_id).first()
        if not image:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image with id {image_id} not found"
            )
        
        self.db.delete(image)
        self.db.commit()
        
        return True
    
    # ========== Tag Operations ==========
    
    def create_tag(self, tag_data: TagCreate) -> Tag:
        """
        Create a new tag.
        """
        # Check if tag already exists
        existing_tag = self.db.query(Tag).filter(Tag.name == tag_data.name).first()
        if existing_tag:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tag '{tag_data.name}' already exists"
            )
        
        new_tag = Tag(name=tag_data.name)
        self.db.add(new_tag)
        self.db.commit()
        self.db.refresh(new_tag)
        
        return new_tag
    
    def get_all_tags(self, skip: int = 0, limit: int = 100, search: Optional[str] = None) -> List[Tag]:
        """
        Get all available tags with optional search and pagination.
        """
        query = self.db.query(Tag)
        
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(Tag.name.ilike(search_pattern))
        
        return query.offset(skip).limit(limit).all()
    
    def get_tag_by_id(self, tag_id: int) -> Tag:
        """
        Get a single tag by ID.
        Raises HTTPException if not found.
        """
        tag = self.db.query(Tag).filter(Tag.id == tag_id).first()
        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag with id {tag_id} not found"
            )
        return tag
    
    def update_tag(self, tag_id: int, tag_data: TagUpdate) -> Tag:
        """
        Update a tag's name.
        """
        tag = self.get_tag_by_id(tag_id)
        
        if tag_data.name:
            # Check if new name already exists
            existing_tag = self.db.query(Tag).filter(
                Tag.name == tag_data.name,
                Tag.id != tag_id
            ).first()
            if existing_tag:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Tag '{tag_data.name}' already exists"
                )
            
            tag.name = tag_data.name
        
        self.db.commit()
        self.db.refresh(tag)
        
        return tag
    
    def delete_tag(self, tag_id: int) -> bool:
        """
        Delete a tag by ID.
        """
        tag = self.get_tag_by_id(tag_id)
        
        self.db.delete(tag)
        self.db.commit()
        
        return True
    
    def add_tags_to_product(self, product_id: int, tag_ids: List[int]) -> Product:
        """
        Add multiple tags to a product.
        """
        product = self.get_product_by_id(product_id)
        
        tags = self.db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
        if len(tags) != len(tag_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more tag IDs not found"
            )
        
        # Add tags (SQLAlchemy handles duplicates)
        for tag in tags:
            if tag not in product.tags:
                product.tags.append(tag)
        
        self.db.commit()
        self.db.refresh(product)
        
        return product
    
    def remove_tag_from_product(self, product_id: int, tag_id: int) -> Product:
        """
        Remove a tag from a product.
        """
        product = self.get_product_by_id(product_id)
        tag = self.get_tag_by_id(tag_id)
        
        if tag in product.tags:
            product.tags.remove(tag)
            self.db.commit()
            self.db.refresh(product)
        
        return product
    
    # ========== Utility Methods ==========
    
    def get_products_by_store(self, store_id: int, skip: int = 0, limit: int = 100) -> List[Product]:
        """
        Get all products for a specific store.
        """
        products = self.db.query(Product).filter(
            Product.store_id == store_id
        ).offset(skip).limit(limit).all()
        
        return products
    
    def get_products_by_category(self, category_id: int, skip: int = 0, limit: int = 100) -> List[Product]:
        """
        Get all products in a specific category.
        """
        products = self.db.query(Product).filter(
            Product.category_id == category_id
        ).offset(skip).limit(limit).all()
        
        return products
    
    def get_products_by_tag(self, tag_id: int, skip: int = 0, limit: int = 100, is_active: bool = True) -> List[Product]:
        """
        Get all products with a specific tag.
        """
        tag = self.get_tag_by_id(tag_id)
        
        # Query products with this tag
        query = self.db.query(Product).join(ProductTag).filter(
            ProductTag.tag_id == tag_id
        )
        
        if is_active:
            query = query.filter(Product.is_active == True)
        
        products = query.offset(skip).limit(limit).all()
        
        return products
    
    def search_products(
        self,
        search_term: str,
        skip: int = 0,
        limit: int = 100,
        category_id: Optional[int] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        in_stock: bool = False
    ) -> List[Product]:
        """
        Search products by name or description with optional filters.
        """
        search_pattern = f"%{search_term}%"
        
        query = self.db.query(Product).filter(
            or_(
                Product.name.ilike(search_pattern),
                Product.short_description.ilike(search_pattern),
                Product.long_description.ilike(search_pattern)
            )
        )
        
        # Apply additional filters
        if category_id is not None:
            query = query.filter(Product.category_id == category_id)
        
        if min_price is not None:
            query = query.filter(Product.price >= min_price)
        
        if max_price is not None:
            query = query.filter(Product.price <= max_price)
        
        if in_stock:
            query = query.filter(Product.stock > 0)
        
        products = query.offset(skip).limit(limit).all()
        
        return products
    
    def get_low_stock_products(self, threshold: int = 10, skip: int = 0, limit: int = 100) -> List[Product]:
        """
        Get products with stock below a certain threshold.
        Useful for inventory management.
        """
        products = self.db.query(Product).filter(
            and_(
                Product.stock <= threshold,
                Product.stock > 0,
                Product.is_active == True
            )
        ).offset(skip).limit(limit).all()
        
        return products
    
    def get_out_of_stock_products(self, skip: int = 0, limit: int = 100) -> List[Product]:
        """
        Get all products that are out of stock.
        """
        products = self.db.query(Product).filter(
            and_(
                Product.stock == 0,
                Product.is_active == True
            )
        ).offset(skip).limit(limit).all()
        
        return products
    
    # ========== Offer/Discount Methods ==========
    
    def get_products_with_active_offers(
        self,
        skip: int = 0,
        limit: int = 100,
        store_id: Optional[int] = None,
        category_id: Optional[int] = None
    ) -> List[Product]:
        """
        Get products with active discount offers.
        
        An offer is active if:
        - Product has a discount_price set (not null)
        - discount_end_date is null (no expiry) OR in the future
        
        Args:
            skip: Pagination offset
            limit: Maximum results
            store_id: Optional filter by store
            category_id: Optional filter by category
            
        Returns:
            List of products with active offers
        """
        from datetime import datetime
        
        query = self.db.query(Product).filter(
            and_(
                Product.discount_price.isnot(None),
                Product.is_active == True,
                or_(
                    Product.discount_end_date.is_(None),
                    Product.discount_end_date > datetime.now()
                )
            )
        )
        
        if store_id is not None:
            query = query.filter(Product.store_id == store_id)
        
        if category_id is not None:
            query = query.filter(Product.category_id == category_id)
        
        return query.offset(skip).limit(limit).all()
    
    def get_store_offers(self, store_id: int, skip: int = 0, limit: int = 100) -> List[Product]:
        """
        Get all products with active offers from a specific store.
        
        Args:
            store_id: ID of the store
            skip: Pagination offset
            limit: Maximum results
            
        Returns:
            List of products with active offers from the store
        """
        return self.get_products_with_active_offers(
            skip=skip,
            limit=limit,
            store_id=store_id
        )
    
    def get_category_offers(self, category_id: int, skip: int = 0, limit: int = 100) -> List[Product]:
        """
        Get all products with active offers from a specific category.
        
        Args:
            category_id: ID of the category
            skip: Pagination offset
            limit: Maximum results
            
        Returns:
            List of products with active offers from the category
        """
        return self.get_products_with_active_offers(
            skip=skip,
            limit=limit,
            category_id=category_id
        )