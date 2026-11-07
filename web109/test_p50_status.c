#include <assert.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include "p50-status.c"
int main(void) {
    char dir[]="/tmp/p50-status-test-XXXXXX";
    assert(mkdtemp(dir));
    char ready[256],failed[256];
    assert(snprintf(ready,sizeof(ready),"%s/READY",dir)>0);
    assert(snprintf(failed,sizeof(failed),"%s/FAILED",dir)>0);
    assert(p50_status(dir,getuid())==P50_WAIT);
    int fd=open(ready,O_CREAT|O_WRONLY,0600);assert(fd>=0);close(fd);
    assert(p50_status(dir,getuid())==P50_READY);
    assert(chmod(ready,0666)==0);assert(p50_status(dir,getuid())==P50_WAIT);
    assert(chmod(ready,0600)==0);assert(p50_status(dir,getuid())==P50_READY);
    fd=open(failed,O_CREAT|O_WRONLY,0600);assert(fd>=0);close(fd);
    assert(p50_status(dir,getuid())==P50_FAILED);
    unlink(ready);assert(p50_status(dir,getuid())==P50_FAILED);
    unlink(failed);assert(p50_status(dir,getuid())==P50_WAIT);
    rmdir(dir);
    puts("Status defaults to keep-USB; failure overrides ready.");
    return 0;
}
