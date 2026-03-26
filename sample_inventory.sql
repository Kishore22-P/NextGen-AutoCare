-- Sample Inventory Data with Product Images
-- Run this SQL in your PostgreSQL database to add sample products

-- Note: Replace the image URLs with the actual paths where you'll host these images
-- For now, using placeholder URLs that you can update

INSERT INTO inventory (name, category, brand, compatible_model, price, purchase_price, stock, is_for_sale, image_url) VALUES
('Bosch Oil Filter 3323', 'Filters', 'Bosch', 'Universal', 450, 300, 25, TRUE, 'https://example.com/images/oil_filter.png'),
('Castrol GTX Magnatec 5W-30', 'Fluids', 'Castrol', 'Universal', 2800, 2200, 15, TRUE, 'https://example.com/images/engine_oil.png'),
('Motul 7100 4T 10W-40', 'Fluids', 'Motul', 'Motorcycles', 1100, 850, 20, TRUE, 'https://example.com/images/motorcycle_oil.png'),
('Bosch Brake Pads Set', 'Brakes', 'Bosch', 'Universal', 1850, 1200, 18, TRUE, 'https://example.com/images/brake_pads.png'),
('Mann Air Filter C25114', 'Filters', 'Mann', 'Universal', 650, 400, 30, TRUE, 'https://example.com/images/air_filter.png'),
('NGK Spark Plugs (Set of 4)', 'Electrical', 'NGK', 'Universal', 1200, 800, 40, TRUE, 'https://via.placeholder.com/300x300/4f46e5/ffffff?text=Spark+Plugs'),
('Exide Car Battery 12V 65Ah', 'Electrical', 'Exide', 'Universal', 6500, 5000, 8, TRUE, 'https://via.placeholder.com/300x300/10b981/ffffff?text=Battery'),
('Prestone Coolant 1L', 'Fluids', 'Prestone', 'Universal', 450, 300, 25, TRUE, 'https://via.placeholder.com/300x300/fbbf24/ffffff?text=Coolant')
ON CONFLICT DO NOTHING;
