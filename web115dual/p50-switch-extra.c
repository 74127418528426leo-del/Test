#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <fcntl.h>
#include <linux/dm-ioctl.h>
#include <signal.h>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>

typedef int (*p50_ioctl_fn)(int, unsigned long, struct dm_ioctl *);
static void p50_init_request(struct dm_ioctl *req, const char *name) {
    memset(req,0,sizeof(*req));
    req->version[0]=DM_VERSION_MAJOR;
    req->version[1]=DM_VERSION_MINOR;
    req->version[2]=DM_VERSION_PATCHLEVEL;
    req->data_size=sizeof(*req);
    req->data_start=sizeof(*req);
    memcpy(req->name,name,strlen(name)+1);
}
int p50_switch_mapping(int fd, p50_ioctl_fn call, const char *name) {
    struct dm_ioctl req;
    if (!call || !name || strcmp(name,"p50-staged-extra")!=0) { errno=EINVAL; return 1; }
    p50_init_request(&req,name);
    if (call(fd,DM_DEV_STATUS,&req)<0 || !(req.flags & DM_INACTIVE_PRESENT_FLAG)) return 1;
    p50_init_request(&req,name);
    req.flags=DM_SUSPEND_FLAG;
    if (call(fd,DM_DEV_SUSPEND,&req)<0) return 1;
    p50_init_request(&req,name);
    if (call(fd,DM_DEV_SUSPEND,&req)==0) return 0;
    /* A failed resume must never be mistaken for readiness. Try to restore
       the old mapping, and report failure regardless of recovery outcome. */
    p50_init_request(&req,name);
    int clear_result=call(fd,DM_TABLE_CLEAR,&req);
    p50_init_request(&req,name);
    int resume_result=call(fd,DM_DEV_SUSPEND,&req);
    return (clear_result==0 && resume_result==0) ? 2 : 3;
}
#ifndef P50_SWITCH_NO_MAIN
static int p50_real_ioctl(int fd, unsigned long request, struct dm_ioctl *arg) {
    return ioctl(fd,request,arg);
}
int main(int argc, char **argv) {
    (void)argv;
    if (argc!=1 || geteuid()!=0) { fprintf(stderr,"expected root and no arguments\n"); return 64; }
    sigset_t blocked;
    if (sigfillset(&blocked)!=0 || sigprocmask(SIG_BLOCK,&blocked,NULL)!=0) { perror("sigprocmask"); return 1; }
    int fd=open("/dev/mapper/control",O_RDWR|O_CLOEXEC);
    if (fd<0) { perror("device mapper control"); return 1; }
    int result=p50_switch_mapping(fd,p50_real_ioctl,"p50-staged-extra");
    if (result!=0) fprintf(stderr,"mapper switch failed: %d (%s)\n",result,strerror(errno));
    close(fd);
    return result;
}
#endif
