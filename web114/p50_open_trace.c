#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <poll.h>
#include <stdint.h>
#include <stddef.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/fanotify.h>
#include <time.h>
#include <unistd.h>

/* Non-blocking notification only: never decides access permissions. */
#define MAX_EVENTS 30000
static int interesting(const char *p) {
    const char *prefixes[]={"/usr/","/etc/","/bin/","/sbin/","/lib/","/lib64/",NULL};
    for(int i=0;prefixes[i];i++)if(strncmp(p,prefixes[i],strlen(prefixes[i]))==0)return 1;
    return 0;
}
static unsigned long long monotonic_us(void) {
    struct timespec t;
    if(clock_gettime(CLOCK_BOOTTIME,&t)!=0) return 0;
    return (unsigned long long)t.tv_sec*1000000ULL+(unsigned long long)t.tv_nsec/1000;
}
static int notify_ready(void) {
    const char *name=getenv("NOTIFY_SOCKET");
    if(!name || !*name) return 0;
    size_t n=strlen(name);
    if(n>=sizeof(((struct sockaddr_un *)0)->sun_path)) return -1;
    struct sockaddr_un addr={.sun_family=AF_UNIX};
    memcpy(addr.sun_path,name,n+1);
    if(addr.sun_path[0]=='@') addr.sun_path[0]='\0';
    int fd=socket(AF_UNIX,SOCK_DGRAM|SOCK_CLOEXEC,0);
    if(fd<0) return -1;
    const char msg[]="READY=1\nSTATUS=Tracing open notifications";
    socklen_t length=(socklen_t)(offsetof(struct sockaddr_un,sun_path)+n+(name[0]=='@'?0:1));
    int rc=sendto(fd,msg,sizeof(msg)-1,0,(struct sockaddr *)&addr,length);
    close(fd);return rc==(int)(sizeof(msg)-1)?0:-1;
}
int main(int argc,char **argv) {
    if(argc!=4) { fprintf(stderr,"usage: p50-open-trace OUTPUT SECONDS MOUNT\n"); return 2; }
    char *end=NULL;long seconds=strtol(argv[2],&end,10);
    if(!end || *end || seconds<1 || seconds>120) return 2;
    int outfd=open(argv[1],O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,0600);
    if(outfd<0) {perror("open output");return 3;}
    FILE *out=fdopen(outfd,"w");if(!out){perror("fdopen");close(outfd);return 3;}
    setvbuf(out,NULL,_IOFBF,1024*1024);
    fprintf(out,"P50_ACCESS_TRACE_V1\n");
    int fan=fanotify_init(FAN_CLASS_NOTIF|FAN_NONBLOCK|FAN_CLOEXEC,O_RDONLY|O_LARGEFILE|O_CLOEXEC);
    if(fan<0){fprintf(out,"P50_ACCESS_ERROR fanotify_init %d\n",errno);fclose(out);return 4;}
    uint64_t mask=FAN_OPEN|FAN_OPEN_EXEC;
    if(fanotify_mark(fan,FAN_MARK_ADD|FAN_MARK_MOUNT,mask,AT_FDCWD,argv[3])<0){fprintf(out,"P50_ACCESS_ERROR fanotify_mark %d\n",errno);close(fan);fclose(out);return 5;}
    fprintf(out,"P50_ACCESS_MARK_OK\n");
    if(notify_ready()<0){fprintf(out,"P50_ACCESS_ERROR notify_ready\n");close(fan);fclose(out);return 8;}
    unsigned long long deadline=monotonic_us()+(unsigned long long)seconds*1000000ULL;
    unsigned int count=0,overflow=0,capped=0;int removed=0,failed=0;
    char buf[65536] __attribute__((aligned(8)));
    while(1){
        if(!removed && monotonic_us()>=deadline){
            if(fanotify_mark(fan,FAN_MARK_REMOVE|FAN_MARK_MOUNT,mask,AT_FDCWD,argv[3])<0) failed=1;
            removed=1;
        }
        struct pollfd pfd={.fd=fan,.events=POLLIN};
        int pr=poll(&pfd,1,removed?0:100);
        if(pr<0){if(errno==EINTR)continue;failed=1;break;}
        if(pr==0){if(removed)break;continue;}
        ssize_t len=read(fan,buf,sizeof(buf));
        if(len<0){if(errno==EINTR || errno==EAGAIN)continue;failed=1;break;}
        if(len==0){failed=1;break;}
        struct fanotify_event_metadata *m=(struct fanotify_event_metadata *)buf;
        for(;FAN_EVENT_OK(m,len);m=FAN_EVENT_NEXT(m,len)){
            if(m->vers!=FANOTIFY_METADATA_VERSION){failed=1;break;}
            if(m->mask & FAN_Q_OVERFLOW){overflow=1;continue;}
            if(m->fd<0)continue;
            char fdpath[64],path[PATH_MAX+1];
            snprintf(fdpath,sizeof(fdpath),"/proc/self/fd/%d",m->fd);
            ssize_t n=readlink(fdpath,path,PATH_MAX);
            if(n>0 && n<PATH_MAX){
                path[n]='\0';
                if(interesting(path) && !strchr(path,'\n') && !strchr(path,'\t')){
                    if(count<MAX_EVENTS){
                        fprintf(out,"EV\t%llu\t%d\t%s\n",monotonic_us(),(int)m->pid,path);count++;
                    }else capped=1;
                }
            }
            close(m->fd);
        }
        if(failed)break;
    }
    close(fan);
    fprintf(out,"P50_ACCESS_END\t%u\t%u\t%u\n",count,overflow,capped || failed);
    if(fclose(out)!=0)return 7;
    return overflow || capped || failed ? 6 : 0;
}
