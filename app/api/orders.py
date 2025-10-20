from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.order import OrderCreate, OrderUpdate, OrderResponse
from app.services.order import OrderService
from app.models.order import OrderStatus
from app.utils.auth_dependencies import get_current_active_user
from app.models.user import User

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
    Validates products, stock availability, and calculates total amount.
    """
    order_service = OrderService(db)
    order = order_service.create_order(order_data)
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
