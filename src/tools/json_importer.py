
import json
from database.database_manager import Manager

# Mapping category names to IDs
CATEGORY_ID_MAP = {
    "Societal Impact": 1,
    "Experimental Learning": 2,
    "AI in Education": 3,
    "Technology enhanced learning": 4,
    "Programming education": 5,
    "Educational Data Science": 6,
    "Methodology & Meta-Research": 7
}

def insert_topics_and_assignments(json_path):
    # Load data from JSON file
    with open(json_path, "r") as f:
        data = json.load(f)

    # Initialize database manager
    db = Manager()
    db.ensure_database_availability()

    # Insert topics
    topic_data = [(entry["title"], entry.get("description", "")) for entry in data]
    db.execute_many("INSERT OR IGNORE INTO topics (title, description) VALUES (?, ?)", topic_data)
    db.commit_changes()

    # Fetch topic IDs
    topic_id_map = {
        title: id_ for id_, title in db.execute("SELECT id, title FROM topics").fetchall()
    }

    # Prepare topicAssignments (topic_id, slice_id = category_id)
    assignment_data = []
    for entry in data:
        topic_id = topic_id_map.get(entry["title"])
        for category in entry.get("categories", []):
            cat_id = CATEGORY_ID_MAP.get(category)
            if topic_id and cat_id:
                assignment_data.append((topic_id, cat_id))

    # Insert into topicAssignment
    db.execute_many(
        "INSERT OR IGNORE INTO topicAssignment (topic_id, slice_id) VALUES (?, ?)",
        assignment_data
    )
    db.commit_changes()

    print(f"Inserted {len(topic_data)} topics and {len(assignment_data)} topicAssignments.")

if __name__ == "__main__":
    insert_topics_and_assignments("data_categorized.json")
