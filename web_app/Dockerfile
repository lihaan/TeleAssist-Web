FROM python:3.10

# set a directory for the app
WORKDIR /Repositories/Competitions/hackgt/TeleAssistWeb/web_app

# copy all the files to the container
COPY . .

# install dependencies
RUN pip install -r requirements.txt --no-cache-dir
# pytorch installation comamnd for linux (with CUDA support, torch package only)
RUN pip install torch --no-cache-dir --default-timeout=900

EXPOSE 5000

# serve on 0.0.0.0: in this context, it is used as a "source", so it means that the app is listening on all the available ip addresses that is given to it. If it is given two, then it will listen on both of them
# "app" is defined by hypercorn
CMD ["hypercorn", "api/__init__:app", "-w", "1", "-b", "0.0.0.0:5000"]