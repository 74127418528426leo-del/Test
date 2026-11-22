/* Observe the first mapped Firefox client before starting the desktop accessories. */
#define _POSIX_C_SOURCE 200809L
#include <X11/Xatom.h>
#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <poll.h>
#include <strings.h>
#include <time.h>

static int ignore_disappearing_window(Display *dpy, XErrorEvent *error)
{
    (void)dpy;
    (void)error;
    return 0;
}

static long milliseconds(void)
{
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0)
        return -1;
    return ts.tv_sec * 1000L + ts.tv_nsec / 1000000L;
}

static int has_browser(Display *dpy, Window root, Atom clients)
{
    Atom type;
    int format;
    unsigned long count, remainder;
    unsigned char *data = NULL;
    if (XGetWindowProperty(dpy, root, clients, 0, 128, False, XA_WINDOW, &type, &format,
                           &count, &remainder, &data) != Success)
        return 0;
    int found = 0;
    if (data && type == XA_WINDOW && format == 32) {
        Window *windows = (Window *)data;
        for (unsigned long i = 0; i < count && !found; ++i) {
            XWindowAttributes window;
            XClassHint hint = {0};
            if (XGetWindowAttributes(dpy, windows[i], &window) && window.map_state == IsViewable
                && !window.override_redirect && XGetClassHint(dpy, windows[i], &hint)) {
                found = hint.res_class && (!strcasecmp(hint.res_class, "firefox-esr") ||
                                           !strcasecmp(hint.res_class, "firefox"));
                if (hint.res_name) XFree(hint.res_name);
                if (hint.res_class) XFree(hint.res_class);
            }
        }
    }
    if (data) XFree(data);
    return found;
}

int main(void)
{
    Display *dpy = XOpenDisplay(NULL);
    if (!dpy) return 1;
    XSetErrorHandler(ignore_disappearing_window);
    Window root = DefaultRootWindow(dpy);
    Atom clients = XInternAtom(dpy, "_NET_CLIENT_LIST", False);
    XSelectInput(dpy, root, PropertyChangeMask);
    struct pollfd input = {.fd = ConnectionNumber(dpy), .events = POLLIN};
    long start = milliseconds();
    int ready = 0;
    while (start >= 0 && milliseconds() - start < 3500) {
        if (has_browser(dpy, root, clients)) {
            ready = 1;
            break;
        }
        while (XPending(dpy)) {
            XEvent event;
            XNextEvent(dpy, &event);
        }
        if (poll(&input, 1, 100) < 0)
            break;
    }
    XCloseDisplay(dpy);
    return ready ? 0 : 1;
}
