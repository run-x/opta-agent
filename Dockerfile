FROM python:3.8-slim
# TODO Does this need to be python specific? version needs to be templatized?
WORKDIR /home/app
RUN pip install pipenv

COPY Pipfile Pipfile.lock ./
RUN pipenv install --deploy

COPY . /home/app

CMD ["bash", "startup.sh" ]