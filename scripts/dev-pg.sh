#!/usr/bin/env bash
# Sobe um PostgreSQL real e descartável para desenvolvimento/testes (sem Docker).
# Uso: scripts/dev-pg.sh start|stop|url      (porta 54329, dados em $TF_PGDATA)
set -euo pipefail
PGBIN=${PGBIN:-$(ls -d /usr/lib/postgresql/*/bin | sort -V | tail -1)}
DATA=${TF_PGDATA:-/tmp/tf-pgdata}
PORT=${TF_PGPORT:-54329}
RUNAS=()
if [ "$(id -u)" = "0" ]; then
  id -u tfpg >/dev/null 2>&1 || useradd -m -s /bin/bash tfpg
  mkdir -p "$DATA" && chown tfpg "$DATA"
  RUNAS=(runuser -u tfpg --)
fi
case "${1:-start}" in
  start)
    if [ ! -f "$DATA/PG_VERSION" ]; then
      "${RUNAS[@]}" "$PGBIN/initdb" -D "$DATA" -U postgres --auth=trust -E UTF8 >/dev/null
    fi
    if ! "${RUNAS[@]}" "$PGBIN/pg_ctl" -D "$DATA" status >/dev/null 2>&1; then
      "${RUNAS[@]}" "$PGBIN/pg_ctl" -D "$DATA" -o "-p $PORT -k /tmp -c listen_addresses=127.0.0.1" -l "$DATA/server.log" -w start >/dev/null
    fi
    "$PGBIN/psql" -h 127.0.0.1 -p $PORT -U postgres -tc "select 1 from pg_database where datname='talentflow_test'" | grep -q 1 \
      || "$PGBIN/createdb" -h 127.0.0.1 -p $PORT -U postgres talentflow_test
    echo "postgresql+psycopg://postgres@127.0.0.1:$PORT/talentflow_test" ;;
  stop) "${RUNAS[@]}" "$PGBIN/pg_ctl" -D "$DATA" -m fast stop ;;
  url)  echo "postgresql+psycopg://postgres@127.0.0.1:$PORT/talentflow_test" ;;
esac
