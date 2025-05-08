import argparse
import requests
from datetime import datetime
from notion_client import Client

def parse_arguments():
    parser = argparse.ArgumentParser(description='Sync WeRead highlights to Notion')
    parser.add_argument('--weread_cookie', required=True, help='WeRead browser cookie')
    parser.add_argument('--notion_token', required=True, help='Notion integration token')
    parser.add_argument('--notion_database_id', required=True, help='Notion database ID')
    return parser.parse_args()

def get_weread_highlights(cookie):
    url = "https://i.weread.qq.com/user/notebooks"
    headers = {
        "Cookie": cookie,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return process_books(response.json())
    except Exception as e:
        print(f"Error getting highlights: {str(e)}")
        return []

def process_books(data):
    highlights = []
    for book in data.get("books", []):
        notes_url = f"https://i.weread.qq.com/book/bookmarklist?bookId={book['bookId']}"
        notes_response = requests.get(notes_url, headers={"Cookie": args.weread_cookie})
        notes_data = notes_response.json()
        
        for chapter in notes_data.get("chapters", []):
            for mark in chapter.get("marks", []):
                highlights.append({
                    "book_id": book["bookId"],
                    "book_title": book["title"],
                    "author": book.get("author", ""),
                    "chapter": chapter.get("chapterTitle", ""),
                    "content": mark.get("markText", ""),
                    "create_time": datetime.fromtimestamp(mark.get("createTime", 0)).strftime("%Y-%m-%d %H:%M:%S"),
                    "range": mark.get("range", "")
                })
    return highlights

def sync_to_notion(highlights, notion_token, database_id):
    notion = Client(auth=notion_token)
    
    for highlight in highlights:
        query = {
            "filter": {
                "and": [
                    {"property": "Book ID", "rich_text": {"equals": highlight["book_id"]}},
                    {"property": "Range", "rich_text": {"equals": highlight["range"]}}
                ]
            }
        }
        
        existing = notion.databases.query(
            database_id=database_id,
            **query
        ).get("results", [])
        
        if not existing:
            create_notion_page(notion, database_id, highlight)

def create_notion_page(notion, database_id, highlight):
    new_page = {
        "parent": {"database_id": database_id},
        "properties": {
            "Book Title": {"title": [{"text": {"content": highlight["book_title"]}}]},
            "Author": {"rich_text": [{"text": {"content": highlight["author"]}}]},
            "Chapter": {"rich_text": [{"text": {"content": highlight["chapter"]}}]},
            "Content": {"rich_text": [{"text": {"content": highlight["content"]}}]},
            "Date": {"date": {"start": highlight["create_time"]}},
            "Book ID": {"rich_text": [{"text": {"content": highlight["book_id"]}}]},
            "Range": {"rich_text": [{"text": {"content": highlight["range"]}}]}
        }
    }
    try:
        notion.pages.create(**new_page)
        print(f"Added: {highlight['book_title'][:20]}...")
    except Exception as e:
        print(f"Error creating page: {str(e)}")

if __name__ == "__main__":
    args = parse_arguments()
    print("Starting sync...")
    
    highlights = get_weread_highlights(args.weread_cookie)
    if highlights:
        print(f"Found {len(highlights)} highlights")
        sync_to_notion(highlights, args.notion_token, args.notion_database_id)
    
    print("Sync completed")
