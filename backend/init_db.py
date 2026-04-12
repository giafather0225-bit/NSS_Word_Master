import sys
import json
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from backend.database import engine, Base, SessionLocal
from backend.models import StudyItem, Progress

def init_db():
    print("Creating tables in SQLite database...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # Check if items are already in DB to avoid dupes
    if db.query(StudyItem).count() > 0:
        print("Database already contains records. Clearing StudyItems to prevent duplicates...")
        db.query(StudyItem).delete()
        db.commit()
    
    # Read raw JSON files from data/raw_json for Vocabulary
    raw_dir = Path(__file__).parent.parent / "data" / "raw_json"
    json_files = list(raw_dir.glob("*.json"))
    
    if not json_files:
        print("No JSON files found in data/raw_json/. Run ocr_engine.py first.")
    else:
        print(f"Found {len(json_files)} JSON files. Loading into DB as 'vocabulary'...")
        total_items = 0
        subject_name = "vocabulary"
        lesson_name = "Lesson_09"

        def first_nonempty(row, keys):
            for k in keys:
                v = row.get(k)
                if isinstance(v, str) and v.strip():
                    return v.strip()
                if isinstance(v, list) and v:
                    for item in v:
                        if isinstance(item, str) and item.strip():
                            return item.strip()
            return ""
        
        discovered_pairs = set()

        for jf in json_files:
            with open(jf, "r", encoding="utf-8") as f:
                data = json.load(f)
                
                for item in data:
                    pos = item.get("pos", "")
                    extra_obj = {"pos": pos}
                    img = item.get("image_url") or item.get("image")
                    if img:
                        extra_obj["image"] = img
                    extra_data_json = json.dumps(extra_obj, ensure_ascii=False)
                    
                    item_sub = item.get("subject", subject_name)
                    item_les = item.get("lesson", lesson_name)
                    discovered_pairs.add((item_sub, item_les))
                    
                    new_item = StudyItem(
                        subject=item_sub,
                        lesson=item_les,
                        question=first_nonempty(
                            item,
                            ["definition", "meaning", "question", "desc", "description"],
                        ),
                        answer=item.get("word", ""),
                        hint=first_nonempty(
                            item,
                            ["example", "example_sentence", "examples", "sentence", "sentences"],
                        ),
                        extra_data=extra_data_json
                    )
                    db.add(new_item)
                    total_items += 1
                    
        db.commit()
        print(f"Successfully inserted {total_items} vocabulary items into the database.")
        
        # Initialize Progress for discovered subject/lesson pairs
        for sub, les in discovered_pairs:
            if db.query(Progress).filter(
                Progress.subject == sub,
                Progress.lesson == les
            ).count() == 0:
                init_prog = Progress(subject=sub, lesson=les, current_index=0, best_streak=0)
                db.add(init_prog)
        
        db.commit()
        print("Initialized progress map for discovered subjects/lessons.")
            
    db.close()
    
if __name__ == "__main__":
    init_db()
