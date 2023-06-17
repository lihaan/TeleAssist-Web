from globals import get_ongoing_busy_session
from model_queues import put_into_inference_queue
from mongoDB import log_session, update_actual_end_time_utc, log_utterance
import datetime as dt
import asyncio


class Session:
    id = None
    start_time_utc = None
    actual_end_time_utc = None
    batching_queue_tasks = {}

    def __init__(self, start_time_utc):
        self.start_time_utc = start_time_utc

    def end_session(self):
        self.actual_end_time_utc = dt.datetime.utcnow()

        return self.actual_end_time_utc

    async def put_into_batching_queue(self, message_obj, chat_id, is_private, reply_callback, respond_callback, reply_queue_callback):
        if chat_id not in self.batching_queue_tasks:
            print(f"creating new batching queue with id {chat_id}")
            q = asyncio.Queue()
            self.batching_queue_tasks[chat_id] = (
                q,
                asyncio.create_task(batching_loop(
                    q, chat_id, is_private, self.id, reply_callback, respond_callback, reply_queue_callback, self.cancel_batching_queue))
            )
        await self.batching_queue_tasks[chat_id][0].put(message_obj)

    def cancel_batching_queue(self, queue_id):
        if queue_id in self.batching_queue_tasks:
            del self.batching_queue_tasks[queue_id]


async def batching_loop(q, chat_id, is_private, session_id, reply_callback, respond_callback, reply_queue_callback, cancel_batching_queue_callback):
    message_list = []
    while True:
        try:
            # Wait for 9 seconds for any new messages to arrive
            message_obj = await asyncio.wait_for(q.get(), timeout=9)
            message_list.append(message_obj)
        except asyncio.exceptions.TimeoutError:
            cancel_batching_queue_callback(chat_id)

            if get_ongoing_busy_session() is None:
                break

            utterance_id = await log_utterance(
                chat_id=chat_id,
                is_private=is_private,
                session_id=session_id,
                is_me=False,
                messages=[message.message for message in message_list],
                message_ids=[message.id for message in message_list],
                start_time_utc=min(
                    [messages_object.date for messages_object in message_list]),
                end_time_utc=max(
                    [messages_object.date for messages_object in message_list]),
            )
            print(f"{len(message_list)} messages batched, placing into inference...")
            await put_into_inference_queue(message_list, chat_id, is_private, session_id, reply_callback, respond_callback, reply_queue_callback)
            break
        except asyncio.CancelledError:
            break
        except Exception as e:
            raise e


class BusySession(Session):
    reason = None
    end_time_utc = None
    users_spoken_to = None
    groups_spoken_to = None

    def __init__(self, reason, start_time_utc, end_time_utc):
        self.reason = reason
        self.end_time_utc = end_time_utc
        self.users_spoken_to = set()
        self.groups_spoken_to = set()
        super().__init__(start_time_utc)

    async def end_session(self):
        actual_end_time_utc = super().end_session()
        result_update_session = await update_actual_end_time_utc(
            session_id=self.id, actual_end_time_utc=actual_end_time_utc)
        self.users_spoken_to = None
        self.groups_spoken_to = None
        print('lol', self.users_spoken_to)

    def add_to_users_spoken_to(self, chat_id):
        self.users_spoken_to.add(chat_id)

    def get_users_spoken_to(self):
        return self.users_spoken_to

    def add_to_groups_spoken_to(self, chat_id):
        self.groups_spoken_to.add(chat_id)

    def get_groups_spoken_to(self):
        return self.groups_spoken_to


async def new_busy_session(reason, duration_mins):
    start_time_utc = dt.datetime.utcnow()
    end_time_utc = start_time_utc + dt.timedelta(minutes=duration_mins)
    session = BusySession(reason, start_time_utc, end_time_utc)
    id = await log_session(
        start_time_utc=session.start_time_utc,
        end_time_utc=session.end_time_utc,
        reason_busy=session.reason,
    )
    session.id = id

    return session
