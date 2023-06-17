# TeleAssist - Web Server

```
Harness the power of Generative AI to reply your Telegram chats for you!
```

## Introduction

Many companies and/or messaging platforms are already harnessing the power of AI to help users with replying messages. Just look at Gmail's nifty Smart Compose (email autocompletion) feature! They have even released a Smart Reply feature for Android Messages, and are slowly but surely improving their Machine Learning (ML) models to generate more appropriate response options to text messages received by users.

What if you are busy and don't have time to even choose messages to send to those NPC characters in your life? What if instead of simply suggesting responses, the model simply picks the best one and sends it directly? What if we are bored of the mundane and want to live a little more chaotically?

## Features

- Bring Your Own Model
  - currently only HuggingFace models are supported right out of the box, though you can easily amend the code of the model loading class to fit your desired model
- Message Batching
  - To account for people's tendency to send multiple messages at once, messages within 9 seconds of one another from a single peer will be batched into one "question" to be answered by the model
- Option to add an introductory / farewell message
  - for responsible users like yourself to inform your peers that it is in fact a model that is speaking to them
  - able to specify a reason why you are busy, which will be included in the introductory message
- Only responds to trusted users and groups, and not to bots or unknown spam users
  - Preconfigured to only reply to people in your contacts list,
  - and group chats (when you are tagged) where everyone in the group is in your contacts list
  - Being tagged in channels will NOT trigger this app's functionality

## Limitations

- Only supports text mediums
  - Photo and sticker support are planned
- Not a fully-fledged chatbot
  - Does not "remember" past conversation turns ie. only replies directly to peer's current batch of messages

## Usage

Note that the functionality of _TeleAssist - Web Server_ is meant to be paired with the [*TeleAssist - Telegram Bot*](TODO: github link). _TeleAssist - Telegram Bot_ acts as the front-end user interface to the functionality provided by this app.

### Requirements

- Python 3
  - Recommended: >= 3.10.4
- Host Machine
  - RAM: at least 1GB to ensure optimal performance (does not include usage by model)
- MongoDB (optional)
  - the app does make a few helper function calls to log information into a local mongodb instance, but you could easily refactor and remove these helper functions from the codebase if you do not wish to log your chats
- Docker (optional)
  - Dockerfile provided if you wish to containerize it

### Steps

1. Obtain Telegram api_id and api_hash
   - [Link to instructions on Telegram docs](https://core.telegram.org/api/obtaining_api_id)
2. Clone repository
   > git clone TODO: github link
   > cd TeleAssistWeb/web_app
3. Create message*templates.py in *./api\_ directory
   - This python file will contain the messages that you wish the app automatically sends at the start / end of the conversation
   - Refer to samples_messages_templates.txt for examples
4. Supply model, tokenizer, generation configuration into the _./text_generation_models_ directory
   - Example folder and naming structure:
     ```
     - text_generation_models/
         - distilgpt2_model_v1/
             - Relevant files (eg. tokenizer.json, vocab.json, special_token_map.json, etc)
         - distilgpt2_tokenizer_v1/
             - Relevant files (eg. config.json, pytorch_model.bin, training_args.bin, etc)
         - contrastive_search_v1/
             - generation_config.json
     ```
5. Create a .env file with the following parameters
   - API_ID (Telegram api_id)
   - API_HASH (Telegram api_hash)
   - MY_PHONE (Phone number used for Telegram, in international format)
   - MY_HANDLE (telegram handle eg. @noobmaster69)
   - TOKENIZER_DIR (eg. "distilgpt2_tokenizer_v1")
   - MODEL_DIR (eg. "distilgpt2_model_v1")
   - GENERATION_CONFIG_DIR (eg. "contrastive_search_v1")
6. Install dependencies TODO:
   - Recommended to create a virtual environment (eg. venv) before installing
     - Navigate to root directory ie. TeleAssistWeb
       > pip install -r requirements.txt
     - Lastly install PyTorch
       - Refer to [PyTorch Get Started Locally](https://pytorch.org/get-started/locally/) for the appropriate way to install torch based on your OS
7. Launch MongoDB instance
   - Either do this, or remove in code all function calls imported from mongoDB.py
   - Default URL: mongodb://localhost:27017
8. Run Locally
   > python web_app/api/\_\_init\_\_.py

# Using Docker

- Dockerfile is provided for reference at /web_app/Dockerfile
  - If you are using TeleAssist - Telegram Bot, or opting to retain the functionality of the MongoDB logging, you should consider placing all the docker containers in the same network. The commands to build and run would be as follows:
    > docker build -t tele-assist-web .
    > docker network create tele-assist-network
    > docker run --name web --net tele-assist-network -p 5000:5000 -d tele-assist-web
- To run the MongoDB instance on Docker, use the following command:
  > docker run --name db -p 27017:27017 --network tele-assist-network --mount source=tele-assist-volume,target=/data/db -d mongo:6.0.6
  - Take note to amend the URL of the MongoDB database in web_app/api/mongoDB.py from localhost to [Name assigned to MongoDB container] (in the command above the name is "db")

## Contributing

Although TeleAssist is simply a pet project of mine, I am super keen on improving it and expanding its capabilities. Feel free to raise issues to provide feedback if you have any. If this project has helped you in any way, do give it a star or [buy this struggling student a coffee](https://www.buymeacoffee.com/lihanong)! Thank you!
