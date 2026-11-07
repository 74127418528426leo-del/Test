#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

enum p50_state { P50_WAIT, P50_READY, P50_FAILED };
static enum p50_state p50_status(const char *dir, uid_t owner) {
    char ready[4096],failed[4096]; struct stat st;
    int a=snprintf(ready,sizeof(ready),"%s/READY",dir);
    int b=snprintf(failed,sizeof(failed),"%s/FAILED",dir);
    if (a<0 || b<0 || (size_t)a>=sizeof(ready) || (size_t)b>=sizeof(failed)) return P50_WAIT;
    if (lstat(failed,&st)==0) return P50_FAILED;
    if (lstat(ready,&st)==0 && S_ISREG(st.st_mode) && st.st_uid==owner && !(st.st_mode & 0022)) return P50_READY;
    return P50_WAIT;
}
#ifndef P50_STATUS_STATE_ONLY
#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <X11/Xatom.h>
#include <string.h>

static unsigned long color(Display *d, int screen, const char *name) {
    XColor exact,screen_color;
    if (!XAllocNamedColor(d,DefaultColormap(d,screen),name,&screen_color,&exact)) return BlackPixel(d,screen);
    return screen_color.pixel;
}
int main(void) {
    Display *d=XOpenDisplay(NULL);
    if (!d) return 1;
    int screen=DefaultScreen(d), width=455, height=34;
    int x=DisplayWidth(d,screen)-width-8, y=DisplayHeight(d,screen)-height-34;
    if (x<0) x=0;
    if (y<0) y=0;
    XSetWindowAttributes attrs={0};attrs.override_redirect=True;
    Window w=XCreateWindow(d,RootWindow(d,screen),x,y,(unsigned)width,(unsigned)height,1,
        CopyFromParent,InputOutput,CopyFromParent,CWOverrideRedirect,&attrs);
    XSelectInput(d,w,ExposureMask|ButtonPressMask);
    XStoreName(d,w,"Puppy50 RAM status");
    GC gc=XCreateGC(d,w,0,NULL);
    XFontStruct *font=XLoadQueryFont(d,"9x15");
    if (!font) font=XLoadQueryFont(d,"fixed");
    if (font) XSetFont(d,gc,font->fid);
    unsigned long amber=color(d,screen,"#e8b84a"),green=color(d,screen,"#66dca0"),red=color(d,screen,"#ff8a80"),ink=color(d,screen,"#111c26");
    XMapRaised(d,w);
    for (;;) {
        enum p50_state state=p50_status("/run/p50-stage",0);
        while (XPending(d)) {
            XEvent e;XNextEvent(d,&e);
            if (e.type==ButtonPress && state==P50_READY) goto finish;
        }
        unsigned long bg=state==P50_READY?green:state==P50_FAILED?red:amber;
        const char *text=state==P50_READY?"RAM READY - USB may be removed (click to close)":
                         state==P50_FAILED?"RAM COPY FAILED - KEEP USB CONNECTED":
                         "KEEP USB CONNECTED - preparing RAM";
        XSetForeground(d,gc,bg);XFillRectangle(d,w,gc,0,0,(unsigned)width,(unsigned)height);
        XSetForeground(d,gc,ink);XDrawString(d,w,gc,8,22,text,(int)strlen(text));
        XRaiseWindow(d,w);XFlush(d);sleep(1);
    }
finish:
    if (font) XFreeFont(d,font);
    XFreeGC(d,gc);XDestroyWindow(d,w);XCloseDisplay(d);return 0;
}
#endif
