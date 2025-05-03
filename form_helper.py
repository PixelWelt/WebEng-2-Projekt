from fastapi import UploadFile
import uuid
from PIL import Image
from pathlib import Path


def explode_ingredient_list(data: dict) -> list:
	"""Extracts a list of ingredients from form data.

	Args:
	    data (dict): The form data containing ingredient names and amounts.

	Returns:
	    list: A list of dictionaries, each containing the name and amount of an ingredient.
	"""
	ingredients = []
	index = 0
	while f"ingredientName[{index}]" in data and f"ingredientAmount[{index}]" in data:
		ingredients.append({
			"name": data[f"ingredientName[{index}]"],
			"amount": data[f"ingredientAmount[{index}]"]
		})
		index += 1
	return ingredients

def get_tags(data: dict, key: str) -> list:
	"""Explodes a form list into a list of dictionaries.

	Args:
		data (dict): The form data.
		key (str): The key to explode.

	Returns:
		list: A list of dictionaries containing the exploded data.
	"""
	exploded_list = []
	for i in range(0, 10):
		print( f"{key}[{i}]")
		if f"{key}[{i}]" in data:
			exploded_list.append(data[f"{key}[{i}]"])
	return exploded_list

def upload_recipe_img(img_path: UploadFile, recipe_name: str) -> str | None:
	"""Uploads a recipe image to the server.

	Args:
		img_path (UploadFile): The image file to upload.
		recipe_name (str): The name of the recipe.

	Returns:
		str: The file path of the uploaded image.
	"""
	try:
		img_path.filename = img_path.filename.replace(" ", "_")
		file_location = f"static/recipe_images/{recipe_name}-{uuid.uuid4()}-{img_path.filename}"
		if not img_path.content_type.startswith("image/"):
			return None
		if img_path.size > 10 * 1024 * 1024:  # Check if file size exceeds 10MB
			return None
		with open(file_location, "wb+") as file_object:
			file_object.write(img_path.file.read())
		file_location = optimize_image(file_location)
		return file_location
	except Exception as e:
		print(f"Error uploading image: {e}")
		return None

def optimize_image(image_path: str) -> str:
	"""Optimizes an image for web use.

	Args:
		image_path (str): The path to the image file.

	Returns:
		str: The path to the optimized image.
	"""
	image = Image.open(image_path)
	image = image.convert("RGB")

	image_path = f"static/recipe_images/{Path(image_path).stem}.webp"

	image.save(image_path, 'webp', optimize=True, quality=10)
	return image_path