FROM python:3.11.0
WORKDIR /engie
COPY requirements.txt .
COPY ./main.py .
COPY ./meritplan.py .
RUN pip install -r requirements.txt 
CMD ["python", "main.py"]
EXPOSE 8888