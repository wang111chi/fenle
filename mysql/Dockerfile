FROM mysql/mysql-server:5.7

COPY mysql/my.cnf /etc/my.cnf
COPY docs/tables/* /docker-entrypoint-initdb.d/
