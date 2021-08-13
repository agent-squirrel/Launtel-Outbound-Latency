FROM python:3

WORKDIR /usr/src/gentelegraf
RUN mkdir -p /etc/telegraf/

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY gentelegraf.py .

CMD [ "python", "-u", "./gentelegraf.py" ]
