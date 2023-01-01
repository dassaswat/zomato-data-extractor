# Description: This file contains the code for concurrency
import json
import logging
import threading
import multiprocessing
import helpers.helper as helper
from helpers.scheduler import Scheduler
import helpers.zomatoDataExtractor as zomatoDataExtractor


lock = multiprocessing.Lock()


class DownloadProcess(multiprocessing.Process):
    def __init__(self, queue):
        multiprocessing.Process.__init__(self)
        self.queue = queue
        self.lock = lock

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

                        self.process_data(info)

                        self.update_global_state(info)

                    else:
                        print(f"Data already exists for {info['city_id']}")
                        logging.info(f"Data already exists for {info['city_id']}")
                        with open("app_state.json", "r") as f:
                            app_state = json.load(f)
                        app_state["LENGTH_OF_DELIVERY_CITIES"] -= 1

                        self.update_global_state(delivery_city)

                        continue
                else:
                    info = zomatoDataExtractor.get_locality_and_restaurant_basic_info(
                        delivery_city
                    )
                    print(f"Extracted Data...")

                    self.process_data(info)

                    self.update_global_state(info)

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
            with open("app_state.json", "r") as f:
                app_state = json.load(f)

            if data["city_id"] == app_state["last_city_id"] + 1:
                app_state["last_city_id"] = data["city_id"]
                app_state["LENGTH_OF_DELIVERY_CITIES"] -= 1
                with open("app_state.json", "w") as f:
                    json.dump(app_state, f)

            else:
                app_state["GLOBAL_STATE_QUEUE"].append(data["city_id"])
                with open("app_state.json", "w") as f:
                    json.dump(app_state, f)

        finally:
            self.lock.release()


def main(data):
    delivery_cities_and_urls = data
    queue = multiprocessing.JoinableQueue()
    for _ in range(3):
        process = DownloadProcess(queue)
        process.daemon = True
        process.start()

    for city in delivery_cities_and_urls:
        queue.put(city)

    queue.join()


if __name__ == "__main__":

    data = helper.get_data_of_delivery_cities()

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

    p2 = threading.Thread(target=main, args=(data,), daemon=True)
    p2.start()
    p1.join()
    p2.join()
