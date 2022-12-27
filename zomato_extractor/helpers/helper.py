# An helper function that return the data of delivery_cities_and_urls
# Path: newExtractor/helper.py
import json
import helpers.zomatoDataExtractor as zomatoDataExtractor


def get_data_of_delivery_cities() -> list:
    data: dict = zomatoDataExtractor.get_delivery_locations_and_its_urls()
    try:
        with open("app_state.json", "r") as f:
            app_state = json.load(f)
    except FileNotFoundError:
        app_state = {
            "last_city_id": 0,
            "LENGTH_OF_DELIVERY_CITIES": 0,
            "GLOBAL_STATE_QUEUE": [],
        }

    if app_state["last_city_id"]:

        temp_delivery_cities_and_urls = data
        del temp_delivery_cities_and_urls[: app_state["last_city_id"] + 1]
        data = temp_delivery_cities_and_urls
        length = len(data)
        app_state["LENGTH_OF_DELIVERY_CITIES"] = length
        with open("app_state.json", "w") as f:
            json.dump(app_state, f)
        return data
    else:
        length = len(data)
        app_state["LENGTH_OF_DELIVERY_CITIES"] = length
        with open("app_state.json", "w") as f:
            json.dump(app_state, f)

        return data
