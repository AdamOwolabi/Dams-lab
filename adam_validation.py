import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
import ollama
import json
import ast   #ast = abstract syntac trees. used to clean up \n, and convert code to tree like structure 
import pprint
from datetime import datetime
import re
from rapidfuzz import fuzz


# 5. Review and evaluate each result manually
# 6. Document which combinations provided the best performance for each stage. log name, prompt, input, output, notes on quality or accuracy


#run: uv run -m src.validators.adam_validation, ollama list, docker ps, 

#1.

# Best Amazon configuration - comprehensive and tested
AMAZON_CONFIG = {
    "selectors": {
        "title": "#productTitle",
        "price_whole": ".a-price-whole",
        "price_fraction": ".a-price-fraction",
        "currency": ".a-price-symbol",
        "features": "#feature-bullets ul li span.a-list-item",
        "images": "#altImages ul li img",
        "main_image": "#landingImage",
        "rating": "span.a-icon-alt",
        "review_count": "#acrCustomerReviewText",
        "brand": "#bylineInfo",
        "availability": "#availability span",
    }
}


async def scrape_amazon(url: str):
    async with async_playwright() as pw:
        # Firefox works best for Amazon
        browser = await pw.firefox.launch(headless=False)
        page = await browser.new_page()
        
        # Apply stealth - bypasses bot detection, spoof browser's fingerprint.
        await stealth_async(page)
        
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        
        # Wait for content dynamic content to load (important!)
        await page.wait_for_timeout(5000)
        
        product_data = {}
        
        for field, selector in AMAZON_CONFIG["selectors"].items():
            try:
                if field == "features":
                    # Get all feature bullets
                    elements = await page.query_selector_all(selector)
                    product_data[field] = [await elem.inner_text() for elem in elements if await elem.inner_text()]
                
                elif field == "images":
                    # Get all product images
                    img_elements = await page.query_selector_all(selector)
                    product_data[field] = []
                    for img in img_elements:
                        src = await img.get_attribute("src") or await img.get_attribute("data-src")
                        if src and "http" in src:
                            product_data[field].append(src)
                
                else:
                    # Get single text element
                    elem = await page.query_selector(selector)
                    product_data[field] = await elem.inner_text() if elem else None
                    
            except Exception as e:
                product_data[field] = None
                print(f"Error extracting {field}: {e}")
        
        await browser.close()
        return product_data


def extract_entities(product_data: dict, model: str = "gemma2") -> dict:
    """
    Extract IoT-related entities from product data using Ollama.
    """

    # Create the prompt
    prompt = f"""

                Extract ONLY entities that are explicitly mentioned in the following product data.

                ### 
                **Strict Rules:**
                 - Do NOT add information based on general knowledge.
                 - Do NOT infer features that aren't stated.
                 - Only List entities fundamental to the product name
                ###

                Extract IoT-related entities from the input JSON dictionary.

                Return only JSON in this format:
                {{"entities": [...]}}

                Do not add any explanations, reasoning, or extra text.

                Entities must include but are not limited to the following:
                - Full product name
                - Manufacturer/brand
                - Device type (e.g., speaker, display, camera, hub, thermostat)
                - Key technologies (e.g., Alexa, Google Assistant, WiFi, Bluetooth, Zigbee)
                - Product capabilities (e.g., voice assistant, smart home control, video streaming)
                - Product line/series name

                Extract ALL relevant IoT entities as separate items.

                ---

                Input:
                {json.dumps(product_data, indent=2)}

                Output:
                
            """

    try:
        # Call Ollama
        client = ollama.Client()
        response = client.generate(
            model=model,
            prompt=prompt,
            options={
                "temperature": 0.1,  # Low temperature for more consistent output
                "num_predict": 500,  # Limit response length
            }
        )
        
        # Extract the response text
        response_text = response['response'].strip()
        
        # Try to parse JSON from response
        # Sometimes models include markdown code blocks
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        # Parse JSON
        entities_data = json.loads(response_text)
        
        return entities_data
        
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON from LLM response: {e}")
        print(f"Raw response: {response_text}")
        return {"entities": [], "error": "JSON parsing failed"}
    except Exception as e:
        print(f"Error in entity extraction: {e}")
        return {"entities": [], "error": str(e)}

def extract_relationships(entities, model="gemma2:2b"):
    """
    Extract relationships between entities using LLM
    """   
    prompt = f"""
    
        You are a data engineer specialized in constructing knowledge graphs. Given a set of extracted entities from an e-commerce 
        website generate triplets in the format:

        [(('type1', 'entity1'), 'relationship', ('type2', 'entity2')), ...]

        ### 
        **Strict Rules:**
        - **Output only the list of triplets.** 
        - **Do not include explanations, summaries, or extra text.** 
        - **Do not label or describe the output.** 
        - **If no valid triplets exist, return [] exactly.**
        ###

        **Entity Types:**
        - These are examples only — extract more types as needed:
        device, manufacturer, application, process, sensor, category, etc.

        ###
        **Relationships:**
        These are examples only — generate more as needed:
        developedBy, manufacturedBy, compatibleWith, hasSensor, performs, etc.

        ###
        **Triplet Schema:**
        Each triplet must follow this schema:
        (('type1', 'entity1'), 'relationship', ('type2', 'entity2'))
        Triplets may involve both known and new entity types or relations, as long as they are semantically valid.

        ### **Example Expected Output:**
        [
        (('device', 'Govee Smart Light Bulbs'), 'manufacturedBy', ('manufacturer', 'Govee')),
        (('device', 'Govee Smart Light Bulbs'), 'compatibleWith', ('application', 'Alexa')),
        (('device', 'Govee Smart Light Bulbs'), 'isCategory', ('category', 'Smart Lighting')),
        (('device', 'Govee Smart Light Bulbs'), 'hasSensor', ('sensor', 'WiFi')),
        (('device', 'Govee Smart Light Bulbs'), 'includesFeature', ('feature', 'Color Control')),
        (('device', 'Govee Smart Light Bulbs'), 'supportsProtocol', ('protocol', 'Zigbee'))
        ]

        **Output must strictly follow the above format with no additional text.**

        If no valid triplets exist, return: []

        **Entities to process:**
        {entities}

        **Output:**"""

    response = ollama.generate(model=model, prompt=prompt)
    raw_output = response['response'].strip()
    print(raw_output)
    
    # Remove any code block markers if present
    if raw_output.startswith('```python'):
        raw_output = raw_output.replace('```python', '').replace('```', '').strip()
    
    # Parse the Python list syntax
    try:
        triplets = ast.literal_eval(raw_output)
        
    except (SyntaxError, ValueError) as e:
        print(f"Error parsing LLM output: {e}")
        print(f"Problematic outputs: {raw_output}")
        return []
    
    return triplets

def evaluate_triplets(relationships, model_name, prompt_version):
        """
        Generate evaluation template for manual review
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        eval_template = f"""
        ### Run: {model_name} - {timestamp}
        **Model:** {model_name}
        **Prompt Version:** {prompt_version}
        **Total Triplets:** {len(relationships)}

        #### Triplets for Evaluation:

        """
        for i, triplet in enumerate(relationships, 1):

            subject, predicate, obj = triplet
            eval_template += f"""
            {i}. `{triplet}`
            - Entity Accuracy: __/5
            - Relationship Accuracy: __/5
            - Type Consistency: __/5
            - Overall Quality: __/5
            - **Notes:** 
            """
                
            eval_template += """
            **Overall Run Score:** __/5
            **Best Triples:** 
            **Worst Triples:** 
            **Key Issues:** 
            **Recommendations:** 

            ---
            """
        
        return eval_template


def normalize_entity(e: str):
    """Normalize strings for comparison."""
    e = e.lower().strip()
    e = re.sub(r'[^a-z0-9\s]', '', e)
    e = re.sub(r'\s+', ' ', e)
    return e


def dedupe_entities(entity_dict: dict, threshold: float = 88.0) -> dict:
    """
    Deduplicate LLM-extracted entities using normalization + fuzzy similarity.
    Input format = {"entities": [...]}
    Output format = {"entities": [...]}
    """
    if "entities" not in entity_dict:
        return entity_dict

    entities = entity_dict["entities"]
    if not entities:
        return entity_dict

    normalized_map = {}  # normalized → original list
    final_entities = []

    for e in entities:
        norm = normalize_entity(e)

        matched = None
        for kept in normalized_map:
            score = fuzz.token_sort_ratio(norm, kept)
            if score >= threshold:
                matched = kept
                break

        if matched:
            normalized_map[matched].append(e)
        else:
            normalized_map[norm] = [e]

    # pick best representative for each group
    for norm_key, group in normalized_map.items():
        # choose longest entity (usually most descriptive)
        best = max(group, key=len)
        final_entities.append(best)

    return {"entities": final_entities}

if __name__ == "__main__":
    # Test URL
    url = "https://www.amazon.com/Amazon-vibrant-helpful-routines-Charcoal/dp/B09B8V1LZ3"
    
    # Run scraper
    scraped_data = asyncio.run(scrape_amazon(url))
    
    # Print results
    print("\n=== SCRAPED DATA ===\n")
    for key, value in scraped_data.items():
        if isinstance(value, list):
            print(f"{key}:")
            for item in value[:3]:  # Show first 3 items for lists
                print(f"  - {item}")
            if len(value) > 3:
                print(f"  ... and {len(value) - 3} more")
        else:
            print(f"{key}: {value}")
        print()

    
    # 2. Pass it into an LLM call for entity extraction
    print("\n=== STEP 2: ENTITY EXTRACTION ===\n")

    model_name = "gemma2:2b"
    
    # Extract entities using LLM
    entities = extract_entities(scraped_data, model=model_name)


    print("Extracted Entities:")
    print(json.dumps(entities, indent=2))


    #Remove duplicate entities
    entities = dedupe_entities(entities)
    
    # Print entities
    print("Extracted Entities:")
    print(json.dumps(entities, indent=2))
    
    # Optional: Save to file or disk
    output = {
        "scraped_data": scraped_data,
        "entities": entities
    }
    
    with open("extracted_entities.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print("\n Results saved to extracted_entities.json")

    # 3. Pass that output into another LLM call for relationship extraction
    print("\n=== STEP 3: RELATIONSHIP EXTRACTION ===\n")


    modelArr = ["gemma2:2b","llama3.2:1b", "gemma3:1b", "phi3:mini", "deepseek-r1:latest"]

    for modelName in modelArr:
        relationships = extract_relationships(entities, model=modelName)
    
        with open("relationship_extracted.txt", "w") as f:
            f.write(pprint.pformat(relationships, width=120))

        
        print("\n=== STEP 5: Generate Evaluation Template ===\n")
        
        eval_log = evaluate_triplets(relationships, modelName, "ecommerce_v1")

        with open(f"evaluation_log_{modelName.replace(':', '_')}.txt", "w") as f:
            f.write(eval_log)

        print(f"\nRelationship Evaluation for {modelName} saved to: evaluation_log_{modelName.replace(':', '_')}.txt")
    


