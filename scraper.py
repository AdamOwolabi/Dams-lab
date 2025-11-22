import asyncio
from playwright.async_api import async_playwright


async def main():
    browsers = ['chromium', 'firefox', 'webkit']
    async with async_playwright() as p:
        for browser_type in browsers:
            browser = await p[browser_type].launch(headless=False)


            page = await browser.new_page()



            await page.goto('https://www.amazon.com/Amazon-vibrant-helpful-routines-Charcoal/dp/B09B8V1LZ3/ref=sr_1_2?crid=1F7IY81ZKSJRO&dib=eyJ2IjoiMSJ9.NsxhwOLVu_7aGdp5IvUXjabPueDGM6IK7SP92o2AdE3oJJiYRBTp7sLFvGfyLSsHMGv6ugcacFLAPxqAPWIVFNwktjBewbZhAf4pCJF25splBzwYD4MJ0EMY_folPNerTpcmKRElFs456HFF-LhGyp3wnPUyVA37_p2jd9htVk0zqi850eXAFDH_W1ktlKf-xMCQbeP6cGvTfGQAqAkIiN2mISFqBFdNRLdfuMlod4OFhJtk6zjO15pcIYUS8q3iFfSml_9AQJKzOF6-aZuHAOilwUss5xV2OCLeeVR-lPY.yHyQNF2QKNfkG2m7cZeVrzfrVnb4USIktcuH_F5drNQ&dib_tag=se&keywords=alexa&qid=1759091443&s=amazon-devices&sprefix=alex%2Camazon-devices%2C95&sr=1-2&ufe=app_do%3Aamzn1.fos.74097168-0c10-4b8a-b96b-8388a1a12daf&th=1')

            
            #await page.screenshot(path=f'py_{browser_type}.png', full_page=True)
            all_products = await page.query_selector_all('#productTitle')

            print(all_products)


            await page.wait_for_timeout(1000)

            await browser.close()

asyncio.run(main())


# import asyncio
# from playwright.async_api import async_playwright


# configurations = {
#     "selectors": {
#         "title": "#productTitle",
#         "integerPartOfPrice": ".a-price-whole", 
#         "decimalPartOfPrice": ".a-price-fraction",
#         "description": "#feature-bullets ul",
#         "images": "#altImages img",
#     }
# }

# async def scrape(configurations, URL):
#     async with async_playwright() as pw:
#         #loading up the browser and going to it, await making sure we get the actual site rather than a hexidecimal obj
#         browser = await pw.chromium.launch(headless=False)
#         page = await browser.new_page()
#         await page.goto(URL)
#         keyFeatures = {}
        
#         for keyword in configurations["selectors"]:
#             if keyword == "images":
#                 image_elements = await page.query_selector_all(configurations["selectors"][keyword])
#                 feature = [await img.get_attribute("src") for img in image_elements]
            
#             elif keyword == "description":
#                 desc_ul = await page.wait_for_selector(configurations["selectors"][keyword])
#                 li_elements = await desc_ul.query_selector_all("li")
#                 feature = [await li.inner_text() for li in li_elements]
            
#             else:
#                 featureElement = await page.wait_for_selector(configurations["selectors"][keyword])
#                 feature = await featureElement.inner_text()

#             keyFeatures[keyword] = feature
            
#         return keyFeatures
            
        
        
# if __name__ == "__main__":
#     keyFeatures = asyncio.run(scrape(configurations, "https://www.amazon.com/Amazon-vibrant-helpful-routines-Charcoal/dp/B09B8V1LZ3/ref=sr_1_2?crid=1F7IY81ZKSJRO&dib=eyJ2IjoiMSJ9.NsxhwOLVu_7aGdp5IvUXjabPueDGM6IK7SP92o2AdE3oJJiYRBTp7sLFvGfyLSsHMGv6ugcacFLAPxqAPWIVFNwktjBewbZhAf4pCJF25splBzwYD4MJ0EMY_folPNerTpcmKRElFs456HFF-LhGyp3wnPUyVA37_p2jd9htVk0zqi850eXAFDH_W1ktlKf-xMCQbeP6cGvTfGQAqAkIiN2mISFqBFdNRLdfuMlod4OFhJtk6zjO15pcIYUS8q3iFfSml_9AQJKzOF6-aZuHAOilwUss5xV2OCLeeVR-lPY.yHyQNF2QKNfkG2m7cZeVrzfrVnb4USIktcuH_F5drNQ&dib_tag=se&keywords=alexa&qid=1759091443&s=amazon-devices&sprefix=alex%2Camazon-devices%2C95&sr=1-2&ufe=app_do%3Aamzn1.fos.74097168-0c10-4b8a-b96b-8388a1a12daf&th=1"))
    
#     for feature in keyFeatures:
#         print(feature, ": ", keyFeatures[feature], '\n')


import asyncio
from playwright.async_api import async_playwright
import ollama


# 1. Get HTML content output from the scraper
# 2. Pass it into an LLM call for entity extraction
# 3. Pass that output into another LLM call for relationship extraction
# 4. Review and evaluate each result manually


#1.


configurations = {
    "selectors": {
        "title": "#productTitle",
        "integerPartOfPrice": ".a-price-whole", 
        "decimalPartOfPrice": ".a-price-fraction",
        "description": "#feature-bullets ul",
        "images": "#altImages img",
    }
}

async def scrape(configurations, URL):
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        page = await browser.new_page()

        await page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        keyFeatures = {}

        for keyword, selector in configurations["selectors"].items():
            try:
                if keyword == "description":
                    desc_ul = await page.query_selector(selector)
                    # debug: print(await desc_ul.inner_text()) or await desc_ul.inner_html()
                    if desc_ul:
                        li_elements = await desc_ul.query_selector_all("li")
                        feature = [await li.inner_text() for li in li_elements]
                        feature = [(await li.inner_text()).strip() for li in li_elements]
+                       feature = [f for f in feature if f]
                    else:
                        feature = []

                elif keyword == "images":
                    img_elements = await page.query_selector_all(selector)
                    feature = []
                    for img in img_elements:
                        src = await img.get_attribute("src") or await img.get_attribute("data-src")
                        if src:
                            feature.append(src)

                else:
                    elem = await page.query_selector(selector)
                    feature = await elem.inner_text() if elem else None

            except Exception as e:
                feature = f"ERROR: {type(e).__name__}: {e}"

            keyFeatures[keyword] = feature

        await browser.close()
        return keyFeatures
        

if __name__ == "__main__":

    # Initialize the Ollama client
    client = ollama.Client()
    model = "gemma2"
    keyFeatures = asyncio.run(scrape(configurations, "https://www.amazon.com/Amazon-vibrant-helpful-routines-Charcoal/dp/B09B8V1LZ3/ref=sr_1_2?crid=1F7IY81ZKSJRO&dib=eyJ2IjoiMSJ9.NsxhwOLVu_7aGdp5IvUXjabPueDGM6IK7SP92o2AdE3oJJiYRBTp7sLFvGfyLSsHMGv6ugcacFLAPxqAPWIVFNwktjBewbZhAf4pCJF25splBzwYD4MJ0EMY_folPNerTpcmKRElFs456HFF-LhGyp3wnPUyVA37_p2jd9htVk0zqi850eXAFDH_W1ktlKf-xMCQbeP6cGvTfGQAqAkIiN2mISFqBFdNRLdfuMlod4OFhJtk6zjO15pcIYUS8q3iFfSml_9AQJKzOF6-aZuHAOilwUss5xV2OCLeeVR-lPY.yHyQNF2QKNfkG2m7cZeVrzfrVnb4USIktcuH_F5drNQ&dib_tag=se&keywords=alexa&qid=1759091443&s=amazon-devices&sprefix=alex%2Camazon-devices%2C95&sr=1-2&ufe=app_do%3Aamzn1.fos.74097168-0c10-4b8a-b96b-8388a1a12daf&th=1"))
    
   
    for feature in keyFeatures:
        print(feature, ": ", keyFeatures[feature], '\n')

    
    # 2. Pass it into an LLM call for entity extraction



 

    
    # # Define the model and the input prompt
    # model = "gemma2"  # Replace with your model name
    # prompt = "can you parse the {keyFeatures} to allow me to extract any important entities that align with "

    # # Send the query to the model
    # response = client.generate(model=model, prompt=prompt)

    # # Print the response from the model
    # print("Response from Ollama:")
    # print(response.response)








