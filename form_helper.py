
def explode_ingredient_list(data: dict) -> list:
	ingredients = []
	index = 0
	while f"ingredientName[{index}]" in data and f"ingredientAmount[{index}]" in data:
		ingredients.append({
			"name": data[f"ingredientName[{index}]"],
			"amount": data[f"ingredientAmount[{index}]"]
		})
		index += 1
	return ingredients

def explode_form_list(data: dict, key: str) -> list:
	"""Explodes a form list into a list of dictionaries.

	Args:
		data (dict): The form data.
		key (str): The key to explode.

	Returns:
		list: A list of dictionaries containing the exploded data.
	"""
	exploded_list = []
	index = 0
	while f"{key}[{index}]" in data:
		exploded_list.append(data[f"{key}[{index}]"])
		index += 1
	return exploded_list