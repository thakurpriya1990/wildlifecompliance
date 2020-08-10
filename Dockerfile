# Prepare the base environment.
FROM ubuntu:18.04 as builder_base_wls
MAINTAINER asi@dbca.wa.gov.au
ENV DEBIAN_FRONTEND=noninteractive
ENV DEBUG=True
ENV TZ=Australia/Perth
ENV EMAIL_HOST="smtp.corporateict.domain"
ENV DEFAULT_FROM_EMAIL='no-reply@dbca.wa.gov.au'
ENV NOTIFICATION_EMAIL='jawaid.mushtaq@dbca.wa.gov.au'
ENV NON_PROD_EMAIL='brendan.blackford@dbca.wa.gov.au, walter.genuit@dbca.wa.gov.au, katsufumi.shibata@dbca.wa.gov.au, mohammed.ahmed@dbca.wa.gov.au, test_licensing@dpaw.wa.gov.au, jawaid.mushtaq@dbca.wa.gov.au, shayne.sharpe@dbca.wa.gov.au'
ENV PRODUCTION_EMAIL=False
ENV EMAIL_INSTANCE='DEV'
ENV SECRET_KEY="ThisisNotRealKey"
ENV SITE_PREFIX='wls-uat'
ENV SITE_DOMAIN='dbca.wa.gov.au'
ENV OSCAR_SHOP_NAME='Department of Biodiversity, Conservation and Attractions'
ENV BPAY_ALLOWED=False
RUN apt-get clean \
  && apt-get update --fix-missing \
  && apt-get upgrade -y \
  && apt-get install -yq git mercurial gcc gdal-bin libsasl2-dev libpq-dev \
  python python-setuptools python-dev python-pip \
  imagemagick poppler-utils \
  libldap2-dev libssl-dev wget build-essential \
  libmagic-dev binutils libproj-dev gunicorn tzdata \
  postgresql-client mtr \
  cron rsyslog
RUN pip install --upgrade pip
RUN apt-get install -yq vim

# Install Python libs from requirements.txt.
FROM builder_base_wls as python_libs_wls
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
  # Update the Django <1.11 bug in django/contrib/gis/geos/libgeos.py
  # Reference: https://stackoverflow.com/questions/18643998/geodjango-geosexception-error
  && sed -i -e "s/ver = geos_version().decode()/ver = geos_version().decode().split(' ')[0]/" /usr/local/lib/python2.7/dist-packages/django/contrib/gis/geos/libgeos.py \
  && rm -rf /var/lib/{apt,dpkg,cache,log}/ /tmp/* /var/tmp/*


# Install the project (ensure that frontend projects have been built prior to this step).
FROM python_libs_wls
COPY gunicorn.ini manage_wc.py ./
COPY timezone /etc/timezone
ENV TZ=Australia/Perth
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN touch /app/.env
COPY .git ./.git
#COPY ledger ./ledger
COPY wildlifecompliance ./wildlifecompliance
RUN python manage_wc.py collectstatic --noinput

RUN mkdir /app/tmp/
RUN chmod 777 /app/tmp/

COPY cron /etc/cron.d/dockercron
COPY startup.sh /
# Cron start
RUN service rsyslog start
RUN chmod 0644 /etc/cron.d/dockercron
RUN crontab /etc/cron.d/dockercron
RUN touch /var/log/cron.log
RUN service cron start
RUN chmod 755 /startup.sh
# cron end

EXPOSE 8080
HEALTHCHECK --interval=1m --timeout=5s --start-period=10s --retries=3 CMD ["wget", "-q", "-O", "-", "http://localhost:8080/"]
CMD ["/startup.sh"]
#CMD ["gunicorn", "wildlifecompliance.wsgi", "--bind", ":8080", "--config", "gunicorn.ini"]
