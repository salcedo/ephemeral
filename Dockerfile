FROM alpine:latest

RUN apk update && apk add --no-cache bash openvpn && mkdir /ephemeral

COPY openvpn.conf /ephemeral/server.conf
COPY certs/* /ephemeral/
COPY init.sh /ephemeral/init.sh

CMD ["/ephemeral/init.sh"]
