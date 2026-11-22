/* Warm only measured parts of the compressed live root in its normal page cache. */
#define _GNU_SOURCE
#define _FILE_OFFSET_BITS 64
#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

#define READ_BUDGET (UINT64_C(128) * 1024 * 1024)

static int warm_region(int fd, uint64_t offset, uint64_t length)
{
    static char buffer[256 * 1024];
    while (length) {
        size_t next = length < sizeof buffer ? (size_t)length : sizeof buffer;
        ssize_t n = pread(fd, buffer, next, (off_t)offset);
        if (n < 0 && errno == EINTR)
            continue;
        if (n <= 0)
            return -1;
        offset += (uint64_t)n;
        length -= (uint64_t)n;
    }
    return 0;
}

static int warm(int fd, FILE *plan)
{
    struct stat root;
    char magic[20];
    uint64_t size, start, length, previous_end = 0, total = 0;
    if (fstat(fd, &root) || !S_ISREG(root.st_mode) || root.st_size < 0 ||
        fscanf(plan, "%19s %" SCNu64, magic, &size) != 2 ||
        strcmp(magic, "P50_READS_V1") || size != (uint64_t)root.st_size)
        return 1;

    /* The plan already includes the chosen readahead. Avoid fetching the gaps. */
    (void)posix_fadvise(fd, 0, 0, POSIX_FADV_RANDOM);
    int fields;
    while ((fields = fscanf(plan, "%" SCNu64 " %" SCNu64, &start, &length)) == 2) {
        if (!length || (start % 4096) || (length % 4096) || start < previous_end ||
            start > size || length > size - start || length > READ_BUDGET - total)
            return 1;
        if (warm_region(fd, start, length) != 0)
            return 1;
        previous_end = start + length;
        total += length;
    }
    return fields != EOF || ferror(plan) || total == 0;
}

int main(int argc, char **argv)
{
    if (argc != 3) {
        fputs("usage: warm-root SQUASHFS PLAN\n", stderr);
        return 2;
    }
    int fd = open(argv[1], O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
    if (fd < 0)
        return 1;
    FILE *plan = fopen(argv[2], "r");
    if (!plan) {
        close(fd);
        return 1;
    }
    errno = 0;
    if (nice(5) == -1 && errno != 0)
        perror("warm-root nice");
    int result = warm(fd, plan);
    fclose(plan);
    close(fd);
    return result;
}
