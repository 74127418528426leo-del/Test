/* Puppy50 v97 research: minimal WPEPlatform 2.54 headless browser
 * Actual JS engine eval and in-page DOM result; sandbox and TLS unchanged.
 * Headless test != working graphical browser or RAM-only OS.
 */
#include <glib.h>
#include <wpe/webkit.h>
#include <jsc/jsc.h>
#include <stdio.h>
#include <stdlib.h>

typedef struct {
  GMainLoop *loop;
  WebKitWebView *view;
  gboolean eval_submitted;
} P50App;

static void finished(GObject *source, GAsyncResult *result, gpointer user_data) {
  (void)user_data;
  GError *error = NULL;
  JSCValue *value = webkit_web_view_evaluate_javascript_finish(
      WEBKIT_WEB_VIEW(source), result, &error);
  if (error) {
    g_printerr("P50_WPE_JS_EVAL_FAILED=%s\n", error->message);
    g_error_free(error);
    return;
  }
  if (!value) {
    g_printerr("P50_WPE_JS_EVAL_MISSING\n");
    return;
  }
  char *s = jsc_value_to_string(value);
  g_print("P50_WPE_MODERN_JS_EVAL_RESULT=%s\n", s ? s : "(NULL)");
  g_free(s);
  g_object_unref(value);
  fflush(stdout);
}
static gboolean evaluate_cb(gpointer user_data) {
  P50App *a = (P50App *)user_data;
  static const char script[] =
      "(() => {const n=[1,2,3].map(v=>v*2).join(','); "
      "const e=document.getElementById('status'); "
      "const t=e ? e.textContent : 'MISSING_DOM'; "
      "return 'MODERN_JS_'+n+'_DOM_'+t;})()";
  webkit_web_view_evaluate_javascript(a->view,script,-1,NULL,NULL,NULL,finished,NULL);
  a->eval_submitted = TRUE;
  return G_SOURCE_REMOVE;
}
static void loaded(WebKitWebView *view, WebKitLoadEvent event, gpointer userdata) {
  (void)view;
  if (event == WEBKIT_LOAD_FINISHED) {
    g_print("P50_WPE_WEBVIEW_LOAD_FINISHED\n");
    g_timeout_add_seconds(3,evaluate_cb,userdata);
  }
}
static gboolean stop(gpointer userdata) {
  P50App *a=(P50App *)userdata;
  g_print("P50_WPE_REACHED_MEASUREMENT_HOLD;JS_EVAL_SUBMITTED=%d\n",a->eval_submitted);
  fflush(stdout);
  g_main_loop_quit(a->loop);
  return G_SOURCE_REMOVE;
}
int main(int argc,char**argv) {
  if(argc<2){fputs("Usage: wpeprobe http://127.0.0.1:8765/03-modern.html\n",stderr);return 2;}
  P50App a={0};
  a.loop=g_main_loop_new(NULL,FALSE);
  a.view=WEBKIT_WEB_VIEW(g_object_new(WEBKIT_TYPE_WEB_VIEW,NULL));
  if(!a.view){fputs("WPE web view creation failed\n",stderr);return 3;}
  g_signal_connect(a.view,"load-changed",G_CALLBACK(loaded),&a);
  g_print("P50_WPE_PLATFORM=%s\n",g_getenv("WPE_PLATFORM"));
  webkit_web_view_load_uri(a.view,argv[1]);
  g_timeout_add_seconds(35,stop,&a);
  g_main_loop_run(a.loop);
  g_object_unref(a.view);
  g_main_loop_unref(a.loop);
  return a.eval_submitted ? 0 : 4;
}
