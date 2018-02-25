FROM arwineap/docker-ubuntu-python3.6

RUN add-apt-repository 'deb http://apt.postgresql.org/pub/repos/apt/ xenial-pgdg main'

RUN wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | \
    sudo apt-key add - \
    sudo apt-get update

RUN apt-get install postgres-10

RUN service postgresql restart

RUN sudo -i -u postgres
RUN psql -c "CREATE USER searcher WITH PASSWORD 'searcher' SUPERUSER"

RUN exit



