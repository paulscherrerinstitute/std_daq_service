FROM continuumio/miniconda3

COPY docker-entrypoint.sh redis_status.sh /usr/bin/
COPY requirements.txt .

RUN conda install -c conda-forge --yes --file requirements.txt
RUN apt-get update && apt-get install vim --yes
RUN mkdir -p /var/log/std-daq

ENTRYPOINT ["/usr/bin/docker-entrypoint.sh"]
CMD ["bash"]
