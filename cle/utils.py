import os
import contextlib

from .errors import CLEError

# https://code.woboq.org/userspace/glibc/include/libc-pointer-arith.h.html#43
def ALIGN_DOWN(base, size):
    return base & -size

# https://code.woboq.org/userspace/glibc/include/libc-pointer-arith.h.html#50
def ALIGN_UP(base, size):
    return ALIGN_DOWN(base + size - 1, size)

# To verify the mmap behavior you can compile and run the following program. Fact is that mmap file mappings
# always map in the entire page into memory from the file if available. If not, it gets zero padded
# pylint: disable=pointless-string-statement
"""#include <stdio.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/mman.h>

void make_test_file()
{
    void* data = (void*)0xdead0000;
    int fd = open("./test.data", O_CREAT | O_RDWR, S_IRUSR | S_IWUSR);
    for (int i = 0; i < 0x1800; i += sizeof(void*)) // Only write 1 1/2 pages worth
    {
        write(fd, &data, sizeof(void*));
        data += sizeof(void*);
    }
    close(fd);
}
int main(int argc, char* argv[])
{
    make_test_file();

    int fd = open("./test.data", O_RDONLY);
    unsigned char* mapping = mmap(NULL, 0x123, PROT_READ, MAP_PRIVATE, fd, 4096);

    for (int i=0; i < 0x1000; i++)
    {
        printf("%02x ", mapping[i]);
        if (i % sizeof(void*) == (sizeof(void*) - 1))
            printf("| ");
        if (i % 16 == 15)
            printf("\n");
    }
}"""
def get_mmaped_data(stream, offset, length, page_size):
    if offset % page_size != 0:
        raise CLEError("libc helper for mmap: Invalid page offset, should be multiple of page size! Stream {}, offset {}, length: {}".format(stream, offset, length))

    read_length = ALIGN_UP(length, page_size)
    stream.seek(offset)
    data = stream.read(read_length)
    return data.ljust(read_length, '\0')

@contextlib.contextmanager
def stream_or_path(obj, perms='rb'):
    if hasattr(obj, 'read') and hasattr(obj, 'seek'):
        obj.seek(0)
        yield obj
    else:
        if not os.path.exists(obj):
            raise CLEError("%r is not a valid path" % obj)

        with open(obj, perms) as f:
            yield f
