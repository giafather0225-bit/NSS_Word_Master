import json
import logging
import os
import re
from pathlib import Path
from tqdm import tqdm
import ollama

log = logging.getLogger(__name__)

def extract_vocab_from_image(image_path: str) -> str:
    """
    Sends the image to the local Ollama llava model with a specific extraction prompt.
    """
    prompt = """
    You are an expert OCR and data extraction assistant.
    Analyze the provided image of an English vocabulary book.
    Extract the list of vocabulary words, their part of speech, English definition (or synonym), and the example sentences provided in the text.
    
    Format the extracted data STRICTLY as a valid JSON array of objects, where each object has these exact keys:
    - "word": The vocabulary word
    - "pos": Part of speech (e.g., "n.", "v.", "adj.")
    - "definition": The English definition or synonym given
    - "example": The English example sentence
    
    Ensure your entire response is a single valid JSON array. Do not include any introductory or concluding text, and do not use markdown blocks like ````json`.
    """
    
    with open(image_path, 'rb') as file:
        response = ollama.generate(
            model='llava',
            prompt=prompt,
            images=[file.read()]
        )
    return response['response']

def process_lesson_images(lesson_folder: str, output_folder: str = "data/raw_json"):
    """
    Processes all images in the specified lesson folder and saves the JSON results.
    """
    base_dir = Path(__file__).parent.parent
    lesson_path = base_dir / lesson_folder
    out_path = base_dir / output_folder
    
    out_path.mkdir(parents=True, exist_ok=True)
    
    # Supported image formats
    extensions = ("*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG")
    image_files = []
    for ext in extensions:
        image_files.extend(lesson_path.glob(ext))
        
    if not image_files:
        log.warning("No images found in %s", lesson_path)
        return

    log.info("Found %d images to process in %s.", len(image_files), lesson_folder)

    for img_path in tqdm(image_files, desc="Processing images with Llava"):
        log.info("Processing: %s", img_path.name)

        try:
            result_text = extract_vocab_from_image(str(img_path))

            # Clean up the output in case llava adds markdown formatting
            clean_text = re.sub(r'^```[a-zA-Z]*\s*', '', result_text.strip())
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]
            clean_text = clean_text.strip()

            output_file_stem = img_path.stem

            try:
                # Validate JSON structure
                parsed_json = json.loads(clean_text)

                json_file = out_path / f"{output_file_stem}.json"
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(parsed_json, f, indent=4, ensure_ascii=False)
                log.info("Extracted and saved to %s", json_file)

            except json.JSONDecodeError:
                log.warning("Failed to parse JSON for %s — saving raw output instead.", img_path.name)
                raw_file = out_path / f"{output_file_stem}_raw.txt"
                with open(raw_file, 'w', encoding='utf-8') as f:
                    f.write(result_text)

        except Exception as e:
            log.error("Error processing %s (check if ollama is running): %s", img_path.name, e)

if __name__ == "__main__":
    # Test execution for Lesson_09
    target_lesson = "Voca_8000/Lesson_09"
    process_lesson_images(target_lesson, "data/raw_json")
