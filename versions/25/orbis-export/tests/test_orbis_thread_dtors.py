#!/usr/bin/env python3
"""The shared runtime's __cxa_thread_atexit_impl (C++ thread_local destructors, which musl lacks):
extracted from orbis_runtime.c and run on the host - destructors run at thread exit, newest first,
and one registered by a destructor still runs."""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
source = (root / 'tools/orbis_runtime.c').read_text()
start = source.index('struct orbis_thread_dtor {')
end = source.index('int orbis_runtime_allocator_probe(')
harness = '''#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
''' + source[start:end] + r'''
static char order[16];
static int count;
static void record(void *tag) {
    order[count++] = *(char *)tag;
    if (*(char *)tag == 'b') {
        static char late = 'z';
        __cxa_thread_atexit_impl(record, &late, NULL);
    }
}
static void *worker(void *unused) {
    static char a = 'a', b = 'b', c = 'c';
    (void)unused;
    __cxa_thread_atexit_impl(record, &a, NULL);
    __cxa_thread_atexit_impl(record, &b, NULL);
    __cxa_thread_atexit_impl(record, &c, NULL);
    return NULL;
}
int main(void) {
    pthread_t thread;
    if (pthread_create(&thread, NULL, worker, NULL) != 0) return 2;
    pthread_join(thread, NULL);
    order[count] = 0;
    printf("%s\n", order);
    return strcmp(order, "cbza") == 0 ? 0 : 1;
}
'''
with tempfile.TemporaryDirectory() as directory:
    c = Path(directory) / 'dtors.c'
    c.write_text(harness)
    subprocess.run(['cc', '-std=c11', '-Wall', '-Werror', '-pthread', str(c), '-o', str(Path(directory) / 'dtors')],
                   check=True)
    result = subprocess.run([str(Path(directory) / 'dtors')], capture_output=True, text=True)
    assert result.returncode == 0, 'destructor order ' + result.stdout
print('Orbis thread_local destructors run at thread exit, newest first: PASS')
