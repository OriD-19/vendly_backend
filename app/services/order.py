from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, case
from fastapi import HTTPException, status
from app.models.order import Order, OrderProduct, OrderStatus
from app.models.product import Product
from app.models.user import User
from app.schemas.order import OrderCreate, OrderUpdate
import random
import string


class OrderService:
    def __init__(self, db_session: Session):
        self.db = db_session
    
    # ========== CRUD Operations ==========
    
    def create_order(self, order_data: OrderCreate, customer_id: int) -> Order:
        """
        Create a new order with products.
        Validates customer, products, and stock availability.
        """
        # Verify customer exists
        customer = self.db.query(User).filter(User.id == customer_id).first()
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        # Generate unique order number
        order_number = self._generate_order_number()
        
        # Calculate total amount and validate products
        total_amount = 0
        order_products_data = []
        
        for item in order_data.products:
            product = self.db.query(Product).filter(Product.id == item.product_id).first()
            
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product with id {item.product_id} not found"
                )
            
            if not product.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product '{product.name}' is not available"
                )
            
            if product.stock < item.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient stock for product '{product.name}'. Available: {product.stock}, Requested: {item.quantity}"
                )
            
            # Determine effective price (use discount if active, otherwise regular price)
            effective_price = product.price
            
            # Check if product has an active discount
            if product.discount_price is not None:
                # Check if discount is still valid
                if product.discount_end_date is None or product.discount_end_date > datetime.utcnow():
                    effective_price = product.discount_price
            
            # Store product data for order creation
            order_products_data.append({
                'product': product,
                'quantity': item.quantity,
                'unit_price': effective_price  # Use effective price (discount or regular)
            })
            
            total_amount += effective_price * item.quantity
        
        # Create order
        new_order = Order(
            order_number=order_number,
            customer_id=customer_id,
            total_amount=total_amount,
            shipping_address=order_data.shipping_address,
            shipping_city=order_data.shipping_city,
            shipping_postal_code=order_data.shipping_postal_code,
            shipping_country=order_data.shipping_country,
            status=OrderStatus.PENDING
        )
        
        self.db.add(new_order)
        self.db.flush()  # Get order ID without committing
        
        # Create order products and update stock
        for item_data in order_products_data:
            order_product = OrderProduct(
                order_id=new_order.id,
                product_id=item_data['product'].id,
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price']
            )
            self.db.add(order_product)
            
            # Reduce product stock
            item_data['product'].stock -= item_data['quantity']
        
        self.db.commit()
        self.db.refresh(new_order)
        
        return new_order
    
    def get_order_by_id(self, order_id: int) -> Order:
        """Get a single order by ID."""
        order = self.db.query(Order).filter(Order.id == order_id).first()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order with id {order_id} not found"
            )
        
        return order
    
    def get_order_by_number(self, order_number: str) -> Order:
        """Get a single order by order number."""
        order = self.db.query(Order).filter(Order.order_number == order_number).first()
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order with number {order_number} not found"
            )
        
        return order
    
    def get_all_orders(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[OrderStatus] = None,
        customer_id: Optional[int] = None,
        store_id: Optional[int] = None
    ) -> List[Order]:
        """
        Get all orders with optional filtering.
        """
        query = self.db.query(Order)
        
        if status:
            query = query.filter(Order.status == status)
        
        if customer_id:
            query = query.filter(Order.customer_id == customer_id)
        
        if store_id:
            # Filter orders containing products from specific store
            query = query.join(OrderProduct).join(Product).filter(Product.store_id == store_id)
        
        orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
        return orders
    
    def update_order(self, order_id: int, order_data: OrderUpdate) -> Order:
        """
        Update order information.
        Handles status changes and timestamps.
        """
        order = self.get_order_by_id(order_id)
        
        update_dict = order_data.model_dump(exclude_unset=True)
        
        # Handle status changes with timestamps
        if 'status' in update_dict:
            new_status = update_dict['status']
            
            if new_status == OrderStatus.SHIPPED and not order.shipped_at:
                order.shipped_at = datetime.utcnow()
            
            elif new_status == OrderStatus.DELIVERED and not order.delivered_at:
                order.delivered_at = datetime.utcnow()
            
            elif new_status == OrderStatus.CANCELED and not order.canceled_at:
                order.canceled_at = datetime.utcnow()
                # Restore product stock
                self._restore_order_stock(order)
            
            order.status = new_status
            del update_dict['status']
        
        # Update other fields
        for field, value in update_dict.items():
            setattr(order, field, value)
        
        self.db.commit()
        self.db.refresh(order)
        
        return order
    
    def cancel_order(self, order_id: int) -> Order:
        """
        Cancel an order and restore product stock.
        """
        order = self.get_order_by_id(order_id)
        
        if order.status in [OrderStatus.DELIVERED, OrderStatus.CANCELED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel order with status: {order.status.value}"
            )
        
        order.status = OrderStatus.CANCELED
        order.canceled_at = datetime.utcnow()
        
        # Restore product stock
        self._restore_order_stock(order)
        
        self.db.commit()
        self.db.refresh(order)
        
        return order
    
    def delete_order(self, order_id: int) -> bool:
        """
        Delete an order (hard delete).
        Should only be used for invalid/test orders.
        """
        order = self.get_order_by_id(order_id)
        
        # Restore stock if order was not delivered or canceled
        if order.status not in [OrderStatus.DELIVERED, OrderStatus.CANCELED]:
            self._restore_order_stock(order)
        
        self.db.delete(order)
        self.db.commit()
        
        return True
    
    # ========== Analytics Methods ==========
    
    def get_total_income(
        self,
        store_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        period: str = "week"
    ) -> Dict[str, Any]:
        """
        Calculate total income for a store in a given period.
        Income = sum of all completed (delivered) orders.
        
        Args:
            store_id: Store ID
            start_date: Start date (optional, uses period if not provided)
            end_date: End date (optional, defaults to now)
            period: Time period if dates not provided (week, month, quarter, year)
        """
        # Set date range
        if not end_date:
            end_date = datetime.utcnow()
        
        if not start_date:
            start_date = self._get_period_start_date(period, end_date)
        
        # Query total income from delivered orders
        total_income = (
            self.db.query(func.sum(OrderProduct.quantity * OrderProduct.unit_price))
            .join(Order, OrderProduct.order_id == Order.id)
            .join(Product, OrderProduct.product_id == Product.id)
            .filter(
                and_(
                    Product.store_id == store_id,
                    Order.status == OrderStatus.DELIVERED,
                    Order.delivered_at >= start_date,
                    Order.delivered_at <= end_date
                )
            )
            .scalar()
        ) or 0
        
        return {
            "store_id": store_id,
            "total_income": float(total_income),
            "period": period,
            "start_date": start_date,
            "end_date": end_date,
            "currency": "USD"
        }
    
    def get_total_revenue(
        self,
        store_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        period: str = "week"
    ) -> Dict[str, Any]:
        """
        Calculate total revenue (profit) for a store.
        Revenue = Income - Production Costs
        
        Args:
            store_id: Store ID
            start_date: Start date
            end_date: End date
            period: Time period (week, month, quarter, year)
        """
        # Set date range
        if not end_date:
            end_date = datetime.utcnow()
        
        if not start_date:
            start_date = self._get_period_start_date(period, end_date)
        
        # Query income and costs
        result = (
            self.db.query(
                func.sum(OrderProduct.quantity * OrderProduct.unit_price).label('income'),
                func.sum(OrderProduct.quantity * Product.production_cost).label('costs')
            )
            .join(Order, OrderProduct.order_id == Order.id)
            .join(Product, OrderProduct.product_id == Product.id)
            .filter(
                and_(
                    Product.store_id == store_id,
                    Order.status == OrderStatus.DELIVERED,
                    Order.delivered_at >= start_date,
                    Order.delivered_at <= end_date
                )
            )
            .first()
        )
        
        income = float(result.income) if result and result.income else 0
        costs = float(result.costs) if result and result.costs else 0
        revenue = income - costs
        profit_margin = (revenue / income * 100) if income > 0 else 0
        
        return {
            "store_id": store_id,
            "total_revenue": revenue,
            "total_income": income,
            "total_costs": costs,
            "profit_margin_percent": round(profit_margin, 2),
            "period": period,
            "start_date": start_date,
            "end_date": end_date,
            "currency": "USD"
        }
    
    def get_total_orders_count(
        self,
        store_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        period: str = "week"
    ) -> Dict[str, Any]:
        """
        Get total number of orders for a store in a period.
        """
        # Set date range
        if not end_date:
            end_date = datetime.utcnow()
        
        if not start_date:
            start_date = self._get_period_start_date(period, end_date)
        
        # Count distinct orders containing store products
        total_orders = (
            self.db.query(func.count(func.distinct(Order.id)))
            .join(OrderProduct, Order.id == OrderProduct.order_id)
            .join(Product, OrderProduct.product_id == Product.id)
            .filter(
                and_(
                    Product.store_id == store_id,
                    Order.created_at >= start_date,
                    Order.created_at <= end_date
                )
            )
            .scalar()
        ) or 0
        
        # Breakdown by status
        status_breakdown = (
            self.db.query(
                Order.status,
                func.count(func.distinct(Order.id)).label('count')
            )
            .join(OrderProduct, Order.id == OrderProduct.order_id)
            .join(Product, OrderProduct.product_id == Product.id)
            .filter(
                and_(
                    Product.store_id == store_id,
                    Order.created_at >= start_date,
                    Order.created_at <= end_date
                )
            )
            .group_by(Order.status)
            .all()
        )
        
        status_dict = {status.value: count for status, count in status_breakdown}
        
        return {
            "store_id": store_id,
            "total_orders": total_orders,
            "status_breakdown": status_dict,
            "period": period,
            "start_date": start_date,
            "end_date": end_date
        }
    
    def get_average_order_value(
        self,
        store_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        period: str = "week"
    ) -> Dict[str, Any]:
        """
        Calculate average order value (AOV) for a store.
        AOV = Total Income / Number of Orders
        """
        # Set date range
        if not end_date:
            end_date = datetime.utcnow()
        
        if not start_date:
            start_date = self._get_period_start_date(period, end_date)
        
        # Get orders with their totals
        orders = (
            self.db.query(
                Order.id,
                func.sum(OrderProduct.quantity * OrderProduct.unit_price).label('order_total')
            )
            .join(OrderProduct, Order.id == OrderProduct.order_id)
            .join(Product, OrderProduct.product_id == Product.id)
            .filter(
                and_(
                    Product.store_id == store_id,
                    Order.status == OrderStatus.DELIVERED,
                    Order.delivered_at >= start_date,
                    Order.delivered_at <= end_date
                )
            )
            .group_by(Order.id)
            .all()
        )
        
        if not orders:
            return {
                "store_id": store_id,
                "average_order_value": 0,
                "total_orders": 0,
                "total_income": 0,
                "period": period,
                "start_date": start_date,
                "end_date": end_date,
                "currency": "USD"
            }
        
        total_income = sum(order.order_total for order in orders)
        order_count = len(orders)
        aov = total_income / order_count if order_count > 0 else 0
        
        return {
            "store_id": store_id,
            "average_order_value": round(float(aov), 2),
            "total_orders": order_count,
            "total_income": float(total_income),
            "period": period,
            "start_date": start_date,
            "end_date": end_date,
            "currency": "USD"
        }
    
    def get_items_sold_count(
        self,
        store_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        period: str = "week"
    ) -> Dict[str, Any]:
        """
        Get total number of items (quantity) sold for a store.
        Sum of all quantities in all orders.
        """
        # Set date range
        if not end_date:
            end_date = datetime.utcnow()
        
        if not start_date:
            start_date = self._get_period_start_date(period, end_date)
        
        # Sum quantities from all order products
        total_items = (
            self.db.query(func.sum(OrderProduct.quantity))
            .join(Order, OrderProduct.order_id == Order.id)
            .join(Product, OrderProduct.product_id == Product.id)
            .filter(
                and_(
                    Product.store_id == store_id,
                    Order.status == OrderStatus.DELIVERED,
                    Order.delivered_at >= start_date,
                    Order.delivered_at <= end_date
                )
            )
            .scalar()
        ) or 0
        
        # Get top selling products
        top_products = (
            self.db.query(
                Product.id,
                Product.name,
                func.sum(OrderProduct.quantity).label('quantity_sold')
            )
            .join(OrderProduct, Product.id == OrderProduct.product_id)
            .join(Order, OrderProduct.order_id == Order.id)
            .filter(
                and_(
                    Product.store_id == store_id,
                    Order.status == OrderStatus.DELIVERED,
                    Order.delivered_at >= start_date,
                    Order.delivered_at <= end_date
                )
            )
            .group_by(Product.id, Product.name)
            .order_by(func.sum(OrderProduct.quantity).desc())
            .limit(10)
            .all()
        )
        
        top_products_list = [
            {
                "product_id": prod.id,
                "product_name": prod.name,
                "quantity_sold": prod.quantity_sold
            }
            for prod in top_products
        ]
        
        return {
            "store_id": store_id,
            "total_items_sold": total_items,
            "top_products": top_products_list,
            "period": period,
            "start_date": start_date,
            "end_date": end_date
        }
    
    def get_returned_orders(
        self,
        store_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        period: str = "week"
    ) -> Dict[str, Any]:
        """
        Get returned (canceled) orders for a store.
        """
        # Set date range
        if not end_date:
            end_date = datetime.utcnow()
        
        if not start_date:
            start_date = self._get_period_start_date(period, end_date)
        
        # Count canceled orders
        returned_count = (
            self.db.query(func.count(func.distinct(Order.id)))
            .join(OrderProduct, Order.id == OrderProduct.order_id)
            .join(Product, OrderProduct.product_id == Product.id)
            .filter(
                and_(
                    Product.store_id == store_id,
                    Order.status == OrderStatus.CANCELED,
                    Order.canceled_at >= start_date,
                    Order.canceled_at <= end_date
                )
            )
            .scalar()
        ) or 0
        
        # Calculate lost revenue
        lost_revenue = (
            self.db.query(func.sum(OrderProduct.quantity * OrderProduct.unit_price))
            .join(Order, OrderProduct.order_id == Order.id)
            .join(Product, OrderProduct.product_id == Product.id)
            .filter(
                and_(
                    Product.store_id == store_id,
                    Order.status == OrderStatus.CANCELED,
                    Order.canceled_at >= start_date,
                    Order.canceled_at <= end_date
                )
            )
            .scalar()
        ) or 0
        
        # Get total orders for percentage
        total_orders = (
            self.db.query(func.count(func.distinct(Order.id)))
            .join(OrderProduct, Order.id == OrderProduct.order_id)
            .join(Product, OrderProduct.product_id == Product.id)
            .filter(
                and_(
                    Product.store_id == store_id,
                    Order.created_at >= start_date,
                    Order.created_at <= end_date
                )
            )
            .scalar()
        ) or 0
        
        return_rate = (returned_count / total_orders * 100) if total_orders > 0 else 0
        
        return {
            "store_id": store_id,
            "returned_orders_count": returned_count,
            "total_orders": total_orders,
            "return_rate_percent": round(return_rate, 2),
            "lost_revenue": float(lost_revenue),
            "period": period,
            "start_date": start_date,
            "end_date": end_date,
            "currency": "USD"
        }
    
    def get_fulfilled_orders(
        self,
        store_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        period: str = "week"
    ) -> Dict[str, Any]:
        """
        Get fulfilled (delivered) orders for a store.
        """
        # Set date range
        if not end_date:
            end_date = datetime.utcnow()
        
        if not start_date:
            start_date = self._get_period_start_date(period, end_date)
        
        # Count delivered orders
        fulfilled_count = (
            self.db.query(func.count(func.distinct(Order.id)))
            .join(OrderProduct, Order.id == OrderProduct.order_id)
            .join(Product, OrderProduct.product_id == Product.id)
            .filter(
                and_(
                    Product.store_id == store_id,
                    Order.status == OrderStatus.DELIVERED,
                    Order.delivered_at >= start_date,
                    Order.delivered_at <= end_date
                )
            )
            .scalar()
        ) or 0
        
        # Get total orders
        total_orders = (
            self.db.query(func.count(func.distinct(Order.id)))
            .join(OrderProduct, Order.id == OrderProduct.order_id)
            .join(Product, OrderProduct.product_id == Product.id)
            .filter(
                and_(
                    Product.store_id == store_id,
                    Order.created_at >= start_date,
                    Order.created_at <= end_date
                )
            )
            .scalar()
        ) or 0
        
        fulfillment_rate = (fulfilled_count / total_orders * 100) if total_orders > 0 else 0
        
        # Average fulfillment time
        avg_fulfillment_time = (
            self.db.query(
                func.avg(
                    func.extract('epoch', Order.delivered_at) - 
                    func.extract('epoch', Order.created_at)
                )
            )
            .join(OrderProduct, Order.id == OrderProduct.order_id)
            .join(Product, OrderProduct.product_id == Product.id)
            .filter(
                and_(
                    Product.store_id == store_id,
                    Order.status == OrderStatus.DELIVERED,
                    Order.delivered_at >= start_date,
                    Order.delivered_at <= end_date
                )
            )
            .scalar()
        )
        
        avg_days = (avg_fulfillment_time / 86400) if avg_fulfillment_time else 0
        
        return {
            "store_id": store_id,
            "fulfilled_orders_count": fulfilled_count,
            "total_orders": total_orders,
            "fulfillment_rate_percent": round(fulfillment_rate, 2),
            "average_fulfillment_days": round(avg_days, 1),
            "period": period,
            "start_date": start_date,
            "end_date": end_date
        }
    
    def get_conversion_rate(
        self,
        store_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        period: str = "week"
    ) -> Dict[str, Any]:
        """
        Calculate conversion rate for a store.
        
        Conversion Rate = (Delivered Orders / Total Orders) * 100
        
        Non-converted users are those who:
        - Created orders but canceled them
        - Created orders that are still pending/processing
        
        Converted users are those who:
        - Completed the order (status = DELIVERED)
        """
        # Set date range
        if not end_date:
            end_date = datetime.utcnow()
        
        if not start_date:
            start_date = self._get_period_start_date(period, end_date)
        
        # Get order counts by status
        order_stats = (
            self.db.query(
                Order.status,
                func.count(func.distinct(Order.id)).label('count')
            )
            .join(OrderProduct, Order.id == OrderProduct.order_id)
            .join(Product, OrderProduct.product_id == Product.id)
            .filter(
                and_(
                    Product.store_id == store_id,
                    Order.created_at >= start_date,
                    Order.created_at <= end_date
                )
            )
            .group_by(Order.status)
            .all()
        )
        
        # Categorize orders
        converted_orders = 0  # Delivered orders
        non_converted_orders = 0  # Canceled or abandoned
        in_progress_orders = 0  # Pending, Confirmed, Shipped
        
        status_breakdown = {}
        
        for status, count in order_stats:
            status_breakdown[status.value] = count
            
            if status == OrderStatus.DELIVERED:
                converted_orders += count
            elif status == OrderStatus.CANCELED:
                non_converted_orders += count
            else:
                in_progress_orders += count
        
        total_orders = converted_orders + non_converted_orders + in_progress_orders
        
        # Calculate conversion rate (only counting completed journeys)
        completed_journeys = converted_orders + non_converted_orders
        conversion_rate = (converted_orders / completed_journeys * 100) if completed_journeys > 0 else 0
        
        # Alternative: Conversion rate including in-progress
        total_conversion_rate = (converted_orders / total_orders * 100) if total_orders > 0 else 0
        
        # Get unique customers who ordered
        total_customers = (
            self.db.query(func.count(func.distinct(Order.customer_id)))
            .join(OrderProduct, Order.id == OrderProduct.order_id)
            .join(Product, OrderProduct.product_id == Product.id)
            .filter(
                and_(
                    Product.store_id == store_id,
                    Order.created_at >= start_date,
                    Order.created_at <= end_date
                )
            )
            .scalar()
        ) or 0
        
        converted_customers = (
            self.db.query(func.count(func.distinct(Order.customer_id)))
            .join(OrderProduct, Order.id == OrderProduct.order_id)
            .join(Product, OrderProduct.product_id == Product.id)
            .filter(
                and_(
                    Product.store_id == store_id,
                    Order.status == OrderStatus.DELIVERED,
                    Order.delivered_at >= start_date,
                    Order.delivered_at <= end_date
                )
            )
            .scalar()
        ) or 0
        
        customer_conversion_rate = (converted_customers / total_customers * 100) if total_customers > 0 else 0
        
        return {
            "store_id": store_id,
            "conversion_rate_percent": round(conversion_rate, 2),
            "total_conversion_rate_percent": round(total_conversion_rate, 2),
            "customer_conversion_rate_percent": round(customer_conversion_rate, 2),
            "converted_orders": converted_orders,
            "non_converted_orders": non_converted_orders,
            "in_progress_orders": in_progress_orders,
            "total_orders": total_orders,
            "completed_journeys": completed_journeys,
            "total_customers": total_customers,
            "converted_customers": converted_customers,
            "status_breakdown": status_breakdown,
            "period": period,
            "start_date": start_date,
            "end_date": end_date,
            "interpretation": {
                "conversion_rate": "Percentage of completed orders that resulted in delivery (excludes in-progress)",
                "total_conversion_rate": "Percentage of all orders that resulted in delivery (includes in-progress)",
                "customer_conversion_rate": "Percentage of unique customers who completed at least one order"
            }
        }
    
    def get_dashboard_analytics(
        self,
        store_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        period: str = "week"
    ) -> Dict[str, Any]:
        """
        Get comprehensive dashboard analytics for a store.
        Combines all analytics into a single response.
        """
        return {
            "store_id": store_id,
            "period": period,
            "date_range": {
                "start": start_date or self._get_period_start_date(period),
                "end": end_date or datetime.utcnow()
            },
            "income": self.get_total_income(store_id, start_date, end_date, period),
            "revenue": self.get_total_revenue(store_id, start_date, end_date, period),
            "orders": self.get_total_orders_count(store_id, start_date, end_date, period),
            "average_order_value": self.get_average_order_value(store_id, start_date, end_date, period),
            "items_sold": self.get_items_sold_count(store_id, start_date, end_date, period),
            "returned_orders": self.get_returned_orders(store_id, start_date, end_date, period),
            "fulfilled_orders": self.get_fulfilled_orders(store_id, start_date, end_date, period),
            "conversion": self.get_conversion_rate(store_id, start_date, end_date, period)
        }
    
    def get_dashboard_summary(
        self,
        store_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        period: str = "week"
    ) -> Dict[str, Any]:
        """
        Get simplified dashboard summary with only the 4 key metrics.
        Each metric includes comparison with the previous period.
        
        Returns:
            - total_revenue: Revenue with percentage change vs previous period
            - total_income: Income with percentage change vs previous period
            - total_orders: Order count with percentage change vs previous period
            - average_order_value: AOV with percentage change vs previous period
        """
        # Set date range for current period
        if not end_date:
            end_date = datetime.utcnow()
        
        if not start_date:
            start_date = self._get_period_start_date(period, end_date)
        
        # Calculate previous period dates
        period_duration = end_date - start_date
        prev_end_date = start_date
        prev_start_date = prev_end_date - period_duration
        
        # Get current period metrics
        current_revenue = self.get_total_revenue(store_id, start_date, end_date, period)
        current_income = self.get_total_income(store_id, start_date, end_date, period)
        current_orders = self.get_total_orders_count(store_id, start_date, end_date, period)
        current_aov = self.get_average_order_value(store_id, start_date, end_date, period)
        
        # Get previous period metrics
        prev_revenue = self.get_total_revenue(store_id, prev_start_date, prev_end_date, period)
        prev_income = self.get_total_income(store_id, prev_start_date, prev_end_date, period)
        prev_orders = self.get_total_orders_count(store_id, prev_start_date, prev_end_date, period)
        prev_aov = self.get_average_order_value(store_id, prev_start_date, prev_end_date, period)
        
        # Calculate percentage changes
        def calc_percentage_change(current: float, previous: float) -> float:
            if previous == 0:
                return 100.0 if current > 0 else 0.0
            return round(((current - previous) / previous) * 100, 1)
        
        revenue_change = calc_percentage_change(
            current_revenue.get("total_revenue", 0),
            prev_revenue.get("total_revenue", 0)
        )
        
        income_change = calc_percentage_change(
            current_income.get("total_income", 0),
            prev_income.get("total_income", 0)
        )
        
        orders_change = calc_percentage_change(
            current_orders.get("total_orders", 0),
            prev_orders.get("total_orders", 0)
        )
        
        aov_change = calc_percentage_change(
            current_aov.get("average_order_value", 0),
            prev_aov.get("average_order_value", 0)
        )
        
        return {
            "store_id": store_id,
            "period": period,
            "date_range": {
                "start": start_date,
                "end": end_date
            },
            "total_revenue": {
                "value": round(current_revenue.get("total_revenue", 0), 2),
                "change_percent": revenue_change,
                "currency": "USD"
            },
            "total_income": {
                "value": round(current_income.get("total_income", 0), 2),
                "change_percent": income_change,
                "currency": "USD"
            },
            "total_orders": {
                "value": current_orders.get("total_orders", 0),
                "change_percent": orders_change
            },
            "average_order_value": {
                "value": round(current_aov.get("average_order_value", 0), 2),
                "change_percent": aov_change,
                "currency": "USD"
            }
        }
    
    def get_sales_performance(
        self,
        store_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive sales performance data for a store.
        
        Returns:
        - Daily sales data
        - Best day sales
        - Average daily sales
        - Total orders
        
        Args:
            store_id: ID of the store
            start_date: Start date for performance (defaults to 30 days ago)
            end_date: End date for performance (defaults to today)
        """
        # Set date range
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Daily sales query
        daily_sales = (
            self.db.query(
                func.date(Order.created_at).label('sale_date'),
                func.sum(Order.total_amount).label('daily_total')
            )
            .join(OrderProduct, Order.id == OrderProduct.order_id)
            .join(Product, OrderProduct.product_id == Product.id)
            .filter(
                Product.store_id == store_id,
                Order.status != OrderStatus.CANCELED,
                Order.created_at >= start_date,
                Order.created_at <= end_date
            )
            .group_by(func.date(Order.created_at))
            .order_by(func.date(Order.created_at))
            .all()
        )
        
        # Convert to list of dictionaries for easier handling
        daily_sales_data = [
            {
                'date': sale.sale_date, 
                'total': float(sale.daily_total)
            } for sale in daily_sales
        ]
        
        # Calculate metrics
        total_sales = sum(day['total'] for day in daily_sales_data)
        avg_daily_sales = total_sales / len(daily_sales_data) if daily_sales_data else 0
        
        # Find best day
        best_day = max(daily_sales_data, key=lambda x: x['total']) if daily_sales_data else None
        
        # Total orders
        total_orders = (
            self.db.query(func.count(func.distinct(Order.id)))
            .join(OrderProduct, Order.id == OrderProduct.order_id)
            .join(Product, OrderProduct.product_id == Product.id)
            .filter(
                Product.store_id == store_id,
                Order.status != OrderStatus.CANCELED,
                Order.created_at >= start_date,
                Order.created_at <= end_date
            )
            .scalar()
        ) or 0
        
        return {
            "store_id": store_id,
            "daily_sales": daily_sales_data,
            "best_day": {
                "date": best_day['date'] if best_day else None,
                "total": best_day['total'] if best_day else 0
            },
            "avg_daily_sales": round(avg_daily_sales, 2),
            "total_orders": total_orders,
            "start_date": start_date,
            "end_date": end_date,
            "currency": "USD"
        }
    
    def get_growth_metrics(
        self,
        store_id: int,
        period: str = "month"
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive growth metrics for a store.
        
        Metrics:
        - Monthly Sales Growth
        - Customer Growth
        - Average Order Value (AOV) Growth
        - Customer Retention Improvement
        
        Args:
            store_id: ID of the store
            period: Time period for comparison (default: month)
        
        Returns:
            Dictionary with growth metrics
        """
        # Current period dates
        end_date = datetime.utcnow()
        start_date = self._get_period_start_date(period, end_date)
        
        # Previous period dates
        prev_end_date = start_date - timedelta(days=1)
        prev_start_date = self._get_period_start_date(period, prev_end_date)
        
        # Current period metrics
        current_sales = (
            self.db.query(func.sum(Order.total_amount))
            .join(OrderProduct, Order.id == OrderProduct.order_id)
            .join(Product, OrderProduct.product_id == Product.id)
            .filter(
                Product.store_id == store_id,
                Order.status != OrderStatus.CANCELED,
                Order.created_at >= start_date,
                Order.created_at <= end_date
            )
            .scalar() or 0
        )
        
        # Previous period metrics
        previous_sales = (
            self.db.query(func.sum(Order.total_amount))
            .join(OrderProduct, Order.id == OrderProduct.order_id)
            .join(Product, OrderProduct.product_id == Product.id)
            .filter(
                Product.store_id == store_id,
                Order.status != OrderStatus.CANCELED,
                Order.created_at >= prev_start_date,
                Order.created_at <= prev_end_date
            )
            .scalar() or 0
        )
        
        # Customer metrics
        current_customers = (
            self.db.query(func.count(func.distinct(Order.customer_id)))
            .join(OrderProduct, Order.id == OrderProduct.order_id)
            .join(Product, OrderProduct.product_id == Product.id)
            .filter(
                Product.store_id == store_id,
                Order.status != OrderStatus.CANCELED,
                Order.created_at >= start_date,
                Order.created_at <= end_date
            )
            .scalar() or 0
        )
        
        previous_customers = (
            self.db.query(func.count(func.distinct(Order.customer_id)))
            .join(OrderProduct, Order.id == OrderProduct.order_id)
            .join(Product, OrderProduct.product_id == Product.id)
            .filter(
                Product.store_id == store_id,
                Order.status != OrderStatus.CANCELED,
                Order.created_at >= prev_start_date,
                Order.created_at <= prev_end_date
            )
            .scalar() or 0
        )
        
        # Average Order Value (AOV) metrics
        current_aov = (
            self.db.query(func.avg(Order.total_amount))
            .join(OrderProduct, Order.id == OrderProduct.order_id)
            .join(Product, OrderProduct.product_id == Product.id)
            .filter(
                Product.store_id == store_id,
                Order.status != OrderStatus.CANCELED,
                Order.created_at >= start_date,
                Order.created_at <= end_date
            )
            .scalar() or 0
        )
        
        previous_aov = (
            self.db.query(func.avg(Order.total_amount))
            .join(OrderProduct, Order.id == OrderProduct.order_id)
            .join(Product, OrderProduct.product_id == Product.id)
            .filter(
                Product.store_id == store_id,
                Order.status != OrderStatus.CANCELED,
                Order.created_at >= prev_start_date,
                Order.created_at <= prev_end_date
            )
            .scalar() or 0
        )
        
        # Retention calculation (repeat customers)
        repeat_customers = (
            self.db.query(func.count(func.distinct(Order.customer_id)))
            .join(OrderProduct, Order.id == OrderProduct.order_id)
            .join(Product, OrderProduct.product_id == Product.id)
            .filter(
                Product.store_id == store_id,
                Order.status != OrderStatus.CANCELED,
                Order.created_at >= start_date,
                Order.created_at <= end_date,
                # Customer has more than one order in the current period
                func.count(func.distinct(Order.id)) > 1
            )
            .group_by(Order.customer_id)
            .having(func.count(func.distinct(Order.id)) > 1)
            .count()
        )
        
        # Calculate growth percentages
        monthly_growth = (
            (current_sales - previous_sales) / previous_sales * 100 
            if previous_sales > 0 else 0
        )
        
        customer_growth = (
            (current_customers - previous_customers) / previous_customers * 100 
            if previous_customers > 0 else 0
        )
        
        aov_growth = (
            (current_aov - previous_aov) / previous_aov * 100 
            if previous_aov > 0 else 0
        )
        
        retention_improvement = (
            (repeat_customers / current_customers * 100) 
            if current_customers > 0 else 0
        )
        
        return {
            "store_id": store_id,
            "monthly_growth": round(monthly_growth, 1),
            "customer_growth": round(customer_growth, 1),
            "aov_growth": round(aov_growth, 1),
            "retention_improvement": round(retention_improvement, 1),
            "period": period,
            "start_date": start_date,
            "end_date": end_date,
            "currency": "USD"
        }
    
    # ========== Utility Methods ==========
    
    def _generate_order_number(self) -> str:
        """Generate a unique order number."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f"ORD-{timestamp}-{random_suffix}"
    
    def _restore_order_stock(self, order: Order) -> None:
        """Restore product stock when order is canceled."""
        for order_product in order.products:
            product = order_product.product
            product.stock += order_product.quantity
    
    def _get_period_start_date(self, period: str, end_date: Optional[datetime] = None) -> datetime:
        """
        Get start date based on period.
        
        Args:
            period: 'week', 'month', 'quarter', 'year'
            end_date: End date (defaults to now)
        
        Returns:
            Start date for the period
        """
        if not end_date:
            end_date = datetime.utcnow()
        
        if period == "week":
            return end_date - timedelta(days=7)
        elif period == "month":
            return end_date - timedelta(days=30)
        elif period == "quarter":
            return end_date - timedelta(days=90)
        elif period == "year":
            return end_date - timedelta(days=365)
        else:
            # Default to week
            return end_date - timedelta(days=7)
    
    def get_customer_orders(self, customer_id: int, skip: int = 0, limit: int = 100) -> List[Order]:
        """Get all orders for a specific customer."""
        orders = (
            self.db.query(Order)
            .filter(Order.customer_id == customer_id)
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return orders