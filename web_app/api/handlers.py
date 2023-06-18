from session import new_busy_session
from mongoDB import log_utterance
from tele_helpers import get_contact_user_ids, enable_notifs, disable_notifs
from model_queues import put_into_inference_queue
from globals import get_ongoing_busy_session, set_ongoing_busy_session, get_reply_queue_task, set_reply_queue_task, cancel_reply_queue, set_model, delete_model
from models import create_default_text_gen
from message_templates import USER_END_TEMPLATE, GROUP_END_TEMPLATE, INTRODUCTION_TEMPLATE
from telethon import events, utils
from dotenv import dotenv_values
import os
import asyncio
import datetime as dt

curr_path = os.path.dirname(__file__)
secret_path = (os.path.abspath(f"{curr_path}/../.env"))
secrets = dotenv_values(secret_path)
MY_HANDLE = secrets["MY_HANDLE"]


async def handleStartAssistSession(data, client):
    if get_ongoing_busy_session() is not None:
        return (False, 1)

    set_model('text_gen', create_default_text_gen())
    set_ongoing_busy_session(await new_busy_session(data["reason"], data["duration_mins"]))

    result_disable_notifs = await disable_notifs(client, get_ongoing_busy_session().end_time_utc)

    client.add_event_handler(handle_new_message,
                             events.NewMessage(incoming=True,
                                               func=lambda event: event.is_private or (
                                                   event.mentioned and MY_HANDLE.lower() in event.message.message.lower()
                                                   and not event.message.post  # don't handle being tagged in a channel
                                               ))
                             )

    if len(result_disable_notifs):
        return (False, 2)

    return (True, None)


async def handleCheckAssistSession():
    if get_ongoing_busy_session() is None:
        return [True, None, None, None]

    reason = get_ongoing_busy_session().reason
    end_time_iso = get_ongoing_busy_session().end_time_utc.isoformat()
    duration_mins_remaining = round(
        (get_ongoing_busy_session().end_time_utc - dt.datetime.utcnow()).total_seconds() / 60)

    return [False, reason, end_time_iso, duration_mins_remaining]


async def handleEndAssistSession(client):
    if get_ongoing_busy_session() is None:
        return (False, 1)

    delete_model('text_gen')

    client.remove_event_handler(handle_new_message)

    result_enable_notifs = await enable_notifs(client)

    if USER_END_TEMPLATE is not None:
        for chat_id in get_ongoing_busy_session().get_users_spoken_to():
            await put_into_reply_queue([USER_END_TEMPLATE], chat_id, True, get_ongoing_busy_session().id, False, True, send_msg_callback=client.send_message)
    if GROUP_END_TEMPLATE is not None:
        for chat_id in get_ongoing_busy_session().get_groups_spoken_to():
            await put_into_reply_queue([GROUP_END_TEMPLATE], chat_id, False, get_ongoing_busy_session().id, False, True, send_msg_callback=client.send_message)

    await get_ongoing_busy_session().end_session()
    set_ongoing_busy_session(None)

    if len(result_enable_notifs):
        return (False, 2)

    return (True, None)


async def handle_new_message(event):
    client = event.client
    message_obj = event.message  # this lookup will be cached by telethon
    user_id = message_obj.sender_id
    # chat_id is the same as user_id for private DMs
    chat_id = utils.resolve_id(message_obj.chat_id)[0]
    intro_msg = INTRODUCTION_TEMPLATE
    if intro_msg is not None:
        intro_msg = intro_msg.format(reason=get_ongoing_busy_session(
        ).reason) if "{reason}" in intro_msg else intro_msg

    if event.is_private:
        if chat_id not in get_ongoing_busy_session().get_users_spoken_to():
            contact_chat_ids = set(await get_contact_user_ids(client))
            if chat_id not in contact_chat_ids:
                print("Unfamiliar user / spam / bot detected")
                return
            get_ongoing_busy_session().add_to_users_spoken_to(chat_id)
            if intro_msg is not None:
                await put_into_reply_queue([intro_msg], chat_id, event.is_private, get_ongoing_busy_session().id, True, False, reply_callback=event.reply, respond_callback=event.respond)
        await get_ongoing_busy_session().put_into_batching_queue(message_obj, chat_id, event.is_private, event.reply, event.respond, put_into_reply_queue)
    elif event.mentioned:
        if chat_id not in get_ongoing_busy_session().get_groups_spoken_to():
            contact_chat_ids = set(await get_contact_user_ids(client))
            async for user in client.iter_participants(chat_id):
                if user.id not in contact_chat_ids:
                    print("Serious chat detected")
                    return
            get_ongoing_busy_session().add_to_groups_spoken_to(chat_id)
            if intro_msg is not None:
                await put_into_reply_queue([intro_msg], chat_id, event.is_private, get_ongoing_busy_session().id, True, False, reply_callback=event.reply, respond_callback=event.respond)
        await put_into_inference_queue([message_obj], chat_id, event.is_private, get_ongoing_busy_session().id, event.reply, event.respond, put_into_reply_queue)

    return ("message handled")


async def put_into_reply_queue(message_list, chat_id, is_private, session_id, prepend, append, reply_callback=None, respond_callback=None, send_msg_callback=None):
    if get_reply_queue_task(chat_id) is None:
        print(f"creating new reply queue with id {chat_id}...")
        q = asyncio.Queue()
        set_reply_queue_task(
            chat_id,
            (q,
             asyncio.create_task(reply_loop(
                 q, chat_id, is_private, session_id, respond_callback, send_msg_callback))
             )
        )
    await get_reply_queue_task(chat_id)[0].put((message_list, prepend, append, reply_callback))


async def reply_loop(q, chat_id, is_private, session_id, respond_callback, send_msg_callback):
    sent_messages = []
    while True:
        try:
            response, prepend, append, reply_callback = await asyncio.wait_for(q.get(), timeout=9)

            prepend_msgs = []
            append_msgs = []

            if prepend or append:
                if prepend:
                    prepend_msgs = response
                if append:
                    append_msgs = response

                content_found = True
                while prepend or append:
                    try:
                        response, prepend, append, inner_reply_callback = await asyncio.wait_for(q.get(), timeout=9)
                        if prepend or append:
                            if prepend:
                                prepend_msgs.extend(response)
                            if append:
                                append_msgs.extend(response)
                            continue
                        reply_callback = inner_reply_callback
                    except asyncio.exceptions.TimeoutError:
                        content_found = False
                        msgs = prepend_msgs + append_msgs
                        if respond_callback is not None:
                            for msg in msgs:
                                await respond_callback(msg)
                        elif send_msg_callback is not None:
                            for msg in msgs:
                                await send_msg_callback(entity=chat_id, message=msg)
                        break
                if not content_found:
                    continue

            response = prepend_msgs + response + append_msgs

            if len(response):
                await reply_callback(response[0])
                for msg in response[1:]:
                    if respond_callback is not None:
                        sent_messages.append(await respond_callback(msg))
                    elif send_msg_callback is not None:
                        sent_messages.append(await send_msg_callback(entity=chat_id, message=msg))

            self_utterance_id = await log_utterance(
                chat_id=chat_id,
                is_private=is_private,
                session_id=session_id,
                is_me=True,
                messages=[
                    messages_object.message for messages_object in sent_messages],
                message_ids=[
                    messages_object.id for messages_object in sent_messages],
                start_time_utc=min(
                    [messages_object.date for messages_object in sent_messages]),
                end_time_utc=max(
                    [messages_object.date for messages_object in sent_messages]),
            )

            sent_messages = []

        except asyncio.exceptions.TimeoutError:
            print('no new replies pending to be sent, closing reply task...')
            cancel_reply_queue(chat_id)
            break
        except asyncio.CancelledError:
            print("reply cancelled!")
            pass
        except Exception as e:
            raise e
