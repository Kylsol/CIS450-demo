# AI Alt Text Generator

## Description
This project is a web-based AI tool that generates captions and alt text for uploaded images. The goal is to improve accessibility by helping users quickly create meaningful alt text without having to write it manually.

The application allows users to upload one or more images and uses pretrained AI models to analyze the content. It then generates a caption, identifies objects in the image, and combines that information into structured alt text.

This project was built using Python, Flask, and Hugging Face Transformers.

---

## Design

### Project Approach (Prototyping Phase)

For this project, I took a prototyping approach where I started simple and built things up step by step. My original idea was actually a lot more complex—I wanted to process live video from an IP camera using OpenCV and possibly do things like motion detection or license plate recognition. After thinking it through, I realized that would take way more time than I had, so I pivoted to something more realistic but still meaningful: an AI-based image caption and alt text generator.

The main goal of this app is to help with accessibility by automatically generating alt text for images. I started by building a basic Flask app that could upload and display images. Once that was working, I added AI captioning using pretrained models, and then expanded it to include object detection and tags. From there, I focused on turning that raw output into something actually useful for alt text.

I built everything incrementally. I would get one piece working, test it, break it, fix it, and then move on to the next part. That helped a lot with debugging because I always knew what I had just changed when something stopped working.

---

### Research & External Resources

I relied mostly on official documentation and a few key resources while building this:

- Flask Documentation: https://flask.palletsprojects.com/  
- Hugging Face Transformers: https://huggingface.co/docs/transformers  
- Pillow (PIL): https://python-pillow.org/ 

These helped me understand how to handle file uploads, process images, and integrate AI models into a working web app.

---

### AI Usage

I used ChatGPT throughout this project mainly as a guide to help me understand problems and find the right direction, rather than just giving me final answers. Most of the time, I used it to figure out what I should be looking up or which tools and concepts were relevant.

For example, when I ran into issues, I would describe the problem to ChatGPT and ask questions like:
- “Why is my Flask form not working when I submit it?”
- “How do I handle multiple file uploads in Flask?”
- “What’s the best way to generate captions from images using AI?”

Based on those prompts, ChatGPT would suggest possible solutions or point me toward specific libraries or approaches. I would then use that information to look at official documentation (like Flask or Hugging Face) and implement the solution myself.

I also used ChatGPT to:
- Help debug issues when the app wasn’t behaving as expected  
- Clean up parts of my code when it became messy  
- Understand error messages and what they meant

Some example prompts I used include:
- “Help me build a Flask app that uploads images and uses Hugging Face for captions, what are some libraries I could use and what are the benefits and downsides to each”
- “After I press generate, nothing, the app clears the uploads and resets without any errors, where would the first place to troubleshoot be”
- “How do I loop through multiple uploaded images in Flask?”
- “How can I make this alt text more useful for accessibility?”

ChatGPT made development faster and helped me stay unstuck, but it wasn’t just copy and paste. I still had to test everything, fix errors, and make adjustments to fit my project. In most cases, I used it to understand the problem first, and then used documentation to confirm and apply the solution.

---

### Development Reflection (Early Investigation)

One thing I realized pretty quickly is that the hard part isn’t getting something to work—it’s getting it to work well. The basic version of this app came together pretty fast, but making it reliable and user-friendly took more time.

Most of the issues I ran into were things like handling file uploads, passing data correctly to the frontend, and cleaning up AI output so it was actually useful. The AI part worked early on, but refining the results into proper alt text took more effort.

This phase helped me build a strong foundation, and I plan to keep improving the UI and overall experience as I continue development.