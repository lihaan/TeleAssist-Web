import datetime as dt
import time
from telethon import events, functions, types, utils


async def enable_notifs(client):
    notify_settings = types.InputPeerNotifySettings(
        show_previews=True,
        silent=False,
        mute_until=dt.datetime.min,
        sound=types.NotificationSoundDefault()
    )

    failed_updates = []
    result = await client(functions.account.UpdateNotifySettingsRequest(
        peer=types.InputNotifyUsers(),
        settings=notify_settings))
    if not result:
        failed_updates.append("users")
    result = await client(functions.account.UpdateNotifySettingsRequest(
        peer=types.InputNotifyChats(),
        settings=notify_settings))
    if not result:
        failed_updates.append("chats")
    result = await client(functions.account.UpdateNotifySettingsRequest(
        peer=types.InputNotifyBroadcasts(),
        settings=notify_settings))
    if not result:
        failed_updates.append("broadcasts")

    print(f"{time.asctime()}: enable_notifs - failed_updates: {failed_updates}")

    return failed_updates


async def disable_notifs(client, end_time_utc):
    notify_setttings = types.InputPeerNotifySettings(
        show_previews=True,  # let notifications still show if I check my phone
        silent=True,
        mute_until=end_time_utc,
    )

    failed_updates = []
    is_success = await client(functions.account.UpdateNotifySettingsRequest(
        peer=types.InputNotifyUsers(),
        settings=notify_setttings))
    if not is_success:
        failed_updates.append("users")
    is_success = await client(functions.account.UpdateNotifySettingsRequest(
        peer=types.InputNotifyChats(),
        settings=notify_setttings))
    if not is_success:
        failed_updates.append("chats")
    is_success = await client(functions.account.UpdateNotifySettingsRequest(
        peer=types.InputNotifyBroadcasts(),
        settings=notify_setttings))
    if not is_success:
        failed_updates.append("broadcasts")

    print(f"{time.asctime()}: disable_notifs - failed_updates: {failed_updates}")

    return failed_updates


async def get_contact_user_ids(client):
    contact_req = await client(functions.contacts.GetContactsRequest(hash=42))
    contact_user_ids = [contact.user_id for contact in contact_req.contacts]

    print(
        f"{time.asctime()}: get_contact_user_ids - no. user IDs found: {len(contact_user_ids)}")

    return contact_user_ids
