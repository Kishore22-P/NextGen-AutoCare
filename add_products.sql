-- Sample Inventory Data with Product Images
-- Run this to add sample products to your database

INSERT INTO inventory (name, category, brand, compatible_model, price, purchase_price, stock, is_for_sale, image_url) VALUES
('Bosch Oil Filter 3323', 'Filters', 'Bosch', 'Universal', 450, 300, 25, TRUE, '/static/images/products/oil_filter.png'),
('Castrol GTX Magnatec 5W-30', 'Fluids', 'Castrol', 'Universal', 2800, 2200, 15, TRUE, '/static/images/products/engine_oil.png'),
('Motul 7100 4T 10W-40', 'Fluids', 'Motul', 'Motorcycles', 1100, 850, 20, TRUE, '/static/images/products/motorcycle_oil.png'),
('Bosch Brake Pads Set', 'Brakes', 'Bosch', 'Universal', 1850, 1200, 18, TRUE, '/static/images/products/brake_pads.png'),
('Mann Air Filter C25114', 'Filters', 'Mann', 'Universal', 650, 400, 30, TRUE, '/static/images/products/air_filter.png'),
('NGK Spark Plugs (Set of 4)', 'Electrical', 'NGK', 'Universal', 1200, 800, 40, TRUE, 'https://images.unsplash.com/photo-1486262715619-67b85e0b08d3?w=400'),
('Exide Car Battery 12V 65Ah', 'Electrical', 'Exide', 'Universal', 6500, 5000, 8, TRUE, 'https://images.unsplash.com/photo-1593941707882-a5bba14938c7?w=400'),
('Prestone Coolant 1L', 'Fluids', 'Prestone', 'Universal', 450, 300, 25, TRUE, 'https://images.unsplash.com/photo-1621939514649-280e2ee25f60?w=400')
ON CONFLICT DO NOTHING;
