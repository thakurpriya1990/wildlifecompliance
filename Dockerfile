FROM ubuntu:18.04
RUN mkdir -p /home/www-data/app && chown -R www-data:www-data /home/www-data/app && chown -R www-data:www-data /tmp
# Set the working directory to /home/www-data/app
WORKDIR /home/www-data/app

# Copy the current directory contents into the container at /home/www-data/app
COPY . /home/www-data/app
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get -y upgrade

RUN apt-get install -y apt-transport-https git nodejs npm
RUN apt-get install -y python-pip virtualenv
RUN apt-get install -y binutils postgresql postgresql-contrib libgdal-dev postgis

RUN npm install npm@latest -g

#USER www-data

RUN git clone -b compliancemanagement_demo https://github.com/mintcoding/ledger.git

WORKDIR ledger/wildlifecompliance/frontend/wildlifecompliance

RUN npm install
RUN npm run build

WORKDIR /home/www-data/app/ledger
ENV VIRTUAL_ENV=/home/www-data/app/ledger/venv
RUN virtualenv -p python $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

#RUN source venv/bin/activate

RUN pip install -r requirements.txt

RUN pip install GDAL==$(gdal-config --version) --global-option=build_ext --global-option="-I/usr/include/gdal"

#RUN ex -s -c "%s/geos_version().decode()/geos_version().decode().split(' ')[0]/g|x" ~/.virtualenvs/ledger/lib/python2.7/site-packages/django/contrib/gis/geos/libgeos.py
RUN sed "s+/geos_version().decode()+/geos_version().decode().split(' ')[0]+g" /home/www-data/app/ledger/venv/lib/python2.7/site-packages/django/contrib/gis/geos/libgeos.py

## Make ports 8073, 8080 available to the world outside this container
EXPOSE 8073
EXPOSE 8080
#
CMD ["manage_py.sh"]
