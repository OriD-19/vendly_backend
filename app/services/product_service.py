from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi import HTTPException, status
from app.models.product import Product, Tag, ProductImage, ProductTag
from app.models.category import Category
from app.models.store import Store
from app.schemas.product import ProductCreate, ProductUpdate


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
    
    def create_tag(self, tag_name: str) -> Tag:
        """
        Create a new tag.
        """
        # Check if tag already exists
        existing_tag = self.db.query(Tag).filter(Tag.name == tag_name).first()
        if existing_tag:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tag '{tag_name}' already exists"
            )
        
        new_tag = Tag(name=tag_name)
        self.db.add(new_tag)
        self.db.commit()
        self.db.refresh(new_tag)
        
        return new_tag
    
    def get_all_tags(self) -> List[Tag]:
        """
        Get all available tags.
        """
        return self.db.query(Tag).all()
    
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
    
    def get_products_by_tag(self, tag_id: int, skip: int = 0, limit: int = 100) -> List[Product]:
        """
        Get all products with a specific tag.
        """
        tag = self.get_tag_by_id(tag_id)
        
        # Use the relationship
        products = tag.products[skip:skip + limit]
        
        return products
    
    def search_products(self, search_term: str, skip: int = 0, limit: int = 100) -> List[Product]:
        """
        Search products by name or description.
        """
        search_pattern = f"%{search_term}%"
        
        products = self.db.query(Product).filter(
            or_(
                Product.name.ilike(search_pattern),
                Product.short_description.ilike(search_pattern),
                Product.long_description.ilike(search_pattern)
            )
        ).offset(skip).limit(limit).all()
        
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