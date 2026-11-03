# Stage compiler files never ship inside the runtime browser closure.
FROM debian:sid AS build
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential pkg-config libwpewebkit-2.0-dev ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY headless_probe.c /src/headless_probe.c
RUN cc -O2 -Wall -Wextra -o /usr/local/bin/puppy50-wpe-headless \
    /src/headless_probe.c \
    $(pkg-config --cflags --libs wpe-webkit-2.0 wpe-platform-2.0)

FROM debian:sid AS runtime
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    libwpewebkit-2.0-1 ca-certificates \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/* \
    && useradd -m -u 1000 -s /usr/sbin/nologin web
COPY --from=build /usr/local/bin/puppy50-wpe-headless /usr/local/bin/puppy50-wpe-headless
COPY interaction.html /usr/share/puppy50wpe/interaction.html
USER 1000:1000
ENV WPE_PLATFORM=headless
ENTRYPOINT ["/usr/local/bin/puppy50-wpe-headless"]
