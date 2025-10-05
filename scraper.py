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



#  page = await browser.new_page()
#         await page.goto(
#             'https://www.amazon.com/b?node=17938598011'
#         )
#         await page.wait_for_timeout(5000)

#         all_products = await page.query_selector_all(
#             '.s-card-container > .a-spacing-base'
#         )

#to run: uv run python scraper.py 