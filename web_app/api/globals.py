GLOBALS = {
    'takeover_session': None,
    'reply_queue_task': {},
    'model_queues': {
        "inference_queue_task": None
    },
    'models': {},
}


def get_ongoing_busy_session():
    return GLOBALS['takeover_session']


def set_ongoing_busy_session(session):
    GLOBALS['takeover_session'] = session


def get_reply_queue_task(queue_id):
    if queue_id not in GLOBALS['reply_queue_task']:
        return None
    return GLOBALS['reply_queue_task'][queue_id]


def set_reply_queue_task(queue_id, q_task):
    GLOBALS['reply_queue_task'][queue_id] = q_task


def cancel_reply_queue(queue_id):
    if get_reply_queue_task(queue_id) is not None:
        del GLOBALS['reply_queue_task'][queue_id]


def get_inference_queue_task():
    return GLOBALS['model_queues']['inference_queue_task']


def set_inference_queue_task(q_task):
    GLOBALS['model_queues']['inference_queue_task'] = q_task


def set_model(model_id, model):
    GLOBALS['models'][model_id] = model


def get_model(model_id):
    if model_id in GLOBALS['models']:
        return GLOBALS['models'][model_id]
    return None


def delete_model(model_id):
    if get_model(model_id) is not None:
        del GLOBALS['models'][model_id]
        print("Model deleted")
