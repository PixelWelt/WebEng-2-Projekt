
async function getRecipe(recipeId) {
    const response = await fetch(`/api/recipe/get-partial/${recipeId}`);
    if (response.ok) {
        document.getElementById('recipe-viewer').innerHTML = await response.text();
    } else {
        document.getElementById('recipe-viewer').innerHTML = "Fehler beim Laden des Rezepts.";
    }
}

async function deleteRecipe(recipeId) {
    const response = await fetch(`/api/recipe/delete/${recipeId}`, {
        method: 'DELETE'
    });
    if (response.ok) {
        document.getElementById('recipe-viewer').innerHTML = "Rezept erfolgreich gelöscht. Seite wird neu geladen...";
        setTimeout(() => {
            window.location.reload();
        }, 2000);
    } else {
        document.getElementById('recipe-viewer').innerHTML = "Fehler beim Löschen des Rezepts.";
    }
}

