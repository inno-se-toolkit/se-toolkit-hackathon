FROM ${REGISTRY_PREFIX}caddy:2-building AS builder

ARG PLUGINS="filemanager browse jsonpath"
RUN xcaddy build ${PLUGINS} \
    --with github.com/abiosoft/caddy-exec \
    --with github.com/qntst/fp-caddy-exec

FROM caddy:latest-alpine AS runtime
COPY --from=builder /usr/bin/caddy /usr/bin/caddy
