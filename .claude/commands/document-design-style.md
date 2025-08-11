---
description: Create or update a design style documentation page with screenshots and examples
---

You are creating/updating a design style documentation page. Follow these steps:

1. **Get the design style name** from the user (e.g., "minimalist", "glassmorphism", "art deco", etc.)

2. **Create the file structure** at `designs/[StyleName].md` with this format:
   ```markdown
   ---
   class: Design Style
   thumbnail: [will be added from first screenshot]
   summary: [Brief description of the style's key characteristics]
   ---
   
   # Screenshots
   [4 screenshot images in a row]
   
   # Websites
   
   ### [Website Name]
   [URL]
   [Brief description of how it uses this style]
   ```

3. **Search for screenshots using DuckDuckGo image search via Playwright MCP**:
   - Use search query: "[style name] web design examples website screenshots"
   - Navigate to DuckDuckGo Images
   - Click on 4-5 preview images to get larger versions
   - Extract the image URLs from the larger previews
   - Add these as inline images in the Screenshots section

4. **Search for example websites**:
   - Use web search to find 5-8 real websites that exemplify this design style
   - For each website, include:
     - The website name as a heading
     - The full URL
     - A brief description of how it demonstrates the style's characteristics

5. **Format considerations**:
   - Use inline images with `![example|500](url)` format
   - Put 4 images on one line separated by spaces
   - Keep descriptions concise and focused on the design elements
   - Use the first screenshot URL as the thumbnail in the frontmatter

6. **If updating an existing file**:
   - Preserve any existing content that's still relevant
   - Update screenshots if they're broken or outdated
   - Add new website examples while keeping good existing ones

Example usage: "Document the glassmorphism design style"