from globals import get_model
from mongoDB import log_model_inference
import datetime as dt


async def get_response_to(messages, chat_id, session_id):
    start_utc = dt.datetime.utcnow()

    model = get_model('text_gen')
    if model is None or not len(messages):
        return None

    prompt = model.process_input(messages, context="")
    tokens = model.tokenize(prompt)
    inference_start_utc, inference_end_utc = None, None
    response = []

    # Make inference, if output not optimal, make it again
    while not len(response) or response == ["(photo)"]:
        inference_start_utc = dt.datetime.utcnow()
        inference = model.predict(tokens)
        inference_end_utc = dt.datetime.utcnow()
        response = model.clean_output(inference, len(prompt))
        print(f"inference: {response}")

    end_utc = dt.datetime.utcnow()
    await log_model_inference(
        raw_inference=inference,
        inference_duration_seconds=round(
            (inference_end_utc - inference_start_utc).total_seconds(), 2),
        total_duration_seconds=round(
            (end_utc - start_utc).total_seconds(), 1),
        input=prompt,
        session_id=session_id,
        model_name=model.model_name,
        tokenizer_name=model.tokenizer_name,
        generation_config_name=model.generation_config_name,
    )

    return response
