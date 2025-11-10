from typing import List, Optional
from datetime import datetime, timedelta
import io
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.order import OrderCreate, OrderUpdate, OrderResponse
from app.services.order import OrderService
from app.models.order import Order, OrderStatus, OrderProduct
from app.models.product import Product
from app.models.user import User
from app.utils.auth_dependencies import get_current_active_user
from app.services.store_service import StoreService

router = APIRouter(prefix="/orders", tags=["orders"])


# ========== CRUD Endpoints ==========

@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new order.
    The order will be created for the currently logged-in customer.
    Validates products, stock availability, and calculates total amount.
    """
    # Validate that only customers can create orders
    from app.models.user import UserType
    if current_user.user_type != UserType.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customers can create orders"
        )
    
    order_service = OrderService(db)
    order = order_service.create_order(order_data, current_user.id)
    return order


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a single order by ID."""
    order_service = OrderService(db)
    order = order_service.get_order_by_id(order_id)
    
    # Authorization: Only customer who placed order or store owner can view
    # TODO: Add store owner check
    if order.customer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this order"
        )
    
    return order


@router.get("/number/{order_number}", response_model=OrderResponse)
def get_order_by_number(
    order_number: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a single order by order number."""
    order_service = OrderService(db)
    order = order_service.get_order_by_number(order_number)
    
    # Authorization check
    if order.customer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this order"
        )
    
    return order


@router.get("/", response_model=List[OrderResponse])
@router.get("", response_model=List[OrderResponse])  # Handle both /orders and /orders/
def get_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    status_filter: Optional[OrderStatus] = Query(None, alias="status"),
    customer_id: Optional[int] = None,
    store_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all orders with optional filtering.
    Customers see only their orders.
    Store owners see orders for their store.
    """
    order_service = OrderService(db)
    
    # If regular customer, only show their orders
    if customer_id and customer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view other customer orders"
        )
    
    # Default to current user's orders if no filter specified
    if not customer_id and not store_id:
        customer_id = current_user.id
    
    orders = order_service.get_all_orders(
        skip=skip,
        limit=limit,
        status=status_filter,
        customer_id=customer_id,
        store_id=store_id
    )
    
    return orders


@router.put("/{order_id}", response_model=OrderResponse)
def update_order(
    order_id: int,
    order_data: OrderUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update order information.
    Only the customer who placed the order can update it.
    """
    order_service = OrderService(db)
    order = order_service.get_order_by_id(order_id)
    
    # Authorization check
    if order.customer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this order"
        )
    
    updated_order = order_service.update_order(order_id, order_data)
    return updated_order


@router.post("/{order_id}/cancel", response_model=OrderResponse)
def cancel_order(
    order_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Cancel an order.
    Restores product stock.
    """
    order_service = OrderService(db)
    order = order_service.get_order_by_id(order_id)
    
    # Authorization check
    if order.customer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to cancel this order"
        )
    
    canceled_order = order_service.cancel_order(order_id)
    return canceled_order


@router.delete("/{order_id}")
def delete_order(
    order_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete an order (hard delete).
    Should only be used for invalid/test orders.
    Admin only.
    """
    order_service = OrderService(db)
    order = order_service.get_order_by_id(order_id)
    
    # Authorization check - TODO: Add admin role check
    if order.customer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this order"
        )
    
    order_service.delete_order(order_id)
    return {"message": "Order deleted successfully"}


@router.get("/customer/{customer_id}", response_model=List[OrderResponse])
def get_customer_orders(
    customer_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all orders for a specific customer."""
    # Authorization: Only the customer themselves can view their orders
    if customer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view other customer orders"
        )
    
    order_service = OrderService(db)
    orders = order_service.get_customer_orders(customer_id, skip, limit)
    return orders


# ========== Analytics Endpoints ==========

@router.get("/analytics/income/{store_id}")
def get_store_income(
    store_id: int,
    period: str = Query("week", regex="^(week|month|quarter|year)$"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get total income for a store in a given period.
    
    Period options: week, month, quarter, year
    """
    # TODO: Add store owner authorization check
    order_service = OrderService(db)
    return order_service.get_total_income(store_id, start_date, end_date, period)


@router.get("/analytics/revenue/{store_id}")
def get_store_revenue(
    store_id: int,
    period: str = Query("week", regex="^(week|month|quarter|year)$"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get total revenue (profit) for a store.
    Revenue = Income - Production Costs
    
    Period options: week, month, quarter, year
    """
    # TODO: Add store owner authorization check
    order_service = OrderService(db)
    return order_service.get_total_revenue(store_id, start_date, end_date, period)


@router.get("/analytics/count/{store_id}")
def get_orders_count(
    store_id: int,
    period: str = Query("week", regex="^(week|month|quarter|year)$"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get total number of orders for a store with status breakdown.
    
    Period options: week, month, quarter, year
    """
    # TODO: Add store owner authorization check
    order_service = OrderService(db)
    return order_service.get_total_orders_count(store_id, start_date, end_date, period)


@router.get("/analytics/average-order-value/{store_id}")
def get_average_order_value(
    store_id: int,
    period: str = Query("week", regex="^(week|month|quarter|year)$"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get average order value (AOV) for a store.
    
    Period options: week, month, quarter, year
    """
    # TODO: Add store owner authorization check
    order_service = OrderService(db)
    return order_service.get_average_order_value(store_id, start_date, end_date, period)


@router.get("/analytics/items-sold/{store_id}")
def get_items_sold(
    store_id: int,
    period: str = Query("week", regex="^(week|month|quarter|year)$"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get total number of items sold for a store.
    Includes top selling products.
    
    Period options: week, month, quarter, year
    """
    # TODO: Add store owner authorization check
    order_service = OrderService(db)
    return order_service.get_items_sold_count(store_id, start_date, end_date, period)


@router.get("/analytics/returned/{store_id}")
def get_returned_orders(
    store_id: int,
    period: str = Query("week", regex="^(week|month|quarter|year)$"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get returned (canceled) orders for a store.
    Includes return rate and lost revenue.
    
    Period options: week, month, quarter, year
    """
    # TODO: Add store owner authorization check
    order_service = OrderService(db)
    return order_service.get_returned_orders(store_id, start_date, end_date, period)


@router.get("/analytics/fulfilled/{store_id}")
def get_fulfilled_orders(
    store_id: int,
    period: str = Query("week", regex="^(week|month|quarter|year)$"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get fulfilled (delivered) orders for a store.
    Includes fulfillment rate and average fulfillment time.
    
    Period options: week, month, quarter, year
    """
    # TODO: Add store owner authorization check
    order_service = OrderService(db)
    return order_service.get_fulfilled_orders(store_id, start_date, end_date, period)


@router.get("/analytics/conversion-rate/{store_id}")
def get_conversion_rate(
    store_id: int,
    period: str = Query("week", regex="^(week|month|quarter|year)$"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get conversion rate for a store.
    
    Conversion Rate = (Delivered Orders / Completed Journeys) * 100
    
    Where:
    - Delivered Orders = Orders with status DELIVERED
    - Completed Journeys = Delivered + Canceled orders
    - In-Progress orders are excluded from conversion calculation
    
    Period options: week, month, quarter, year
    """
    # TODO: Add store owner authorization check
    order_service = OrderService(db)
    return order_service.get_conversion_rate(store_id, start_date, end_date, period)


@router.get("/analytics/dashboard/{store_id}")
def get_dashboard_analytics(
    store_id: int,
    period: str = Query("week", regex="^(week|month|quarter|year)$"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive dashboard analytics for a store.
    
    Returns all analytics in a single response:
    - Income
    - Revenue (profit)
    - Order count
    - Average order value
    - Items sold
    - Returned orders
    - Fulfilled orders
    - Conversion rate
    
    Period options: week, month, quarter, year
    """
    # TODO: Add store owner authorization check
    order_service = OrderService(db)
    return order_service.get_dashboard_analytics(store_id, start_date, end_date, period)


@router.get("/analytics/summary/{store_id}")
def get_dashboard_summary(
    store_id: int,
    period: str = Query("week", regex="^(week|month|quarter|year)$"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get simplified dashboard summary with key metrics for a store.
    
    Returns only the 4 main metrics:
    - Total Revenue (profit)
    - Total Income
    - Total Orders
    - Average Order Value
    
    Each metric includes comparison with previous period.
    
    Period options: week, month, quarter, year
    """
    # TODO: Add store owner authorization check
    order_service = OrderService(db)
    return order_service.get_dashboard_summary(store_id, start_date, end_date, period)


@router.get("/export/{store_id}", response_class=Response)
def export_store_order_history(
    store_id: int,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Export store order history to Excel.
    
    Parameters:
    - store_id: ID of the store
    - start_date: Optional start date for filtering orders
    - end_date: Optional end date for filtering orders
    
    Returns:
    - Excel file with order history
    """
    order_service = OrderService(db)
    
    # If no dates provided, default to last 30 days
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    # Get all orders for the store within the date range
    query = db.query(Order, OrderProduct, Product, User)\
        .join(OrderProduct, Order.id == OrderProduct.order_id)\
        .join(Product, OrderProduct.product_id == Product.id)\
        .join(User, Order.customer_id == User.id)\
        .filter(
            Product.store_id == store_id,
            Order.created_at >= start_date,
            Order.created_at <= end_date
        )
    
    # Execute query
    results = query.all()
    
    # Prepare data for DataFrame
    order_data = []
    for order, order_product, product, customer in results:
        order_data.append({
            'Order Number': order.order_number,
            'Order Date': order.created_at,
            'Customer Name': customer.username,
            'Customer Email': customer.email,
            'Product Name': product.name,
            'Product Quantity': order_product.quantity,
            'Unit Price': order_product.unit_price,
            'Total Product Price': order_product.quantity * order_product.unit_price,
            'Order Total': order.total_amount,
            'Order Status': order.status.value,
            'Shipping Address': order.shipping_address,
            'Shipping City': order.shipping_city,
            'Shipping Postal Code': order.shipping_postal_code,
            'Shipping Country': order.shipping_country
        })
    
    # Create DataFrame
    df = pd.DataFrame(order_data)
    
    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Order History', index=False)
    
    output.seek(0)
    
    return Response(
        content=output.getvalue(), 
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={
            'Content-Disposition': f'attachment; filename=store_{store_id}_order_history_{start_date.date()}_{end_date.date()}.xlsx'
        }
    )


@router.get("/sales-performance/{store_id}")
def get_sales_performance(
    store_id: int,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive sales performance data for a store.
    
    Returns:
    - Daily sales data for the last 30 days
    - Best day sales
    - Average daily sales
    - Total orders
    
    Parameters:
    - store_id: ID of the store
    - start_date: Optional start date (defaults to 30 days ago)
    - end_date: Optional end date (defaults to today)
    """
    order_service = OrderService(db)
    
    # Verify store ownership (optional, can be adjusted based on requirements)
    store_service = StoreService(db)
    store_service.verify_store_ownership(store_id, current_user.id)
    
    return order_service.get_sales_performance(store_id, start_date, end_date)


@router.get("/growth-metrics/{store_id}")
def get_growth_metrics(
    store_id: int,
    period: str = Query("month", regex="^(week|month|quarter|year)$"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive growth metrics for a store.
    
    Returns:
    - Monthly Sales Growth
    - Customer Growth
    - Average Order Value (AOV) Growth
    - Customer Retention Improvement
    
    Parameters:
    - store_id: ID of the store
    - period: Time period for comparison (week, month, quarter, year)
    """
    order_service = OrderService(db)
    
    # Verify store ownership (optional, can be adjusted based on requirements)
    store_service = StoreService(db)
    store_service.verify_store_ownership(store_id, current_user.id)
    
    return order_service.get_growth_metrics(store_id, period)
