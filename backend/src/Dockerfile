FROM python:3.9

WORKDIR /usr/src/app
RUN pip install --upgrade pip
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8080

COPY . .

CMD ["python", "main.py"]