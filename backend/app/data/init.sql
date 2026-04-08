-- Restaurant Allergen Advisor database seed
-- Dishes with ingredients and allergen flags

INSERT INTO dish (name, ingredients, allergens, is_vegan, is_gluten_free, created_at, updated_at) VALUES
('Margherita Pizza', 'tomato, mozzarella, basil, wheat flour', 'milk, gluten', false, false, NOW(), NOW()),
('Spaghetti Carbonara', 'eggs, pecorino, pancetta, wheat pasta', 'eggs, gluten', false, false, NOW(), NOW()),
('Caesar Salad', 'romaine, parmesan, croutons, anchovy, Caesar dressing', 'milk, gluten, eggs', false, false, NOW(), NOW()),
('Grilled Salmon', 'salmon fillet, olive oil, lemon, herbs', '', false, true, NOW(), NOW()),
('Vegan Buddha Bowl', 'quinoa, chickpeas, avocado, kale, tahini', '', true, true, NOW(), NOW()),
('Pad Thai', 'rice noodles, shrimp, peanuts, bean sprouts, tamarind', 'nuts, soy', false, true, NOW(), NOW()),
('Berry Smoothie', 'strawberries, blueberries, yogurt, honey', 'milk', false, true, NOW(), NOW()),
('Gluten-Free Pancakes', 'rice flour, eggs, maple syrup', 'eggs', false, true, NOW(), NOW());
