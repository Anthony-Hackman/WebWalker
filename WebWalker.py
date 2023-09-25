import os
import random
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import asyncio
import tkinter as tk
from tkinter import ttk
import urllib3
import csv
from urllib.parse import urlparse

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Global variables
visited_urls = set()
crawl_executor = None
data = []
stop_event = None  # Define stop_event as a global variable
crawling = False

# Create a GUI window
window = tk.Tk()
window.title("World-Web-Walker")
window.geometry("600x200")

status_text = tk.StringVar()
current_site_text = tk.StringVar()
animated_status_text = tk.StringVar()
current_site_label = None  # Define current_site_label as a global variable

# Function to format the current time as a string
def current_time():
    now = datetime.now()
    return now.strftime('%Y-%m-%d %H:%M:%S')

# Function to update the status text with animated periods
def update_status_text(periods):
    status = "Walking" + "." * periods
    animated_status_text.set(status)
    periods = (periods + 1) % 4
    window.after(1000, update_status_text, periods)

# Function to search for keywords in HTML content
def find_keywords(html_content, keywords):
    soup = BeautifulSoup(html_content, 'lxml')
    found_keywords = [keyword for keyword in keywords if keyword in html_content]
    return found_keywords

# Function to check if a URL is valid
def is_valid_url(url):
    parsed_url = urlparse(url)
    return parsed_url.scheme in ('http', 'https') and parsed_url.netloc.endswith('.com')

# Function to export data to CSV
def export_to_csv(data, visited_urls):
    create_results_directory()  # Create the 'Scrape Results' directory if it doesn't exist

    now = datetime.now()
    timestamp = now.strftime('%Y-%m-%d_%H-%M-%S')
    output_file = os.path.join('Scrape Results', f'crawler_output_{timestamp}.csv')

    with open(output_file, mode='w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow(['Date', 'Error Code', 'Keyword', 'URL'])
        for item in data:
            csv_writer.writerow([item[0], item[1], item[2], item[3]])
        csv_writer.writerow([])
        csv_writer.writerow(['Visited URLs:'])
        for url in visited_urls:
            csv_writer.writerow([url])

    status_text.set(f"Data saved to CSV file: {output_file}")

# Function to create the 'Scrape Results' directory if it doesn't exist
def create_results_directory():
    if not os.path.exists('Scrape Results'):
        os.makedirs('Scrape Results')

# Function to perform web crawling
async def crawl_async(start_url, keywords):
    global data, visited_urls, crawling, stop_event

    try:
        # Validate the start_url before proceeding
        if not is_valid_url(start_url):
            return  # Skip invalid URLs

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        }
        response = requests.get(start_url, headers=headers, verify=False)

        if response.status_code == 200:
            html_content = response.text
            found_keywords = find_keywords(html_content, keywords)

            for keyword in found_keywords:
                data.append([current_time(), "", keyword, start_url])

            visited_urls.add(start_url)
            current_site_text.set(f"Current Site: {start_url}")

            soup = BeautifulSoup(html_content, 'lxml')
            links = soup.find_all('a')
            for link in links:
                href = link.get('href')
                if href and href.startswith('http') and href not in visited_urls:
                    if crawling and not stop_event.is_set():
                        await crawl_async(href, keywords)
                    else:
                        return

            await asyncio.sleep(1 + 2 * random.random())

    except Exception as e:
        error_code = str(e)
        data.append([current_time(), error_code, "", start_url])
        print(f"[{current_time()}] Error: {e}")

    finally:
        if crawling:
            crawling = False

# Function to start or stop crawling
def toggle_crawling():
    global crawl_executor, visited_urls, data, current_site_label, crawling, stop_event

    if crawl_executor is None:
        start_url = start_url_entry.get()
        if not start_url:
            status_text.set("Please enter a valid starting URL.")
            return

        keyword_input = keyword_entry.get()
        keywords = [keyword.strip() for keyword in keyword_input.split(',')]
        visited_urls.clear()
        data.clear()
        stop_event = asyncio.Event()  # Create a new stop event
        crawling = True

        status_text.set("Walking...")  # Set status to "Walking..."
        crawl_button.config(text="Stop Walking")
        animated_status_text.set("")
        animated_status_label.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        update_status_text(0)

        # Add or update the "Current Site" label
        if current_site_label:
            current_site_label.grid_forget()
        current_site_label = ttk.Label(window, textvariable=current_site_text, anchor="w", width=75)
        current_site_label.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="w")

        loop = asyncio.get_event_loop()
        crawl_executor = loop.create_task(crawl_async(start_url, keywords))

    else:
        # Set the stop event to stop the crawling process gracefully
        stop_event.set()
        crawl_button.config(text="Stopping...")
        status_text.set("Stopping...")

url_label = ttk.Label(window, text="Starting URL:")
start_url_entry = ttk.Entry(window, width=50)
keyword_label = ttk.Label(window, text="Keywords (comma-separated):")
keyword_entry = ttk.Entry(window, width=30)
crawl_button = ttk.Button(window, text="Start Walking", command=toggle_crawling)

status_frame = ttk.LabelFrame(window, text="Status")
status_label = ttk.Label(status_frame, textvariable=status_text, anchor="w")
animated_status_label = ttk.Label(status_frame, textvariable=animated_status_text, anchor="w")

url_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
start_url_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
status_label.grid(row=0, column=2, padx=5, pady=5, sticky="w")
keyword_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
keyword_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
status_frame.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky="w")
crawl_button.grid(row=4, column=0, columnspan=3, padx=5, pady=5, sticky="w")

# Function to update the progress bar
def update_progress_bar():
    total_urls = len(visited_urls)
    if total_urls > 0:
        crawled_urls = len(data)
        progress = min(crawled_urls / total_urls * 100, 100)
        progress_bar["value"] = progress
    window.after(1000, update_progress_bar)

# Progress bar
progress_bar = ttk.Progressbar(window, orient="horizontal", length=200, mode="determinate")
progress_bar.grid(row=5, column=0, columnspan=3, padx=10, pady=10)
update_progress_bar()

window.mainloop()