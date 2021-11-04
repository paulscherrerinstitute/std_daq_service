FROM continuumio/miniconda3

RUN conda install -y -c conda-forge pyzmq pyepics flask pika redis

COPY docker-entrypoint.sh redis_status.sh /usr/bin/

ENTRYPOINT ["/usr/bin/docker-entrypoint.sh"]
CMD ["bash"]
