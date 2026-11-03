#include <wpe/webkit.h>
#include <glib.h>
#include <stdio.h>
#include <stdlib.h>

static int loaded = 0;
static gboolean finish_timeout(gpointer data) {
    GMainLoop *loop = (GMainLoop *)data;
    printf("PUPPY50_WPE_HEADLESS_TEST_END loaded=%d\n", loaded);
    fflush(stdout);
    g_main_loop_quit(loop);
    return G_SOURCE_REMOVE;
}

static void on_load(WebKitWebView *view, WebKitLoadEvent event, gpointer data) {
    if (event != WEBKIT_LOAD_FINISHED) return;
    const gchar *uri = webkit_web_view_get_uri(view);
    if (uri && g_str_has_prefix(uri, "file:///usr/share/puppy50wpe/")) {
        loaded = 1;
        printf("PUPPY50_WPE_HEADLESS_LOCAL_LOAD_FINISHED\n");
    } else {
        printf("PUPPY50_WPE_HEADLESS_UNEXPECTED_URI\n");
    }
    fflush(stdout);
}
static gboolean on_failed(WebKitWebView *view, WebKitLoadEvent event, gchar *uri,
                      GError *error, gpointer data) {
    printf("PUPPY50_WPE_LOAD_FAILED code=%d message=%s\n",
           error ? error->code : -1, error ? error->message : "unknown");
    fflush(stdout);
    return FALSE;
}
int main(void) {
    GMainLoop *loop = g_main_loop_new(NULL, FALSE);
    WebKitWebView *view = WEBKIT_WEB_VIEW(g_object_new(WEBKIT_TYPE_WEB_VIEW, NULL));
    if (!view) {
        fprintf(stderr, "PUPPY50_WPE_VIEW_CREATE_FAILED\n");
        return 2;
    }
    g_signal_connect(view, "load-changed", G_CALLBACK(on_load), NULL);
    g_signal_connect(view, "load-failed", G_CALLBACK(on_failed), NULL);
    puts("PUPPY50_WPE_HEADLESS_BEGIN");
    fflush(stdout);
    webkit_web_view_load_uri(view, "file:///usr/share/puppy50wpe/interaction.html");
    /* Hold the browser process family for memory sampling. This only proves
       local headless loading, NOT pixels, input, HTTPS or graphics. */
    g_timeout_add_seconds(38, finish_timeout, loop);
    g_main_loop_run(loop);
    g_object_unref(view);
    g_main_loop_unref(loop);
    return loaded ? 0 : 3;
}
