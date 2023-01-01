import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By


def get_delivery_locations_and_its_urls() -> list[dict]:
    service = ChromeService(executable_path="chromedriver")
    driver = webdriver.Chrome(service=service)
    BASE_URL: str = "https://www.zomato.com/delivery-cities"
    driver.get(BASE_URL)  # Get the base url
    delivery_locations_and_urls_data: list[dict] = []

    try:  # Try to get the data

        print("------ Extracting Data ------")
        parent_div = driver.find_element(
            By.XPATH, '//*[@id="root"]/div/div[3]/div'  # XPATH of the Wrapper Div
        )

        elements = parent_div.find_elements(
            By.TAG_NAME, "a"
        )  # Get all the anchor tags containing the city name and its url

        print(
            "------ Extracted data! Creating location object and appending to list ------"
        )
        start = time.time()

        for index, element in enumerate(elements):
            data: dict = {
                "city_id": index,
                "city_name": element.text,
                "restaurants": [],
                "total_restaurant_in_locality": 0,
            }

            delivery_locations_and_urls_data.append(data)

        print(f"------ Time taken: {time.time() - start} seconds ------")
        print("------ Location object created and appended to list ------")
        print("\n")

        driver.quit()
        return delivery_locations_and_urls_data

    except:  # If any error occurs
        raise Exception("Error Occurred while getting data!")


def get_locality_and_restaurant_basic_info(location: dict):
    service = ChromeService(executable_path="chromedriver")
    driver = webdriver.Chrome(service=service)
    driver.get(
        f"https://www.zomato.com/{location['city_name'].lower()}/restaurants"
    )  # Get the city restaurants url

    try:
        print("------ Extracting Data ------")

        # Getting the restaurant data
        current_screen_height = driver.execute_script("return window.screen.height;")
        index_count = 1
        web_scroll_wait_time = 3.5

        while True:  # Scrolling to load the full page in order to get all of the data
            driver.execute_script(
                f"window.scrollTo(0, {current_screen_height}*{index_count});"
            )
            index_count += 1
            time.sleep(web_scroll_wait_time)
            scroll_height = driver.execute_script("return document.body.scrollHeight;")
            if (
                current_screen_height
            ) * index_count > scroll_height:  # Once we reach the end of the page we handle the data

                try:
                    h1_element_text1 = driver.find_elements(By.TAG_NAME, "h1")[1].text
                    base_divs = []

                    counter = 1
                    while True:
                        restaurant_row = driver.find_element(
                            By.XPATH,
                            f"//h1[contains(text(), '{h1_element_text1}')]/parent::*/following-sibling::div[{counter}]",
                        )
                        counter += 1

                        if (
                            restaurant_row.text == "End of search results"
                        ):  # Checking if we have reached the end of the search results
                            break
                        else:
                            base_divs.append(restaurant_row)

                    # Base div holds three restaurant card at a time
                    # Getting restaurant urls, names and image
                    restaurants = []
                    for item in base_divs:
                        restaurant_images = []
                        restaurants_urls = []
                        restaurant_list = []

                        temp_restaurants_urls = item.find_elements(
                            By.TAG_NAME, "a"
                        )  # Getting the urls of the restaurants (it contains duplicates)

                        restaurant_names = item.find_elements(
                            By.TAG_NAME, "h4"
                        )  # Getting the names of the restaurants

                        # Removing duplicates from restaurant_urls
                        for index, temp_url in enumerate(temp_restaurants_urls):
                            if not index % 2 == 0:
                                continue
                            else:
                                restaurants_urls.append(temp_url)

                        # Getting restaurant image (with just the first url)
                        for url in restaurants_urls:
                            img = url.find_element(By.TAG_NAME, "img")
                            restaurant_images.append(img.get_attribute("src"))

                        for loc, value in enumerate(restaurants_urls):
                            try:
                                restaurant = {
                                    "name": restaurant_names[loc].text,
                                    "url": value.get_attribute("href"),
                                    "image": restaurant_images[loc],
                                }
                                restaurant_list.append(restaurant)
                            except Exception as e:
                                print(f"{e}.")
                                break

                        restaurants.extend(restaurant_list)

                    location["total_restaurant_in_locality"] = len(restaurants)
                    location["restaurants"].extend(restaurants)
                    print("------ Extracted data! ------")
                    break
                except:
                    print(
                        "Some error occured while getting the restaurant data! \n"
                        "Or there are no restaurants in this locality!"
                    )
                    break

        driver.close()
        return location

    except Exception as err:
        print(f"Critical Error!")
