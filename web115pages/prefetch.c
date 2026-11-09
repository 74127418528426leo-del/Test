#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

/* Test-only: bounded, read-only warming of selected regular file ranges. */
int main(int argc,char **argv){
    if(argc!=2){fprintf(stderr,"usage: prefetch PLAN\n");return 2;}
    FILE *plan=fopen(argv[1],"r");if(!plan){perror("plan");return 3;}
    char *line=NULL;size_t cap=0;ssize_t got;int fd=-1,files=0,rc=0;
    unsigned long long size=0,page=0,last_end=0,total=0;char path[4096],extra,buf[131072];
    while((got=getline(&line,&cap,plan))>=0){
        if(got>8192){rc=4;break;}
        while(got>0&&(line[got-1]=='\n'||line[got-1]=='\r'))line[--got]='\0';
        if(strncmp(line,"P50_FILE\t",9)==0){
            if(sscanf(line,"P50_FILE\t%4095[^\t]\t%llu\t%llu%c",path,&size,&page,&extra)!=3||path[0]!='/'||size==0||size>2147483648ULL||page!=(unsigned long long)sysconf(_SC_PAGESIZE)||files>=3){rc=4;break;}
            if(fd>=0)close(fd);
            fd=open(path,O_RDONLY|O_CLOEXEC|O_NOFOLLOW);struct stat st;
            if(fd<0||fstat(fd,&st)||!S_ISREG(st.st_mode)||(unsigned long long)st.st_size!=size){rc=4;break;}
            files++;last_end=0;
        }else if(strncmp(line,"RANGE\t",6)==0){
            unsigned long long start,len;
            if(fd<0||sscanf(line,"RANGE\t%llu\t%llu%c",&start,&len,&extra)!=2||len==0||start%page||len%page||start<last_end||start>size||len>((size+page-1)/page)*page-start){rc=4;break;}
            last_end=start+len;unsigned long long end=last_end<size?last_end:size;
            while(start<end){
                size_t want=(end-start)>sizeof(buf)?sizeof(buf):(size_t)(end-start);
                ssize_t n=pread(fd,buf,want,(off_t)start);
                if(n<0&&errno==EINTR)continue;
                if(n<=0){rc=5;break;}
                start+=(unsigned long long)n;total+=(unsigned long long)n;
                if(total>536870912ULL){rc=4;break;}
            }
            if(rc)break;
        }else{rc=4;break;}
    }
    if(ferror(plan)||!files)rc=4;
    if(fd>=0)close(fd);
    free(line);fclose(plan);
    if(rc){fprintf(stderr,"prefetch refused or could not read the plan\n");return rc;}
    printf("P50_PREFETCH_BYTES %llu\n",total);return 0;
}
