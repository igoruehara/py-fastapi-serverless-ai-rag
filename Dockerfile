FROM public.ecr.aws/lambda/python:3.14

WORKDIR /var/task

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

CMD ["app.lambda_handler.handler"]
