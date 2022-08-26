FROM python:3.10.6-alpine

WORKDIR /source

COPY . .

RUN pip install -r requirements.txt
CMD ["python", "main.py"]