# v61 source build: modern WPE WebKit with Debian glibc, never mix Alpine musl.
FROM debian:sid AS build
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential pkg-config libwpewebkit-2.0-dev ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY web61/headless_probe.c /src/headless_probe.c
RUN cc -O2 -Wall -Wextra -o /usr/local/bin/puppy50-wpe-headless \
    /src/headless_probe.c \
    $(pkg-config --cflags --libs wpe-webkit-2.0 wpe-platform-2.0)

FROM debian:sid AS runtime
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    libwpewebkit-2.0-1 ca-certificates busybox-static util-linux \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/* \
    && useradd -m -u 1000 -s /bin/sh web
COPY --from=build /usr/local/bin/puppy50-wpe-headless /usr/local/bin/puppy50-wpe-headless
COPY wpe_feasibility/interaction.html /usr/share/puppy50wpe/interaction.html
COPY web61/guest_init.sh /sbin/init
RUN chmod 755 /sbin/init \
    && test -x /bin/busybox \
    && test -x /usr/bin/setpriv \
    && test -x /usr/local/bin/puppy50-wpe-headless
ENV WPE_PLATFORM=headless
# This image is only exported to a disposable QEMU root. The QEMU kernel
# and /initrd are supplied separately by the dedicated workflow.
ENTRYPOINT ["/sbin/init"]
