FROM continuumio/miniconda3

RUN conda install -y -c conda-forge pika pyzmq flask conda-build
