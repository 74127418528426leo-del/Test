/* Create the local :0 X11 authorization record in the volatile live home. */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <sys/random.h>
#include <unistd.h>

static unsigned char *field(unsigned char *out, const void *data, size_t size)
{
    *out++ = (unsigned char)(size >> 8);
    *out++ = (unsigned char)size;
    memcpy(out, data, size);
    return out + size;
}

int main(int argc, char **argv)
{
    const char protocol[] = "MIT-MAGIC-COOKIE-1";
    unsigned char cookie[16];
    char host[256];
    unsigned char record[2 + 8 + sizeof(host) + 1 + sizeof(protocol) + sizeof(cookie)];
    if (argc != 2) {
        fputs("usage: p50-write-xauthority FILE\n", stderr);
        return 2;
    }
    if (gethostname(host, sizeof(host)) != 0 || !memchr(host, '\0', sizeof(host))) {
        perror("gethostname");
        return 1;
    }
    ssize_t generated;
    do {
        generated = getrandom(cookie, sizeof(cookie), 0);
    } while (generated < 0 && errno == EINTR);
    if (generated != sizeof(cookie)) {
        fputs("Cannot generate a complete X11 cookie\n", stderr);
        return 1;
    }
    record[0] = 1;
    record[1] = 0; /* X11 FamilyLocal (256), in network order. */
    unsigned char *end = field(record + 2, host, strlen(host));
    end = field(end, "0", 1);
    end = field(end, protocol, sizeof(protocol) - 1);
    end = field(end, cookie, sizeof(cookie));
    size_t remaining = (size_t)(end - record);
    int fd = open(argv[1], O_WRONLY | O_CLOEXEC | O_CREAT | O_EXCL | O_NOFOLLOW, 0600);
    if (fd < 0) {
        perror("open Xauthority");
        return 1;
    }
    unsigned char *next = record;
    while (remaining) {
        ssize_t size = write(fd, next, remaining);
        if (size < 0 && errno == EINTR)
            continue;
        if (size <= 0) {
            perror("write Xauthority");
            close(fd);
            unlink(argv[1]);
            return 1;
        }
        next += size;
        remaining -= (size_t)size;
    }
    if (close(fd) != 0) {
        perror("close Xauthority");
        unlink(argv[1]);
        return 1;
    }
    return 0;
}
