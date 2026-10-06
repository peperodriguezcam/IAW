FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y apache2 && apt-get clean

# Configuración MPM Event
RUN a2dismod mpm_prefork mpm_worker && a2enmod mpm_event

EXPOSE 8080

CMD ["apachectl", "-D", "FOREGROUND"]
