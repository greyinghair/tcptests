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

    IAM role (same role as used for SSM) permissions: [PutMetricData,  CreateLogGroup, CreateLogStream, PutLogEvents, DescribeLogStreams]

     role inline attached policy: <iam_inline_role.yml>
     role attached AWS managed policy: "AmazonSSMManagedInstanceCore"
     Trust Relationships: <iam_trust_relationship.yml>


Logging


    - Client Local Logging : Info level logging is sent to /var/log/tcp_client.log
    - Cloudwatch Logging


Server

Create tcp_server.py in /opt/scripts containing code:
```
sudo mkdir /opt/scripts && sudo nano /opt/scripts/tcp_server.py
```

<tcp_server.py>

Setup service to run on boot:
```sudo nano /etc/systemd/system/tcpserver.service```

```
[Unit]
Description=TCP Server
 
[Service]
ExecStart=/usr/bin/python3 /opt/scripts/tcp_server.py
WorkingDirectory=/opt/scripts/
Restart=always
User=root
 
[Install]
WantedBy=multi-user.target
```

Start service & enable at boot: ```sudo systemctl start tcpserver.service && sudo systemctl enable tcpserver.service```

Verify service status: ```sudo systemctl status tcpserver.service```
Verify service is listening on both ports: ```netstat -ltn```
Check Logs for service: ```sudo journalctl -u tcpserver```


Client

Install client pre-req: ```sudo yum install pip -y && sudo pip3 install boto3 watchtower```

Create tcp_client.py in /opt/scripts containing code: ```sudo mkdir /opt/scripts && sudo nano /opt/scripts/tcp_client.py```

<tcp_client.py>

Setup client tests to ruin as a service: ```sudo nano /etc/systemd/system/tcpclient.service```

```
[Unit]
Description=TCP Client
 
[Service]
ExecStart=/usr/bin/python3 /opt/scripts/tcp_client.py
WorkingDirectory=/opt/scripts/
Restart=always
User=root
 
[Install]
WantedBy=multi-user.target
```

Start service & configure to run at boot: ```sudo systemctl start tcpclient.service && sudo systemctl enable tcpclient.service```