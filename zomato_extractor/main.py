# Description: This file contains the code for concurrency
import json
import logging
import threading
import multiprocessing
import helpers.helper as helper
from helpers.scheduler import Scheduler
import helpers.zomatoDataExtractor as zomatoDataExtractor


logging.basicConfig(
    level=logging.NOTSET,
    format="{asctime} {levelname} {message}",
    style="{",
    filename="%slog" % __file__[:-2],
    filemode="w",
)
lock = multiprocessing.Lock()


class DownloadProcess(multiprocessing.Process):
    def __init__(self, queue, global_state):
        multiprocessing.Process.__init__(self)
        self.queue = queue
        self.lock = lock
        self.global_state = global_state

    def run(self):
        while True:
            try:
                print(f"Extracting Data...")
                logging.info("Extracting Data...")
                delivery_city = self.queue.get()

                with open("app_state.json", "r") as f:
                    data = json.load(f)

                if len(data["GLOBAL_STATE_QUEUE"]) != 0:
                    if delivery_city["city_id"] not in [
                        id for id in data["GLOBAL_STATE_QUEUE"]
                    ]:

                        info = (
                            zomatoDataExtractor.get_locality_and_restaurant_basic_info(
                                delivery_city
                            )
                        )
                        print(f"Extracted Data...")
                        logging.info("Extracted Data...")
                        logging.info("Processing Data...")
                        self.process_data(info)
                        logging.info("Processed Data...")
                        logging.info("Updating Global State...")
                        self.update_global_state(delivery_city)
                        logging.info("Updated Global State...")
                    else:
                        print(f"Data already exists for {delivery_city['city_id']}")
                        logging.info(
                            f"Data already exists for {delivery_city['city_id']}"
                        )
                        with open(self.global_state, "r") as f:
                            app_state = json.load(f)
                        app_state["LENGTH_OF_DELIVERY_CITIES"] -= 1
                        logging.info("Updating Global State...")
                        self.update_global_state(delivery_city)
                        logging.info("Updated Global State...")
                        continue
                else:
                    info = zomatoDataExtractor.get_locality_and_restaurant_basic_info(
                        delivery_city
                    )
                    print(f"Extracted Data...")
                    logging.info("Extracted Data...")
                    logging.info("Processing Data...")
                    self.process_data(info)
                    logging.info("Processed Data...")
                    logging.info("Updating Global State...")
                    self.update_global_state(delivery_city)
                    logging.info("Updated Global State...")
            finally:
                self.queue.task_done()

    def process_data(self, data):
        with open("zomatodata.json", "r") as f:
            data_list = json.load(f)
            data_list["data"].append(data)

        with open("zomatodata.json", "w") as f:
            json.dump(data_list, f)

    def update_global_state(self, data):
        self.lock.acquire()

        try:
            with open(self.global_state, "r") as f:
                app_state = json.load(f)

            if data["city_id"] == app_state["city_id"] + 1:
                app_state["last_city_id"] = data["city_id"]
                app_state["LENGTH_OF_DELIVERY_CITIES"] -= 1
                with open(self.global_state, "w") as f:
                    json.dump(app_state, f)

            else:
                app_state["GLOBAL_STATE_QUEUE"].append(data["city_id"])
                with open(self.global_state, "w") as f:
                    json.dump(app_state, f)

        finally:
            self.lock.release()


def main(data):
    delivery_cities_and_urls = data
    logging.info("Loading the data if exist else building new json file")

    logging.info("Starting the download process...")
    queue = multiprocessing.JoinableQueue()
    for _ in range(3):
        process = DownloadProcess(queue, "app_state.json")
        process.daemon = True
        process.start()

    for city in delivery_cities_and_urls:
        queue.put(city)

    queue.join()


if __name__ == "__main__":
    logging.info("Starting the program...")
    logging.info(
        "Visisting 'https://www.zomato.com/delivery-cities' and extracticting basic location details"
    )
    data = helper.get_data_of_delivery_cities()
    logging.info("Extracted basic location details")
    logging.info("Starting the concurrent download process...")
    logging.info("Starting the state manager...")

    try:
        with open("zomatodata.json", "r") as f:
            json.load(f)
    except FileNotFoundError:
        with open("zomatodata.json", "w") as f:
            json.dump({"data": []}, f)

    p1 = threading.Thread(
        target=Scheduler().schedule,
        args=(
            10,
            "No more cities remaining!! Breaking...",
        ),
        daemon=True,
    )
    p1.start()
    logging.info("Starting the main function...")
    p2 = threading.Thread(target=main, args=(data,), daemon=True)
    p2.start()
    p1.join()
    p2.join()
