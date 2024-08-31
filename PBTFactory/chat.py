import os
import threading
import time
import typing as T
import uuid

from PBTFactory.message import MessageManager
from PBTFactory.request_manager import RequestManager, RequestType


class Chat:
    _lock: threading.Lock
    _msgs: T.Dict[uuid.UUID, T.Tuple[str, float]]

    def __init__(self, save_folder, system_message=None):
        self.save_folder = save_folder
        self.system_message = system_message
        self.msg_count = 0
        self.total_time = 0
        self._msgs = {}
        self._lock = threading.Lock()

    def _on_response(self, id, msg, timeused):
        with self._lock:
            self._msgs[id] = (msg, timeused)
            self.total_time += timeused

    def ask(
        self,
        message_manager: MessageManager,
        step_name=None,
        request_type: RequestType = RequestType.long_answer,
    ):
        id = uuid.uuid4()
        if self.system_message:
            messages = [
                {"role": "system", "content": self.system_message}
            ] + message_manager.messages
        else:
            messages = message_manager.messages

        request = {
            "id": id,
            "messages": messages,
            "callback": self._on_response,
            "info": f"{step_name}\t{self.save_folder}_{self.msg_count}",
        }
        RequestManager().add(request, self.save_folder, request_type)

        while True:
            with self._lock:
                if id in self._msgs:
                    msg = self._msgs[id][0]
                    break
            time.sleep(1)

        tmp_mm = message_manager.copy()
        tmp_mm.add_assistant_message(msg)
        save_name = f"{self.msg_count}"
        if step_name:
            save_name += f"_{step_name}"
        save_name += ".txt"
        save_path = os.path.join(self.save_folder, "msg", save_name)
        tmp_mm.save(save_path)

        self.msg_count += 1

        return msg
