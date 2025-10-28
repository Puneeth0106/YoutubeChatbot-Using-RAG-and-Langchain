YouTube Transcript Q&A — Chrome extension

What this extension does

- Detects the YouTube video ID on the active youtube.com page.
- Opens your local Streamlit Q&A app with the video prefilled via a query parameter.

How to load (developer/unpacked)

1. Start your Streamlit app locally (if you want to connect to local dev):

```bash
source myenv/bin/activate
streamlit run Youtube_Chatbot/streamlit_app.py
```

2. Open Chrome and go to chrome://extensions
3. Enable "Developer mode" (top-right)
4. Click "Load unpacked" and select the folder:

   Langchain_prompts/Youtube_Chatbot/chrome_extension

5. Open any YouTube video page and click the extension icon. The popup will show the detected video id and an "Open Q&A" button.

Notes

- The extension opens the Streamlit app in a new tab with `?video_id=VIDEOID` appended to the URL.
- By default the popup targets `http://localhost:8501`. Change the URL in the popup if your Streamlit app is served elsewhere.
- This is a thin launcher; it does not call the Streamlit app API directly. The Streamlit app must be running and accept the `video_id` query parameter (the current `streamlit_app.py` reads it from the UI, or we can adapt it to pre-populate based on query params).

Potential enhancements

- Pre-fill the Streamlit UI automatically from query params (I can add that change).
- Make the extension call a REST endpoint on the server to start indexing in the background (requires adding an API endpoint to the app).
