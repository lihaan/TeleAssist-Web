import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, GenerationConfig
import os
from dotenv import dotenv_values

curr_path = os.path.dirname(__file__)
secret_path = (os.path.abspath(f"{curr_path}/../.env"))
secrets = dotenv_values(secret_path)
TOKENIZER_DIR = secrets["TOKENIZER_DIR"]
MODEL_DIR = secrets["MODEL_DIR"]
GENERATION_CONFIG_DIR = secrets["GENERATION_CONFIG_DIR"]


class TextGen:
    def __init__(self, tokenizer_dir, model_dir, generation_config_dir):
        self.tokenizer_name = tokenizer_dir
        self.model_name = model_dir
        self.generation_config_name = generation_config_dir

        curr_path = os.path.dirname(__file__)
        tokenizer_path = (os.path.abspath(
            f"{curr_path}/../text_generation_models/{self.tokenizer_name}"))
        model_path = (os.path.abspath(
            f"{curr_path}/../text_generation_models/{self.model_name}"))
        generation_config_path = (os.path.abspath(
            f"{curr_path}/../text_generation_models/{self.generation_config_name}"))

        self.device = torch.device(
            "cuda:0" if torch.cuda.is_available() else "cpu")

        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
        self.pad_token_id = self.tokenizer.eos_token_id

        self.model = AutoModelForCausalLM.from_pretrained(
            model_path).to(self.device)

        self.generation_config = GenerationConfig.from_pretrained(
            generation_config_path)
        # clean_up_tokenization_spaces=True, # doesn't seem to have any effect

        print("Model initialised")

    def tokenize(self, prompt):
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

        return inputs

    def predict(self, tokens):
        outputs = self.model.generate(
            **tokens, generation_config=self.generation_config)
        raw_inference = self.tokenizer.batch_decode(
            outputs, skip_special_tokens=True)

        return raw_inference[0]

    # TODOs
    # def process_context(self, utterance_list):

    #     utterance_joined = [", ".join(utterance)
    #                         for utterance in utterance_list]
    #     utterance_prefixed = [
    #         "[PersonA]: {utterance} \n" for utterance in utterance_list]

    #     return context

    def process_input(self, new_msgs, context=""):
        # Additional processing to form prompt

        new_text = ", ".join(new_msgs)
        context = context + " " if len(context) else ""
        # Check whether need escape with double backslash
        # comment: Actually i think when I passed this input to the model, it recognises the \n token as an actual newline and not the escaped \n, so I think we don't need to escape
        prompt = f"{context}[PersonA]: {new_text} \n [Li Han]:"

        return prompt

    def clean_output(self, inference, prompt_length):
        # Clean raw inference before it is used
        response = inference[prompt_length:]
        response = map(lambda x: x.strip(),
                       response.split("\n")[0].split(","))
        response = [msg for msg in response if msg != ""]

        return response


def create_default_text_gen():
    model = TextGen(
        tokenizer_dir=TOKENIZER_DIR,
        model_dir=MODEL_DIR,
        generation_config_dir=GENERATION_CONFIG_DIR,
    )
    return model
