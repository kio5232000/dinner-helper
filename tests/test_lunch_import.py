import unittest
from scripts.import_tainan_pilot import parse_menu

DATE = "2026-11-05"

def dishes_html(names):
    return "".join(
        '<div style="background-color:#009688"><img src="https://fatraceschool.k12ea.gov.tw/dish/pic/123" alt="'+name+'"><div>'+cat+'</div><div>'+name+'</div></div>'
        for cat,name in names
    )

class LunchParsingTests(unittest.TestCase):
    def test_valid_image_cards(self):
        html = "<h2>柳營國小"+DATE+"午餐資訊</h2>"+dishes_html([
            ("主食","小米飯"),("主菜","蒜香翅小腿"),("蔬菜","蒜香青花菜"),("湯品","絲瓜龍骨湯")
        ])
        meals = parse_menu(html, "柳營國小", DATE)
        self.assertEqual([x["name"] for x in meals], ["小米飯","蒜香翅小腿","蒜香青花菜","絲瓜龍骨湯"])

    def test_text_only_homepage(self):
        html = "<h2>佳興國小"+DATE+"午餐資訊</h2><p>本校一律使用國產豬肉</p>"
        html += "".join("<p>"+x+"</p>" for x in ["主食","燕麥飯","主菜","栗子燒雞","蔬菜","蒜香空心菜","湯品","紫菜豆腐湯"])
        html += '<a>點此校園食材登錄平臺觀看詳細資訊</a>'
        meals = parse_menu(html, "佳興國小", DATE)
        self.assertEqual(meals[1]["name"], "栗子燒雞")
        self.assertEqual(meals[1]["category"], "主菜")
        self.assertIsNone(meals[1]["photo_url"])

    def test_wrong_day_rejected(self):
        html = "<h2>佳興國小2026-11-04午餐資訊</h2><p>主食</p><p>白飯</p>"
        with self.assertRaises(ValueError):
            parse_menu(html, "佳興國小", DATE)

    def test_wrong_school_rejected(self):
        html = "<h2>其他國小"+DATE+"午餐資訊</h2>"+dishes_html([
            ("主食","白飯"),("主菜","雞腿"),("蔬菜","空心菜")
        ])
        with self.assertRaises(ValueError):
            parse_menu(html, "柳營國小", DATE)

    def test_second_snack_menu_ignored(self):
        html = "<h2>柳營國小"+DATE+"午餐資訊</h2>"+dishes_html([
            ("主食","小米飯"),("主菜","三杯雞"),("蔬菜","青江菜"),("湯品","南瓜湯"),
            ("附餐","水果"),("主食","幼兒園點心"),("主菜","其他菜")
        ])
        meals = parse_menu(html, "柳營國小", DATE)
        self.assertEqual(len(meals),5)

if __name__=="__main__":
    unittest.main()
