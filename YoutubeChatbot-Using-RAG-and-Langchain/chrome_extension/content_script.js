(() => {
  function getVideoIdFromUrl(url) {
    // video id is 11 chars
    const m = url.match(/[?&]v=([A-Za-z0-9_-]{11})/);
    if (m) return m[1];
    const m2 = url.match(/youtu\.be\/([A-Za-z0-9_-]{11})/);
    if (m2) return m2[1];
    return null;
  }

    let currentVideoId = getVideoIdFromUrl(window.location.href);

    // Write initial id to storage so popup can read it
    if (currentVideoId) {
      try { chrome.storage.local.set({ yt_video_id: currentVideoId }); } catch (e) {}
    }

    // Respond to popup requests with the latest id
    chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
      if (msg === 'GET_VIDEO_ID') {
        sendResponse({ videoId: currentVideoId });
      }
    });

    // Some YouTube navigation doesn't reload the page (SPA). Poll for URL changes
    // and update storage when the video id changes. Polling is simple and reliable.
    const POLL_INTERVAL_MS = 1000;
    setInterval(() => {
      try {
        const newId = getVideoIdFromUrl(window.location.href);
        if (newId !== currentVideoId) {
          currentVideoId = newId;
          chrome.storage.local.set({ yt_video_id: currentVideoId });
        }
      } catch (e) {
        // ignore
      }
    }, POLL_INTERVAL_MS);

    // Also update when the page becomes visible (user switches back to the tab)
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden) {
        try {
          const newId = getVideoIdFromUrl(window.location.href);
          if (newId !== currentVideoId) {
            currentVideoId = newId;
            chrome.storage.local.set({ yt_video_id: currentVideoId });
          }
        } catch (e) {}
      }
    });
})();
