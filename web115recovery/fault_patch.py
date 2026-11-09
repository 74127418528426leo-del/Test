#!/usr/bin/env python3
"""Inject a diagnostic resume error only after a real extra-mapper suspend."""
from pathlib import Path
import argparse

HELPER_MARKER='''    p50_init_request(&req,name);
    if (call(fd,DM_DEV_SUSPEND,&req)==0) return 0;
    /* A failed resume'''
HELPER_INJECTION='''    p50_init_request(&req,name);
    /* Test only: the real target is suspended; simulate the first resume
       returning EIO, then exercise actual DM_TABLE_CLEAR and resume ioctls. */
    fprintf(stderr,"P50_TEST_POST_SUSPEND_INJECTED\\n");
    errno=EIO;
    /* A failed resume'''
HELPER_RESULT='''    int resume_result=call(fd,DM_DEV_SUSPEND,&req);
    return (clear_result==0 && resume_result==0) ? 2 : 3;'''
HELPER_REPORT='''    int resume_result=call(fd,DM_DEV_SUSPEND,&req);
    fprintf(stderr,"P50_TEST_REAL_RECOVERY clear=%d resume=%d\\n",clear_result,resume_result);
    return (clear_result==0 && resume_result==0) ? 2 : 3;'''
MIGRATE_MARKER="/run/p50-stage/tools/p50-switch-extra || fail 'cannot complete extra mapper switch'"
MIGRATE_INJECTION='''if /run/p50-stage/tools/p50-switch-extra; then
    fail 'fault injection unexpectedly succeeded'
fi
"$B" grep -Fq 'P50_TEST_POST_SUSPEND_INJECTED' /run/p50-stage/migration.log || fail 'suspend injection not observed'
"$B" grep -Fq 'P50_TEST_REAL_RECOVERY clear=0 resume=0' /run/p50-stage/migration.log || fail 'kernel recovery did not succeed'
emit P50_TEST_REAL_RECOVERY_RETURNED_ZERO
extra_restored_table=$("$DM" table p50-staged-extra) || fail 'cannot inspect recovered extra table'
[ "$extra_restored_table" = "$extra_old_table" ] || fail 'extra original table was not restored'
emit P50_TEST_EXTRA_TABLE_RESTORED
fail 'injected post-suspend failure'
'''

def replace_once(text,old,new):
    if text.count(old)!=1:raise ValueError('Unexpected diagnostic input')
    return text.replace(old,new,1)

def patch_helper(source):
    if 'P50_TEST_POST_SUSPEND_INJECTED' in source:raise ValueError('Already patched helper')
    return replace_once(replace_once(source,HELPER_MARKER,HELPER_INJECTION),HELPER_RESULT,HELPER_REPORT)

def patch_migration(source):
    if 'P50_TEST_EXTRA_TABLE_RESTORED' in source:raise ValueError('Already patched migration')
    return replace_once(source,MIGRATE_MARKER,MIGRATE_INJECTION)

def main():
    p=argparse.ArgumentParser();p.add_argument('helper',type=Path);p.add_argument('migration',type=Path);args=p.parse_args()
    for path in (args.helper,args.migration):
        if path.is_symlink() or not path.is_file():raise ValueError('Expected isolated regular file')
    helper=patch_helper(args.helper.read_text());migration=patch_migration(args.migration.read_text())
    args.helper.write_text(helper);args.migration.write_text(migration)

if __name__=='__main__':main()
