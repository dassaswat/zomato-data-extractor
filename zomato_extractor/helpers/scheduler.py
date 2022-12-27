# Description: This file contains the Scheduler class which is used to schedule the execution of a function at a given time interval. The Scheduler class also checks the global state to see if the program should be terminated or not.
import json
import time
import schedule


class Scheduler:
    def state_management_function(self):
        with open("app_state.json", "r") as f:
            app_state = json.load(f)

        global_state_queue = app_state["GLOBAL_STATE_QUEUE"]
        for city_id in global_state_queue:

            if city_id == app_state["last_city_id"] + 1:
                app_state["last_city_id"] = city_id
                app_state["LENGTH_OF_DELIVERY_CITIES"] -= 1
                global_state_queue.remove(city_id)

                with open("app_state.json", "w") as f:
                    json.dump(app_state, f)

    def schedule(
        self,
        time_interval,
        break_condition_text,
    ):

        print("Building scheduler...")
        schedule.every(time_interval).seconds.do(self.state_management_function)
        print("Checking Global State...")

        while True:
            with open("app_state.json", "r") as f:
                app_state = json.load(f)
            if app_state["LENGTH_OF_DELIVERY_CITIES"] == 0:
                print(f"{break_condition_text}")
                break
            schedule.run_pending()
            time.sleep(1)
