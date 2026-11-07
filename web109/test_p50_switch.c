#include <assert.h>
#include <errno.h>
#include <linux/dm-ioctl.h>
#include <stdio.h>
#include <string.h>
#include "p50-switch.c"

static int step, scenario;
static int mock_ioctl(int fd, unsigned long request, struct dm_ioctl *io) {
    (void)fd;
    assert(strcmp(io->name, "p50-staged-root") == 0);
    ++step;
    if (step == 1) {
        assert(request == DM_DEV_STATUS);
        if (scenario != 5) io->flags |= DM_INACTIVE_PRESENT_FLAG;
        return 0;
    }
    if (step == 2) {
        assert(request == DM_DEV_SUSPEND && (io->flags & DM_SUSPEND_FLAG));
        if (scenario == 1) { errno=EIO; return -1; }
        return 0;
    }
    if (step == 3) {
        assert(request == DM_DEV_SUSPEND && !(io->flags & DM_SUSPEND_FLAG));
        if (scenario >= 2) { errno=EIO; return -1; }
        return 0;
    }
    if (step == 4) {
        assert(request == DM_TABLE_CLEAR);
        if (scenario == 3) { errno=EIO; return -1; }
        return 0;
    }
    if (step == 5) {
        assert(request == DM_DEV_SUSPEND && !(io->flags & DM_SUSPEND_FLAG));
        if (scenario == 4) { errno=EIO; return -1; }
        return 0;
    }
    assert(0); return -1;
}
int main(void) {
    scenario=0;step=0;assert(p50_switch_mapping(3,mock_ioctl,"p50-staged-root")==0);assert(step==3);
    scenario=1;step=0;assert(p50_switch_mapping(3,mock_ioctl,"p50-staged-root")!=0);assert(step==2);
    scenario=2;step=0;assert(p50_switch_mapping(3,mock_ioctl,"p50-staged-root")!=0);assert(step==5);
    scenario=3;step=0;assert(p50_switch_mapping(3,mock_ioctl,"p50-staged-root")!=0);assert(step==5);
    scenario=4;step=0;assert(p50_switch_mapping(3,mock_ioctl,"p50-staged-root")!=0);assert(step==5);
    scenario=5;step=0;assert(p50_switch_mapping(3,mock_ioctl,"p50-staged-root")!=0);assert(step==1);
    scenario=0;step=0;assert(p50_switch_mapping(3,mock_ioctl,"other-device")!=0);assert(step==0);
    puts("Inactive-table check, suspend/resume, recovery, and target restrictions passed.");
    return 0;
}
