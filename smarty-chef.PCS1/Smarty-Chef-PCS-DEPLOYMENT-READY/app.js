
// Frontend logic for Smart Recipe Generator
const generateBtn = document.getElementById("generateBtn");
const saveAllBtn = document.getElementById("saveAllBtn");
const recipesDiv = document.getElementById("recipes");

generateBtn.addEventListener("click", generateRecipe);
saveAllBtn.addEventListener("click", saveAllRecipes);

async function generateRecipe(){
  const ingredientsRaw = document.getElementById("ingredients").value.trim();
  if(!ingredientsRaw){
    alert("Please enter at least one ingredient.");
    return;
  }
  const ingredients = ingredientsRaw.split(",").map(s=>s.trim()).filter(Boolean);
  const diet = document.getElementById("diet").value;

  recipesDiv.innerHTML = `<div class="card">Generating recipes... 🍳</div>`;

  try{
    const res = await fetch("/generate-recipe", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({ ingredients, dietaryPreference: diet })
    });
    const data = await res.json();
    if(!data || !data.recipes) {
      recipesDiv.innerHTML = `<div class="card">No recipes returned. Try different ingredients.</div>`;
      console.log("AI response:", data);
      return;
    }
    displayRecipes(data.recipes);
  }catch(err){
    console.error(err);
    recipesDiv.innerHTML = `<div class="card">Error generating recipes. Check console for details.</div>`;
  }
}

function displayRecipes(recipes){
  recipesDiv.innerHTML = "";
  recipes.forEach((r, idx) => {
    const card = document.createElement("div");
    card.className = "recipe-card card";
    card.innerHTML = `
      <h2>${r.title || "Untitled Recipe"}</h2>
      <div class="meta">${r.dietary_labels ? r.dietary_labels.join(" • ") : ""} • ${r.time || ""}</div>
      <p>${r.description || ""}</p>
      <strong>Ingredients</strong>
      <ul>${(r.ingredients||[]).map(i=>`<li>${i}</li>`).join("")}</ul>
      <strong>Instructions</strong>
      <ol>${(r.instructions||[]).map(s=>`<li>${s}</li>`).join("")}</ol>
      <div style="display:flex;gap:8px;margin-top:8px">
        <button class="save-btn" data-idx="${idx}">Save</button>
      </div>
    `;
    recipesDiv.appendChild(card);
  });

  // attach save buttons
  document.querySelectorAll(".save-btn").forEach(btn=>{
    btn.addEventListener("click", (e)=>{
      const i = Number(e.target.dataset.idx);
      saveRecipe(recipes[i]);
    });
  });
}

function saveRecipe(recipe){
  const saved = JSON.parse(localStorage.getItem("saved_recipes")||"[]");
  saved.push(recipe);
  localStorage.setItem("saved_recipes", JSON.stringify(saved));
  alert("Recipe saved for offline use!");
}

function saveAllRecipes(){
  const cards = document.querySelectorAll(".recipe-card");
  if(cards.length===0){ alert("No recipes to save."); return; }
  const saved = JSON.parse(localStorage.getItem("saved_recipes")||"[]");
  // gather from displayed cards by reading DOM (simpler)
  const recipes = [];
  cards.forEach(c=>{
    const title = c.querySelector("h2").innerText;
    const description = c.querySelector("p").innerText;
    const ingredients = Array.from(c.querySelectorAll("ul li")).map(li=>li.innerText);
    const instructions = Array.from(c.querySelectorAll("ol li")).map(li=>li.innerText);
    recipes.push({ title, description, ingredients, instructions });
  });
  const merged = saved.concat(recipes);
  localStorage.setItem("saved_recipes", JSON.stringify(merged));
  alert("All recipes saved locally!");
}

// register service worker
if('serviceWorker' in navigator){
  navigator.serviceWorker.register('/service-worker.js').then(()=>console.log('SW registered'));
}
