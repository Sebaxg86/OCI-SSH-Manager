#include <Python.h>
#include <CoreFoundation/CoreFoundation.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef OCI_PYTHON_HOME
#define OCI_PYTHON_HOME "/opt/homebrew/opt/python@3.13/Frameworks/Python.framework/Versions/3.13"
#endif

int main(int argc, char **argv) {
    CFBundleRef bundle = CFBundleGetMainBundle();
    CFURLRef url = CFBundleCopyBundleURL(bundle);
    CFStringRef path = CFURLCopyFileSystemPath(url, kCFURLPOSIXPathStyle);
    char bundle_path[PATH_MAX];
    if (!CFStringGetCString(path, bundle_path, sizeof(bundle_path), kCFStringEncodingUTF8)) return 1;
    CFRelease(path); CFRelease(url);
    setenv("PYTHONHOME", OCI_PYTHON_HOME, 1);
    setenv("PYTHONDONTWRITEBYTECODE", "1", 1);
    if (argc > 1 && strcmp(argv[1], "--diagnose") == 0) {
        char identity[256];
        CFStringRef identifier = CFBundleGetIdentifier(bundle);
        if (!identifier || !CFStringGetCString(identifier, identity, sizeof(identity), kCFStringEncodingUTF8)) return 1;
        printf("Bundle: %s\n", identity); fflush(stdout);
        char *args[] = {argv[0], "-c", "import tkinter as tk; root=tk.Tk(); root.title('OCI launcher test'); root.after(200,root.destroy); root.mainloop(); print('Native Python/Tk launcher OK')", NULL};
        return Py_BytesMain(3, args);
    }
    char script[PATH_MAX];
    char *last = strrchr(bundle_path, '/');
    if (!last) return 1;
    *last = '\0';
    int length = snprintf(script, sizeof(script), "%s/gui.py", bundle_path);
    if (length < 0 || (size_t)length >= sizeof(script)) return 1;
    char *args[] = {argv[0], script, NULL};
    return Py_BytesMain(2, args);
}
