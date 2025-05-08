import requests
import json
import os
from dotenv import load_dotenv
from notion_client import Client

load_dotenv()

# 从环境变量或配置文件中获取 Cookie
COOKIE = os.getenv("WEREAD_COOKIE")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

# 确保 Cookie, Notion Token 和 Database ID 存在
if not COOKIE:
    print("请设置 WEREAD_COOKIE 环境变量")
    exit()
if not NOTION_TOKEN:
    print("请设置 NOTION_TOKEN 环境变量")
    exit()
if not NOTION_DATABASE_ID:
    print("请设置 NOTION_DATABASE_ID 环境变量")
    exit()

# 将 Cookie 字符串转换为字典
def cookie_string_to_dict(cookie_string):
    cookies = {}
    for cookie in cookie_string.split(';'):
        if cookie:
            name, value = cookie.strip().split('=', 1)
            cookies[name] = value
    return cookies

cookies = cookie_string_to_dict(COOKIE)

# 初始化 Notion 客户端
notion = Client(auth=NOTION_TOKEN)

def get_weread_data(url, params=None, cookies=None):
    """
    发送请求到微信读书 API 并返回 JSON 数据。
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
        "Referer": "https://weread.qq.com/"  # 模拟从微信读书页面发起的请求
    }
    try:
        response = requests.get(url, headers=headers, params=params, cookies=cookies)
        response.raise_for_status()  # 检查请求是否成功
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return None

def get_notebooks(cookies):
    """
    获取用户书架上的书籍信息。
    """
    url = "https://i.weread.qq.com/user/notebooks"
    return get_weread_data(url, cookies=cookies)


def get_bookmarks(book_id, cookies):
    """
    获取书籍的划线和笔记信息。
    """
    url = "https://i.weread.qq.com/book/bookmarklist"
    params = {"bookId": book_id}
    return get_weread_data(url, params=params, cookies=cookies)


def get_book_info(book_id, cookies):
    """
    获取书籍信息
    """
    url = "https://i.weread.qq.com/book/info"
    params = {"bookId": book_id}
    return get_weread_data(url, params=params, cookies=cookies)

def create_notion_page(database_id, book_title, chapter_title, highlight_text, note_text):
    """
    在 Notion 数据库中创建一个页面。
    """
    try:
        notion.pages.create(
            parent={"database_id": database_id},
            properties={
                "书名": {"title": [{"text": {"content": book_title}}]},
                "章节": {"rich_text": [{"text": {"content": chapter_title}}]},
                "划线": {"rich_text": [{"text": {"content": highlight_text}}]},
                "笔记": {"rich_text": [{"text": {"content": note_text}}]},
            },
        )
        print(f"成功创建 Notion 页面: {book_title} - {chapter_title}")
    except Exception as e:
        print(f"创建 Notion 页面失败: {e}")

if __name__ == "__main__":
    # 使用示例
    notebooks_data = get_notebooks(cookies)

    if notebooks_data and "books" in notebooks_data:
        books = notebooks_data["books"]
        for book in books:
            book_id = book["bookId"]
            book_info = get_book_info(book_id, cookies)
            bookmarks_data = get_bookmarks(book_id, cookies)

            if bookmarks_data and "chapters" in bookmarks_data:
                book_title = book_info.get('title', 'N/A')
                for chapter in bookmarks_data["chapters"]:
                    chapter_title = chapter.get('title', 'N/A')
                    if "highlights" in chapter:
                        for highlight in chapter["highlights"]:
                            highlight_text = highlight.get('markText', 'N/A')
                            note_text = highlight.get('note', 'N/A')

                            # 创建 Notion 页面
                            create_notion_page(NOTION_DATABASE_ID, book_title, chapter_title, highlight_text, note_text)
            else:
                print(f"获取书摘失败 bookId: {book_id}")
    else:
        print("获取书架信息失败")
