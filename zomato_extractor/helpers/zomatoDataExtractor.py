import time
from multiprocessing.pool import ThreadPool
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

count = 0


def location_dict_builder(element):
    global count
    data: dict = {
        "city_id": count,
        "city_name": element.text,
        "city_page_url": element.get_attribute("href"),
        "localities": [],
    }
    count += 1
    return data


def concurrently_build_location_dict(arg):
    with ThreadPool() as pool:
        results = pool.map(location_dict_builder, arg)
    return results


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

        arg_list = [element for element in elements]
        results = concurrently_build_location_dict(arg_list)
        delivery_locations_and_urls_data.extend(results)

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
    driver.get(location["city_page_url"])  # Get the base url
    time.sleep(3)
    localities: list = []
    intial_localities: list = []
    temp_locality_data_store: list = []
    try:
        print("---------------------------------------")
        print("------ Searching the parent div ------")
        parent_div = driver.find_elements(
            By.CLASS_NAME,
            "sc-bke1zw-0",
        )
        print("------ Located parent div with Class Name ------")
        print("---------------------------------------")
        print("\n")

        if len(parent_div) == 3:  # Removing unnecessary elements
            parent_div.pop()
            parent_div.pop()
        elif len(parent_div) == 4:  # Removing unnecessary elements
            parent_div.pop()
            parent_div.pop()
            parent_div.remove(parent_div[0])

        print("---------------------------------------")
        print("------ Searching for localities ------")

        temp_localities = parent_div[0].find_elements(By.CLASS_NAME, "sc-bke1zw-1")
        for index, temp_locality in enumerate(temp_localities):
            try:
                temp_locality.find_element(By.TAG_NAME, "a")
                intial_localities.append(temp_locality)

            except NoSuchElementException:
                try:
                    wrapping_div = temp_locality.find_element(By.TAG_NAME, "div")
                    text_div = wrapping_div.find_element(By.TAG_NAME, "div").text
                    if text_div == "see more":
                        intial_localities.append(temp_locality)
                        break
                    else:
                        print(
                            "9th element is not see more so breaking to avoid potential issues!"
                        )
                        break

                except NoSuchElementException:
                    if not index < 8:
                        break
                    else:
                        continue

        if (
            len(intial_localities) == 9
        ):  # Checking if there are more localities than 9 if so clicking on the see more button and replacing the existing localities with all of the localities(which includes the initial 8 (9 - see more element)) else returing just the same localities

            see_more_button = intial_localities.pop()
            see_more_button.click()  # Clicking the see more button
            time.sleep(3)
            temp_local = parent_div[0].find_elements(By.CLASS_NAME, "sc-bke1zw-1")
            intial_localities = []
            for index, temp_loc in enumerate(temp_local):
                try:
                    temp_loc.find_element(By.TAG_NAME, "a")
                    intial_localities.append(temp_loc)

                except NoSuchElementException:
                    try:
                        wrapping_div = temp_loc.find_element(By.TAG_NAME, "div")
                        text_div = wrapping_div.find_element(By.TAG_NAME, "div").text
                        if text_div == "see less":
                            break
                        else:
                            print("Element unidentified")
                            continue
                    except NoSuchElementException:
                        continue

        for locality_element in intial_localities:

            base_anchor_element = locality_element.find_element(By.TAG_NAME, "a")
            locality_url = base_anchor_element.get_attribute("href")
            locality_name = base_anchor_element.find_element(By.TAG_NAME, "h5").text

            locality_data: dict[str, str, list, int] = {
                "locality_name": locality_name,
                "locality_url": locality_url,
                "locality_restaurants": [],
                "total_restaurant_in_locality": 0,
            }

            temp_locality_data_store.append(locality_data)

        for locality in temp_locality_data_store:
            locality_copy = locality
            driver.get(locality["locality_url"])

            current_screen_height = driver.execute_script(
                "return window.screen.height;"
            )
            index_count = 1
            web_scroll_wait_time = 3.5

            while (
                True
            ):  # Scrolling to load the full page in order to get all of the data
                driver.execute_script(
                    f"window.scrollTo(0, {current_screen_height}*{index_count});"
                )
                index_count += 1
                time.sleep(web_scroll_wait_time)
                scroll_height = driver.execute_script(
                    "return document.body.scrollHeight;"
                )
                if (
                    current_screen_height
                ) * index_count > scroll_height:  # Once we reach the end of the page we handle the data

                    try:
                        h1_element_text1 = driver.find_elements(By.TAG_NAME, "h1")[
                            1
                        ].text
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

                        locality_copy["total_restaurant_in_locality"] = len(restaurants)
                        locality_copy["locality_restaurants"].extend(restaurants)
                        localities.append(locality_copy)
                        break
                    except:
                        print(
                            "Some error occured while getting the restaurant data! \n"
                            "Or there are no restaurants in this locality!"
                        )
                        break

        location["localities"].extend(localities)
        driver.close()
        return location

    except Exception as err:
        print(f"Critical Error!")
