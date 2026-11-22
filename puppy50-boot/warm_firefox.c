/* Warm the first 128 MiB of libxul in the kernel's normal file cache. */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <unistd.h>

int main(int argc, char **argv)
{
    static unsigned char bytes[256 * 1024];
    size_t remaining = 128 * 1024 * 1024;
    if (argc != 2) {
        fputs("usage: p50-warm-firefox LIBXUL\n", stderr);
        return 2;
    }
    errno = 0;
    if (nice(5) == -1 && errno != 0) {
        perror("nice");
        return 1;
    }
    int fd = open(argv[1], O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
    if (fd < 0) {
        perror("open Firefox library");
        return 1;
    }
    posix_fadvise(fd, 0, remaining, POSIX_FADV_SEQUENTIAL);
    while (remaining > 0) {
        size_t request = remaining < sizeof(bytes) ? remaining : sizeof(bytes);
        ssize_t count = read(fd, bytes, request);
        if (count < 0 && errno == EINTR)
            continue;
        if (count <= 0) {
            fputs("Cannot read the expected Firefox library region\n", stderr);
            close(fd);
            return 1;
        }
        remaining -= (size_t)count;
    }
    return close(fd) != 0;
}
