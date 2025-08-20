# Booktab Downloader

A Python script to download your Zanichelli books from web Booktab platform as PDFs.

This tool allows you to create personal backup copies of your digital textbooks by downloading individual chapter PDFs from the Booktab web service and merging them into a single, complete PDF file.

## Important Notes

- **Compatibility**: This script works with the classic web Booktab reader. It does **not** work with the newer Kitaboo reader. For Kitaboo books, please use [kitaboo-downloader](https://github.com/Leone25/kitaboo-downloader) instead.
- **Legal Disclaimer**: You are responsible for ensuring your use complies with local laws and the terms of service. This tool is intended for creating personal backup copies of books you legitimately own access to.

## How It Works

The script works by:

1. **Authentication**: Uses your browser's session cookie to authenticate with Booktab
2. **Book Structure Discovery**: Fetches the book's structure from `spine.xml` or `volume.xml`
3. **Chapter Enumeration**: Identifies all available chapters/units in the book
4. **Individual Downloads**: Downloads each chapter as a separate PDF
5. **Merging**: Combines all chapter PDFs into a single, complete book PDF
6. **Memory Efficient**: Uses streaming to handle large PDFs without excessive memory usage

## Requirements

- Python 3.6 or higher
- Internet connection
- Valid Booktab account with access to the book you want to download

## Installation

1. **Download this repository**:
   ```bash
   git clone https://github.com/gabrySerra/booktab-downloader.git
   cd booktab-downloader
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Step 1: Run the Script
```bash
python3 main.py
```

### Step 2: Get Your Authentication Cookie

1. Open [Booktab Web](http://web.booktab.it/) in your browser and log in
2. Open your browser's Developer Tools (F12)
3. Navigate to the **Application** tab (Chrome) or **Storage** tab (Firefox)
4. In the sidebar, expand **Cookies** and click on `web.booktab.it`
5. Look for a cookie with "shibsession" in its name
6. Copy the entire **Value** of this cookie
7. Paste it into the terminal when prompted

![Cookie Location Reference](cookie.png)

### Step 3: Enter Book ISBN

1. Find the ISBN of the book you want to download (usually visible in your Booktab library)
2. Enter the ISBN when prompted
3. The script will validate the ISBN and check your access

### Step 4: Download Process

The script will:
- Verify your authentication and book access
- Analyze the book structure and identify chapters
- Display progress as it downloads each chapter
- Skip any chapters that aren't available as PDFs (e.g., Flash content)

### Step 5: Save Your Book

- When download completes, you'll be prompted for a filename
- Enter a descriptive name for your book (`.pdf` extension will be added automatically)
- The merged PDF will be saved in the same directory as the script

## Technical Details

### ResponseStream Class

The script includes a custom `ResponseStream` class that enables memory-efficient PDF processing:

- **Purpose**: Allows PyPDF2 to read PDF data directly from HTTP response streams
- **Benefit**: Reduces memory usage by not loading entire PDFs into RAM at once
- **Implementation**: Provides a file-like interface with `read()`, `seek()`, and `tell()` methods

### Error Handling

The script includes comprehensive error handling for common issues:

- **Invalid cookies**: Clear error messages with guidance for resolution
- **Missing books**: Verification that the ISBN exists in your library
- **Network issues**: Graceful handling of connection problems
- **Corrupted chapters**: Automatic skipping of problematic content
- **File system errors**: Protection against invalid filenames and permissions

### API Endpoints

The script interacts with several Booktab API endpoints:

- `spine.xml` or `volume.xml`: Book structure and chapter organization
- `config.xml`: Individual chapter metadata and file locations
- PDF endpoints: Direct chapter content downloads

## Troubleshooting

### "Invalid shibsession cookie"
- Ensure you're logged into Booktab in the same browser session
- Copy the complete cookie value, including any special characters
- The cookie expires; you may need to get a fresh one

### "Invalid ISBN"
- Verify the ISBN matches exactly what's shown in your Booktab library
- Ensure you have access to the book (it appears in your personal library)
- Some books may not be available for download

### "No chapters found"
- Some books may use different structural formats
- Verify the book is accessible through the web interface
- Contact support if the issue persists

### Download Failures
- Check your internet connection stability
- Some chapters may be unavailable (Flash content, restricted access)
- The script will skip problematic chapters and continue with others

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for:

- Bug fixes and improvements
- Additional error handling
- Support for different book formats
- Documentation enhancements

## Disclaimer

This software is provided "as is" for educational and personal backup purposes. Users are responsible for ensuring their use complies with:

- Local copyright laws
- Booktab's terms of service  
- Their institution's acceptable use policies

The authors are not responsible for any misuse of this software.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
