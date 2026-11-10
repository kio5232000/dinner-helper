import unittest
from scripts.probe_school_source import inspect

class FakeResponse:
    status=200
    def __init__(self, html, url):
        self.html=html.encode("utf-8")
        self.url=url
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def geturl(self):return self.url
    def read(self, max_bytes):return self.html[:max_bytes]

class ProbeSchoolTest(unittest.TestCase):
    def setUp(self):
        self.registry=[{"city":"臺南市","level":"國小","district":"南區",
                        "name":"市立南區新興國小","code":"213608"}]
        self.day="2026-11-10"
        self.url="https://www.sses.tn.edu.tw/index.php"
        self.html="""<h3>新興國小2026-11-10午餐資訊</h3>
        <p>主食</p><p>白飯</p>
        <p>主菜</p><p>三杯雞</p>
        <p>蔬菜</p><p>高麗菜</p>
        <p>湯品</p><p>蛋花湯</p>"""
    def test_valid_public_page(self):
        def opener(req, timeout): return FakeResponse(self.html,req.full_url)
        result=inspect("新興國小","國小","南區",self.url,self.day,self.registry,opener)
        self.assertEqual(result["status"],"ok")
        self.assertEqual(result["school_code"],"213608")
        self.assertEqual(result["dishes"][1]["name"],"三杯雞")
    def test_reject_non_school_url(self):
        called=[]
        def opener(req,timeout):
            called.append(True); raise AssertionError("should not fetch")
        result=inspect("新興國小","國小","南區","https://example.com/",self.day,self.registry,opener)
        self.assertEqual(result["status"],"unavailable")
        self.assertFalse(called)
    def test_reject_different_day_and_school(self):
        def opener(req,timeout): return FakeResponse(self.html,req.full_url)
        wrong=inspect("新興國小","國小","南區",self.url,"2026-11-11",self.registry,opener)
        self.assertEqual(wrong["status"],"unavailable")
        wrong=inspect("新興國小","國小","北區",self.url,self.day,self.registry,opener)
        self.assertEqual(wrong["status"],"unavailable")

if __name__=="__main__":
    unittest.main()
