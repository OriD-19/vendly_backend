"""
Seed database with mock data.

This script populates the database with realistic test data including:
- Store owners and customers
- Stores with products
- Categories and tags
- Orders and chat messages

Usage:
    python seed_database.py
"""

from datetime import datetime, timedelta
from app.database import SessionLocal, init_db
from app.models.user import User, UserType, UserPreferences
from app.models.store import Store
from app.models.category import Category
from app.models.product import Product, ProductImage, Tag, ProductTag
from app.models.order import Order, OrderProduct, OrderStatus
from app.models.chat_message import ChatMessage
from app.services.auth_service import AuthService


def clear_database(db):
    """Clear all existing data (optional)."""
    print("⚠️  Clearing existing data...")
    
    # Delete in correct order to avoid foreign key constraints
    db.query(ChatMessage).delete()
    db.query(OrderProduct).delete()
    db.query(Order).delete()
    db.query(ProductTag).delete()
    db.query(Tag).delete()
    db.query(ProductImage).delete()
    db.query(Product).delete()
    db.query(Category).delete()
    db.query(Store).delete()
    db.query(UserPreferences).delete()
    db.query(User).delete()
    
    db.commit()
    print("✅ Database cleared")


def create_users(db):
    """Create store owners and customers."""
    print("\n👥 Creating users...")
    
    # Password: storeowner123 / customer123
    password_hash = AuthService.hash_password("storeowner123")
    customer_hash = AuthService.hash_password("customer123")
    
    users = [
        # Store Owners
        User(
            username="techstore_owner",
            email="techstore@example.com",
            password_hash=password_hash,
            user_type=UserType.STORE
        ),
        User(
            username="fashion_boutique",
            email="fashion@example.com",
            password_hash=password_hash,
            user_type=UserType.STORE
        ),
        # Customers
        User(
            username="john_doe",
            email="john@example.com",
            password_hash=customer_hash,
            user_type=UserType.CUSTOMER
        ),
        User(
            username="jane_smith",
            email="jane@example.com",
            password_hash=customer_hash,
            user_type=UserType.CUSTOMER
        ),
        User(
            username="mike_wilson",
            email="mike@example.com",
            password_hash=customer_hash,
            user_type=UserType.CUSTOMER
        ),
    ]
    
    for user in users:
        db.add(user)
    
    db.commit()
    print(f"✅ Created {len(users)} users")
    return users


def create_stores(db, users):
    """Create stores."""
    print("\n🏪 Creating stores...")
    
    tech_owner = db.query(User).filter(User.username == "techstore_owner").first()
    fashion_owner = db.query(User).filter(User.username == "fashion_boutique").first()
    
    stores = [
        Store(
            name="TechHub Electronics",
            owner_id=tech_owner.id,
            phone="+1-555-0123",
            email="contact@techhub.com",
            store_location="123 Tech Street, Silicon Valley, CA 94025",
            type="Electronics",
            profile_image="https://images.unsplash.com/photo-1550009158-9ebf69173e03?w=400"
        ),
        Store(
            name="Chic Fashion Boutique",
            owner_id=fashion_owner.id,
            phone="+1-555-0456",
            email="hello@chicfashion.com",
            store_location="456 Fashion Ave, New York, NY 10001",
            type="Fashion",
            profile_image="https://images.unsplash.com/photo-1441984904996-e0b6ba687e04?w=400"
        ),
    ]
    
    for store in stores:
        db.add(store)
    
    db.commit()
    
    # Update users with store_id
    tech_owner.store_id = stores[0].id
    fashion_owner.store_id = stores[1].id
    db.commit()
    
    print(f"✅ Created {len(stores)} stores")
    return stores


def create_categories(db):
    """Create product categories."""
    print("\n📁 Creating categories...")
    
    categories = [
        Category(name="Smartphones"),
        Category(name="Laptops"),
        Category(name="Accessories"),
        Category(name="Audio"),
        Category(name="Mens Clothing"),
        Category(name="Womens Clothing"),
        Category(name="Shoes"),
        Category(name="Bags & Accessories"),
    ]
    
    for category in categories:
        db.add(category)
    
    db.commit()
    print(f"✅ Created {len(categories)} categories")
    return categories


def create_tech_products(db, store, categories):
    """Create tech products for TechHub Electronics."""
    print("\n💻 Creating tech products...")
    
    smartphones = db.query(Category).filter(Category.name == "Smartphones").first()
    laptops = db.query(Category).filter(Category.name == "Laptops").first()
    audio = db.query(Category).filter(Category.name == "Audio").first()
    accessories = db.query(Category).filter(Category.name == "Accessories").first()
    
    products = [
        # Smartphones
        Product(
            name="iPhone 15 Pro Max",
            descriptions="Latest iPhone with titanium design, A17 Pro chip, and advanced camera system. Features ProMotion display and USB-C connectivity.",
            price=119999,
            production_cost=85000,
            stock=25,
            is_active=True,
            store_id=store.id,
            category_id=smartphones.id
        ),
        Product(
            name="Samsung Galaxy S24 Ultra",
            descriptions="Premium Android flagship with S Pen, 200MP camera, and AI features. Includes 12GB RAM and 5000mAh battery.",
            price=109999,
            production_cost=78000,
            stock=30,
            is_active=True,
            store_id=store.id,
            category_id=smartphones.id
        ),
        Product(
            name="Google Pixel 8 Pro",
            descriptions="Google flagship phone with advanced AI photography, Tensor G3 chip, and pure Android experience.",
            price=89999,
            production_cost=62000,
            stock=20,
            is_active=True,
            store_id=store.id,
            category_id=smartphones.id
        ),
        # Laptops
        Product(
            name='MacBook Pro 16" M3 Max',
            descriptions="Professional laptop with M3 Max chip, 36GB unified memory, and stunning Liquid Retina XDR display. Perfect for creative professionals.",
            price=349999,
            production_cost=280000,
            stock=15,
            is_active=True,
            store_id=store.id,
            category_id=laptops.id
        ),
        Product(
            name="Dell XPS 15",
            descriptions="Premium Windows laptop with Intel i9 processor, NVIDIA RTX 4070, and 4K OLED display. Ideal for work and gaming.",
            price=229999,
            production_cost=170000,
            stock=12,
            is_active=True,
            store_id=store.id,
            category_id=laptops.id
        ),
        # Audio
        Product(
            name="Sony WH-1000XM5",
            descriptions="Industry-leading noise canceling headphones with exceptional sound quality and 30-hour battery life.",
            price=39999,
            production_cost=25000,
            stock=50,
            is_active=True,
            store_id=store.id,
            category_id=audio.id
        ),
        Product(
            name="AirPods Pro (2nd Gen)",
            descriptions="Apple wireless earbuds with active noise cancellation, spatial audio, and MagSafe charging case.",
            price=24999,
            production_cost=16000,
            stock=60,
            is_active=True,
            store_id=store.id,
            category_id=audio.id
        ),
        Product(
            name="Bose SoundLink Flex",
            descriptions="Portable Bluetooth speaker with waterproof design and 12-hour battery. Perfect for outdoor adventures.",
            price=14999,
            production_cost=9000,
            stock=40,
            is_active=True,
            store_id=store.id,
            category_id=audio.id
        ),
        # Accessories
        Product(
            name="Anker PowerCore 20000mAh",
            descriptions="High-capacity portable charger with fast charging support for multiple devices simultaneously.",
            price=4999,
            production_cost=2500,
            stock=100,
            is_active=True,
            store_id=store.id,
            category_id=accessories.id
        ),
        Product(
            name="Logitech MX Master 3S",
            descriptions="Advanced wireless mouse with ergonomic design, 8K DPI sensor, and customizable buttons for productivity.",
            price=9999,
            production_cost=6000,
            stock=45,
            is_active=True,
            store_id=store.id,
            category_id=accessories.id
        ),
        Product(
            name="USB-C Hub 11-in-1",
            descriptions="Multiport adapter with HDMI, USB 3.0, SD card reader, and 100W power delivery. Essential for laptops.",
            price=5999,
            production_cost=3000,
            stock=80,
            is_active=True,
            store_id=store.id,
            category_id=accessories.id
        ),
    ]
    
    for product in products:
        db.add(product)
    
    db.commit()
    print(f"✅ Created {len(products)} tech products")
    return products


def create_fashion_products(db, store, categories):
    """Create fashion products for Chic Fashion Boutique."""
    print("\n👗 Creating fashion products...")
    
    mens = db.query(Category).filter(Category.name == "Mens Clothing").first()
    womens = db.query(Category).filter(Category.name == "Womens Clothing").first()
    shoes = db.query(Category).filter(Category.name == "Shoes").first()
    bags = db.query(Category).filter(Category.name == "Bags & Accessories").first()
    
    products = [
        # Men's
        Product(
            name="Premium Cotton T-Shirt",
            descriptions="Ultra-soft 100% organic cotton t-shirt with modern fit. Available in multiple colors. Perfect for casual wear.",
            price=2999,
            production_cost=1200,
            stock=150,
            is_active=True,
            store_id=store.id,
            category_id=mens.id
        ),
        Product(
            name="Slim Fit Denim Jeans",
            descriptions="Classic blue denim jeans with stretch fabric for comfort. Features modern slim fit and durable construction.",
            price=7999,
            production_cost=3500,
            stock=80,
            is_active=True,
            store_id=store.id,
            category_id=mens.id
        ),
        # Women's
        Product(
            name="Floral Summer Dress",
            descriptions="Beautiful flowing dress with vibrant floral print. Light and breathable fabric perfect for summer days.",
            price=8999,
            production_cost=4000,
            stock=60,
            is_active=True,
            store_id=store.id,
            category_id=womens.id
        ),
        Product(
            name="Elegant Blouse",
            descriptions="Sophisticated silk-blend blouse with delicate design. Versatile piece for professional or evening wear.",
            price=6999,
            production_cost=3200,
            stock=70,
            is_active=True,
            store_id=store.id,
            category_id=womens.id
        ),
        # Shoes
        Product(
            name="White Leather Sneakers",
            descriptions="Classic minimalist sneakers in premium leather. Comfortable insole and versatile design for everyday wear.",
            price=8999,
            production_cost=4500,
            stock=50,
            is_active=True,
            store_id=store.id,
            category_id=shoes.id
        ),
        Product(
            name="Ankle Boots - Black",
            descriptions="Stylish Chelsea boots with elastic side panels. Durable leather construction with comfortable heel.",
            price=12999,
            production_cost=7000,
            stock=40,
            is_active=True,
            store_id=store.id,
            category_id=shoes.id
        ),
        # Accessories
        Product(
            name="Leather Crossbody Bag",
            descriptions="Compact genuine leather bag with adjustable strap. Perfect size for essentials with multiple compartments.",
            price=9999,
            production_cost=5000,
            stock=45,
            is_active=True,
            store_id=store.id,
            category_id=bags.id
        ),
        Product(
            name="Silk Scarf Collection",
            descriptions="Luxurious silk scarf with artistic print. Versatile accessory that adds elegance to any outfit.",
            price=3999,
            production_cost=1800,
            stock=100,
            is_active=True,
            store_id=store.id,
            category_id=bags.id
        ),
    ]
    
    for product in products:
        db.add(product)
    
    db.commit()
    print(f"✅ Created {len(products)} fashion products")
    return products


def create_product_images(db):
    """Add product images."""
    print("\n🖼️  Adding product images...")
    
    images = [
        ("iPhone 15 Pro Max", "https://images.unsplash.com/photo-1695048133142-1a20484d2569?w=800"),
        ("Samsung Galaxy S24 Ultra", "https://images.unsplash.com/photo-1610945415295-d9bbf067e59c?w=800"),
        ('MacBook Pro 16" M3 Max', "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=800"),
        ("Sony WH-1000XM5", "https://images.unsplash.com/photo-1546435770-a3e426bf472b?w=800"),
        ("AirPods Pro (2nd Gen)", "https://images.unsplash.com/photo-1606841837239-c5a1a4a07af7?w=800"),
        ("Floral Summer Dress", "https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=800"),
        ("White Leather Sneakers", "https://images.unsplash.com/photo-1549298916-b41d501d3772?w=800"),
        ("Leather Crossbody Bag", "https://images.unsplash.com/photo-1590874103328-eac38a683ce7?w=800"),
    ]
    
    count = 0
    for product_name, image_url in images:
        product = db.query(Product).filter(Product.name == product_name).first()
        if product:
            db.add(ProductImage(product_id=product.id, image_url=image_url))
            count += 1
    
    db.commit()
    print(f"✅ Added {count} product images")


def create_tags(db):
    """Create product tags."""
    print("\n🏷️  Creating tags...")
    
    tag_names = [
        "Premium", "Best Seller", "New Arrival", "Sale", "Limited Edition",
        "Eco-Friendly", "5G", "Wireless", "Waterproof", "Fast Charging",
        "AI-Powered", "Professional", "Gaming", "Portable", "Trending",
        "Summer Collection", "Sustainable", "Handcrafted"
    ]
    
    tags = [Tag(name=name) for name in tag_names]
    for tag in tags:
        db.add(tag)
    
    db.commit()
    print(f"✅ Created {len(tags)} tags")
    return tags


def assign_tags(db):
    """Assign tags to products."""
    print("\n🔗 Assigning tags to products...")
    
    assignments = [
        ("iPhone 15 Pro Max", ["Premium", "Best Seller", "5G"]),
        ("Samsung Galaxy S24 Ultra", ["Premium", "AI-Powered", "5G"]),
        ('MacBook Pro 16" M3 Max', ["Premium", "Professional", "Best Seller"]),
        ("Sony WH-1000XM5", ["Best Seller", "Wireless"]),
        ("AirPods Pro (2nd Gen)", ["Best Seller", "Wireless", "Waterproof"]),
        ("Bose SoundLink Flex", ["Portable", "Waterproof", "Wireless"]),
        ("Floral Summer Dress", ["Summer Collection", "Trending"]),
        ("Premium Cotton T-Shirt", ["Eco-Friendly", "Best Seller"]),
        ("Leather Crossbody Bag", ["Handcrafted", "Premium"]),
    ]
    
    count = 0
    for product_name, tag_names in assignments:
        product = db.query(Product).filter(Product.name == product_name).first()
        if product:
            for tag_name in tag_names:
                tag = db.query(Tag).filter(Tag.name == tag_name).first()
                if tag:
                    db.add(ProductTag(product_id=product.id, tag_id=tag.id))
                    count += 1
    
    db.commit()
    print(f"✅ Assigned {count} tags to products")


def create_orders(db):
    """Create customer orders."""
    print("\n📦 Creating orders...")
    
    john = db.query(User).filter(User.username == "john_doe").first()
    jane = db.query(User).filter(User.username == "jane_smith").first()
    mike = db.query(User).filter(User.username == "mike_wilson").first()
    
    # Order 1: John buys iPhone and AirPods (delivered)
    order1 = Order(
        order_number="ORD-2025-001",
        customer_id=john.id,
        total_amount=144998,
        status=OrderStatus.DELIVERED,
        shipping_address="789 Customer Lane, Apt 4B",
        shipping_city="New York",
        shipping_postal_code="10002",
        shipping_country="USA",
        created_at=datetime.now() - timedelta(days=7),
        shipped_at=datetime.now() - timedelta(days=5),
        delivered_at=datetime.now() - timedelta(days=3)
    )
    db.add(order1)
    db.flush()
    
    iphone = db.query(Product).filter(Product.name == "iPhone 15 Pro Max").first()
    airpods = db.query(Product).filter(Product.name == "AirPods Pro (2nd Gen)").first()
    
    db.add(OrderProduct(order_id=order1.id, product_id=iphone.id, quantity=1, unit_price=119999))
    db.add(OrderProduct(order_id=order1.id, product_id=airpods.id, quantity=1, unit_price=24999))
    
    # Order 2: Jane buys fashion items (shipped)
    order2 = Order(
        order_number="ORD-2025-002",
        customer_id=jane.id,
        total_amount=21997,
        status=OrderStatus.SHIPPED,
        shipping_address="456 Fashion Street",
        shipping_city="Los Angeles",
        shipping_postal_code="90001",
        shipping_country="USA",
        created_at=datetime.now() - timedelta(days=2),
        shipped_at=datetime.now() - timedelta(days=1)
    )
    db.add(order2)
    db.flush()
    
    dress = db.query(Product).filter(Product.name == "Floral Summer Dress").first()
    sneakers = db.query(Product).filter(Product.name == "White Leather Sneakers").first()
    scarf = db.query(Product).filter(Product.name == "Silk Scarf Collection").first()
    
    db.add(OrderProduct(order_id=order2.id, product_id=dress.id, quantity=1, unit_price=8999))
    db.add(OrderProduct(order_id=order2.id, product_id=sneakers.id, quantity=1, unit_price=8999))
    db.add(OrderProduct(order_id=order2.id, product_id=scarf.id, quantity=1, unit_price=3999))
    
    # Order 3: Mike buys laptop (pending)
    order3 = Order(
        order_number="ORD-2025-003",
        customer_id=mike.id,
        total_amount=395997,
        status=OrderStatus.PENDING,
        shipping_address="123 Tech Road",
        shipping_city="London",
        shipping_postal_code="SW1A 1AA",
        shipping_country="UK",
        created_at=datetime.now() - timedelta(hours=1)
    )
    db.add(order3)
    db.flush()
    
    macbook = db.query(Product).filter(Product.name == 'MacBook Pro 16" M3 Max').first()
    headphones = db.query(Product).filter(Product.name == "Sony WH-1000XM5").first()
    hub = db.query(Product).filter(Product.name == "USB-C Hub 11-in-1").first()
    
    db.add(OrderProduct(order_id=order3.id, product_id=macbook.id, quantity=1, unit_price=349999))
    db.add(OrderProduct(order_id=order3.id, product_id=headphones.id, quantity=1, unit_price=39999))
    db.add(OrderProduct(order_id=order3.id, product_id=hub.id, quantity=2, unit_price=5999))
    
    db.commit()
    print("✅ Created 3 orders with products")


def create_chat_messages(db):
    """Create chat messages."""
    print("\n💬 Creating chat messages...")
    
    john = db.query(User).filter(User.username == "john_doe").first()
    jane = db.query(User).filter(User.username == "jane_smith").first()
    tech_owner = db.query(User).filter(User.username == "techstore_owner").first()
    fashion_owner = db.query(User).filter(User.username == "fashion_boutique").first()
    
    tech_store = db.query(Store).filter(Store.name == "TechHub Electronics").first()
    fashion_store = db.query(Store).filter(Store.name == "Chic Fashion Boutique").first()
    
    messages = [
        # Tech store conversation
        ChatMessage(
            sender_id=john.id,
            store_id=tech_store.id,
            message="Hi! Does the iPhone 15 Pro Max come with a charger?",
            created_at=datetime.now() - timedelta(days=10)
        ),
        ChatMessage(
            sender_id=tech_owner.id,
            store_id=tech_store.id,
            message="Hello! The iPhone 15 Pro Max comes with a USB-C to USB-C cable, but the power adapter is sold separately. We have great options available!",
            created_at=datetime.now() - timedelta(days=10, minutes=-15)
        ),
        ChatMessage(
            sender_id=john.id,
            store_id=tech_store.id,
            message="Thanks! I will also need the AirPods Pro. Do you have them in stock?",
            created_at=datetime.now() - timedelta(days=10, minutes=-30)
        ),
        ChatMessage(
            sender_id=tech_owner.id,
            store_id=tech_store.id,
            message="Yes, we have plenty in stock! Both products can ship together if you order today.",
            created_at=datetime.now() - timedelta(days=10, minutes=-45)
        ),
        # Fashion store conversation
        ChatMessage(
            sender_id=jane.id,
            store_id=fashion_store.id,
            message="What sizes do you have for the Floral Summer Dress?",
            created_at=datetime.now() - timedelta(days=3)
        ),
        ChatMessage(
            sender_id=fashion_owner.id,
            store_id=fashion_store.id,
            message="We have sizes XS through XL available! The dress runs true to size. Would you like me to check a specific size for you?",
            created_at=datetime.now() - timedelta(days=3, minutes=-20)
        ),
        ChatMessage(
            sender_id=jane.id,
            store_id=fashion_store.id,
            message="Perfect! I need a medium. Also, can you recommend shoes to go with it?",
            created_at=datetime.now() - timedelta(days=3, minutes=-35)
        ),
        ChatMessage(
            sender_id=fashion_owner.id,
            store_id=fashion_store.id,
            message="Great choice! Our White Leather Sneakers would be perfect for a casual look, or the Ankle Boots for a more elegant style. Both complement the dress beautifully!",
            created_at=datetime.now() - timedelta(days=3, minutes=-50)
        ),
    ]
    
    for msg in messages:
        db.add(msg)
    
    db.commit()
    print(f"✅ Created {len(messages)} chat messages")


def create_user_preferences(db):
    """Create user preferences."""
    print("\n⚙️  Creating user preferences...")
    
    john = db.query(User).filter(User.username == "john_doe").first()
    jane = db.query(User).filter(User.username == "jane_smith").first()
    mike = db.query(User).filter(User.username == "mike_wilson").first()
    
    preferences = [
        UserPreferences(user_id=john.id, theme="dark", notifications_enabled=True, email_alerts=True, timezone="America/New_York", language="en", currency="USD"),
        UserPreferences(user_id=jane.id, theme="light", notifications_enabled=True, email_alerts=False, timezone="America/Los_Angeles", language="en", currency="USD"),
        UserPreferences(user_id=mike.id, theme="dark", notifications_enabled=False, email_alerts=False, timezone="Europe/London", language="en", currency="GBP"),
    ]
    
    for pref in preferences:
        db.add(pref)
    
    db.commit()
    print(f"✅ Created {len(preferences)} user preferences")


def print_summary(db):
    """Print summary of seeded data."""
    print("\n" + "=" * 60)
    print("📊 Database Seeding Summary")
    print("=" * 60)
    
    print(f"\n👥 Users: {db.query(User).count()}")
    print(f"   - Store Owners: {db.query(User).filter(User.user_type == UserType.STORE).count()}")
    print(f"   - Customers: {db.query(User).filter(User.user_type == UserType.CUSTOMER).count()}")
    
    print(f"\n🏪 Stores: {db.query(Store).count()}")
    print(f"📁 Categories: {db.query(Category).count()}")
    print(f"📦 Products: {db.query(Product).count()}")
    print(f"🖼️  Product Images: {db.query(ProductImage).count()}")
    print(f"🏷️  Tags: {db.query(Tag).count()}")
    print(f"🛒 Orders: {db.query(Order).count()}")
    print(f"💬 Chat Messages: {db.query(ChatMessage).count()}")
    
    # Store details
    print("\n" + "=" * 60)
    print("🏪 Store Inventory")
    print("=" * 60)
    
    stores = db.query(Store).all()
    for store in stores:
        products = db.query(Product).filter(Product.store_id == store.id).all()
        total_stock = sum(p.stock for p in products)
        total_value = sum(p.price * p.stock for p in products) / 100.0
        
        print(f"\n{store.name}")
        print(f"   Products: {len(products)}")
        print(f"   Total Stock: {total_stock} items")
        print(f"   Inventory Value: ${total_value:,.2f}")
    
    print("\n" + "=" * 60)
    print("✨ Database seeding complete!")
    print("=" * 60)
    
    print("\n📝 Login Credentials:")
    print("\n   Store Owners:")
    print("   - Username: techstore_owner | Password: storeowner123")
    print("   - Username: fashion_boutique | Password: storeowner123")
    print("\n   Customers:")
    print("   - Username: john_doe | Password: customer123")
    print("   - Username: jane_smith | Password: customer123")
    print("   - Username: mike_wilson | Password: customer123")
    print("\n" + "=" * 60)


def main():
    """Main seeding function."""
    print("=" * 60)
    print("🌱 Vendly Database Seeding Script")
    print("=" * 60)
    
    # Initialize database
    print("\n📦 Initializing database...")
    init_db()
    
    db = SessionLocal()
    
    try:
        # Optional: Clear existing data
        # Uncomment the next line to clear database before seeding
        # clear_database(db)
        
        # Seed data
        users = create_users(db)
        stores = create_stores(db, users)
        categories = create_categories(db)
        
        tech_store = db.query(Store).filter(Store.name == "TechHub Electronics").first()
        fashion_store = db.query(Store).filter(Store.name == "Chic Fashion Boutique").first()
        
        create_tech_products(db, tech_store, categories)
        create_fashion_products(db, fashion_store, categories)
        create_product_images(db)
        create_tags(db)
        assign_tags(db)
        create_orders(db)
        create_chat_messages(db)
        create_user_preferences(db)
        
        # Print summary
        print_summary(db)
        
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
