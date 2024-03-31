# template_python

[![Python Lint](https://github.com/greyinghair/template_python/actions/workflows/python-lint.yaml/badge.svg?branch=main)](https://github.com/greyinghair/template_python/actions/workflows/python-lint.yaml)

TCP Tests
=========

Long Lived Connections (LLC) & Short Lived connections (SLC)


All test will be from Client-1 to Server-1, Client-2 to Server-2 etc

Each server listens on 2 x ports.  1 port for Short Lived Connections and the 3nd port for Long lived Connections:

| Connection Type | Server port | Keepalive | New Conn Every |
| --------------- | ----------- | --------- | -------------- |
| Long Lived | 12345 | Every 10 seconds	| n/a |
| Short Lived	| 54321	| n/a | Every 1 sec |


Prerequisites

    IAM role for Cloud watch with permissions: [PutMetricData,  CreateLogGroup, CreateLogStream, PutLogEvents, DescribeLogStreams]


