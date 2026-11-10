import unittest
from scripts.import_tainan_pilot import parse_menu

DATE = "2026-11-05"

def dishes_html(names):
    return "".join(
        '<div style="background-color:#009688"><img src="https://fatraceschool.k12ea.gov.tw/dish/pic/123" alt="'+name+'"><div>'+cat+'</div><div>'+name+'</div></div>'
        for cat,name in names
    )


def tad_section(name, day, dish_items):
    # Based on the upstream op_tad_lunch3_list.tpl template.
    return ('<h3><img alt="臺南市東區'+name+'午餐資訊" src="images/groceries.png">'
            +name+'<form><input type="text" name="period" value="'+day+'"></form>午餐資訊</h3>'
            +dishes_html(dish_items)
            +'<a href="/modules/tad_lunch3/index.php?op=re_get&period='+day+'">重新擷取資料</a>')

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


    def test_alt_heading_with_nearby_date(self):
        page = ('<div><img alt="臺南市東區勝利國小午餐資訊" src="/title.png">'
                '<p>2026-11-05 午餐資訊</p></div>')
        page += dishes_html([
            ("主食","糙米飯"),("主菜","高昇排骨"),
            ("蔬菜","有機蔬菜"),("湯品","玉米蛋花湯")
        ])
        result = parse_menu(page, "勝利國小", DATE)
        self.assertEqual(result[1]["name"], "高昇排骨")

    def test_future_date_only_in_other_news_rejected(self):
        page = '<h2>柳營國小2026-11-05午餐資訊</h2>'
        page += '<article>明天 2026-11-06 校外教學</article>'
        page += dishes_html([
            ("主食","小米飯"),("主菜","蒜香翅小腿"),
            ("蔬菜","青花菜")
        ])
        with self.assertRaises(ValueError):
            parse_menu(page, "柳營國小", "2026-11-06")


    def test_tad_header_date_input_and_image_menu(self):
        html = tad_section("勝利國小", DATE, [
            ("主食","糙米飯"),("主菜","高昇排骨"),("副菜","水蓮銀芽"),
            ("蔬菜","有機蔬菜"),("湯品","玉米蛋花湯"),("附餐","義美保久乳")
        ])
        dishes = parse_menu(html, "勝利國小", DATE)
        self.assertEqual(len(dishes), 6)
        self.assertEqual(dishes[1]["name"], "高昇排骨")

    def test_tad_school_does_not_merge_kindergarten(self):
        primary = tad_section("勝利國小", DATE, [
            ("主食","糙米飯"),("主菜","高昇排骨"),("蔬菜","青菜"),("湯品","蛋花湯")
        ])
        kindergarten = tad_section("勝利國小附設幼兒園", DATE, [
            ("主食","麵線"),("主菜","紅燒肉"),("蔬菜","高麗菜"),("湯品","蔬菜湯")
        ])
        result = parse_menu(primary + kindergarten, "勝利國小", DATE)
        self.assertEqual([d["name"] for d in result],["糙米飯","高昇排骨","青菜","蛋花湯"])

    def test_tad_input_must_match_date_even_if_url_contains_day(self):
        html = tad_section("新生國小", "2026-11-04", [
            ("主食","白飯"),("主菜","滷雞腿"),("蔬菜","青江菜")
        ]) + '<p>新聞活動 2026-11-05</p>'
        with self.assertRaises(ValueError):
            parse_menu(html, "新生國小", DATE)

    def test_tad_correct_school_after_other_school(self):
        wrong = tad_section("其他國小", DATE, [
            ("主食","白飯"),("主菜","豬排"),("蔬菜","青江菜")
        ])
        correct = tad_section("崇明國小", DATE, [
            ("主食","糙米飯"),("主菜","烤雞腿"),("蔬菜","地瓜葉")
        ])
        result = parse_menu(wrong + correct, "崇明國小", DATE)
        self.assertEqual(result[1]["name"], "烤雞腿")

    def test_detect_multiple_kitchen_tabs_from_matching_school(self):
        from scripts.import_tainan_pilot import detect_tad_menu_options
        html = ('<h3><img alt="臺南市東區勝利國小午餐資訊">'
                '<input name="period" value="'+DATE+'"></h3>'
                '<div id="kitchenTab"><ul class="resp-tabs-list vert">'
                '<li>中央廚房 A</li><li>中央廚房 B</li></ul></div>')
        self.assertEqual(detect_tad_menu_options(html,"勝利國小",DATE),
                         ["中央廚房 A","中央廚房 B"])
        self.assertEqual(detect_tad_menu_options(html,"其他國小",DATE),[])
        self.assertEqual(detect_tad_menu_options(html,"勝利國小","2026-11-06"),[])

    def test_detect_options_does_not_take_next_school_section(self):
        from scripts.import_tainan_pilot import detect_tad_menu_options
        html = ('<h3><img alt="臺南市勝利國小午餐資訊">'
                '<input name="period" value="'+DATE+'"></h3>'
                '<p>一般午餐</p>'
                '<h3><img alt="臺南市勝利國小附設幼兒園午餐資訊">'
                '<input name="period" value="'+DATE+'"></h3>'
                '<div id="lunch3Tab"><ul class="resp-tabs-list"><li>午餐</li><li>下午點心</li></ul></div>')
        self.assertEqual(detect_tad_menu_options(html,"勝利國小",DATE),[])

    def test_menu_fingerprint_and_schedule_targets(self):
        from scripts.import_tainan_pilot import fingerprint, choose_dates
        dishes=[{"name":"白飯","category":"主食"},{"name":"三杯雞","category":"主菜"}]
        self.assertEqual(fingerprint(dishes), fingerprint(list(dishes)))
        changed=[dict(d) for d in dishes]
        changed[1]["name"]="咖哩雞"
        self.assertNotEqual(fingerprint(dishes), fingerprint(changed))
        self.assertEqual(len(choose_dates("auto", 7)), 2)
        self.assertEqual(len(choose_dates("auto", 9)), 1)
        self.assertEqual(len(choose_dates("auto", 19)), 1)
        self.assertEqual(len(choose_dates("both", 22)), 2)

if __name__=="__main__":
    unittest.main()
