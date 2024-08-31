import logging
import os
import queue
import threading
import time
import typing as T
from dataclasses import dataclass, field
from enum import Enum

from openai import OpenAI


class RequestType(Enum):  #  This is for API cost saving
    short_answer = "short_answer"
    long_answer = "long_answer"

    @classmethod
    def from_string(cls, string):
        try:
            return cls(string)
        except ValueError:
            raise ValueError(f"Invalid RequestType: {string}")

    @classmethod
    def get_all_types(cls):
        return [e.value for e in cls]


# https://docs.python.org/3/library/queue.html
@dataclass(order=True)
class PrioritizedItem:
    priority: str
    item: T.Any = field(compare=False)


class RequestManager:
    _instance = None
    _lock = threading.Lock()
    stop = False
    verbose = False
    waitings: dict[RequestType, queue.PriorityQueue]

    @classmethod
    def init(cls, config):
        with cls._lock:
            assert cls._instance is None, "RequestManager is a singleton"
            cls._instance = super(RequestManager, cls).__new__(cls)
            cls._instance.waitings = {}
            for llm_server_config in config["llm_servers"]:
                llm_server = OpenAI(
                    api_key=llm_server_config["api_key"],
                    base_url=llm_server_config["base_url"],
                )
                for _ in range(llm_server_config["concurrent"]):
                    threading.Thread(
                        target=cls._instance.run,
                        args=(
                            llm_server,
                            llm_server_config["model"],
                            llm_server_config["allow_request_type"],
                            llm_server_config["retry"],
                        ),
                    ).start()
        return cls._instance

    def __new__(cls):
        assert cls._instance is not None, "RequestManager is not initialized"
        return cls._instance

    def add(self, request, rank, request_type: RequestType):
        item = PrioritizedItem(rank, request)
        if request_type in self.waitings:
            self.waitings[request_type].put(item)
        else:
            self.waitings[request_type] = queue.PriorityQueue()
            self.waitings[request_type].put(item)

    def run(self, llm_server, model, allow_request_types: T.List[RequestType], retry):
        should_pause = False
        last_time_log_pause = 0
        last_time_log_waiting = 0

        while not self.stop:
            should_pause = self.check_pause_status(should_pause)
            if should_pause:
                last_time_log_pause = self.log_status_pause(last_time_log_pause)
                time.sleep(5)
                continue

            item = None
            for request_type in allow_request_types:
                if request_type not in self.waitings:
                    continue
                try:
                    item = self.waitings[request_type].get(block=False)
                    break
                except queue.Empty:
                    continue
            if item is None:
                last_time_log_waiting = self.log_status_waiting(last_time_log_waiting)
                time.sleep(5)
                continue

            try:
                self.process_request(item.item, llm_server, model, retry)
                last_time_log_waiting = time.time()
            except Exception as e:
                logging.error(f"Request failed: {e}", exc_info=True)
                raise

        logging.info("RequestManager stopped")

    def check_pause_status(self, should_pause):
        if os.path.exists("pause.txt"):
            with open("pause.txt") as f:
                pause_status = f.read().strip() == "1"
                if should_pause != pause_status:
                    should_pause = pause_status
                    if self.verbose:
                        logging.info("Paused" if should_pause else "Resumed")
        return should_pause

    def process_request(self, request, llm_server, model, retry=5):
        try:
            t0 = time.time()
            chat_completion = llm_server.chat.completions.create(
                model=model, max_tokens=8 * 1024, messages=request["messages"]
            )
            timeused = time.time() - t0
            # completion_tokens = chat_completion.usage.completion_tokens

            if self.verbose:
                logging.info(f"Request: {request['info']}")

            request["callback"](
                request["id"], chat_completion.choices[0].message.content, timeused
            )
        except Exception as e:
            logging.warning(f"Request failed: {e}, retrying {retry} times")
            if retry > 0:
                time.sleep(600)
                return self.process_request(request, llm_server, model, retry - 1)
            else:
                raise e

    def log_status_pause(self, last_time_log_pause):
        if time.time() - last_time_log_pause > 600:
            if self.verbose:
                logging.info("Paused")
            last_time_log_pause = time.time()
        return last_time_log_pause

    def log_status_waiting(self, last_time_log_waiting):
        if time.time() - last_time_log_waiting > 600:
            if self.verbose:
                logging.info("Waiting for request")
            last_time_log_waiting = time.time()
        return last_time_log_waiting
