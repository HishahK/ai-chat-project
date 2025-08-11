FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends lubuntu-desktop xrdp && \
    adduser xrdp ssl-cert


RUN useradd -m -s /bin/bash testuser && \
    echo "testuser:1234" | chpasswd && \
    usermod -aG sudo testuser && \
   
    echo "startlubuntu" > /home/testuser/.xsession && \
   
    chown testuser:testuser /home/testuser/.xsession


RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/*

EXPOSE 3389


CMD /etc/init.d/dbus start && /usr/sbin/xrdp --nodaemon