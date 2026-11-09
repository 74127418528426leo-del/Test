#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>

/* mincore reports page-cache residency without deliberately reading file data. */
int main(int argc,char **argv) {
    if(argc!=2){fprintf(stderr,"usage: resident FILE\n");return 2;}
    int fd=open(argv[1],O_RDONLY|O_CLOEXEC|O_NOFOLLOW);
    if(fd<0){perror("open");return 3;}
    struct stat st;
    if(fstat(fd,&st)||!S_ISREG(st.st_mode)||st.st_size<=0){fprintf(stderr,"bad file\n");close(fd);return 4;}
    long page=sysconf(_SC_PAGESIZE);
    if(page<=0||(uint64_t)st.st_size>SIZE_MAX-(size_t)page){close(fd);return 4;}
    size_t length=(size_t)st.st_size, n=(length+(size_t)page-1)/(size_t)page;
    void *m=mmap(NULL,length,PROT_READ,MAP_SHARED,fd,0);
    if(m==MAP_FAILED){perror("mmap");close(fd);return 5;}
    unsigned char *v=calloc(n,1);
    if(!v){perror("calloc");munmap(m,length);close(fd);return 5;}
    if(mincore(m,length,v)){perror("mincore");free(v);munmap(m,length);close(fd);return 6;}
    printf("P50_FILE\t%s\t%zu\t%ld\n",argv[1],length,page);
    for(size_t i=0;i<n;){
        if(!(v[i]&1)){i++;continue;}
        size_t first=i;while(i<n && (v[i]&1))i++;
        printf("RANGE\t%zu\t%zu\n",first*(size_t)page,(i-first)*(size_t)page);
    }
    free(v);munmap(m,length);close(fd);return ferror(stdout)?7:0;
}
