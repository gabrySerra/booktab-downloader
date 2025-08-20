#!/usr/bin/env python3
"""
Booktab Downloader

A Python script to download Zanichelli books from web Booktab platform as PDFs.
This script extracts individual PDF chapters from the Booktab web service and merges
them into a single PDF file.

Author: Enrico (gabrySerra)
License: MIT License
"""

import sys  
import requests
import base64
from xml.dom.minidom import parseString
from io import BytesIO, SEEK_SET, SEEK_END 
import PyPDF2
from typing import Iterator, Optional


class ResponseStream(object):
    """
    A file-like object that wraps HTTP response content for streaming PDF processing.
    
    This class allows PyPDF2 to read PDF data directly from an HTTP response stream
    without loading the entire PDF into memory at once. This is particularly useful
    for large PDF files as it reduces memory usage during download and processing.
    
    The class implements the necessary file-like interface methods (read, seek, tell)
    that PyPDF2.PdfFileReader expects, while internally managing the HTTP response
    stream and buffering data as needed.
    """
      
    def __init__(self, request_iterator: Iterator[bytes]) -> None:
        """
        Initialize the ResponseStream with an HTTP response iterator.
        
        Args:
            request_iterator: An iterator that yields chunks of bytes from an HTTP response
                             (typically from requests.Response.iter_content())
        """
        self._bytes = BytesIO() 
        self._iterator = request_iterator 
   
    def _load_all(self) -> None:
        """
        Load all remaining data from the HTTP response into the internal buffer.
        
        This method consumes the entire response stream and stores it in memory.
        It's called when we need to seek to the end of the file or read all data.
        """
        self._bytes.seek(0, SEEK_END) 
          
        for chunk in self._iterator: 
            self._bytes.write(chunk) 
   
    def _load_until(self, goal_position: int) -> None:
        """
        Load data from the HTTP response until we reach the specified position.
        
        This method incrementally loads data from the response stream until
        we have enough data to satisfy a read operation at the goal position.
        
        Args:
            goal_position: The byte position we need to reach in the buffer
        """
        current_position = self._bytes.seek(0, SEEK_END) 
          
        while current_position < goal_position: 
            try: 
                chunk = next(self._iterator)
                current_position += self._bytes.write(chunk) 
                  
            except StopIteration: 
                break
   
    def tell(self) -> int:
        """
        Return the current position in the stream.
        
        Returns:
            The current byte position in the stream
        """
        return self._bytes.tell() 
   
    def read(self, size: Optional[int] = None) -> bytes:
        """
        Read data from the stream.
        
        Args:
            size: Number of bytes to read. If None, read all remaining data.
        
        Returns:
            Bytes read from the stream
        """
        left_off_at = self._bytes.tell() 
          
        if size is None: 
            self._load_all() 
        else: 
            goal_position = left_off_at + size 
            self._load_until(goal_position) 
   
        self._bytes.seek(left_off_at) 
          
        return self._bytes.read(size) 
   
    def seek(self, position: int, whence: int = SEEK_SET) -> int:
        """
        Change the stream position to the given byte offset.
        
        Args:
            position: Byte position to seek to
            whence: How to interpret the position (SEEK_SET, SEEK_CUR, SEEK_END)
        
        Returns:
            The new absolute position
        """          
        if whence == SEEK_END: 
            self._load_all() 
        
        return self._bytes.seek(position, whence)



def main() -> None:
    """
    Main function that orchestrates the book download process.
    
    This function:
    1. Prompts user for authentication cookie and book ISBN
    2. Fetches book structure from Booktab API
    3. Downloads individual PDF chapters
    4. Merges all chapters into a single PDF file
    """
    # Get authentication cookie from user
    # The shibsession cookie is required to authenticate with the Booktab API
    # Users can find this cookie in their browser's developer tools after logging in
    print("=== Booktab PDF Downloader ===")
    print("Make sure you're logged into web.booktab.it first!")
    print()
    cookie = input("Paste the shibsession cookie: ")

    # Get the ISBN of the book to download
    # ISBN (International Standard Book Number) uniquely identifies the book
    isbn = input("Input the ISBN of the book you want to download: ")

    print("\nGathering information about the volume...")

    # Construct the authentication header with the shibsession cookie
    # This cookie maintains the user's authenticated session with Booktab
    auth_headers = {
        'Cookie': '_shibsession_626f6f6b746162776562687474703a2f2f7765622e626f6f6b7461622e69742f73686962626f6c657468=' + cookie
    }

    # First attempt: Try to fetch the book's spine.xml file
    # The spine.xml contains the structure and organization of the book chapters
    spine_url = f'http://web.booktab.it/boooks_web/{isbn}/spine.xml'
    spine = requests.get(spine_url, allow_redirects=False, headers=auth_headers)

    # Handle different response codes to provide meaningful error messages
    if spine.status_code == 302:
        print("❌ Error: Invalid shibsession cookie. Please check your cookie and try again.")
        print("   Make sure you copied the entire cookie value from your browser.")
        sys.exit(1) 
    elif spine.status_code != 200:
        # If spine.xml fails, try volume.xml as a fallback
        # Some books use volume.xml instead of spine.xml for their structure
        print("Spine.xml not found, trying volume.xml...")
        volume_url = f'http://web.booktab.it/boooks_web/{isbn}/volume.xml'
        spine = requests.get(volume_url, allow_redirects=False, headers=auth_headers)
        
        if spine.status_code == 302:
            print("❌ Error: Invalid shibsession cookie. Please check your cookie and try again.")
            sys.exit(1) 
        elif spine.status_code != 200:
            print(f"❌ Error: Invalid ISBN '{isbn}'. Please check the ISBN and try again.")
            print("   Make sure the book is available in your Booktab library.")
            sys.exit(1)

    print("✅ Book information retrieved successfully!")
    print("📖 Extracting chapter structure...")

    # Parse the XML response to extract book structure
    try:
        spine_xml = parseString(spine.text)
    except Exception as e:
        print(f"❌ Error parsing book structure: {e}")
        sys.exit(1)

    # Find all "unit" elements which represent individual chapters or sections
    parts = spine_xml.getElementsByTagName("unit")
    
    if not parts:
        print("❌ Error: No chapters found in this book.")
        sys.exit(1)

    print(f"📚 Found {len(parts)} chapters to download")

    # Initialize PDF merger to combine all chapters
    merger = PyPDF2.PdfFileMerger()

    print("⬇️  Downloading and processing chapters...")

    # Process each chapter/unit
    for i, part in enumerate(parts, 1):
        # Skip Flash-based content as it's not downloadable as PDF
        if part.getAttribute("features") == 'flash':
            print(f"   Chapter {i}: Skipping (Flash content)")
            continue

        print(f"   Chapter {i}/{len(parts)}: Processing...")

        # Get the chapter's unique identifier
        chapter_id = part.getAttribute("btbid")
        if not chapter_id:
            print(f"   Chapter {i}: Skipping (no chapter ID)")
            continue

        # Fetch the chapter's configuration file
        # config.xml contains metadata and file locations for the chapter
        config_url = f'http://web.booktab.it/boooks_web/{isbn}/{chapter_id}/config.xml'
        part_info = requests.get(config_url, headers=auth_headers)

        if part_info.status_code != 200:
            print(f"   Chapter {i}: Skipping (config not accessible)")
            continue

        try:
            # Parse the chapter configuration
            part_xml = parseString(part_info.text)
            
            # Extract the content key which identifies the main content file
            content_elements = part_xml.getElementsByTagName("content")
            if not content_elements or not content_elements[0].firstChild:
                print(f"   Chapter {i}: Skipping (no content key)")
                continue
                
            content_key = content_elements[0].firstChild.nodeValue

            # Find the PDF file URL in the entry elements
            pdf_url = ''
            pdf_key = content_key + ".pdf"
            
            for entry in part_xml.getElementsByTagName("entry"):
                if entry.getAttribute("key") == pdf_key and entry.firstChild:
                    pdf_url = entry.firstChild.nodeValue + ".pdf"
                    break

            if not pdf_url:
                print(f"   Chapter {i}: Skipping (PDF not found)")
                continue

        except Exception as e:
            print(f"   Chapter {i}: Skipping (error parsing config: {e})")
            continue

        # Download the PDF chapter
        try:
            chapter_pdf_url = f'http://web.booktab.it/boooks_web/{isbn}/{chapter_id}/{pdf_url}'
            pdf_response = requests.get(chapter_pdf_url, headers=auth_headers, stream=True)
            
            if pdf_response.status_code != 200:
                print(f"   Chapter {i}: Skipping (download failed)")
                continue

            # Add the PDF to the merger using our custom ResponseStream
            # This allows processing the PDF without loading it entirely into memory
            pdf_stream = ResponseStream(pdf_response.iter_content(chunk_size=8192))
            merger.append(PyPDF2.PdfFileReader(pdf_stream))
            print(f"   Chapter {i}: ✅ Downloaded")

        except Exception as e:
            print(f"   Chapter {i}: ❌ Error: {e}")
            continue

    # Save the merged PDF
    print("\n💾 Saving merged PDF...")
    try:
        output_filename = input("Input a title for the file: ").strip()
        if not output_filename:
            output_filename = f"booktab_{isbn}"
        
        # Ensure the filename ends with .pdf
        if not output_filename.lower().endswith('.pdf'):
            output_filename += '.pdf'
            
        merger.write(output_filename)
        print(f"✅ Successfully saved: {output_filename}")
        
    except Exception as e:
        print(f"❌ Error saving file: {e}")
        sys.exit(1)
    finally:
        merger.close()


if __name__ == "__main__":
    main()
