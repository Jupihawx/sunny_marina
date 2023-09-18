FROM kitware/trame

COPY --chown=trame-user:trame-user . /deploy
# RUN apt-get update && apt-get install ffmpeg libsm6 libxext6 libgl1-mesa-glx xvfb -y
RUN /opt/trame/entrypoint.sh build