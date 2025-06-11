
const recipeManager = document.getElementById('recipe-viewer');

function getRecipe(id){
    recipeManager.src = `${window.location.origin}/recipe/view/${id}`;
}



