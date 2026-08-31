# Nutrition values — manual review list

The 25 most common classes (fried_chicken is not a Food-101 class; fried_rice listed instead), listed for manual verification against USDA FoodData Central. All 101 rows in data/nutrition_table.json carry needs_review: true until checked.

| Food | kcal/100g | Protein g | Carbs g | Fat g | Default portion g |
|---|---|---|---|---|---|
| pizza | 280 | 10.0 | 36.0 | 10.0 | 280 |
| hamburger | 220 | 18.0 | 18.0 | 10.0 | 220 |
| french_fries | 310 | 3.0 | 37.0 | 15.0 | 150 |
| caesar_salad | 120 | 5.0 | 8.0 | 8.0 | 200 |
| greek_salad | 100 | 5.0 | 8.0 | 5.5 | 200 |
| sushi | 140 | 6.0 | 20.0 | 3.0 | 150 |
| ramen | 120 | 4.0 | 18.0 | 3.0 | 300 |
| pad_thai | 160 | 8.0 | 18.0 | 7.0 | 250 |
| tacos | 200 | 12.0 | 20.0 | 8.0 | 150 |
| chicken_curry | 140 | 12.0 | 8.0 | 5.0 | 250 |
| chicken_wings | 220 | 18.0 | 2.0 | 16.0 | 150 |
| steak | 240 | 26.0 | 0.0 | 14.0 | 220 |
| spaghetti_bolognese | 140 | 10.0 | 16.0 | 3.0 | 250 |
| spaghetti_carbonara | 190 | 12.0 | 16.0 | 9.0 | 200 |
| lasagna | 170 | 12.0 | 15.0 | 7.0 | 200 |
| macaroni_and_cheese | 210 | 9.0 | 26.0 | 10.0 | 200 |
| omelette | 200 | 15.0 | 1.0 | 15.0 | 120 |
| pancakes | 220 | 6.0 | 32.0 | 8.0 | 150 |
| french_toast | 240 | 8.0 | 28.0 | 11.0 | 150 |
| ice_cream | 200 | 3.5 | 24.0 | 10.0 | 120 |
| cheesecake | 380 | 5.0 | 35.0 | 24.0 | 100 |
| chocolate_cake | 370 | 4.0 | 45.0 | 18.0 | 100 |
| donuts | 320 | 3.0 | 38.0 | 16.0 | 75 |
| hot_dog | 240 | 12.0 | 18.0 | 14.0 | 140 |
| Fried Rice | 180 | 6.0 | 22.0 | 8.0 | 250 |

## How to verify

Look up each dish on fdc.nal.usda.gov (FoodData Central), search for the prepared dish name, and compare the per-100g macronutrient values against what is listed here. When values match (within ±5%), set "needs_review": false for that entry in nutrition_table.json. Focus first on the highest-impact items: pizza, fried foods, and desserts are common sources of error. Complete the spot-check on 25 items to establish confidence, then extend to the full 101 as time permits.

## Tunisian additions (2026-08-30) — please verify these yourself

Added on request: 16 Tunisian dishes, selectable via the "Wrong food?" search (the vision model itself only knows the 101 Food-101 classes). Values are per-100g estimates for typical home preparations — **you know these dishes better than any database; correct them from experience or a Tunisian nutrition reference.**

| Food | kcal/100g | Protein g | Carbs g | Fat g | Default portion g |
|---|---|---|---|---|---|
| Couscous | 145 | 6.5 | 18 | 5.5 | 400 |
| Marga | 95 | 6.0 | 7 | 4.5 | 300 |
| Loubia | 110 | 6.5 | 13 | 3.5 | 300 |
| Mloukhiya | 160 | 8.0 | 6 | 12.0 | 250 |
| Ojja | 125 | 7.5 | 5 | 8.5 | 300 |
| Lablabi | 115 | 6.0 | 15 | 3.5 | 400 |
| Brik | 260 | 10.0 | 22 | 15.0 | 120 |
| Kafteji | 155 | 5.0 | 12 | 10.0 | 300 |
| Tajine Tunisien | 185 | 12.0 | 6 | 13.0 | 200 |
| Chorba | 60 | 4.0 | 7 | 1.8 | 350 |
| Salade Méchouia | 105 | 4.0 | 6 | 7.5 | 200 |
| Chakchouka | 100 | 5.5 | 6.5 | 6.0 | 300 |
| Merguez | 280 | 15.0 | 3 | 23.0 | 100 |
| Fricassé | 300 | 10.0 | 28 | 17.0 | 130 |
| Makroudh | 400 | 5.0 | 62 | 15.0 | 60 |
| Bambalouni | 330 | 6.0 | 48 | 12.5 | 90 |
