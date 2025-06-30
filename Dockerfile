FROM python:3.9

RUN apt-get update && apt-get install -y --no-install-recommends \
  graphviz \
  libgl1-mesa-glx \
  libxrender1 \
  libxext6 \
  && rm -rf /var/lib/apt/lists/* \
  && apt-get clean

WORKDIR /app

# Download aiida data.
RUN wget -O export_hcofs_co2.aiida "https://archive.materialscloud.org/records/6yq0e-2be96/files/export_hcofs_co2.aiida?download=1"

# Install discover section
ENV AIIDA_PATH /app
ENV PYTHONPATH /app
WORKDIR /app

COPY figure ./figure

# Use uv generated requirements.txt [this seems to not break]
COPY requirements.txt /app/
RUN pip install -r requirements.txt
COPY serve-app.sh /opt/

WORKDIR /app
# New verdi method for databasing.
RUN verdi profile setup core.sqlite_zip -p hcofs-co2 -n --filepath ./export_hcofs_co2.aiida


# start bokeh server
EXPOSE 5006
CMD ["/opt/serve-app.sh"]

#EOF
