import time
from typing import Self

class SpeedAnalyser:
    def __init__(self) -> None:
        self.reset()

    def reset(self):
        self.duration_steps = {}
        self.start()

    def start(self):
        self.current_timer = time.time()
        self.current_step_name = None

    def step(self, name, sub_timer=False) -> Self:
        self.end_step()
        # Initialization if first time encountered
        if name not in self.duration_steps.keys() and name is not None:
            self.duration_steps[name] = {"duration": 0.}
            if sub_timer:
                self.duration_steps[name]["node"] = SpeedAnalyser()
                self.duration_steps[name]["node"].start()

        self.current_timer = time.time()
        self.current_step_name = name

        if sub_timer:
            return self.duration_steps[name]["node"]
    def end_step(self):
        # Handle previous step
        if self.current_step_name is not None:
            self.duration_steps[self.current_step_name]["duration"] += (
                time.time() - self.current_timer
            )
            if "node" in self.duration_steps[self.current_step_name]:
                self.duration_steps[self.current_step_name]["node"].end_step()
        self.current_step_name = None

    def __recursive_print(self, level =0):
        elapsed_time = sum(
            [value["duration"] for value in self.duration_steps.values()]
        )
        for step_name, values in self.duration_steps.items():
            print(
                "".join(["  " for _ in range(level+1)]),
                step_name,
                f"{values['duration']:0.2f}s",
                f"({100*values['duration']/elapsed_time:0.2f})%" if elapsed_time > 0 else "0.00%"
            )
            if "node" in values:
                values["node"].__recursive_print(level= level+1)

    def end(self):
        self.end_step()

        # Print
        elapsed_time = sum(
            [value["duration"] for value in self.duration_steps.values()]
        )
        print(f"Total Elapsed : {elapsed_time:0.2}s")
        self.__recursive_print()
        # Reset
        self.reset()
    
    # def __recursive_print(self, tree : dict, level = 0):
    #     for step_name, values in tree.items():
    #         print("".join(["  " for _ in range(level+1)]), step_name, f" - {values['duration']} ({values['duration_percent']})")
    #         if values["node"] is not None:
    #             self.__recursive_print(tree = values["node"], level= +1)