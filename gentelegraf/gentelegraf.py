#!/usr/bin/env python3

import pymysql
from jinja2 import Template
import os.path
import sys
import time
import docker

def main():
    try:
        db = pymysql.connect(host="latency.launtel.net.au",user="latency",password="meih7Baes",db="latency",cursorclass=pymysql.cursors.DictCursor)
        cursor = db.cursor()
        cursor.execute("checksum table urls")
        checksum_start = cursor.fetchone()
        db.commit()
    except Exception as e:
        print(e)
        raise

    print("Building Telegraf Config")
    cursor.execute("select INET_NTOA(`ipaddr`) as ipaddr, name as name from urls")
    allrows = cursor.fetchall()
    telegraf_config = """
    # Global Agent Configuration
    [agent]
      flush_interval = "15s"
      interval = "15s"
    
    # Output Plugin InfluxDB
    [[outputs.influxdb]]
      database = "latency"
      urls = [ "http://latency.launtel.net.au:8086" ]
      username = "admin"
      password = "oaW6eghe"
    {% for rows in allrows %}
    [[inputs.ping]]
        urls = [ {{ rows.ipaddr|tojson }} ]
        [inputs.ping.tags]
            name = {{ rows.name|tojson }}
    {% endfor %}

    """
    template = Template(telegraf_config)
    print("Templating Telegraf")
    output = (template.render(allrows=allrows))
    print(output)
    with open('/etc/telegraf/telegraf.conf', 'w') as f:
       f.write(output)
    checksum_current = checksum_start
    db.commit()

    while True:
        print("Checking for new records")
        cursor = db.cursor()
        cursor.execute("checksum table urls")
        checksum_current = cursor.fetchone()
        if checksum_current != checksum_start:
            print("Getting new records")
            cursor.execute("select INET_NTOA(`ipaddr`) as ipaddr, name as name from urls")
            allrows = cursor.fetchall()
            telegraf_config = """
	    # Global Agent Configuration
	    [agent]
	      flush_interval = "15s"
	      interval = "15s"
	    
	    # Output Plugin InfluxDB
	    [[outputs.influxdb]]
	      database = "latency"
	      urls = [ "http://latency.launtel.net.au:8086" ]
	      username = "admin"
	      password = "oaW6eghe"
            {% for rows in allrows %}
            [[inputs.ping]]
                urls = [ {{ rows.ipaddr|tojson }} ]
                [inputs.ping.tags]
                    name = {{ rows.name|tojson }}
            {% endfor %}

            """
            template = Template(telegraf_config)
            print("Templating Telegraf")
            output = (template.render(allrows=allrows))
            print(output)
            with open('/etc/telegraf/telegraf.conf', 'w') as f:
               f.write(output)
            checksum_start = checksum_current
            db.commit()
            print ("Restarting telegraf container")
            client = docker.DockerClient(base_url='unix://run/docker.sock', version='1.41')
            containers = client.containers.list(all=True)
            container = client.containers.get('outbound_latency_dockerized_launtel_telegraf_1')
            container.restart()
            print("Sleeping after new record collection")
            time.sleep(300)
        else:
            print("Nothing to do, sleeping")
            db.commit()
            time.sleep(60)

if __name__ == '__main__':
    main()
