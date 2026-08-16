import asyncio
from playwright.async_api import async_playwright
import subprocess
import time
import os

async def main():
    # Start streamlit app in background
    with open('test_st.py', 'w') as f:
        f.write('import streamlit as st\n')
        f.write('st.sidebar.radio("Test", ["Dashboard", "Infrastructure"])\n')
        
    p = subprocess.Popen(['.\\.venv\\Scripts\\python.exe', '-m', 'streamlit', 'run', 'test_st.py', '--server.port', '8505', '--server.headless', 'true'])
    
    # Wait for it to start
    time.sleep(5)
    
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await browser.new_page()
        await page.goto('http://localhost:8505')
        
        # Wait for the radio group to load
        await page.wait_for_selector('div[role="radiogroup"]')
        
        # Get the HTML of the first label
        html = await page.evaluate('''() => {
            const el = document.querySelector('div[role="radiogroup"] label');
            return el ? el.outerHTML : "Not found";
        }''')
        
        with open('streamlit_radio.html', 'w', encoding='utf-8') as f:
            f.write(html)
            
        await browser.close()
        
    p.terminate()

if __name__ == '__main__':
    asyncio.run(main())
