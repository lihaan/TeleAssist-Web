import motor.motor_asyncio

DB_DOCKER_NAME = "db"
# DB_DOCKER_NAME = "localhost"
DB_URL = f"mongodb://{DB_DOCKER_NAME}:27017"  # default port

client = motor.motor_asyncio.AsyncIOMotorClient(
    DB_URL)

main_db = client.main_db

sessions_collection = main_db.sessions
inferences_collection = main_db.inferences
utterances_collection = main_db.utterances


async def log_session(start_time_utc, end_time_utc, reason_busy):
    session_json = {
        "start_time_utc": start_time_utc,
        "end_time_utc": end_time_utc,
        "actual_end_time_utc": None,
        "reason_busy": reason_busy
    }
    session_id = (await sessions_collection.insert_one(session_json)).inserted_id
    return session_id


async def get_session_info(session_id):
    session_info = await sessions_collection.find_one({"_id": session_id})

    return session_info


async def update_actual_end_time_utc(session_id, actual_end_time_utc):
    result = await sessions_collection.update_one(
        {'_id': session_id}, {'$set': {'actual_end_time_utc': actual_end_time_utc}})

    return result


async def log_model_inference(raw_inference, inference_duration_seconds, total_duration_seconds, input, session_id, model_name, tokenizer_name, generation_config_name):
    inference_json = {
        "raw_inference": raw_inference,
        "inference_duration_seconds": inference_duration_seconds,
        "total_duration_seconds":  total_duration_seconds,
        "input": input,
        "session_id": session_id,
        "model_name": model_name,
        "tokenizer_name": tokenizer_name,
        "generation_config_name": generation_config_name
    }
    inference_id = (await inferences_collection.insert_one(inference_json)).inserted_id
    return inference_id


async def log_utterance(chat_id, is_private, session_id, is_me, messages, message_ids, start_time_utc, end_time_utc):
    utterance_json = {
        "chat_id": chat_id,
        "is_private": is_private,
        "session_id": session_id,
        # session_id will be null if if the messages are not SENT during the session (even if the messages are retrieved via telegram api during the session)
        "is_me": is_me,
        "messages_ids": message_ids,
        "messages_text": messages,
        "start_time_utc": start_time_utc,
        "end_time_utc": end_time_utc,
    }
    utterance_id = (await utterances_collection.insert_one(utterance_json)).inserted_id
    return utterance_id

# TODOs
# async def retrieve_user_context(chat_id, session_id):
#     user_utterances = main_db.user_utterances
#     pass


# async def log_group_utterance(chat_id, session_id, messages, response):
#     pass


# async def retrieve_group_context(chat_id, session_id):
#     pass
