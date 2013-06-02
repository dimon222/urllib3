import unittest

from io import BytesIO, BufferedReader

from urllib3.response import HTTPResponse
from urllib3.exceptions import DecodeError

class TestLegacyResponse(unittest.TestCase):
    def test_getheaders(self):
        headers = {'host': 'example.com'}
        r = HTTPResponse(headers=headers)
        self.assertEqual(r.getheaders(), headers)

    def test_getheader(self):
        headers = {'host': 'example.com'}
        r = HTTPResponse(headers=headers)
        self.assertEqual(r.getheader('host'), 'example.com')


class TestResponse(unittest.TestCase):
    def test_cache_content(self):
        r = HTTPResponse('foo')
        self.assertEqual(r.data, 'foo')
        self.assertEqual(r._body, 'foo')

    def test_default(self):
        r = HTTPResponse()
        self.assertEqual(r.data, None)

    def test_none(self):
        r = HTTPResponse(None)
        self.assertEqual(r.data, None)

    def test_preload(self):
        fp = BytesIO(b'foo')

        r = HTTPResponse(fp, preload_content=True)

        self.assertEqual(fp.tell(), len(b'foo'))
        self.assertEqual(r.data, b'foo')

    def test_no_preload(self):
        fp = BytesIO(b'foo')

        r = HTTPResponse(fp, preload_content=False)

        self.assertEqual(fp.tell(), 0)
        self.assertEqual(r.data, b'foo')
        self.assertEqual(fp.tell(), len(b'foo'))

    def test_decode_bad_data(self):
        fp = BytesIO(b'\x00' * 10)
        self.assertRaises(DecodeError, HTTPResponse, fp, headers={
            'content-encoding': 'deflate'
        })

    def test_decode_deflate(self):
        import zlib
        data = zlib.compress(b'foo')

        fp = BytesIO(data)
        r = HTTPResponse(fp, headers={'content-encoding': 'deflate'})

        self.assertEqual(r.data, b'foo')

    def test_decode_deflate_case_insensitve(self):
        import zlib
        data = zlib.compress(b'foo')

        fp = BytesIO(data)
        r = HTTPResponse(fp, headers={'content-encoding': 'DeFlAtE'})

        self.assertEqual(r.data, b'foo')

    def test_chunked_decoding_deflate(self):
        import zlib
        data = zlib.compress(b'foo')

        fp = BytesIO(data)
        r = HTTPResponse(fp, headers={'content-encoding': 'deflate'},
                         preload_content=False)

        self.assertEqual(r.read(3), b'')
        self.assertEqual(r.read(1), b'f')
        self.assertEqual(r.read(2), b'oo')

    def test_chunked_decoding_deflate2(self):
        import zlib
        compress = zlib.compressobj(6, zlib.DEFLATED, -zlib.MAX_WBITS)
        data = compress.compress(b'foo')
        data += compress.flush()

        fp = BytesIO(data)
        r = HTTPResponse(fp, headers={'content-encoding': 'deflate'},
                         preload_content=False)

        self.assertEqual(r.read(1), b'')
        self.assertEqual(r.read(1), b'f')
        self.assertEqual(r.read(2), b'oo')

    def test_chunked_decoding_gzip(self):
        import zlib
        compress = zlib.compressobj(6, zlib.DEFLATED, 16 + zlib.MAX_WBITS)
        data = compress.compress(b'foo')
        data += compress.flush()

        fp = BytesIO(data)
        r = HTTPResponse(fp, headers={'content-encoding': 'gzip'},
                         preload_content=False)

        self.assertEqual(r.read(11), b'')
        self.assertEqual(r.read(1), b'f')
        self.assertEqual(r.read(2), b'oo')

    def test_io(self):
        fp = BytesIO(b'foo')
        resp = HTTPResponse(fp, preload_content=False)

        self.assertEqual(resp.closed, False)
        self.assertEqual(resp.readable(), True)
        self.assertEqual(resp.writable(), False)
        self.assertRaises(IOError, resp.fileno)

        resp.close()
        self.assertEqual(resp.closed, True)

        #also try when only data is present.
        resp2 = HTTPResponse('foodata')
        self.assertRaises(IOError, resp2.fileno)

        resp2._fp = 2
        # A corner case where _fp is present but doesn't have `closed`,
        # `isclosed`, or `fileno`.  Unlikely, but possible.
        self.assertEqual(resp.closed, True)
        self.assertRaises(IOError, resp2.fileno)

    def test_io_bufferedreader(self):
        fp = BytesIO(b'foo')
        resp = HTTPResponse(fp, preload_content=False)
        br = BufferedReader(resp)

        self.assertEqual(br.read(), b'foo')

        br.close()
        self.assertEqual(resp.closed, True)


if __name__ == '__main__':
    unittest.main()
