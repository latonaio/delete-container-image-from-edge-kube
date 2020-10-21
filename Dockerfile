FROM l4t:latest

# Definition of a Device & Service
ENV POSITION=Runtime \
    SERVICE=delete-container-image-from-edge\
    AION_HOME=/var/lib/aion

RUN mkdir ${AION_HOME}
WORKDIR ${AION_HOME}
# Setup Directoties
RUN mkdir -p \
    $POSITION/$SERVICE
WORKDIR ${AION_HOME}/$POSITION/$SERVICE/

RUN rm -rf /usr/local/lib/python3.6/dist-packages/protobuf*

ADD requirements.txt .
RUN pip3 install -r requirements.txt

ENV PYTHONPATH ${AION_HOME}/$POSITION/$SERVICE
ENV REGISTRY_USER aion

ADD docker-entrypoint.sh .
ADD src/ .

CMD ["/bin/sh", "docker-entrypoint.sh"]
# CMD ["/bin/sh", "-c", "while :; do sleep 10000; done"]
