# Create the perfect deployment-ready structure with all files properly configured
import zipfile
import os

# Create enhanced deployment ready files
enhanced_package_json = '''{
  "name": "smarty-chef-pcs",
  "version": "2.0.0",
  "description": "Smart Recipe Generator with Spoonacular API - Made by Clement",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "node server.js",
    "test": "echo \\"No test specified\\" && exit 0"
  },
  "keywords": [
    "recipe", "cooking", "spoonacular", "ingredients", "ai", "pwa"
  ],
  "author": "Clement",
  "license": "MIT",
  "dependencies": {
    "body-parser": "^1.20.2",
    "cors": "^2.8.5",
    "express": "^4.18.2",
    "node-fetch": "^2.7.0"
  },
  "engines": {
    "node": ">=14.0.0"
  }
}'''

# Enhanced server.js with better error handling
enhanced_server = '''const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const path = require('path');

const app = express();

// Middleware
app.use(cors());
app.use(bodyParser.json());
app.use(express.static(path.join(__dirname)));

const PORT = process.env.PORT || 3000;
const SPOONACULAR_API_KEY = process.env.SPOONACULAR_API_KEY || '7800762921d34589b4b49897b5c09778';

console.log('🍳 Starting Smarty-Chef.PCS Server...');
console.log('🗝️ API Key:', SPOONACULAR_API_KEY ? '✅ Configured' : '❌ Missing');

// Helper to transform Spoonacular recipe data
function transformRecipe(recipe) {
  const ingredients = recipe.extendedIngredients 
    ? recipe.extendedIngredients.map(ingredient => ingredient.original)
    : [];

  let instructions = [];
  if (recipe.analyzedInstructions && recipe.analyzedInstructions.length > 0) {
    instructions = recipe.analyzedInstructions[0].steps.map(step => step.step);
  } else if (recipe.instructions) {
    instructions = recipe.instructions
      .split(/[\\r\\n]+/)
      .filter(instruction => instruction.trim().length > 0)
      .map(instruction => instruction.trim());
  }

  const description = recipe.summary 
    ? recipe.summary.replace(/<[^>]*>/g, '').substring(0, 200) + '...'
    : 'A delicious recipe made with your selected ingredients.';

  return {
    title: recipe.title || "Delicious Recipe",
    description: description,
    ingredients: ingredients,
    instructions: instructions,
    time: recipe.readyInMinutes ? `${recipe.readyInMinutes} minutes` : '',
    dietary_labels: [
      recipe.vegetarian ? 'Vegetarian' : null,
      recipe.vegan ? 'Vegan' : null,
      recipe.glutenFree ? 'Gluten-Free' : null,
      recipe.dairyFree ? 'Dairy-Free' : null,
      recipe.veryHealthy ? 'Healthy' : null,
      ...(recipe.dishTypes || []),
      ...(recipe.cuisines || [])
    ].filter(Boolean),
    category: recipe.dishTypes ? recipe.dishTypes[0] : 'Main Course',
    servings: recipe.servings ? recipe.servings.toString() : '',
    image: recipe.image || '',
    sourceUrl: recipe.sourceUrl || '',
    spoonacularScore: recipe.spoonacularScore || 0,
    healthScore: recipe.healthScore || 0
  };
}

// Fallback recipe generator
function createFallbackRecipe(ingredients, dietaryPreference) {
  const mainIngredient = ingredients[0] || 'ingredients';
  const cuisineHint = dietaryPreference === 'indian' ? 'Indian-Style ' : '';
  
  return {
    title: `${cuisineHint}${mainIngredient.charAt(0).toUpperCase() + mainIngredient.slice(1)} Delight`,
    description: `A delicious homemade ${cuisineHint.toLowerCase()}dish featuring ${ingredients.slice(0, 3).join(', ')} and more fresh ingredients.`,
    ingredients: [
      ...ingredients.map(ing => `1-2 portions ${ing}`),
      "Salt and pepper to taste",
      "2 tbsp cooking oil",
      "Fresh herbs (optional)",
      "Spices as needed"
    ],
    instructions: [
      "Wash and prepare all your fresh ingredients",
      `Heat oil in a large pan or pot over medium heat`,
      `Add ${ingredients[0]} and cook until lightly golden`,
      ingredients.length > 1 ? `Add ${ingredients.slice(1).join(', ')} and cook for 5-7 minutes` : "Continue cooking for 5-7 minutes",
      "Season with salt, pepper, and your favorite spices",
      dietaryPreference === 'indian' ? "Add Indian spices like turmeric, cumin, or garam masala" : "Add herbs and spices to taste",
      "Cook until all ingredients are tender and well combined",
      "Taste and adjust seasoning as needed",
      "Serve hot and enjoy your homemade creation!"
    ],
    time: "25-30 minutes",
    dietary_labels: dietaryPreference ? [dietaryPreference] : ["Homemade"],
    category: "Main Course",
    servings: "2-4",
    image: '',
    sourceUrl: '',
    spoonacularScore: 0,
    healthScore: 0
  };
}

// Enhanced /generate-recipe endpoint
app.post('/generate-recipe', async (req, res) => {
  try {
    const { ingredients = [], dietaryPreference = '', allergies = '' } = req.body;
    
    if (!ingredients || ingredients.length === 0) {
      return res.status(400).json({ 
        error: 'Please provide at least one ingredient', 
        recipes: [] 
      });
    }

    console.log('🔍 Searching recipes for ingredients:', ingredients);
    console.log('🥗 Dietary preference:', dietaryPreference);
    console.log('⚠️ Allergies:', allergies);

    // Import fetch dynamically to handle different Node.js versions
    const fetch = (await import('node-fetch')).default;

    const ingredientsString = ingredients.join(',+');
    const searchUrl = `https://api.spoonacular.com/recipes/findByIngredients?ingredients=${encodeURIComponent(ingredientsString)}&number=8&ranking=2&ignorePantry=true&apiKey=${SPOONACULAR_API_KEY}`;
    
    console.log('🌐 Calling Spoonacular API...');
    
    const searchResponse = await fetch(searchUrl);
    if (!searchResponse.ok) {
      throw new Error(`Spoonacular search failed: ${searchResponse.status}`);
    }

    const foundRecipes = await searchResponse.json();
    console.log(`📋 Found ${foundRecipes.length} recipe matches`);

    if (!foundRecipes || foundRecipes.length === 0) {
      const fallbackRecipe = createFallbackRecipe(ingredients, dietaryPreference);
      return res.json({ 
        recipes: [fallbackRecipe],
        apiSource: 'Fallback',
        message: 'No matches found, showing custom recipe'
      });
    }

    // Get detailed information for recipes
    const detailedRecipes = await Promise.all(
      foundRecipes.slice(0, 5).map(async (recipe) => {
        try {
          const detailUrl = `https://api.spoonacular.com/recipes/${recipe.id}/information?includeNutrition=false&apiKey=${SPOONACULAR_API_KEY}`;
          const detailResponse = await fetch(detailUrl);
          
          if (!detailResponse.ok) {
            console.warn(`Failed to get details for recipe ${recipe.id}`);
            return null;
          }
          
          const detailData = await detailResponse.json();
          return transformRecipe(detailData);
        } catch (error) {
          console.error(`Error fetching recipe ${recipe.id}:`, error.message);
          return null;
        }
      })
    );

    let validRecipes = detailedRecipes.filter(recipe => recipe !== null);

    // Apply dietary preferences filtering
    if (dietaryPreference && validRecipes.length > 0) {
      const filteredByDiet = validRecipes.filter(recipe => {
        const labels = recipe.dietary_labels.map(label => label.toLowerCase());
        const preference = dietaryPreference.toLowerCase().replace('-', ' ');
        return labels.some(label => label.includes(preference));
      });
      
      if (filteredByDiet.length > 0) {
        validRecipes = filteredByDiet;
      }
    }

    // Filter out recipes with allergens
    if (allergies && validRecipes.length > 0) {
      const allergensList = allergies.split(',').map(a => a.trim().toLowerCase());
      validRecipes = validRecipes.filter(recipe => {
        const recipeText = (recipe.title + ' ' + recipe.ingredients.join(' ')).toLowerCase();
        return !allergensList.some(allergen => recipeText.includes(allergen));
      });
    }

    // Ensure we have at least one recipe
    if (validRecipes.length === 0) {
      const fallbackRecipe = createFallbackRecipe(ingredients, dietaryPreference);
      validRecipes = [fallbackRecipe];
    }

    console.log(`✅ Returning ${validRecipes.length} recipes`);

    res.json({ 
      recipes: validRecipes,
      apiSource: 'Spoonacular',
      totalFound: foundRecipes.length,
      afterFiltering: validRecipes.length
    });

  } catch (error) {
    console.error('❌ Recipe generation error:', error.message);
    
    const { ingredients = [], dietaryPreference = '' } = req.body;
    const fallbackRecipe = createFallbackRecipe(ingredients, dietaryPreference);
    
    res.json({
      recipes: [fallbackRecipe],
      apiSource: 'Fallback',
      error: error.message,
      message: 'API unavailable, showing demo recipe'
    });
  }
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ 
    status: "✅ Smarty-Chef.PCS Server Running!", 
    timestamp: new Date().toISOString(),
    apiKey: SPOONACULAR_API_KEY ? "✅ Configured" : "❌ Missing",
    version: "2.0.0"
  });
});

// API status endpoint
app.get('/api-status', async (req, res) => {
  try {
    const fetch = (await import('node-fetch')).default;
    const testUrl = `https://api.spoonacular.com/recipes/random?number=1&apiKey=${SPOONACULAR_API_KEY}`;
    const response = await fetch(testUrl);
    
    res.json({
      spoonacularAPI: response.ok ? "✅ Connected" : "❌ Failed",
      statusCode: response.status,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.json({
      spoonacularAPI: "❌ Connection Failed",
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Serve static files
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({ 
    error: 'Endpoint not found',
    availableEndpoints: [
      'GET / - Main application',
      'POST /generate-recipe - Generate recipes',
      'GET /health - Server health check',
      'GET /api-status - API connection status'
    ]
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 Server started on port ${PORT}`);
  console.log(`📱 Web App: http://localhost:${PORT}`);
  console.log(`🔧 Health: http://localhost:${PORT}/health`);
  console.log(`🍳 Made with ❤️ by Clement`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('🔄 Server shutting down...');
  process.exit(0);
});

process.on('SIGINT', () => {
  console.log('🔄 Server shutting down...');
  process.exit(0);
});'''

# Create README for deployment
deployment_readme = '''# 🍳 Smarty-Chef.PCS - Ready for Deployment

## 🚀 Render Deployment Instructions

### 1. Upload to GitHub
- Extract all files to a folder
- Push to your GitHub repository

### 2. Create Render Web Service
- Connect your GitHub repo
- **Environment**: Node
- **Build Command**: `npm install`
- **Start Command**: `npm start`
- **Root Directory**: (leave empty - files are in root)

### 3. Set Environment Variables
Add these in Render dashboard:

| Variable Name | Value |
|---------------|-------|
| `SPOONACULAR_API_KEY` | `7800762921d34589b4b49897b5c09778` |
| `PORT` | `10000` |

### 4. Deploy
- Click "Create Web Service"
- Render will build and deploy automatically
- Your app will be live with Spoonacular API integration

## 📁 Project Structure
```
smarty-chef-pcs/
├── package.json       # Dependencies and scripts
├── server.js          # Express backend with Spoonacular API
├── index.html         # Main frontend
├── style.css          # Styles
├── app.js             # Frontend JavaScript
├── manifest.json      # PWA manifest
├── service-worker.js  # PWA service worker
└── assets/            # Images and icons
```

## ✅ What's Included
- ✅ Spoonacular API integration
- ✅ Visual ingredient selection
- ✅ Modern responsive UI
- ✅ Login/signup forms
- ✅ Privacy policy & about pages
- ✅ PWA support
- ✅ Error handling and fallbacks
- ✅ Made by Clement branding

## 🔧 Local Development
```bash
npm install
npm start
# Open http://localhost:3000
```

## 🌟 Features
- 100+ ingredients with visual selection
- Real-time recipe generation
- Dietary preference filtering
- Allergy awareness
- Recipe saving
- Mobile responsive
- Offline support

Made with ❤️ by Clement
'''

# Create .gitignore
gitignore_content = '''# Dependencies
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Environment variables (keep API keys secure)
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Runtime data
pids
*.pid
*.seed
*.pid.lock

# Coverage directory used by tools like istanbul
coverage/

# Optional npm cache directory
.npm

# Optional REPL history
.node_repl_history

# Output of 'npm pack'
*.tgz

# Yarn Integrity file
.yarn-integrity

# Mac
.DS_Store

# Windows
Thumbs.db

# Logs
logs
*.log

# Build directories
build/
dist/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~'''

# Save enhanced files
with open('package.json', 'w', encoding='utf-8') as f:
    f.write(enhanced_package_json)

with open('server.js', 'w', encoding='utf-8') as f:
    f.write(enhanced_server)

with open('README.md', 'w', encoding='utf-8') as f:
    f.write(deployment_readme)

with open('.gitignore', 'w', encoding='utf-8') as f:
    f.write(gitignore_content)

# Create deployment-ready ZIP
files_to_zip = [
    'package.json',
    'server.js', 
    'index.html',
    'style.css',
    'app.js',
    'manifest.json',
    'service-worker.js',
    'README.md',
    '.gitignore',
    'chef-PCS.jpg',
    'icon-192.jpg',
    'icon-512.jpg',
    'image.jpeg'
]

zip_filename = 'Smarty-Chef-PCS-DEPLOYMENT-READY.zip'

with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for filename in files_to_zip:
        if os.path.exists(filename):
            zipf.write(filename)
            print(f"✅ Added: {filename}")

print(f"\n🎉 DEPLOYMENT-READY PACKAGE CREATED!")
print(f"📦 File: {zip_filename}")
print(f"\n✅ READY FOR RENDER:")
print("- All files in root directory")
print("- Enhanced server.js with better error handling")
print("- Proper package.json with correct scripts")
print("- README with deployment instructions")
print("- .gitignore for security")
print("- Full Spoonacular API integration")

zip_filename