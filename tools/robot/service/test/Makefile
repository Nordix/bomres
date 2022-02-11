include ../build/config/settings
CONTAINER_IMAGE = $(SERVICE_IMAGE):$(SERVICE_VERSION)

CONTAINER_IMAGE = docker.io/bomres/alpine_robot:1.0.1

VERSION=a
PROJECT=b


OPTIONS =  -v ${PWD}/robot:/opt/robot
OPTIONS += -e ROBOT_SYSLOG_FILE=/opt/test/robot/syslog.txt

CM_INFO = --Metadata Version:$(VERSION) --Metadata Target:$(PROJECT)

robot:
	docker run  $(OPTIONS)  -i -t $(CONTAINER_IMAGE) robot $(CM_INFO)  token.rst

.PHONY: robot


