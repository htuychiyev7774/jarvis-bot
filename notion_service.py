from notion_client import Client
import config

def get_notion_client():
    """Initializes and returns the Notion API client."""
    return Client(auth=config.NOTION_TOKEN)

def get_pending_tasks():
    """Retrieves pending tasks from the Notion database."""
    notion = get_notion_client()
    
    # Query the database
    # We try to filter by "Status" checkbox (Done = False) or Status select.
    # To be flexible, we query without hard filters first, then filter in python,
    # or query with a filter and fall back if the filter fails.
    try:
        response = notion.databases.query(
            database_id=config.NOTION_DATABASE_ID,
            filter={
                "or": [
                    {
                        "property": "Status",
                        "checkbox": {
                            "equals": False
                        }
                    },
                    {
                        "property": "Status",
                        "status": {
                            "does_not_equal": "Done"
                        }
                    }
                ]
            }
        )
    except Exception as e:
        print(f"Warning: Notion filtered query failed (property 'Status' might not exist): {e}")
        # Fallback: query all and we'll handle parsing gracefully
        response = notion.databases.query(database_id=config.NOTION_DATABASE_ID)
        
    tasks = []
    for page in response.get("results", []):
        page_id = page.get("id")
        properties = page.get("properties", {})
        
        # Try to find the title property (type: title)
        title_text = "Untitled"
        title_prop_name = None
        
        for name, prop in properties.items():
            if prop.get("type") == "title":
                title_prop_name = name
                title_list = prop.get("title", [])
                if title_list:
                    title_text = "".join([t.get("plain_text", "") for t in title_list])
                break
                
        # Check completion status if Status property exists
        is_completed = False
        status_prop = properties.get("Status", {})
        if status_prop:
            if status_prop.get("type") == "checkbox":
                is_completed = status_prop.get("checkbox", False)
            elif status_prop.get("type") == "status":
                status_name = status_prop.get("status", {}).get("name", "")
                is_completed = (status_name.lower() in ["done", "completed", "bajarildi"])
                
        if not is_completed:
            tasks.append({
                "id": page_id,
                "title": title_text,
                "title_property": title_prop_name or "Name"
            })
            
    return tasks

def add_task(title):
    """Adds a new task page to the Notion database."""
    notion = get_notion_client()
    
    # We assume the title property is named "Name". If the database has a different
    # title property, this will fail, so we instruct the user to name it "Name".
    properties = {
        "Name": {
            "title": [
                {
                    "text": {
                        "content": title
                    }
                }
            ]
        }
    }
    
    # Check database schema to see if Status property is status or checkbox, and initialize it
    try:
        db = notion.databases.retrieve(database_id=config.NOTION_DATABASE_ID)
        status_type = db.get("properties", {}).get("Status", {}).get("type")
        if status_type == "checkbox":
            properties["Status"] = {"checkbox": False}
        elif status_type == "status":
            properties["Status"] = {"status": {"name": "To Do"}}
    except Exception as e:
        print(f"Warning: Could not retrieve database schema to set status: {e}")
        
    new_page = notion.pages.create(
        parent={"database_id": config.NOTION_DATABASE_ID},
        properties=properties
    )
    return new_page

def complete_task(page_id):
    """Marks a task as completed in Notion."""
    notion = get_notion_client()
    
    # Determine Status property type on the page
    try:
        page = notion.pages.retrieve(page_id=page_id)
        properties = page.get("properties", {})
        status_prop = properties.get("Status", {})
        
        status_update = {}
        if status_prop.get("type") == "checkbox":
            status_update = {"checkbox": True}
        elif status_prop.get("type") == "status":
            status_update = {"status": {"name": "Done"}}
        else:
            # Fallback: if Status doesn't exist or is not status/checkbox, try checkbox
            status_update = {"checkbox": True}
            
        notion.pages.update(
            page_id=page_id,
            properties={
                "Status": status_update
            }
        )
        return True
    except Exception as e:
        print(f"Error completing Notion task {page_id}: {e}")
        return False
