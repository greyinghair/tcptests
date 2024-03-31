import asyncio
import threading
import socket
import time
import logging
import boto3
import watchtower
from botocore.exceptions import NoCredentialsError

# Initialize CloudWatch client with a specified region
aws_region: str = "your_aws_region"  # e.g., "us-east-1"
cloudwatch = boto3.client('cloudwatch', region_name=aws_region)
namespace: str = 'TCPTests'
ec2_hostname = socket.gethostname()  # Get EC2 instance hostname

# Server details
server_ip: str= "your_server_ip"  # Replace with the actual server IP
long_lived_port: int = 12345
short_lived_port: int = 54321

# Configure logging
log_file_path = "/var/log/tcp_client.log"  # Specify your log file path here
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename=log_file_path,
                    filemode='a')  # 'a' means append; use 'w' to overwrite each time

# Add CloudWatch logging
try:
    cloudwatch_handler = watchtower.CloudWatchLogHandler(log_group="TCPTest",
                                                            stream_name=f"client_{ec2_hostname}",
                                                            use_queues=False,  # Set to True for async logging
                                                            create_log_group=True)
    logging.getLogger().addHandler(cloudwatch_handler)
except NoCredentialsError:
    logging.error("AWS credentials not found.")


def publish_metric(metric_name: str, value: int):
    full_metric_name = f"client_{ec2_hostname}_{metric_name}"  # Prepend the hostname
    try:
        cloudwatch.put_metric_data(
            Namespace=namespace,
            MetricData=[
                {
                    'MetricName': full_metric_name,
                    'Value': value,
                    'Unit': 'Count'
                },
            ]
        )
    except Exception as e:
        logging.error(f"Failed to publish metric {full_metric_name}: {e}")

def handle_long_lived_connection():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.connect((server_ip, long_lived_port))
            logging.info(f"LLC - Connected to the server for a long-lived connection.")
            while True:
                message: str = "heartbeat from long-lived connection"
                sock.sendall(message.encode('utf-8'))
                logging.info(f"LLC - Sent long-lived heartbeat to {server_ip}.")
                data = sock.recv(1024)
                if data:
                    logging.info(f"LLC - Received from server {server_ip}: {data.decode()}")
                    publish_metric('LongLivedConnection', 1)
                else:
                    publish_metric('LongLivedConnection', 0)
                time.sleep(10)
        except Exception as e:
            logging.error(f"LLC - An error occurred in the long-lived connection with {server_ip}: {e}")
            publish_metric('LongLivedConnection', 0)

async def handle_short_lived_connection_async():
    while True:
        try:
            reader, writer = await asyncio.open_connection(server_ip, short_lived_port)
            message: str = "message from short-lived connection"
            logging.info(f"SLC - Sending message on short-lived connection to {server_ip}.")
            writer.write(message.encode('utf-8'))
            await writer.drain()
            data = await reader.read(1024)
            if data:
                logging.info(f"SLC - Received reply on short-lived connection from {server_ip}: {data.decode()}")
                publish_metric('ShortLivedConnection', 1)
            else:
                publish_metric('ShortLivedConnection', 0)
            writer.close()
            await writer.wait_closed()
            logging.info(f"SLC - Short-lived connection with {server_ip} closed.")
        except Exception as e:
            logging.error(f"SLC - An error occurred in the short-lived connection with {server_ip}: {e}")
            publish_metric('ShortLivedConnection', 0)
        await asyncio.sleep(1)

def start_short_lived_connections():
    asyncio.run(handle_short_lived_connection_async())

if __name__ == "__main__":
    long_lived_thread = threading.Thread(target=handle_long_lived_connection, daemon=True)
    long_lived_thread.start()
    start_short_lived_connections()
