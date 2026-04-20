# AI Alt Text Generator

## Description
This project is a web-based AI tool that generates captions, tags, and accessibility-friendly alt text for uploaded images. The goal is to improve accessibility by helping users quickly create meaningful alt text without having to write it manually.

The application allows users to upload one or more images and uses pretrained AI models to analyze the content. It generates a caption, detects objects within the image, and combines that information into structured, readable alt text.

This project was built using Python, Flask, and Hugging Face Transformers, along with computer vision models for captioning and object detection.

---

## Features
- Upload single or multiple images  
- AI-generated image captions  
- Object detection with bounding boxes  
- Keyword/tag generation from captions  
- Automatically generated accessibility-friendly alt text  
- Adjustable detection threshold for object filtering  

---

## Tech Stack
- **Backend:** Python, Flask  
- **AI Models:**  
  - BLIP (Salesforce) for image captioning  
  - DETR (Facebook) for object detection  
- **Libraries:**  
  - Hugging Face Transformers  
  - Pillow (PIL)  
  - Matplotlib  
  - PyTorch  

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
- PyTorch: https://pytorch.org/  
- Pillow (PIL): https://python-pillow.org/  

These helped me understand how to handle file uploads, process images, and integrate AI models into a working web app.

---

### AI Usage

I used ChatGPT throughout this project mainly as a guide to help me understand problems and find the right direction, rather than just giving me final answers. Most of the time, I used it to figure out what I should be looking up or which tools and concepts were relevant.

For example, when I ran into issues, I would describe the problem and ask questions like:
- “Why is my Flask form not working when I submit it?”  
- “How do I handle multiple file uploads in Flask?”  
- “What’s the best way to generate captions from images using AI?”  

Based on those prompts, I was guided toward possible solutions or relevant tools. I would then verify and implement those solutions using official documentation.

I also used AI to:
- Debug errors (especially with Transformers and model loading)  
- Understand pipeline differences and model requirements  
- Refactor messy code into cleaner structure  
- Improve how alt text is generated from raw model output  

Some example prompts I used include: 
- “My pipeline is throwing an unknown task error, what could be causing this?”  
- “Why does this model require text input?”  
- “How can I make this alt text more useful for accessibility?”  

ChatGPT made development faster and helped me stay unstuck, but it wasn’t just copy and paste. I still had to test everything, fix errors, and adapt solutions to fit my project.

---

### Development Reflection

One thing I realized pretty quickly is that the hard part isn’t getting something to work—it’s getting it to work well. The basic version of this app came together pretty fast, but making it reliable and user-friendly took more time.

A big challenge was working with AI models and understanding how different pipelines behave. For example, I ran into issues with mismatched pipeline tasks (`image-to-text` vs `image-text-to-text`) and missing dependencies like `timm` for object detection. Fixing these required digging into documentation and understanding how the models actually work rather than just calling them.

Another issue I ran into was moving the project from macOS (where I initially developed it) to Windows. Differences in Python versions, package installations, and command usage (such as `python` vs `python3`) caused unexpected errors. Some libraries also behaved differently or required additional dependencies on Windows. This forced me to better understand my environment setup and how to properly manage dependencies across platforms.

Most of the issues I ran into were things like:
- Handling file uploads correctly  
- Passing data between backend and frontend  
- Debugging model errors and environment issues  
- Cleaning up AI output so it was actually useful  

The AI part worked early on, but refining the results into proper, readable alt text took more effort.

This project helped me get more comfortable working with APIs, debugging real-world issues, and building something step by step. Going forward, I would like to improve the UI, optimize performance, and possibly expand this into a more polished accessibility tool.