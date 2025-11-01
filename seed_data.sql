-- ============================================================
-- Vendly Database Mock Data - Seed Script
-- ============================================================
-- This script populates the database with realistic test data:
-- - 2 Store Owners with their stores
-- - 3 Customers
-- - Categories
-- - Products with images and tags
-- - Sample orders
-- - User preferences
-- - Chat messages
--
-- Usage:
--   PostgreSQL: psql -U postgres -d vendly < seed_data.sql
--   SQLite: sqlite3 vendly.db < seed_data.sql
-- ============================================================

-- Clear existing data (optional - comment out if you want to keep existing data)
-- TRUNCATE TABLE chat_messages, order_products, orders, product_tags, tags, product_images, products, categories, stores, user_preferences, users RESTART IDENTITY CASCADE;

-- ============================================================
-- USERS (Store Owners and Customers)
-- ============================================================

-- Store Owners
INSERT INTO users (username, email, password_hash, user_type, created_at, updated_at)
VALUES 
    -- Password: storeowner123
    ('techstore_owner', 'techstore@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5UpRFz7hQWx4W', 'store', NOW(), NOW()),
    -- Password: fashionstore123
    ('fashion_boutique', 'fashion@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5UpRFz7hQWx4W', 'store', NOW(), NOW());

-- Customers
INSERT INTO users (username, email, password_hash, user_type, created_at, updated_at)
VALUES 
    -- Password: customer123
    ('john_doe', 'john@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5UpRFz7hQWx4W', 'customer', NOW(), NOW()),
    -- Password: customer123
    ('jane_smith', 'jane@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5UpRFz7hQWx4W', 'customer', NOW(), NOW()),
    -- Password: customer123
    ('mike_wilson', 'mike@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5UpRFz7hQWx4W', 'customer', NOW(), NOW());

-- ============================================================
-- STORES
-- ============================================================

INSERT INTO stores (name, owner_id, phone, email, store_location, type, profile_image, created_at, updated_at)
VALUES 
    (
        'TechHub Electronics',
        (SELECT id FROM users WHERE username = 'techstore_owner'),
        '+1-555-0123',
        'contact@techhub.com',
        '123 Tech Street, Silicon Valley, CA 94025',
        'Electronics',
        'https://images.unsplash.com/photo-1550009158-9ebf69173e03?w=400',
        NOW(),
        NOW()
    ),
    (
        'Chic Fashion Boutique',
        (SELECT id FROM users WHERE username = 'fashion_boutique'),
        '+1-555-0456',
        'hello@chicfashion.com',
        '456 Fashion Ave, New York, NY 10001',
        'Fashion',
        'https://images.unsplash.com/photo-1441984904996-e0b6ba687e04?w=400',
        NOW(),
        NOW()
    );

-- Update store owners with their store_id
UPDATE users 
SET store_id = (SELECT id FROM stores WHERE name = 'TechHub Electronics')
WHERE username = 'techstore_owner';

UPDATE users 
SET store_id = (SELECT id FROM stores WHERE name = 'Chic Fashion Boutique')
WHERE username = 'fashion_boutique';

-- ============================================================
-- CATEGORIES
-- ============================================================

INSERT INTO categories (name, description, created_at, updated_at)
VALUES 
    ('Smartphones', 'Latest smartphones and mobile devices', NOW(), NOW()),
    ('Laptops', 'Laptops and portable computers', NOW(), NOW()),
    ('Accessories', 'Tech accessories and peripherals', NOW(), NOW()),
    ('Audio', 'Headphones, speakers, and audio equipment', NOW(), NOW()),
    ('Mens Clothing', 'Fashion for men', NOW(), NOW()),
    ('Womens Clothing', 'Fashion for women', NOW(), NOW()),
    ('Shoes', 'Footwear for all occasions', NOW(), NOW()),
    ('Bags & Accessories', 'Fashion accessories', NOW(), NOW());

-- ============================================================
-- PRODUCTS (TechHub Electronics)
-- ============================================================

INSERT INTO products (name, descriptions, price, production_cost, stock, is_active, store_id, category_id, created_at, updated_at)
VALUES 
    -- Smartphones
    (
        'iPhone 15 Pro Max',
        'Latest iPhone with titanium design, A17 Pro chip, and advanced camera system. Features ProMotion display and USB-C connectivity.',
        119999,
        85000,
        25,
        true,
        (SELECT id FROM stores WHERE name = 'TechHub Electronics'),
        (SELECT id FROM categories WHERE name = 'Smartphones'),
        NOW(),
        NOW()
    ),
    (
        'Samsung Galaxy S24 Ultra',
        'Premium Android flagship with S Pen, 200MP camera, and AI features. Includes 12GB RAM and 5000mAh battery.',
        109999,
        78000,
        30,
        true,
        (SELECT id FROM stores WHERE name = 'TechHub Electronics'),
        (SELECT id FROM categories WHERE name = 'Smartphones'),
        NOW(),
        NOW()
    ),
    (
        'Google Pixel 8 Pro',
        'Google flagship phone with advanced AI photography, Tensor G3 chip, and pure Android experience.',
        89999,
        62000,
        20,
        true,
        (SELECT id FROM stores WHERE name = 'TechHub Electronics'),
        (SELECT id FROM categories WHERE name = 'Smartphones'),
        NOW(),
        NOW()
    ),
    
    -- Laptops
    (
        'MacBook Pro 16" M3 Max',
        'Professional laptop with M3 Max chip, 36GB unified memory, and stunning Liquid Retina XDR display. Perfect for creative professionals.',
        349999,
        280000,
        15,
        true,
        (SELECT id FROM stores WHERE name = 'TechHub Electronics'),
        (SELECT id FROM categories WHERE name = 'Laptops'),
        NOW(),
        NOW()
    ),
    (
        'Dell XPS 15',
        'Premium Windows laptop with Intel i9 processor, NVIDIA RTX 4070, and 4K OLED display. Ideal for work and gaming.',
        229999,
        170000,
        12,
        true,
        (SELECT id FROM stores WHERE name = 'TechHub Electronics'),
        (SELECT id FROM categories WHERE name = 'Laptops'),
        NOW(),
        NOW()
    ),
    (
        'ThinkPad X1 Carbon Gen 11',
        'Business ultrabook with 14" display, Intel vPro platform, and military-grade durability. Lightweight at 2.48 lbs.',
        189999,
        140000,
        18,
        true,
        (SELECT id FROM stores WHERE name = 'TechHub Electronics'),
        (SELECT id FROM categories WHERE name = 'Laptops'),
        NOW(),
        NOW()
    ),
    
    -- Audio
    (
        'Sony WH-1000XM5',
        'Industry-leading noise canceling headphones with exceptional sound quality and 30-hour battery life.',
        39999,
        25000,
        50,
        true,
        (SELECT id FROM stores WHERE name = 'TechHub Electronics'),
        (SELECT id FROM categories WHERE name = 'Audio'),
        NOW(),
        NOW()
    ),
    (
        'AirPods Pro (2nd Gen)',
        'Apple wireless earbuds with active noise cancellation, spatial audio, and MagSafe charging case.',
        24999,
        16000,
        60,
        true,
        (SELECT id FROM stores WHERE name = 'TechHub Electronics'),
        (SELECT id FROM categories WHERE name = 'Audio'),
        NOW(),
        NOW()
    ),
    (
        'Bose SoundLink Flex',
        'Portable Bluetooth speaker with waterproof design and 12-hour battery. Perfect for outdoor adventures.',
        14999,
        9000,
        40,
        true,
        (SELECT id FROM stores WHERE name = 'TechHub Electronics'),
        (SELECT id FROM categories WHERE name = 'Audio'),
        NOW(),
        NOW()
    ),
    
    -- Accessories
    (
        'Anker PowerCore 20000mAh',
        'High-capacity portable charger with fast charging support for multiple devices simultaneously.',
        4999,
        2500,
        100,
        true,
        (SELECT id FROM stores WHERE name = 'TechHub Electronics'),
        (SELECT id FROM categories WHERE name = 'Accessories'),
        NOW(),
        NOW()
    ),
    (
        'Logitech MX Master 3S',
        'Advanced wireless mouse with ergonomic design, 8K DPI sensor, and customizable buttons for productivity.',
        9999,
        6000,
        45,
        true,
        (SELECT id FROM stores WHERE name = 'TechHub Electronics'),
        (SELECT id FROM categories WHERE name = 'Accessories'),
        NOW(),
        NOW()
    ),
    (
        'USB-C Hub 11-in-1',
        'Multiport adapter with HDMI, USB 3.0, SD card reader, and 100W power delivery. Essential for laptops.',
        5999,
        3000,
        80,
        true,
        (SELECT id FROM stores WHERE name = 'TechHub Electronics'),
        (SELECT id FROM categories WHERE name = 'Accessories'),
        NOW(),
        NOW()
    );

-- ============================================================
-- PRODUCTS (Chic Fashion Boutique)
-- ============================================================

INSERT INTO products (name, descriptions, price, production_cost, stock, is_active, store_id, category_id, created_at, updated_at)
VALUES 
    -- Men's Clothing
    (
        'Premium Cotton T-Shirt',
        'Ultra-soft 100% organic cotton t-shirt with modern fit. Available in multiple colors. Perfect for casual wear.',
        2999,
        1200,
        150,
        true,
        (SELECT id FROM stores WHERE name = 'Chic Fashion Boutique'),
        (SELECT id FROM categories WHERE name = 'Mens Clothing'),
        NOW(),
        NOW()
    ),
    (
        'Slim Fit Denim Jeans',
        'Classic blue denim jeans with stretch fabric for comfort. Features modern slim fit and durable construction.',
        7999,
        3500,
        80,
        true,
        (SELECT id FROM stores WHERE name = 'Chic Fashion Boutique'),
        (SELECT id FROM categories WHERE name = 'Mens Clothing'),
        NOW(),
        NOW()
    ),
    (
        'Casual Oxford Shirt',
        'Smart-casual button-down shirt in breathable cotton blend. Perfect for office or weekend wear.',
        4999,
        2200,
        100,
        true,
        (SELECT id FROM stores WHERE name = 'Chic Fashion Boutique'),
        (SELECT id FROM categories WHERE name = 'Mens Clothing'),
        NOW(),
        NOW()
    ),
    
    -- Women's Clothing
    (
        'Floral Summer Dress',
        'Beautiful flowing dress with vibrant floral print. Light and breathable fabric perfect for summer days.',
        8999,
        4000,
        60,
        true,
        (SELECT id FROM stores WHERE name = 'Chic Fashion Boutique'),
        (SELECT id FROM categories WHERE name = 'Womens Clothing'),
        NOW(),
        NOW()
    ),
    (
        'Elegant Blouse',
        'Sophisticated silk-blend blouse with delicate design. Versatile piece for professional or evening wear.',
        6999,
        3200,
        70,
        true,
        (SELECT id FROM stores WHERE name = 'Chic Fashion Boutique'),
        (SELECT id FROM categories WHERE name = 'Womens Clothing'),
        NOW(),
        NOW()
    ),
    (
        'High-Waisted Palazzo Pants',
        'Trendy wide-leg pants with comfortable elastic waist. Flowing fabric and flattering silhouette.',
        5999,
        2800,
        90,
        true,
        (SELECT id FROM stores WHERE name = 'Chic Fashion Boutique'),
        (SELECT id FROM categories WHERE name = 'Womens Clothing'),
        NOW(),
        NOW()
    ),
    
    -- Shoes
    (
        'White Leather Sneakers',
        'Classic minimalist sneakers in premium leather. Comfortable insole and versatile design for everyday wear.',
        8999,
        4500,
        50,
        true,
        (SELECT id FROM stores WHERE name = 'Chic Fashion Boutique'),
        (SELECT id FROM categories WHERE name = 'Shoes'),
        NOW(),
        NOW()
    ),
    (
        'Ankle Boots - Black',
        'Stylish Chelsea boots with elastic side panels. Durable leather construction with comfortable heel.',
        12999,
        7000,
        40,
        true,
        (SELECT id FROM stores WHERE name = 'Chic Fashion Boutique'),
        (SELECT id FROM categories WHERE name = 'Shoes'),
        NOW(),
        NOW()
    ),
    
    -- Bags & Accessories
    (
        'Leather Crossbody Bag',
        'Compact genuine leather bag with adjustable strap. Perfect size for essentials with multiple compartments.',
        9999,
        5000,
        45,
        true,
        (SELECT id FROM stores WHERE name = 'Chic Fashion Boutique'),
        (SELECT id FROM categories WHERE name = 'Bags & Accessories'),
        NOW(),
        NOW()
    ),
    (
        'Silk Scarf Collection',
        'Luxurious silk scarf with artistic print. Versatile accessory that adds elegance to any outfit.',
        3999,
        1800,
        100,
        true,
        (SELECT id FROM stores WHERE name = 'Chic Fashion Boutique'),
        (SELECT id FROM categories WHERE name = 'Bags & Accessories'),
        NOW(),
        NOW()
    );

-- ============================================================
-- PRODUCT IMAGES
-- ============================================================

-- iPhone 15 Pro Max
INSERT INTO product_images (product_id, image_url)
VALUES 
    ((SELECT id FROM products WHERE name = 'iPhone 15 Pro Max'), 'https://images.unsplash.com/photo-1695048133142-1a20484d2569?w=800'),
    ((SELECT id FROM products WHERE name = 'iPhone 15 Pro Max'), 'https://images.unsplash.com/photo-1695048133143-07975b8b0b0f?w=800');

-- Samsung Galaxy S24 Ultra
INSERT INTO product_images (product_id, image_url)
VALUES 
    ((SELECT id FROM products WHERE name = 'Samsung Galaxy S24 Ultra'), 'https://images.unsplash.com/photo-1610945415295-d9bbf067e59c?w=800'),
    ((SELECT id FROM products WHERE name = 'Samsung Galaxy S24 Ultra'), 'https://images.unsplash.com/photo-1598327105666-5b89351aff97?w=800');

-- MacBook Pro
INSERT INTO product_images (product_id, image_url)
VALUES 
    ((SELECT id FROM products WHERE name = 'MacBook Pro 16" M3 Max'), 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=800'),
    ((SELECT id FROM products WHERE name = 'MacBook Pro 16" M3 Max'), 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=800');

-- Sony Headphones
INSERT INTO product_images (product_id, image_url)
VALUES 
    ((SELECT id FROM products WHERE name = 'Sony WH-1000XM5'), 'https://images.unsplash.com/photo-1546435770-a3e426bf472b?w=800');

-- AirPods Pro
INSERT INTO product_images (product_id, image_url)
VALUES 
    ((SELECT id FROM products WHERE name = 'AirPods Pro (2nd Gen)'), 'https://images.unsplash.com/photo-1606841837239-c5a1a4a07af7?w=800');

-- Fashion items
INSERT INTO product_images (product_id, image_url)
VALUES 
    ((SELECT id FROM products WHERE name = 'Floral Summer Dress'), 'https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=800'),
    ((SELECT id FROM products WHERE name = 'White Leather Sneakers'), 'https://images.unsplash.com/photo-1549298916-b41d501d3772?w=800'),
    ((SELECT id FROM products WHERE name = 'Leather Crossbody Bag'), 'https://images.unsplash.com/photo-1590874103328-eac38a683ce7?w=800');

-- ============================================================
-- TAGS
-- ============================================================

INSERT INTO tags (name)
VALUES 
    ('Premium'),
    ('Best Seller'),
    ('New Arrival'),
    ('Sale'),
    ('Limited Edition'),
    ('Eco-Friendly'),
    ('5G'),
    ('Wireless'),
    ('Waterproof'),
    ('Fast Charging'),
    ('AI-Powered'),
    ('Professional'),
    ('Gaming'),
    ('Portable'),
    ('Trending'),
    ('Summer Collection'),
    ('Sustainable'),
    ('Handcrafted');

-- ============================================================
-- PRODUCT TAGS
-- ============================================================

-- Tag products appropriately
INSERT INTO product_tags (product_id, tag_id)
VALUES 
    -- iPhone
    ((SELECT id FROM products WHERE name = 'iPhone 15 Pro Max'), (SELECT id FROM tags WHERE name = 'Premium')),
    ((SELECT id FROM products WHERE name = 'iPhone 15 Pro Max'), (SELECT id FROM tags WHERE name = 'Best Seller')),
    ((SELECT id FROM products WHERE name = 'iPhone 15 Pro Max'), (SELECT id FROM tags WHERE name = '5G')),
    
    -- Samsung
    ((SELECT id FROM products WHERE name = 'Samsung Galaxy S24 Ultra'), (SELECT id FROM tags WHERE name = 'Premium')),
    ((SELECT id FROM products WHERE name = 'Samsung Galaxy S24 Ultra'), (SELECT id FROM tags WHERE name = 'AI-Powered')),
    ((SELECT id FROM products WHERE name = 'Samsung Galaxy S24 Ultra'), (SELECT id FROM tags WHERE name = '5G')),
    
    -- MacBook
    ((SELECT id FROM products WHERE name = 'MacBook Pro 16" M3 Max'), (SELECT id FROM tags WHERE name = 'Premium')),
    ((SELECT id FROM products WHERE name = 'MacBook Pro 16" M3 Max'), (SELECT id FROM tags WHERE name = 'Professional')),
    ((SELECT id FROM products WHERE name = 'MacBook Pro 16" M3 Max'), (SELECT id FROM tags WHERE name = 'Best Seller')),
    
    -- Sony Headphones
    ((SELECT id FROM products WHERE name = 'Sony WH-1000XM5'), (SELECT id FROM tags WHERE name = 'Best Seller')),
    ((SELECT id FROM products WHERE name = 'Sony WH-1000XM5'), (SELECT id FROM tags WHERE name = 'Wireless')),
    
    -- AirPods
    ((SELECT id FROM products WHERE name = 'AirPods Pro (2nd Gen)'), (SELECT id FROM tags WHERE name = 'Best Seller')),
    ((SELECT id FROM products WHERE name = 'AirPods Pro (2nd Gen)'), (SELECT id FROM tags WHERE name = 'Wireless')),
    ((SELECT id FROM products WHERE name = 'AirPods Pro (2nd Gen)'), (SELECT id FROM tags WHERE name = 'Waterproof')),
    
    -- Bose Speaker
    ((SELECT id FROM products WHERE name = 'Bose SoundLink Flex'), (SELECT id FROM tags WHERE name = 'Portable')),
    ((SELECT id FROM products WHERE name = 'Bose SoundLink Flex'), (SELECT id FROM tags WHERE name = 'Waterproof')),
    ((SELECT id FROM products WHERE name = 'Bose SoundLink Flex'), (SELECT id FROM tags WHERE name = 'Wireless')),
    
    -- Fashion items
    ((SELECT id FROM products WHERE name = 'Floral Summer Dress'), (SELECT id FROM tags WHERE name = 'Summer Collection')),
    ((SELECT id FROM products WHERE name = 'Floral Summer Dress'), (SELECT id FROM tags WHERE name = 'Trending')),
    ((SELECT id FROM products WHERE name = 'Premium Cotton T-Shirt'), (SELECT id FROM tags WHERE name = 'Eco-Friendly')),
    ((SELECT id FROM products WHERE name = 'Premium Cotton T-Shirt'), (SELECT id FROM tags WHERE name = 'Best Seller')),
    ((SELECT id FROM products WHERE name = 'Leather Crossbody Bag'), (SELECT id FROM tags WHERE name = 'Handcrafted')),
    ((SELECT id FROM products WHERE name = 'Leather Crossbody Bag'), (SELECT id FROM tags WHERE name = 'Premium'));

-- ============================================================
-- USER PREFERENCES
-- ============================================================

INSERT INTO user_preferences (user_id, theme, notifications_enabled, email_alerts, timezone, language, currency, created_at, updated_at)
VALUES 
    ((SELECT id FROM users WHERE username = 'john_doe'), 'dark', true, true, 'America/New_York', 'en', 'USD', NOW(), NOW()),
    ((SELECT id FROM users WHERE username = 'jane_smith'), 'light', true, false, 'America/Los_Angeles', 'en', 'USD', NOW(), NOW()),
    ((SELECT id FROM users WHERE username = 'mike_wilson'), 'dark', false, false, 'Europe/London', 'en', 'GBP', NOW(), NOW());

-- ============================================================
-- ORDERS (Customer Journey)
-- ============================================================

-- Order 1: John buys iPhone and AirPods from TechHub
INSERT INTO orders (
    order_number, 
    customer_id, 
    total_amount, 
    status, 
    shipping_address, 
    shipping_city, 
    shipping_postal_code, 
    shipping_country,
    created_at,
    updated_at,
    shipped_at,
    delivered_at
)
VALUES (
    'ORD-2025-001',
    (SELECT id FROM users WHERE username = 'john_doe'),
    144998,  -- iPhone + AirPods
    'delivered',
    '789 Customer Lane, Apt 4B',
    'New York',
    '10002',
    'USA',
    NOW() - INTERVAL '7 days',
    NOW() - INTERVAL '3 days',
    NOW() - INTERVAL '5 days',
    NOW() - INTERVAL '3 days'
);

-- Order 1 Products
INSERT INTO order_products (order_id, product_id, quantity, unit_price)
VALUES 
    (
        (SELECT id FROM orders WHERE order_number = 'ORD-2025-001'),
        (SELECT id FROM products WHERE name = 'iPhone 15 Pro Max'),
        1,
        119999
    ),
    (
        (SELECT id FROM orders WHERE order_number = 'ORD-2025-001'),
        (SELECT id FROM products WHERE name = 'AirPods Pro (2nd Gen)'),
        1,
        24999
    );

-- Order 2: Jane buys fashion items from Chic Fashion Boutique
INSERT INTO orders (
    order_number, 
    customer_id, 
    total_amount, 
    status, 
    shipping_address, 
    shipping_city, 
    shipping_postal_code, 
    shipping_country,
    created_at,
    updated_at,
    shipped_at
)
VALUES (
    'ORD-2025-002',
    (SELECT id FROM users WHERE username = 'jane_smith'),
    22997,  -- Dress + Sneakers + Bag
    'shipped',
    '456 Fashion Street',
    'Los Angeles',
    '90001',
    'USA',
    NOW() - INTERVAL '2 days',
    NOW() - INTERVAL '1 day',
    NOW() - INTERVAL '1 day'
);

-- Order 2 Products
INSERT INTO order_products (order_id, product_id, quantity, unit_price)
VALUES 
    (
        (SELECT id FROM orders WHERE order_number = 'ORD-2025-002'),
        (SELECT id FROM products WHERE name = 'Floral Summer Dress'),
        1,
        8999
    ),
    (
        (SELECT id FROM orders WHERE order_number = 'ORD-2025-002'),
        (SELECT id FROM products WHERE name = 'White Leather Sneakers'),
        1,
        8999
    ),
    (
        (SELECT id FROM orders WHERE order_number = 'ORD-2025-002'),
        (SELECT id FROM products WHERE name = 'Silk Scarf Collection'),
        1,
        3999
    );

-- Order 3: Mike buys laptop and accessories (pending)
INSERT INTO orders (
    order_number, 
    customer_id, 
    total_amount, 
    status, 
    shipping_address, 
    shipping_city, 
    shipping_postal_code, 
    shipping_country,
    created_at,
    updated_at
)
VALUES (
    'ORD-2025-003',
    (SELECT id FROM users WHERE username = 'mike_wilson'),
    365997,  -- MacBook + Sony Headphones + USB Hub
    'pending',
    '123 Tech Road',
    'London',
    'SW1A 1AA',
    'UK',
    NOW() - INTERVAL '1 hour',
    NOW() - INTERVAL '1 hour'
);

-- Order 3 Products
INSERT INTO order_products (order_id, product_id, quantity, unit_price)
VALUES 
    (
        (SELECT id FROM orders WHERE order_number = 'ORD-2025-003'),
        (SELECT id FROM products WHERE name = 'MacBook Pro 16" M3 Max'),
        1,
        349999
    ),
    (
        (SELECT id FROM orders WHERE order_number = 'ORD-2025-003'),
        (SELECT id FROM products WHERE name = 'Sony WH-1000XM5'),
        1,
        39999
    ),
    (
        (SELECT id FROM orders WHERE order_number = 'ORD-2025-003'),
        (SELECT id FROM products WHERE name = 'USB-C Hub 11-in-1'),
        2,
        5999
    );

-- Order 4: John buys more accessories
INSERT INTO orders (
    order_number, 
    customer_id, 
    total_amount, 
    status, 
    shipping_address, 
    shipping_city, 
    shipping_postal_code, 
    shipping_country,
    created_at,
    updated_at
)
VALUES (
    'ORD-2025-004',
    (SELECT id FROM users WHERE username = 'john_doe'),
    29997,  -- 3 power banks
    'confirmed',
    '789 Customer Lane, Apt 4B',
    'New York',
    '10002',
    'USA',
    NOW() - INTERVAL '3 hours',
    NOW() - INTERVAL '2 hours'
);

-- Order 4 Products
INSERT INTO order_products (order_id, product_id, quantity, unit_price)
VALUES 
    (
        (SELECT id FROM orders WHERE order_number = 'ORD-2025-004'),
        (SELECT id FROM products WHERE name = 'Anker PowerCore 20000mAh'),
        3,
        4999
    ),
    (
        (SELECT id FROM orders WHERE order_number = 'ORD-2025-004'),
        (SELECT id FROM products WHERE name = 'Logitech MX Master 3S'),
        1,
        9999
    );

-- ============================================================
-- CHAT MESSAGES
-- ============================================================

-- Customer inquiry about iPhone
INSERT INTO chat_messages (sender_id, store_id, message, created_at, updated_at)
VALUES 
    (
        (SELECT id FROM users WHERE username = 'john_doe'),
        (SELECT id FROM stores WHERE name = 'TechHub Electronics'),
        'Hi! Does the iPhone 15 Pro Max come with a charger?',
        NOW() - INTERVAL '10 days',
        NOW() - INTERVAL '10 days'
    ),
    (
        (SELECT id FROM users WHERE username = 'techstore_owner'),
        (SELECT id FROM stores WHERE name = 'TechHub Electronics'),
        'Hello! The iPhone 15 Pro Max comes with a USB-C to USB-C cable, but the power adapter is sold separately. We have great options available!',
        NOW() - INTERVAL '10 days' + INTERVAL '15 minutes',
        NOW() - INTERVAL '10 days' + INTERVAL '15 minutes'
    ),
    (
        (SELECT id FROM users WHERE username = 'john_doe'),
        (SELECT id FROM stores WHERE name = 'TechHub Electronics'),
        'Thanks! I will also need the AirPods Pro. Do you have them in stock?',
        NOW() - INTERVAL '10 days' + INTERVAL '30 minutes',
        NOW() - INTERVAL '10 days' + INTERVAL '30 minutes'
    ),
    (
        (SELECT id FROM users WHERE username = 'techstore_owner'),
        (SELECT id FROM stores WHERE name = 'TechHub Electronics'),
        'Yes, we have plenty in stock! Both products can ship together if you order today.',
        NOW() - INTERVAL '10 days' + INTERVAL '45 minutes',
        NOW() - INTERVAL '10 days' + INTERVAL '45 minutes'
    );

-- Fashion inquiry
INSERT INTO chat_messages (sender_id, store_id, message, created_at, updated_at)
VALUES 
    (
        (SELECT id FROM users WHERE username = 'jane_smith'),
        (SELECT id FROM stores WHERE name = 'Chic Fashion Boutique'),
        'What sizes do you have for the Floral Summer Dress?',
        NOW() - INTERVAL '3 days',
        NOW() - INTERVAL '3 days'
    ),
    (
        (SELECT id FROM users WHERE username = 'fashion_boutique'),
        (SELECT id FROM stores WHERE name = 'Chic Fashion Boutique'),
        'We have sizes XS through XL available! The dress runs true to size. Would you like me to check a specific size for you?',
        NOW() - INTERVAL '3 days' + INTERVAL '20 minutes',
        NOW() - INTERVAL '3 days' + INTERVAL '20 minutes'
    ),
    (
        (SELECT id FROM users WHERE username = 'jane_smith'),
        (SELECT id FROM stores WHERE name = 'Chic Fashion Boutique'),
        'Perfect! I need a medium. Also, can you recommend shoes to go with it?',
        NOW() - INTERVAL '3 days' + INTERVAL '35 minutes',
        NOW() - INTERVAL '3 days' + INTERVAL '35 minutes'
    ),
    (
        (SELECT id FROM users WHERE username = 'fashion_boutique'),
        (SELECT id FROM stores WHERE name = 'Chic Fashion Boutique'),
        'Great choice! Our White Leather Sneakers would be perfect for a casual look, or the Ankle Boots for a more elegant style. Both complement the dress beautifully!',
        NOW() - INTERVAL '3 days' + INTERVAL '50 minutes',
        NOW() - INTERVAL '3 days' + INTERVAL '50 minutes'
    );

-- ============================================================
-- SUMMARY
-- ============================================================

-- Display summary of created data
SELECT '✅ Database populated successfully!' as status;
SELECT 'Users created: ' || COUNT(*) as summary FROM users;
SELECT 'Stores created: ' || COUNT(*) as summary FROM stores;
SELECT 'Categories created: ' || COUNT(*) as summary FROM categories;
SELECT 'Products created: ' || COUNT(*) as summary FROM products;
SELECT 'Product images: ' || COUNT(*) as summary FROM product_images;
SELECT 'Tags created: ' || COUNT(*) as summary FROM tags;
SELECT 'Orders created: ' || COUNT(*) as summary FROM orders;
SELECT 'Chat messages: ' || COUNT(*) as summary FROM chat_messages;

-- Show store inventory
SELECT 
    s.name as store_name,
    COUNT(p.id) as total_products,
    SUM(p.stock) as total_inventory,
    SUM(p.price * p.stock) / 100.0 as inventory_value_usd
FROM stores s
LEFT JOIN products p ON p.store_id = s.id
GROUP BY s.id, s.name;
