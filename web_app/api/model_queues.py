import asyncio
from serve import get_response_to
from globals import get_inference_queue_task, set_inference_queue_task, get_ongoing_busy_session


async def put_into_inference_queue(message_list, chat_id, is_private, session_id, reply_callback, respond_callback, reply_queue_callback):
    if get_inference_queue_task() is None:
        print(f"creating new inference queue...")
        q = asyncio.Queue()
        set_inference_queue_task(
            (q, asyncio.create_task(inference_loop(q, reply_queue_callback)))
        )
    await get_inference_queue_task()[0].put((message_list, chat_id, is_private, session_id, reply_callback, respond_callback))


def cancel_inference_queue_task():
    if get_inference_queue_task() is not None:
        set_inference_queue_task(None)
        pass


async def inference_loop(q, reply_queue_callback):
    response = []
    while True:
        try:
            message_list, chat_id, is_private, session_id, reply_callback, respond_callback = await asyncio.wait_for(q.get(), timeout=9)
            to_infer = []
            for message_obj in message_list:
                if message_obj.message:
                    to_infer.append(message_obj.message)
                elif message_obj.photo:
                    # extract info from photo
                    pass
                elif message_obj.sticker:
                    # extract info from sticker image and emoji
                    pass

            if get_ongoing_busy_session() is None:
                cancel_inference_queue_task()
                break

            response = await get_response_to(to_infer, chat_id, session_id)
            if response is None:
                continue

            print("final response ready, sending to reply queue...")
            await reply_queue_callback(response, chat_id, is_private, session_id, False, False, reply_callback=reply_callback, respond_callback=respond_callback)

        except asyncio.exceptions.TimeoutError:
            print('no new messages pending inference, closing inference task...')
            cancel_inference_queue_task()
            break
        except asyncio.CancelledError:
            break
        except Exception as e:
            raise e
