FROM python:3.7

RUN apt-get update && apt-get install -y --no-install-recommends \
  graphviz \
  && rm -rf /var/lib/apt/lists/* \
  && apt-get clean all

WORKDIR /app
#
# Install discover section
ENV AIIDA_PATH /app
ENV PYTHONPATH /app
WORKDIR /app/discover-cofs

COPY figure ./figure
COPY setup.py ./
RUN pip install -e .
COPY .docker/serve-app.sh /opt/
COPY .docker/config.json $AIIDA_PATH/.aiida/

# start bokeh server
EXPOSE 5006
CMD ["/opt/serve-app.sh"]

#EOF
