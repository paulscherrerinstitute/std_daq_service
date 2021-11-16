FROM continuumio/miniconda3

RUN conda install -y -c conda-forge pyzmq pyepics flask pika redis pcaspy

COPY docker-entrypoint.sh redis_status.sh /usr/bin/

RUN mkdir -p /var/log/std-daq

ENTRYPOINT ["/usr/bin/docker-entrypoint.sh"]
CMD ["bash"]
